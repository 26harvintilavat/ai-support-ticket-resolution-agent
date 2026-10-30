"""Insert fully embedded documents using the caller's database transaction.

Component 2.6 implements insert-only persistence. Component 2.7 will own
unchanged-document detection, replacement, and ingestion orchestration.
"""

import math
from collections.abc import Sequence
from numbers import Real

from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.contracts import SourceDocument
from app.ingestion.embeddings import (
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_MODEL_NAME,
    EmbeddedChunk,
)
from app.ingestion.models import KnowledgeChunk, KnowledgeDocument


class KnowledgeVectorRepository:
    """Persist one source document and its vectors without committing the session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert_document(
        self,
        document: SourceDocument,
        embedded_chunks: Sequence[EmbeddedChunk],
    ) -> int:
        """Insert a new document and all vectors; return the generated document ID.

        The caller MUST use a transaction, e.g. `async with session.begin()`.
        Duplicate source IDs raise IntegrityError. No upsert or delete occurs here.
        """
        if not isinstance(document, SourceDocument):
            raise TypeError("document must be a SourceDocument")
        if not isinstance(embedded_chunks, Sequence) or isinstance(embedded_chunks, (str, bytes)):
            raise TypeError("embedded_chunks must be a sequence of EmbeddedChunk")
        if not embedded_chunks:
            raise ValueError("a document must have at least one embedded chunk")

        # Validate everything BEFORE adding any ORM objects to the session.
        rows: list[KnowledgeChunk] = []
        for expected_index, item in enumerate(embedded_chunks):
            if not isinstance(item, EmbeddedChunk):
                raise TypeError("every item must be an EmbeddedChunk")

            chunk = item.chunk
            if chunk.source_id != document.source_id:
                raise ValueError("chunk source_id does not match its document")
            if chunk.chunk_index != expected_index:
                raise ValueError("chunk indexes must be consecutive, starting at zero")
            if (
                chunk.end_char > len(document.text)
                or document.text[chunk.start_char : chunk.end_char] != chunk.text
            ):
                raise ValueError("chunk text and offsets must match the source document")
            if item.model_name != DEFAULT_MODEL_NAME:
                raise ValueError("embedding model is not supported by this knowledge index")
            if item.dimensions != DEFAULT_EMBEDDING_DIMENSIONS:
                raise ValueError("embedding dimensions do not match the knowledge index")
            if len(item.embedding) != DEFAULT_EMBEDDING_DIMENSIONS:
                raise ValueError("embedding vector has an incorrect length")

            vector: list[float] = []
            for value in item.embedding:
                if isinstance(value, bool) or not isinstance(value, Real):
                    raise ValueError("embedding vector contains a non-numeric value")
                number = float(value)
                if not math.isfinite(number):
                    raise ValueError("embedding vector contains a non-finite value")
                vector.append(number)
            if not any(vector):
                raise ValueError("embedding vector must not be all zeros")

            rows.append(
                KnowledgeChunk(
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char,
                    section_title=chunk.section_title,
                    embedding=vector,
                    embedding_model=item.model_name,
                )
            )

        record = KnowledgeDocument(
            source_id=document.source_id,
            title=document.title,
            document_type=document.document_type,
            content_sha256=document.content_sha256,
            text=document.text,
        )
        record.chunks.extend(rows)
        self._session.add(record)
        await self._session.flush()
        return record.id
