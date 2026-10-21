"""Split normalized documents into bounded, traceable text excerpts.

SourceDocument already removes BOM and normalizes line endings. This service
keeps the remaining text intact so source hashes and character offsets stay
meaningful; it removes only whitespace at the boundaries of each chunk.
"""

import re
from bisect import bisect_right

from app.ingestion.contracts import DocumentChunk, SourceDocument

DEFAULT_MAX_CHUNK_CHARS = 1_000
DEFAULT_OVERLAP_CHARS = 150

_HEADING_RE = re.compile(r"^ {0,3}#{1,6}(?:[ \t]+(?P<title>.*)|[ \t]*)$")
_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_PARAGRAPH_GAP_RE = re.compile(r"\n[ \t]*\n")
_TRAILING_HASHES_RE = re.compile(r"[ \t]+#+[ \t]*$")


def _markdown_headings(text: str) -> list[tuple[int, str]]:
    """Find ATX headings outside fenced code, using source character offsets."""
    headings: list[tuple[int, str]] = []
    fence_marker: str | None = None
    fence_length = 0
    offset = 0

    for line in text.splitlines(keepends=True):
        content = line.rstrip("\n")
        fence = _FENCE_RE.match(content)

        if fence:
            marker = fence.group(1)
            if fence_marker is None:
                fence_marker, fence_length = marker[0], len(marker)
            elif (
                marker[0] == fence_marker
                and len(marker) >= fence_length
                and not content[fence.end() :].strip()
            ):
                fence_marker = None
                fence_length = 0
        elif fence_marker is None:
            match = _HEADING_RE.match(content)
            if match:
                raw = (match.group("title") or "").strip()
                title = _TRAILING_HASHES_RE.sub("", raw).strip()[:200].rstrip()
                if title:
                    headings.append((offset, title))
        offset += len(line)

    return headings


class DocumentChunker:
    """Produce deterministic SourceDocument-relative chunks without I/O."""

    def __init__(
        self,
        *,
        max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS,
        overlap_chars: int = DEFAULT_OVERLAP_CHARS,
    ) -> None:
        if (
            isinstance(max_chunk_chars, bool)
            or not isinstance(max_chunk_chars, int)
            or max_chunk_chars <= 0
        ):
            raise ValueError("max_chunk_chars must be a positive integer")
        if (
            isinstance(overlap_chars, bool)
            or not isinstance(overlap_chars, int)
            or overlap_chars < 0
            or overlap_chars > max_chunk_chars // 2
        ):
            raise ValueError("overlap_chars must be an integer between 0 and half the chunk size")

        self.max_chunk_chars = max_chunk_chars
        self.overlap_chars = overlap_chars

    def _choose_end(self, text: str, start: int, heading_offsets: list[int]) -> tuple[int, bool]:
        """Prefer the next section, then paragraphs, lines, and word breaks."""
        limit = min(start + self.max_chunk_chars, len(text))
        if limit == len(text):
            return limit, False

        minimum = start + max(self.max_chunk_chars // 2, self.overlap_chars + 1)
        heading_index = bisect_right(heading_offsets, limit) - 1
        heading_minimum = start + max(self.max_chunk_chars // 4, self.overlap_chars + 1)
        if heading_index >= 0 and heading_offsets[heading_index] >= heading_minimum:
            return heading_offsets[heading_index], True

        paragraph_end = None
        for paragraph_break in _PARAGRAPH_GAP_RE.finditer(text, minimum, limit):
            paragraph_end = paragraph_break.end()
        if paragraph_end is not None:
            return paragraph_end, False

        line_break = text.rfind("\n", minimum, limit)
        if line_break >= 0:
            return line_break + 1, False

        for position in range(limit - 1, minimum - 1, -1):
            if text[position].isspace():
                return position + 1, False

        return limit, False

    def chunk(self, document: SourceDocument) -> list[DocumentChunk]:
        """Chunk one document, preserving exact source slices and all nonspace text."""
        if not isinstance(document, SourceDocument):
            raise TypeError("document must be a SourceDocument")

        text = document.text
        headings = _markdown_headings(text) if document.document_type == "markdown" else []
        positions = [offset for offset, _ in headings]
        result: list[DocumentChunk] = []
        start = 0

        while start < len(text):
            while start < len(text) and text[start].isspace():
                start += 1
            if start == len(text):
                break

            raw_end, at_heading = self._choose_end(text, start, positions)
            end = raw_end
            while end > start and text[end - 1].isspace():
                end -= 1

            if end == start:
                start = raw_end
                continue

            heading_index = bisect_right(positions, start) - 1
            section_title = headings[heading_index][1] if heading_index >= 0 else None

            result.append(
                DocumentChunk(
                    source_id=document.source_id,
                    chunk_index=len(result),
                    text=text[start:end],
                    start_char=start,
                    end_char=end,
                    section_title=section_title,
                )
            )

            if raw_end == len(text):
                break
            if at_heading or self.overlap_chars == 0:
                start = raw_end
                continue

            start = max(start + 1, end - self.overlap_chars)
            # Prefer restarting at a word boundary rather than in mid-word.
            if start < end and not text[start - 1].isspace():
                while start < end and not text[start].isspace():
                    start += 1

        return result
