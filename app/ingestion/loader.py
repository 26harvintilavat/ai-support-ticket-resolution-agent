"""Load trusted local markdown and text files into ingestion contracts."""

import os
import stat
from pathlib import Path, PurePosixPath

from pydantic import TypeAdapter, ValidationError

from app.ingestion.contracts import SourceDocument, SourceId

DEFAULT_MAX_FILE_BYTES = 2 * 1024 * 1024
_SUPPORTED_EXTENSIONS = (".md", ".txt")
_SOURCE_ID_ADAPTER = TypeAdapter(SourceId)


class DocumentLoadError(ValueError):
    """A document cannot be safely loaded as a SourceDocument."""


def _is_link_or_junction(path: Path) -> bool:
    return path.is_symlink() or path.is_junction()


def _on_walk_error(error: OSError) -> None:
    raise DocumentLoadError(f"Unable to scan documentation directory: {error}") from error


class DocumentLoader:
    """Read bounded UTF-8 documentation beneath one configured directory.

    Does not chunk, embed, persist, or delete documents.
    """

    def __init__(
        self,
        root: str | Path,
        *,
        max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    ) -> None:
        if isinstance(max_file_bytes, bool) or not isinstance(max_file_bytes, int):
            raise ValueError("max_file_bytes must be a positive integer")
        if max_file_bytes <= 0:
            raise ValueError("max_file_bytes must be a positive integer")

        root_path = Path(root).expanduser()
        try:
            resolved_root = root_path.resolve(strict=True)
        except OSError as exc:
            raise DocumentLoadError(f"Cannot access documentation root: {root_path}") from exc

        if not resolved_root.is_dir():
            raise DocumentLoadError(f"Documentation root is not a directory: {root_path}")

        self.root = resolved_root
        self.max_file_bytes = max_file_bytes

    def _file_path(self, source_id: str) -> Path:
        """Validate a canonical source ID before touching the filesystem."""
        try:
            _SOURCE_ID_ADAPTER.validate_python(source_id)
        except ValidationError as exc:
            raise DocumentLoadError(f"Invalid document source_id: {source_id!r}") from exc

        path = self.root
        for segment in source_id.split("/"):
            path = path / segment
            if _is_link_or_junction(path):
                raise DocumentLoadError(f"Symlinks and junctions are not supported: {source_id}")

        try:
            resolved_path = path.resolve(strict=True)
        except OSError as exc:
            raise DocumentLoadError(f"Cannot access document: {source_id}") from exc

        if not resolved_path.is_relative_to(self.root):
            raise DocumentLoadError(f"Document escapes the configured root: {source_id}")
        if not resolved_path.is_file():
            raise DocumentLoadError(f"Document is not a regular file: {source_id}")

        return resolved_path

    def load(self, source_id: str) -> SourceDocument:
        """Read and validate one document using its root-relative POSIX path."""
        path = self._file_path(source_id)
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)

        try:
            with os.fdopen(os.open(path, flags), "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise DocumentLoadError(f"Document is not a regular file: {source_id}")

                payload = stream.read(self.max_file_bytes + 1)
        except OSError as exc:
            raise DocumentLoadError(f"Cannot read document: {source_id}") from exc

        if len(payload) > self.max_file_bytes:
            raise DocumentLoadError(
                f"Document exceeds {self.max_file_bytes} byte limit: {source_id}"
            )

        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentLoadError(f"Document is not valid UTF-8: {source_id}") from exc

        title = self._title(source_id, text)
        try:
            return SourceDocument(source_id=source_id, text=text, title=title)
        except ValidationError as exc:
            raise DocumentLoadError(f"Invalid document content: {source_id}") from exc

    def load_all(self) -> list[SourceDocument]:
        """Load all supported files in deterministic relative-path order.

        Unrelated file extensions are ignored when scanning, but an explicit
        load() of an unsupported extension raises DocumentLoadError.
        """
        source_ids: list[str] = []

        for directory, dirnames, filenames in os.walk(
            self.root, topdown=True, followlinks=False, onerror=_on_walk_error
        ):
            current_dir = Path(directory)
            for name in dirnames:
                if _is_link_or_junction(current_dir / name):
                    raise DocumentLoadError(f"Linked directory is not supported: {name}")

            dirnames.sort()
            for name in filenames:
                if name.lower().endswith(_SUPPORTED_EXTENSIONS):
                    relative_path = (current_dir / name).relative_to(self.root)
                    source_ids.append(relative_path.as_posix())

        return [self.load(source_id) for source_id in sorted(source_ids)]

    @staticmethod
    def _title(source_id: str, text: str) -> str | None:
        text = text.removeprefix("\ufeff")
        if source_id.lower().endswith(".md"):
            for line in text.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("# "):
                    heading = stripped[2:].strip()
                    if 1 <= len(heading) <= 200:
                        return heading
                break

        filename_stem = PurePosixPath(source_id).stem
        return filename_stem if 1 <= len(filename_stem) <= 200 else None
