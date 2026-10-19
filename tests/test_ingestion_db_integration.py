"""Integration checks for the 2.2 schema in an isolated PostgreSQL database."""

import asyncio
import hashlib
import os

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.ingestion.models import KnowledgeChunk, KnowledgeDocument


@pytest.fixture
def test_database_url() -> str:
    raw_url = os.environ.get("TEST_DATABASE_URL")

    if not raw_url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL integration tests.")

    url = make_url(raw_url)

    if url.drivername != "postgresql+asyncpg" or url.database != "support_agent_test":
        pytest.fail("TEST_DATABASE_URL must reference PostgreSQL database support_agent_test.")

    return raw_url


@pytest.mark.integration
def test_document_chunk_storage_and_constraints(
    test_database_url: str,
) -> None:
    async def verify() -> None:
        engine = create_async_engine(
            test_database_url,
            poolclass=NullPool,
        )

        try:
            async with engine.connect() as connection:
                transaction = await connection.begin()

                try:
                    async with AsyncSession(
                        bind=connection,
                        expire_on_commit=False,
                    ) as session:
                        text = "Restart the application."

                        document = KnowledgeDocument(
                            source_id="integration/component-2-2.md",
                            title="Test document",
                            document_type="markdown",
                            content_sha256=hashlib.sha256(text.encode()).hexdigest(),
                            text=text,
                        )

                        session.add(document)
                        await session.flush()

                        document_id = document.id

                        session.add(
                            KnowledgeChunk(
                                document_id=document_id,
                                chunk_index=0,
                                text=text,
                                start_char=0,
                                end_char=len(text),
                                section_title="Setup",
                            )
                        )

                        await session.flush()

                        stored_chunks = (
                            await session.scalars(
                                select(KnowledgeChunk).where(
                                    KnowledgeChunk.document_id == document_id
                                )
                            )
                        ).all()

                        assert len(stored_chunks) == 1
                        assert stored_chunks[0].text == text
                        assert stored_chunks[0].section_title == "Setup"

                        # A duplicate source path must be rejected.
                        with pytest.raises(IntegrityError):
                            async with session.begin_nested():
                                session.add(
                                    KnowledgeDocument(
                                        source_id=document.source_id,
                                        document_type="markdown",
                                        content_sha256=document.content_sha256,
                                        text=text,
                                    )
                                )
                                await session.flush()

                        # A duplicate chunk position must be rejected.
                        with pytest.raises(IntegrityError):
                            async with session.begin_nested():
                                session.add(
                                    KnowledgeChunk(
                                        document_id=document_id,
                                        chunk_index=0,
                                        text=text,
                                        start_char=0,
                                        end_char=len(text),
                                    )
                                )
                                await session.flush()

                        # Invalid character offsets must be rejected.
                        with pytest.raises(IntegrityError):
                            async with session.begin_nested():
                                session.add(
                                    KnowledgeChunk(
                                        document_id=document_id,
                                        chunk_index=1,
                                        text="incorrect offsets",
                                        start_char=0,
                                        end_char=5,
                                    )
                                )
                                await session.flush()

                        # Deleting a parent must cascade to child rows.
                        await session.execute(
                            delete(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
                        )

                        remaining = await session.scalar(
                            select(func.count())
                            .select_from(KnowledgeChunk)
                            .where(KnowledgeChunk.document_id == document_id)
                        )

                        assert remaining == 0

                finally:
                    # All test changes are rolled back.
                    await transaction.rollback()

        finally:
            await engine.dispose()

    asyncio.run(verify())
