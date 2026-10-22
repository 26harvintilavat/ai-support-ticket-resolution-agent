"""Tests for deterministic, source-offset-preserving document chunking."""

import pytest

from app.ingestion.chunker import DocumentChunker
from app.ingestion.contracts import DocumentChunk, SourceDocument


def _document(
    text: str,
    source_id: str = "guides/help.md",
) -> SourceDocument:
    return SourceDocument(
        source_id=source_id,
        text=text,
    )


def _assert_exact_coverage(
    document: SourceDocument,
    chunks: list[DocumentChunk],
) -> None:
    covered: set[int] = set()

    for index, chunk in enumerate(chunks):
        assert chunk.source_id == document.source_id
        assert chunk.chunk_index == index

        assert chunk.text == document.text[chunk.start_char : chunk.end_char]

        assert chunk.text.strip()

        covered.update(range(chunk.start_char, chunk.end_char))

    assert all(character.isspace() or i in covered for i, character in enumerate(document.text))


def test_short_document_is_one_exact_chunk() -> None:
    document = _document("\ufeff# Reset\r\n\r\nUse the link.\r\n")

    chunks = DocumentChunker().chunk(document)

    assert len(chunks) == 1
    assert chunks[0].text == "# Reset\n\nUse the link."
    assert chunks[0].start_char == 0
    assert chunks[0].end_char == len(chunks[0].text)
    assert chunks[0].section_title == "Reset"

    _assert_exact_coverage(document, chunks)


def test_document_hash_and_text_are_not_changed() -> None:
    document = _document("  # Title  \n\n  Some   spaced  text.  \n")

    original_text = document.text
    checksum = document.content_sha256

    chunker = DocumentChunker(
        max_chunk_chars=14,
        overlap_chars=3,
    )

    chunks = chunker.chunk(document)

    _assert_exact_coverage(document, chunks)

    assert document.text == original_text
    assert document.content_sha256 == checksum


def test_markdown_prefers_section_boundary_without_cross_section_overlap() -> None:
    first = "# Alpha\n\n" + "Intro facts here.\n"
    second = "## Beta\n\n" + "The second section has its own content."

    document = _document(first + second)

    boundary = document.text.index("## Beta")

    chunker = DocumentChunker(
        max_chunk_chars=60,
        overlap_chars=12,
    )

    chunks = chunker.chunk(document)

    assert chunks[0].end_char <= boundary
    assert chunks[1].start_char == boundary
    assert chunks[0].section_title == "Alpha"
    assert chunks[1].section_title == "Beta"

    _assert_exact_coverage(document, chunks)


def test_long_paragraph_is_split_and_overlapped() -> None:
    document = _document(
        "Rotate your access key before retrying. " * 20,
        "guide.txt",
    )

    chunker = DocumentChunker(
        max_chunk_chars=80,
        overlap_chars=20,
    )

    chunks = chunker.chunk(document)

    assert len(chunks) > 1

    assert any(
        later.start_char < earlier.end_char
        for earlier, later in zip(chunks, chunks[1:], strict=False)
    )

    assert all(len(chunk.text) <= 80 for chunk in chunks)

    _assert_exact_coverage(document, chunks)


def test_plain_text_has_no_markdown_section_titles() -> None:
    document = _document(
        "# Looks like a heading\n\n" + "a " * 80,
        "faq.txt",
    )

    chunker = DocumentChunker(
        max_chunk_chars=45,
        overlap_chars=8,
    )

    chunks = chunker.chunk(document)

    assert all(chunk.section_title is None for chunk in chunks)

    _assert_exact_coverage(document, chunks)


def test_fenced_code_headings_are_ignored() -> None:
    document = _document(
        "# Real\n\n```bash\n## Fake inside code\n```\n\n## Actual\n\n" + "More details. " * 12
    )

    chunker = DocumentChunker(
        max_chunk_chars=65,
        overlap_chars=10,
    )

    chunks = chunker.chunk(document)

    assert all(chunk.section_title != "Fake inside code" for chunk in chunks)

    assert any(chunk.section_title == "Actual" for chunk in chunks)

    _assert_exact_coverage(document, chunks)


def test_heading_metadata_is_bounded() -> None:
    document = _document("## " + "A" * 230 + " ###\n\nSome text.")

    chunker = DocumentChunker(
        max_chunk_chars=500,
        overlap_chars=0,
    )

    chunks = chunker.chunk(document)

    assert chunks[0].section_title == "A" * 200

    _assert_exact_coverage(document, chunks)


def test_empty_heading_does_not_become_metadata() -> None:
    document = _document("#\n\nSome text.")

    chunks = DocumentChunker().chunk(document)

    assert chunks[0].section_title is None

    _assert_exact_coverage(document, chunks)


def test_trailing_whitespace_and_long_blank_runs_do_not_create_blank_chunks() -> None:
    document = _document("Start" + " \n" * 100 + "Finish\n\n    ")

    chunker = DocumentChunker(
        max_chunk_chars=30,
        overlap_chars=5,
    )

    chunks = chunker.chunk(document)

    assert all(chunk.text.strip() for chunk in chunks)

    assert chunks[-1].text == "Finish"

    _assert_exact_coverage(document, chunks)


def test_long_unbroken_words_cannot_be_lost() -> None:
    document = _document(
        "Q" * 211,
        "faq.txt",
    )

    chunker = DocumentChunker(
        max_chunk_chars=31,
        overlap_chars=9,
    )

    chunks = chunker.chunk(document)

    assert len(chunks) > 1

    assert all(len(chunk.text) <= 31 for chunk in chunks)

    _assert_exact_coverage(document, chunks)


def test_unicode_character_offsets_are_python_character_indices() -> None:
    document = _document(
        "🔑 Restart सेवा. " * 20,
        "guide.txt",
    )

    chunker = DocumentChunker(
        max_chunk_chars=28,
        overlap_chars=5,
    )

    chunks = chunker.chunk(document)

    _assert_exact_coverage(document, chunks)

    assert len(chunks) >= 2


def test_repeated_execution_is_deterministic() -> None:
    document = _document("# Steps\n\n" + "Do the next action.\n\n" * 35)

    chunker = DocumentChunker(
        max_chunk_chars=63,
        overlap_chars=12,
    )

    first = chunker.chunk(document)
    second = chunker.chunk(document)

    assert first == second

    _assert_exact_coverage(document, first)


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        0,
        -1,
        2.5,
        "100",
    ],
)
def test_invalid_chunk_sizes_are_rejected(
    value: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="max_chunk_chars",
    ):
        DocumentChunker(
            max_chunk_chars=value,
            overlap_chars=0,
        )


@pytest.mark.parametrize(
    "value",
    [
        True,
        -1,
        26,
        1.5,
        "5",
    ],
)
def test_invalid_overlap_is_rejected(
    value: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="overlap_chars",
    ):
        DocumentChunker(
            max_chunk_chars=50,
            overlap_chars=value,
        )


def test_wrong_input_type_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="SourceDocument",
    ):
        DocumentChunker().chunk("some string")
