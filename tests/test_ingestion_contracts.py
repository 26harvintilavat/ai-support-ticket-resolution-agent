"""Tests for Phase 2's document and chunk data contracts."""

import hashlib

import pytest
from pydantic import ValidationError

from app.ingestion.contracts import DocumentChunk, SourceDocument


def test_document_normalizes_text_and_computes_checksum() -> None:
    document = SourceDocument(
        source_id="guides/authentication.md",
        text="\ufeff# Authentication\r\nRestart after rotation.\r",
        title="Authentication",
    )

    expected_text = "# Authentication\nRestart after rotation.\n"

    assert document.text == expected_text
    assert document.document_type == "markdown"
    assert document.content_sha256 == hashlib.sha256(expected_text.encode("utf-8")).hexdigest()

    assert document.model_dump()["content_sha256"] == document.content_sha256


def test_plain_text_document_type() -> None:
    document = SourceDocument(
        source_id="faq/errors.TXT",
        text="Error 401",
    )

    assert document.document_type == "text"
    assert document.title is None


@pytest.mark.parametrize(
    "source_id",
    [
        "",
        "/absolute/auth.md",
        "../secrets.md",
        "guides/../secrets.md",
        "guides//auth.md",
        "guides/./auth.md",
        r"guides\auth.md",
        "C:/guides/auth.md",
        "guides/auth.pdf",
        " guides/auth.md",
    ],
)
def test_invalid_source_ids_are_rejected(source_id: str) -> None:
    with pytest.raises(ValidationError):
        SourceDocument(
            source_id=source_id,
            text="Valid content",
        )


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   \n  ",
        "text\x00invalid",
    ],
)
def test_invalid_document_text_is_rejected(text: str) -> None:
    with pytest.raises(ValidationError):
        SourceDocument(
            source_id="guide.md",
            text=text,
        )


def test_unexpected_document_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        SourceDocument.model_validate(
            {
                "source_id": "guide.md",
                "text": "Hello",
                "unexpected": "value",
            }
        )


def test_chunk_accepts_exact_text_offsets() -> None:
    document = SourceDocument(
        source_id="guides/auth.md",
        text="Intro\nRestart services",
    )

    start = document.text.index("Restart")
    chunk_text = document.text[start:]

    chunk = DocumentChunk(
        source_id=document.source_id,
        chunk_index=0,
        text=chunk_text,
        start_char=start,
        end_char=len(document.text),
        section_title="Rotation",
    )

    assert document.text[chunk.start_char : chunk.end_char] == chunk.text
    assert chunk.chunk_index == 0


@pytest.mark.parametrize(
    "override",
    [
        {"chunk_index": -1},
        {"chunk_index": 1.5},
        {"start_char": -1},
        {"end_char": 0},
        {"end_char": 6},
        {"text": "  "},
        {"section_title": ""},
    ],
)
def test_invalid_chunks_are_rejected(override: dict) -> None:
    data = {
        "source_id": "guide.md",
        "chunk_index": 0,
        "text": "hello",
        "start_char": 0,
        "end_char": 5,
    }

    data.update(override)

    with pytest.raises(ValidationError):
        DocumentChunk.model_validate(data)
