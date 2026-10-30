"""Pgvector round-trip and transaction checks (isolated test DB only)."""

import asyncio
import os

import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.ingestion.chunker import DocumentChunker
from app.ingestion.contracts import SourceDocument
from app.ingestion.embeddings import (
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_MODEL_NAME,
    EmbeddedChunk,
)
from app.ingestion.models import KnowledgeChunk, KnowledgeDocument
from app.ingestion.repository import KnowledgeVectorRepository


@pytest.fixture
def test_database_url() -> str:
    raw_url = os.environ.get("TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL integration tests.")
    url = make_url(raw_url)
    if url.drivername != "postgresql+asyncpg" or url.database != "support_agent_test":
        pytest.fail("TEST_DATABASE_URL must reference PostgreSQL database support_agent_test.")
    return raw_url


def _data() -> tuple[SourceDocument, list[EmbeddedChunk]]:
    document = SourceDocument(
        source_id="integration/component-2-6.md",
        title="API key rotation",
        text="# API keys\n\nUpdate credentials, then restart the API.",
    )
    chunks = DocumentChunker(max_chunk_chars=40, overlap_chars=0).chunk(document)
    items = [
        EmbeddedChunk(
            chunk=chunk,
            embedding=(float(index + 1),) + (0.0,) * (DEFAULT_EMBEDDING_DIMENSIONS - 1),
            model_name=DEFAULT_MODEL_NAME,
            dimensions=DEFAULT_EMBEDDING_DIMENSIONS,
        )
        for index, chunk in enumerate(chunks)
    ]
    return document, items


@pytest.mark.integration
def test_pgvector_round_trip_and_metadata(test_database_url: str) -> None:
    async def verify() -> None:
        engine = create_async_engine(test_database_url, poolclass=NullPool)
        try:
            async with engine.connect() as connection:
                transaction = await connection.begin()
                try:
                    async with AsyncSession(bind=connection, expire_on_commit=False) as session:
                        document, items = _data()
                        document_id = await KnowledgeVectorRepository(session).insert_document(
                            document, items
                        )
                        stored = await session.get(KnowledgeDocument, document_id)
                        assert stored is not None
                        assert stored.source_id == document.source_id
                        assert stored.content_sha256 == document.content_sha256
                        assert stored.title == document.title

                        rows = (
                            await session.scalars(
                                select(KnowledgeChunk)
                                .where(KnowledgeChunk.document_id == document_id)
                                .order_by(KnowledgeChunk.chunk_index)
                            )
                        ).all()
                        assert len(rows) == len(items)
                        for row, item in zip(rows, items, strict=True):
                            assert row.embedding_model == DEFAULT_MODEL_NAME
                            assert row.start_char == item.chunk.start_char
                            assert row.end_char == item.chunk.end_char
                            assert row.section_title == item.chunk.section_title
                            stored_vector = [float(x) for x in row.embedding]
                            assert stored_vector == pytest.approx(item.embedding)
                finally:
                    await transaction.rollback()
        finally:
            await engine.dispose()

    asyncio.run(verify())


@pytest.mark.integration
def test_duplicate_write_rolls_back_without_corrupting_existing_data(
    test_database_url: str,
) -> None:
    async def verify() -> None:
        engine = create_async_engine(test_database_url, poolclass=NullPool)
        try:
            async with engine.connect() as connection:
                transaction = await connection.begin()
                try:
                    async with AsyncSession(bind=connection, expire_on_commit=False) as session:
                        document, items = _data()
                        repository = KnowledgeVectorRepository(session)
                        async with session.begin_nested():
                            first_id = await repository.insert_document(document, items)

                        with pytest.raises(IntegrityError):
                            async with session.begin_nested():
                                await repository.insert_document(document, items)

                        count = await session.scalar(
                            select(func.count())
                            .select_from(KnowledgeDocument)
                            .where(KnowledgeDocument.source_id == document.source_id)
                        )
                        assert count == 1
                        chunk_count = await session.scalar(
                            select(func.count())
                            .select_from(KnowledgeChunk)
                            .where(KnowledgeChunk.document_id == first_id)
                        )
                        assert chunk_count == len(items)
                finally:
                    await transaction.rollback()
        finally:
            await engine.dispose()

    asyncio.run(verify())
