"""Create relational storage for documents and document chunks.

Revision ID: 0002_knowledge
Revises: 0001_pgvector
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_knowledge"
down_revision: str | None = "0001_pgvector"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create knowledge document and chunk tables."""

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.String(length=512), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("document_type", sa.String(length=8), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "source_id",
            name="uq_knowledge_documents_source_id",
        ),
        sa.CheckConstraint(
            "document_type IN ('markdown', 'text')",
            name="ck_knowledge_documents_type",
        ),
        sa.CheckConstraint(
            "content_sha256 ~ '^[0-9a-f]{64}$'",
            name="ck_knowledge_documents_checksum",
        ),
        sa.CheckConstraint(
            "char_length(btrim(text)) > 0",
            name="ck_knowledge_documents_text_nonblank",
        ),
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("start_char", sa.Integer(), nullable=False),
        sa.Column("end_char", sa.Integer(), nullable=False),
        sa.Column("section_title", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["knowledge_documents.id"],
            name="fk_knowledge_chunks_document_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_knowledge_chunks_position",
        ),
        sa.CheckConstraint(
            "chunk_index >= 0",
            name="ck_knowledge_chunks_index",
        ),
        sa.CheckConstraint(
            "start_char >= 0 AND end_char > start_char",
            name="ck_knowledge_chunks_offsets",
        ),
        sa.CheckConstraint(
            "char_length(text) = end_char - start_char",
            name="ck_knowledge_chunks_text_length",
        ),
        sa.CheckConstraint(
            "char_length(btrim(text)) > 0",
            name="ck_knowledge_chunks_text_nonblank",
        ),
    )


def downgrade() -> None:
    """Remove knowledge tables in reverse dependency order."""

    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")
