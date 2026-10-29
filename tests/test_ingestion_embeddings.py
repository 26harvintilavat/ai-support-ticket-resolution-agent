"""Unit tests for Component 2.5; no downloads or database required."""

import math

import pytest

from app.ingestion.chunker import DocumentChunker
from app.ingestion.contracts import SourceDocument
from app.ingestion.embeddings import (
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_MODEL_NAME,
    EmbeddedChunk,
    EmbeddingGenerationError,
    EmbeddingService,
)


class FakeEncoder:
    """A deterministic substitute for SentenceTransformer during tests."""

    def __init__(self, *, dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS) -> None:
        self.dimensions = dimensions
        self.calls: list[list[str]] = []
        self.output_override: object | None = None
        self.fail = False

    def get_sentence_embedding_dimension(self) -> int:
        return self.dimensions

    def encode(
        self,
        sentences: list[str],
        *,
        batch_size: int,
        convert_to_numpy: bool,
        normalize_embeddings: bool,
        show_progress_bar: bool,
    ) -> object:
        assert batch_size > 0
        assert convert_to_numpy is True
        assert normalize_embeddings is True
        assert show_progress_bar is False
        self.calls.append(list(sentences))
        if self.fail:
            raise RuntimeError("simulated encoder failure")
        if self.output_override is not None:
            return self.output_override
        return [[float(len(text))] + [0.0] * (self.dimensions - 1) for text in sentences]


def _chunks():
    document = SourceDocument(
        source_id="guides/api-keys.md",
        text="# API keys\n\nRotate your API key.\n\nRestart the service after rotation.",
    )
    return DocumentChunker(max_chunk_chars=45, overlap_chars=0).chunk(document)


def test_generates_one_embedding_per_chunk_with_source_identity() -> None:
    chunks = _chunks()
    fake = FakeEncoder()
    service = EmbeddingService(encoder=fake)

    embedded = service.embed_chunks(chunks)

    assert len(embedded) == len(chunks)
    assert fake.calls == [[chunk.text for chunk in chunks]]
    assert all(isinstance(item, EmbeddedChunk) for item in embedded)
    for input_chunk, result in zip(chunks, embedded, strict=True):
        assert result.chunk is input_chunk
        assert result.chunk.source_id == "guides/api-keys.md"
        assert result.model_name == DEFAULT_MODEL_NAME
        assert result.dimensions == DEFAULT_EMBEDDING_DIMENSIONS
        assert len(result.embedding) == DEFAULT_EMBEDDING_DIMENSIONS
        assert result.embedding[0] == float(len(input_chunk.text))
        assert isinstance(result.embedding, tuple)
        assert all(math.isfinite(x) for x in result.embedding)


def test_fake_embedding_output_is_repeatable_and_does_not_mutate_chunks() -> None:
    chunks = _chunks()
    original = list(chunks)
    service = EmbeddingService(encoder=FakeEncoder())

    assert service.embed_chunks(chunks) == service.embed_chunks(chunks)
    assert chunks == original


def test_empty_input_returns_without_loading_or_calling_model() -> None:
    fake = FakeEncoder()
    assert EmbeddingService(encoder=fake).embed_chunks([]) == []
    assert fake.calls == []


def test_rejects_non_chunk_inputs() -> None:
    service = EmbeddingService(encoder=FakeEncoder())
    with pytest.raises(TypeError, match="sequence"):
        service.embed_chunks("not chunks")
    with pytest.raises(TypeError, match="every item"):
        service.embed_chunks(["not a chunk"])


@pytest.mark.parametrize("bad_value", [0, -5, True, 1.2, "384"])
def test_rejects_invalid_dimensions(bad_value: object) -> None:
    with pytest.raises(ValueError, match="dimensions"):
        EmbeddingService(dimensions=bad_value, encoder=FakeEncoder())


@pytest.mark.parametrize("bad_value", [0, -1, False, 1.5, "32"])
def test_rejects_invalid_batch_size(bad_value: object) -> None:
    with pytest.raises(ValueError, match="batch_size"):
        EmbeddingService(batch_size=bad_value, encoder=FakeEncoder())


def test_rejects_empty_model_name() -> None:
    with pytest.raises(ValueError, match="model_name"):
        EmbeddingService(model_name=" ", encoder=FakeEncoder())


def test_rejects_model_with_unexpected_dimension() -> None:
    service = EmbeddingService(encoder=FakeEncoder(dimensions=768))
    with pytest.raises(EmbeddingGenerationError, match="dimension mismatch"):
        service.embed_chunks(_chunks())


def test_rejects_missing_vectors() -> None:
    fake = FakeEncoder()
    fake.output_override = []
    with pytest.raises(EmbeddingGenerationError, match="exactly one vector"):
        EmbeddingService(encoder=fake).embed_chunks(_chunks())


def test_rejects_wrong_vector_size() -> None:
    fake = FakeEncoder()
    fake.output_override = [[0.0] * 10 for _ in _chunks()]
    with pytest.raises(EmbeddingGenerationError, match="invalid vector dimension"):
        EmbeddingService(encoder=fake).embed_chunks(_chunks())


@pytest.mark.parametrize("bad_component", [float("nan"), float("inf"), -float("inf")])
def test_rejects_non_finite_vector_components(bad_component: float) -> None:
    fake = FakeEncoder()
    fake.output_override = [
        [bad_component] + [0.0] * (DEFAULT_EMBEDDING_DIMENSIONS - 1) for _ in _chunks()
    ]
    with pytest.raises(EmbeddingGenerationError, match="non-finite"):
        EmbeddingService(encoder=fake).embed_chunks(_chunks())


def test_rejects_non_numeric_vector_component() -> None:
    fake = FakeEncoder()
    fake.output_override = [[True] + [0.0] * (DEFAULT_EMBEDDING_DIMENSIONS - 1) for _ in _chunks()]
    with pytest.raises(EmbeddingGenerationError, match="non-numeric"):
        EmbeddingService(encoder=fake).embed_chunks(_chunks())


def test_encoder_failure_is_wrapped() -> None:
    fake = FakeEncoder()
    fake.fail = True
    with pytest.raises(EmbeddingGenerationError, match="failed to generate vectors"):
        EmbeddingService(encoder=fake).embed_chunks(_chunks())
