"""Add typed pgvector embeddings and embedding-model metadata.

Revision ID: 0003_vectors
Revises: 0002_knowledge

The columns are nullable so rows created by Component 2.2 remain valid.
New ingestion writes always supply both fields.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import VECTOR

revision: str = "0003_vectors"
down_revision: str | None = "0002_knowledge"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "knowledge_chunks",
        sa.Column("embedding", VECTOR(384), nullable=True),
    )
    op.add_column(
        "knowledge_chunks",
        sa.Column("embedding_model", sa.String(length=200), nullable=True),
    )
    op.create_check_constraint(
        "ck_knowledge_chunks_embedding_contract",
        "knowledge_chunks",
        "(embedding IS NULL AND embedding_model IS NULL) OR "
        "(embedding IS NOT NULL AND "
        "embedding_model = 'sentence-transformers/all-MiniLM-L6-v2')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_knowledge_chunks_embedding_contract", "knowledge_chunks", type_="check")
    op.drop_column("knowledge_chunks", "embedding_model")
    op.drop_column("knowledge_chunks", "embedding")
