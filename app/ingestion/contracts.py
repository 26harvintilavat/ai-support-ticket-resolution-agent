"""Validated data contracts shared by the knowledge-ingestion pipeline."""

import hashlib
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)


def validate_source_id(value: str) -> str:
    """Require a canonical path relative to the configured documentation root."""
    parts = value.split("/")

    if (
        value != value.strip()
        or value.startswith("/")
        or "\\" in value
        or ":" in value
        or "\x00" in value
        or any(part in ("", ".", "..") for part in parts)
    ):
        raise ValueError("source_id must be a canonical relative POSIX path")

    if not value.lower().endswith((".md", ".txt")):
        raise ValueError("source_id must point to a .md or .txt document")

    return value


SourceId = Annotated[
    str,
    Field(min_length=1, max_length=512),
    AfterValidator(validate_source_id),
]


class SourceDocument(BaseModel):
    """A validated document before it is divided into chunks."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: SourceId
    text: str
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        value = value.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")

        if not value.strip() or "\x00" in value:
            raise ValueError("document text must be non-empty and contain no NUL bytes")

        return value

    @computed_field
    @property
    def content_sha256(self) -> str:
        """Hash normalized UTF-8 text to detect changed source content."""
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()

    @computed_field
    @property
    def document_type(self) -> Literal["markdown", "text"]:
        return "markdown" if self.source_id.lower().endswith(".md") else "text"


class DocumentChunk(BaseModel):
    """One exact substring of a normalized source document."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: SourceId
    chunk_index: int = Field(ge=0, strict=True)
    text: str
    start_char: int = Field(ge=0, strict=True)
    end_char: int = Field(ge=0, strict=True)

    section_title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    @model_validator(mode="after")
    def validate_chunk_bounds(self) -> Self:
        if not self.text.strip():
            raise ValueError("chunk text must not be blank")

        if self.end_char - self.start_char != len(self.text):
            raise ValueError("chunk offsets must watch the exact chunk text length")

        return self
