"""Unit tests for Component 2.6; no database connection is required."""

import asyncio
from dataclasses import replace

import pytest
from pgvector.sqlalchemy import VECTOR
from sqlalchemy import CheckConstraint

from app.ingestion.chunker import DocumentChunker
from app.ingestion.contracts import SourceDocument
from app.ingestion.embeddings import (
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_MODEL_NAME,
    EmbeddedChunk,
)
from app.ingestion.models import KnowledgeChunk
from app.ingestion.repository import KnowledgeVectorRepository


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.flush_count = 0

    def add(self, record: object) -> None:
        self.added.append(record)

    async def flush(self) -> None:
        self.flush_count += 1
        # PostgreSQL would allocate the primary key during flush.
        self.added[-1].id = 123  # type: ignore[attr-defined]


def _document_and_embeddings() -> tuple[SourceDocument, list[EmbeddedChunk]]:
    document = SourceDocument(
        source_id="guides/rotation.md",
        text="# Rotation\n\nUpdate the API key.\n\nRestart the service.",
        title="Rotation",
    )
    chunks = DocumentChunker(max_chunk_chars=40, overlap_chars=0).chunk(document)
    embedded = [
        EmbeddedChunk(
            chunk=chunk,
            embedding=(1.0,) + (0.0,) * (DEFAULT_EMBEDDING_DIMENSIONS - 1),
            model_name=DEFAULT_MODEL_NAME,
            dimensions=DEFAULT_EMBEDDING_DIMENSIONS,
        )
        for chunk in chunks
    ]
    return document, embedded


def test_orm_declares_pgvector_with_correct_dimension_and_metadata() -> None:
    column = KnowledgeChunk.__table__.c.embedding
    assert isinstance(column.type, VECTOR)
    assert column.type.dim == DEFAULT_EMBEDDING_DIMENSIONS
    assert KnowledgeChunk.__table__.c.embedding_model.type.length == 200
    assert column.nullable  # keeps records from the previous schema valid
    assert any(
        isinstance(constraint, CheckConstraint)
        and constraint.name == "ck_knowledge_chunks_embedding_contract"
        for constraint in KnowledgeChunk.__table__.constraints
    )


def test_inserts_document_and_source_linked_vector_rows_without_committing() -> None:
    document, items = _document_and_embeddings()
    session = FakeSession()

    document_id = asyncio.run(KnowledgeVectorRepository(session).insert_document(document, items))

    assert document_id == 123
    assert session.flush_count == 1
    assert len(session.added) == 1
    record = session.added[0]
    assert record.source_id == document.source_id
    assert record.content_sha256 == document.content_sha256
    assert len(record.chunks) == len(items)
    for row, source in zip(record.chunks, items, strict=True):
        assert row.document is record
        assert row.text == source.chunk.text
        assert row.chunk_index == source.chunk.chunk_index
        assert row.embedding_model == DEFAULT_MODEL_NAME
        assert row.embedding == list(source.embedding)


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda item: replace(item, model_name="other-model"), "model"),
        (lambda item: replace(item, dimensions=768), "dimensions"),
        (lambda item: replace(item, embedding=(1.0,)), "length"),
        (
            lambda item: replace(item, embedding=(float("nan"),) + item.embedding[1:]),
            "non-finite",
        ),
        (lambda item: replace(item, embedding=(0.0,) * 384), "all zeros"),
        (
            lambda item: replace(item, embedding=(True,) + item.embedding[1:]),
            "non-numeric",
        ),
        (
            lambda item: replace(
                item, chunk=item.chunk.model_copy(update={"source_id": "guides/other.md"})
            ),
            "source_id",
        ),
        (
            lambda item: replace(
                item, chunk=item.chunk.model_copy(update={"text": "not the original text"})
            ),
            "text and offsets",
        ),
    ],
)
def test_invalid_embedding_is_rejected_before_any_write(mutate, message: str) -> None:
    document, items = _document_and_embeddings()
    session = FakeSession()
    items[0] = mutate(items[0])

    with pytest.raises(ValueError, match=message):
        asyncio.run(KnowledgeVectorRepository(session).insert_document(document, items))

    assert session.added == []
    assert session.flush_count == 0


def test_nonconsecutive_chunk_indexes_are_rejected() -> None:
    document, items = _document_and_embeddings()
    items[0] = replace(items[0], chunk=items[0].chunk.model_copy(update={"chunk_index": 3}))
    session = FakeSession()
    with pytest.raises(ValueError, match="consecutive"):
        asyncio.run(KnowledgeVectorRepository(session).insert_document(document, items))
    assert not session.added


def test_no_chunk_is_rejected() -> None:
    document, _ = _document_and_embeddings()
    with pytest.raises(ValueError, match="at least one"):
        asyncio.run(KnowledgeVectorRepository(FakeSession()).insert_document(document, []))
