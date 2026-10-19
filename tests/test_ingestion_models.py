"""SQLAlchemy model tests that do not require PostgreSQL."""

import hashlib

from sqlalchemy import inspect

from app.ingestion.models import KnowledgeChunk, KnowledgeDocument
from app.orm import Base


def test_model_tables_are_registered_for_migrations() -> None:
    assert set(Base.metadata.tables) == {
        "knowledge_documents",
        "knowledge_chunks",
    }

    assert KnowledgeDocument.__table__.c.source_id.type.length == 512
    assert KnowledgeChunk.__table__.c.section_title.type.length == 200


def test_chunk_foreign_key_is_cascading() -> None:
    foreign_key = next(iter(KnowledgeChunk.__table__.c.document_id.foreign_keys))

    assert foreign_key.target_fullname == "knowledge_documents.id"
    assert foreign_key.ondelete == "CASCADE"


def test_schema_has_uniqueness_and_offset_constraints() -> None:
    document_names = {constraint.name for constraint in KnowledgeDocument.__table__.constraints}

    chunk_names = {constraint.name for constraint in KnowledgeChunk.__table__.constraints}

    assert "uq_knowledge_documents_source_id" in document_names
    assert "uq_knowledge_chunks_position" in chunk_names
    assert "ck_knowledge_chunks_offsets" in chunk_names
    assert "ck_knowledge_chunks_text_length" in chunk_names

    assert inspect(KnowledgeDocument).relationships["chunks"].uselist is True


def test_python_models_can_link_a_document_and_chunk() -> None:
    original = "Restart the service."

    document = KnowledgeDocument(
        source_id="guides/auth.md",
        title="Authentication",
        document_type="markdown",
        content_sha256=hashlib.sha256(original.encode()).hexdigest(),
        text=original,
    )

    document.chunks.append(
        KnowledgeChunk(
            chunk_index=0,
            text=original,
            start_char=0,
            end_char=len(original),
        )
    )

    assert document.chunks[0].document is document
    assert document.chunks[0].chunk_index == 0
