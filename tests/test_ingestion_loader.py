"""Focused file-loading tests; no PostgreSQL or external services needed."""

import hashlib

import pytest

from app.ingestion.loader import DocumentLoader, DocumentLoadError


def test_load_markdown_normalizes_text_and_derives_metadata(tmp_path) -> None:
    root = tmp_path / "docs"
    (root / "guides").mkdir(parents=True)
    (root / "guides" / "authentication.md").write_bytes(
        b"\xef\xbb\xbf# API Authentication\r\n\r\nUse a valid key.\r\n"
    )

    document = DocumentLoader(root).load("guides/authentication.md")

    assert document.source_id == "guides/authentication.md"
    assert document.title == "API Authentication"
    assert document.document_type == "markdown"
    assert document.text == "# API Authentication\n\nUse a valid key.\n"
    assert document.content_sha256 == hashlib.sha256(document.text.encode()).hexdigest()


def test_load_plain_text_uses_filename_for_title(tmp_path) -> None:
    (tmp_path / "troubleshooting.TXT").write_text("Restart the service.\n", encoding="utf-8")

    document = DocumentLoader(tmp_path).load("troubleshooting.TXT")

    assert document.document_type == "text"
    assert document.title == "troubleshooting"
    assert document.text == "Restart the service.\n"


def test_load_all_is_sorted_recursive_and_ignores_other_extensions(tmp_path) -> None:
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "z.txt").write_text("Z", encoding="utf-8")
    (tmp_path / "a.md").write_text("# A", encoding="utf-8")
    (tmp_path / "ignored.pdf").write_bytes(b"not supported")
    loader = DocumentLoader(tmp_path)

    first = loader.load_all()
    second = loader.load_all()

    assert [doc.source_id for doc in first] == ["a.md", "nested/z.txt"]
    assert [doc.content_sha256 for doc in first] == [doc.content_sha256 for doc in second]


@pytest.mark.parametrize(
    "source_id",
    [
        "../secrets.md",
        "nested/../../secrets.md",
        "/absolute.md",
        "C:/secrets.md",
        r"nested\secrets.md",
        "nested//oops.md",
        "./oops.md",
        "archive.pdf",
        "a.md ",
        "a" * 513 + ".md",
    ],
)
def test_reject_invalid_source_ids(tmp_path, source_id: str) -> None:
    with pytest.raises(DocumentLoadError, match="Invalid document source_id"):
        DocumentLoader(tmp_path).load(source_id)


@pytest.mark.parametrize("payload", [b"", b" \n\t ", b"Valid\x00invalid"])
def test_reject_empty_or_invalid_content(tmp_path, payload: bytes) -> None:
    (tmp_path / "bad.txt").write_bytes(payload)

    with pytest.raises(DocumentLoadError, match="Invalid document content"):
        DocumentLoader(tmp_path).load("bad.txt")


def test_reject_invalid_utf8(tmp_path) -> None:
    (tmp_path / "bad.md").write_bytes(b"\xff\xfe")

    with pytest.raises(DocumentLoadError, match="not valid UTF-8"):
        DocumentLoader(tmp_path).load("bad.md")


def test_reject_large_document(tmp_path) -> None:
    (tmp_path / "large.txt").write_bytes(b"a" * 11)

    with pytest.raises(DocumentLoadError, match="exceeds 10 byte limit"):
        DocumentLoader(tmp_path, max_file_bytes=10).load("large.txt")


def test_accept_file_exactly_at_size_limit(tmp_path) -> None:
    (tmp_path / "exact.txt").write_bytes(b"a" * 10)

    assert DocumentLoader(tmp_path, max_file_bytes=10).load("exact.txt").text == "a" * 10


def test_reject_invalid_size_limit(tmp_path) -> None:
    for value in (0, -1, True, 1.5):
        with pytest.raises(ValueError, match="positive integer"):
            DocumentLoader(tmp_path, max_file_bytes=value)


def test_reject_missing_root_or_regular_file_as_root(tmp_path) -> None:
    (tmp_path / "file.md").write_text("hello", encoding="utf-8")
    with pytest.raises(DocumentLoadError):
        DocumentLoader(tmp_path / "missing")
    with pytest.raises(DocumentLoadError):
        DocumentLoader(tmp_path / "file.md")


def test_reject_missing_document_or_directory(tmp_path) -> None:
    (tmp_path / "directory.md").mkdir()
    loader = DocumentLoader(tmp_path)

    with pytest.raises(DocumentLoadError):
        loader.load("missing.md")
    with pytest.raises(DocumentLoadError):
        loader.load("directory.md")


def test_changed_contents_change_checksum_but_not_source_id(tmp_path) -> None:
    path = tmp_path / "same.md"
    path.write_text("Old", encoding="utf-8")
    loader = DocumentLoader(tmp_path)
    first = loader.load("same.md")

    path.write_text("New", encoding="utf-8")
    second = loader.load("same.md")

    assert first.source_id == second.source_id
    assert first.content_sha256 != second.content_sha256


def test_symlinked_file_is_rejected(tmp_path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    target = tmp_path / "outside.md"
    target.write_text("Secret", encoding="utf-8")

    try:
        (root / "linked.md").symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is not available on this machine")

    loader = DocumentLoader(root)
    with pytest.raises(DocumentLoadError, match="Symlinks"):
        loader.load("linked.md")
    with pytest.raises(DocumentLoadError, match="Symlinks"):
        loader.load_all()


def test_symlinked_directory_is_rejected(tmp_path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    external = tmp_path / "outside"
    external.mkdir()
    (external / "hidden.md").write_text("Secret", encoding="utf-8")
    try:
        (root / "link").symlink_to(external, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is not available on this machine")

    loader = DocumentLoader(root)
    with pytest.raises(DocumentLoadError, match="Symlinks"):
        loader.load("link/hidden.md")
    with pytest.raises(DocumentLoadError, match="Linked directory"):
        loader.load_all()
