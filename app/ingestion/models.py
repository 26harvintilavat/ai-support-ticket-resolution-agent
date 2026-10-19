"""PostgreSQL records for product documentation and its text chunks."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.orm import Base


class KnowledgeDocument(Base):
    """One canonical source document, regardless of its future revisions."""

    __tablename__ = "knowledge_documents"

    __table_args__ = (
        UniqueConstraint(
            "source_id",
            name="uq_knowledge_documents_source_id",
        ),
        CheckConstraint(
            "document_type IN ('markdown', 'text')",
            name="ck_knowledge_documents_type",
        ),
        CheckConstraint(
            "content_sha256 ~ '^[0-9a-f]{64}$'",
            name="ck_knowledge_documents_checksum",
        ),
        CheckConstraint(
            "char_length(btrim(text)) > 0",
            name="ck_knowledge_documents_text_nonblank",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    source_id: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )

    title: Mapped[str | None] = mapped_column(
        String(200),
    )

    document_type: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
    )

    content_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="KnowledgeChunk.chunk_index",
    )


class KnowledgeChunk(Base):
    """One positional excerpt of its parent's normalized text."""

    __tablename__ = "knowledge_chunks"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_knowledge_chunks_position",
        ),
        CheckConstraint(
            "chunk_index >= 0",
            name="ck_knowledge_chunks_index",
        ),
        CheckConstraint(
            "start_char >= 0 AND end_char > start_char",
            name="ck_knowledge_chunks_offsets",
        ),
        CheckConstraint(
            "char_length(text) = end_char - start_char",
            name="ck_knowledge_chunks_text_length",
        ),
        CheckConstraint(
            "char_length(btrim(text)) > 0",
            name="ck_knowledge_chunks_text_nonblank",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey(
            "knowledge_documents.id",
            name="fk_knowledge_chunks_document_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    start_char: Mapped[str] = mapped_column(
        Integer,
        nullable=False,
    )

    end_char: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    section_title: Mapped[str | None] = mapped_column(
        String(200),
    )

    document: Mapped[KnowledgeDocument] = relationship(
        back_populates="chunks",
    )
