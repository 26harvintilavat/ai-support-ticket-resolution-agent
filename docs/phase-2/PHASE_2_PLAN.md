# Phase 2 — Knowledge Ingestion Plan

## Project

AI Support Ticket Resolution Agent

**Phase:** 2 — Knowledge Ingestion  
**Branch:** `phase/2-knowledge-ingestion`  
**Status:** IN PROGRESS

## 1. Goal

Build a reliable ingestion pipeline that transforms product
documentation into validated, chunked, embedded, and persisted
knowledge for future RAG retrieval.

Phase 2 does not generate support-ticket resolutions.

## 2. Existing Foundation

Phase 1 provides:

- Python 3.12 with uv
- FastAPI and Pydantic v2
- PostgreSQL and pgvector
- SQLAlchemy 2 async
- Alembic migrations
- Docker Compose
- pytest, Ruff, and GitHub CI

Reuse this foundation. Do not introduce unnecessary infrastructure.

## 3. Ingestion Architecture

The expected workflow is:

1. Read documents from a configured local directory.
2. Validate file formats and content.
3. Normalize document text.
4. Divide documents into meaningful text chunks.
5. Generate embeddings for those chunks.
6. Store documents, chunks, vectors, and metadata.
7. Detect unchanged documents on repeated ingestion.
8. Replace changed content consistently.

Every stage must be testable independently.

## 4. Supported Document Formats

Initial support:

- Markdown (.md)
- Plain text (.txt)

PDF, DOCX, and other formats are deferred until the basic
ingestion pipeline works reliably.

Historical support tickets are handled in Phase 4.

## 5. Ingestion Data Contracts

Component 2.1 introduces two Pydantic models:

### SourceDocument

Fields:

- source_id: canonical relative POSIX-style document path
- text: normalized document content
- title: optional title
- content_sha256: computed SHA-256 checksum
- document_type: computed document format

Rules:

- Identifiers must remain relative.
- Only supported extensions are accepted.
- Blank documents are invalid.
- CRLF and CR are normalized to LF.
- A leading UTF-8 BOM is removed.
- Unexpected fields are rejected.
- Models are immutable after validation.
- The checksum is derived from normalized UTF-8 text.

The ingestion loader must additionally enforce filesystem safety,
including root containment and permitted file sizes.

### DocumentChunk

Fields:

- source_id: parent document source identifier
- chunk_index: zero-based chunk position
- text: exact chunk text
- start_char: inclusive start offset
- end_char: exclusive end offset
- section_title: optional section heading

Rules:

- Chunk indexes are non-negative integers.
- Character offsets must be valid.
- Chunk text must not be blank.
- Offset length must equal text length.
- Offsets refer to normalized document text.
- Chunk order must be deterministic.

A complete ingestion pipeline must verify that each chunk's
text matches the corresponding source document substring.

Overlapping chunks are permitted if the chunking strategy
requires them.

## 6. Metadata and Document Identity

Source identity is based on the document's canonical relative
path under the configured ingestion root.

Store sufficient metadata for future citations:

- Source identifier
- Document title
- Document type
- Document checksum
- Chunk index
- Section title
- Character offsets
- Embedding model identity

The same source document should retain its source identity
when its content changes.

## 7. Embedding Strategy

Use one embedding model consistently for the initial version.

A small local sentence-transformer model is preferred for
cost-effective development.

The final model and vector dimension are selected in
Component 2.5.

Embedding model identity and dimensionality must be tracked.

Do not mix incompatible embeddings within one search index.

Embedding calls must be replaceable with deterministic test
implementations.

## 8. Persistence Strategy

Store the following in PostgreSQL:

- Document records
- Chunk records
- Embedding vectors
- Source metadata

Use pgvector for vector representation.

Introduce database tables through Alembic migrations.

A document and its chunks must remain consistent across
successful and failed ingestion attempts.

## 9. Repeatability and Updates

Ingestion must support repeated execution.

Required behavior:

- Unchanged documents should not create duplicates.
- Changed documents should be reprocessed.
- Changes to the embedding model or relevant chunking
  configuration should trigger appropriate reprocessing.
- Failed updates must not leave partially replaced content.
- A failed update should preserve the previous valid version.
- Missing files must not automatically delete stored knowledge
  unless deletion is explicitly supported and requested.

## 10. Phase 2 Components

| Component | Description                        |
| --------- | ---------------------------------- |
| 2.1       | Planning and ingestion contracts   |
| 2.2       | Database models and migrations     |
| 2.3       | Document loading and validation    |
| 2.4       | Text cleaning and chunking         |
| 2.5       | Embedding generation               |
| 2.6       | Vector storage and metadata        |
| 2.7       | Ingestion pipeline orchestration   |
| 2.8       | Integration testing and quality    |
| 2.9       | Documentation and phase acceptance |

Each component must have focused tests and a separate commit.

## 11. Component 2.1 Acceptance

Component 2.1 is complete when:

- The Phase 2 plan exists.
- SourceDocument is implemented.
- DocumentChunk is implemented.
- Source identifiers are validated.
- Content checksums are deterministic.
- Chunk bounds are validated.
- Contract tests pass.
- Ruff lint and formatting checks pass.
- No future-component implementation is introduced.
- The changes are committed on the Phase 2 branch.

## 12. Phase 2 Definition of Done

Phase 2 will be complete when:

- Markdown and text documents can be loaded.
- Unsupported or invalid files are rejected safely.
- Documents can be chunked deterministically.
- Embeddings can be generated.
- Documents and chunks are stored in PostgreSQL.
- Vectors are stored with pgvector.
- Source metadata is preserved.
- Duplicate ingestion is handled correctly.
- Changed documents are processed correctly.
- Ingestion failures leave consistent database state.
- Automated and database integration tests pass.
- Ruff and GitHub CI pass.
- Documentation describes the working system.
- Fresh-environment acceptance succeeds.

## 13. Out of Scope

Do not implement the following during Phase 2:

- Support-ticket classification
- Historical ticket intelligence
- LLM response generation
- LangGraph workflows
- Reranking
- Citation validation
- Human escalation
- Langfuse integration
- Full help-desk integrations
- Frontend dashboards
- Complex authentication or RBAC

Basic RAG retrieval begins in Phase 3.

## 14. Development Workflow

For each component:

1. Verify the working Git branch.
2. Implement only the current component.
3. Add focused automated tests.
4. Run the focused tests.
5. Run applicable regression tests.
6. Run Ruff linting and formatting checks.
7. Review the changed files.
8. Commit the completed component.
9. Continue to the next component.

Use uv for Python dependency management.

Do not create empty placeholder files or speculative modules.

PROJECT_CONTEXT.md remains the primary architecture and
scope reference.

## 15. Final Deliverable

Phase 2 must deliver a working knowledge-ingestion pipeline:

Product Documentation
↓
Validated Documents
↓
Normalized Text
↓
Document Chunks
↓
Embeddings
↓
PostgreSQL + pgvector

The stored knowledge becomes the input for Phase 3 —
Basic RAG.
