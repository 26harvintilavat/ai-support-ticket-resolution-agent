"""Generate validated, source-linked embeddings for ingestion chunks.

This component performs no database writes or vector searches.
The sentence-transformer is loaded lazily so unit tests can use fake encoders.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from numbers import Real
from typing import Protocol

from app.ingestion.contracts import DocumentChunk

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_EMBEDDING_DIMENSIONS = 384
DEFAULT_BATCH_SIZE = 32


class EmbeddingGenerationError(RuntimeError):
    """Embedding output is unavailable or does not satisfy our contract."""


class EmbeddingEncoder(Protocol):
    """The small part of SentenceTransformer that the service needs."""

    def get_sentence_embedding_dimension(self) -> int | None: ...

    def encode(
        self,
        sentences: list[str],
        *,
        batch_size: int,
        convert_to_numpy: bool,
        normalize_embeddings: bool,
        show_progress_bar: bool,
    ) -> object: ...


@dataclass(frozen=True, slots=True)
class EmbeddedChunk:
    """One original chunk paired with its model-specific vector."""

    chunk: DocumentChunk
    embedding: tuple[float, ...]
    model_name: str
    dimensions: int


class EmbeddingService:
    """Embed batches of validated chunks without changing their order or text."""

    def __init__(
        self,
        *,
        model_name: str = DEFAULT_MODEL_NAME,
        dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS,
        batch_size: int = DEFAULT_BATCH_SIZE,
        encoder: EmbeddingEncoder | None = None,
    ) -> None:
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("model_name must be a non-empty string")
        if isinstance(dimensions, bool) or not isinstance(dimensions, int) or dimensions <= 0:
            raise ValueError("dimensions must be a positive integer")
        if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size <= 0:
            raise ValueError("batch_size must be a positive integer")

        self.model_name = model_name.strip()
        self.dimensions = dimensions
        self.batch_size = batch_size
        self._encoder = encoder

    def _get_encoder(self) -> EmbeddingEncoder:
        """Load the local CPU model only when embeddings are actually requested."""
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer

            self._encoder = SentenceTransformer(self.model_name, device="cpu")
        return self._encoder

    def embed_chunks(self, chunks: Sequence[DocumentChunk]) -> list[EmbeddedChunk]:
        """Produce one validated embedding per chunk, preserving input order."""
        if not isinstance(chunks, Sequence) or isinstance(chunks, (str, bytes)):
            raise TypeError("chunks must be a sequence of DocumentChunk")
        if any(not isinstance(chunk, DocumentChunk) for chunk in chunks):
            raise TypeError("every item must be a DocumentChunk")
        if not chunks:
            return []

        try:
            encoder = self._get_encoder()
            actual_dimensions = encoder.get_sentence_embedding_dimension()
            if actual_dimensions != self.dimensions:
                raise EmbeddingGenerationError(
                    f"Embedding dimension mismatch: expected {self.dimensions},"
                    f"model returned {actual_dimensions}"
                )

            raw_vectors = encoder.encode(
                [chunk.text for chunk in chunks],
                batch_size=self.batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        except EmbeddingGenerationError:
            raise
        except Exception as exc:
            raise EmbeddingGenerationError("Embedding model failed to generate vectors") from exc

        if hasattr(raw_vectors, "tolist"):
            raw_vectors = raw_vectors.tolist()

        if not isinstance(raw_vectors, (list, tuple)) or len(raw_vectors) != len(chunks):
            raise EmbeddingGenerationError("Expected exactly one vector per document chunk")

        results: list[EmbeddedChunk] = []
        for chunk, vector in zip(chunks, raw_vectors, strict=True):
            if not isinstance(vector, (list, tuple)) or len(vector) != self.dimensions:
                raise EmbeddingGenerationError("An embedding has an invalid vector dimension")

            components: list[float] = []
            for value in vector:
                if isinstance(value, bool) or not isinstance(value, Real):
                    raise EmbeddingGenerationError("An embedding contains a non-numeric value")
                number = float(value)
                if not math.isfinite(number):
                    raise EmbeddingGenerationError("An embedding contains a non-finite value")
                components.append(number)

            results.append(
                EmbeddedChunk(
                    chunk=chunk,
                    embedding=tuple(components),
                    model_name=self.model_name,
                    dimensions=self.dimensions,
                )
            )

        return results
