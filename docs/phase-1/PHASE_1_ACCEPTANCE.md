# Phase 1 — Project Foundation Acceptance

## Project

AI Support Ticket Resolution Agent

**Phase:** 1 — Project Foundation

**Branch:** `phase/1-project-foundation`

**Status:** PENDING FINAL VERIFICATION

## 1. Purpose

This document records the acceptance results for Phase 1.

Phase 1 delivers the backend foundation required for
future knowledge ingestion, RAG, and agentic workflows.

No AI resolution functionality is included in this phase.

## 2. Component Inventory

| Component | Description                              | Implementation       |
| --------- | ---------------------------------------- | -------------------- |
| 1.1       | Python toolchain and repository baseline | Implemented          |
| 1.2       | FastAPI application foundation           | Implemented          |
| 1.3       | PostgreSQL and SQLAlchemy foundation     | Implemented          |
| 1.4       | Alembic and pgvector bootstrap           | Implemented          |
| 1.5       | Docker development environment           | Implemented          |
| 1.6       | Tests and GitHub quality gates           | Implemented          |
| 1.7       | Documentation and acceptance             | Pending verification |

## 3. Acceptance Checklist

Mark items complete only after actual verification.

### Environment

- [ ] Python 3.12 is available.
- [ ] uv dependency synchronization succeeds.
- [ ] uv.lock is synchronized with pyproject.toml.
- [ ] No secrets are tracked in Git.

### Application

- [ ] FastAPI starts successfully.
- [ ] GET /health returns HTTP 200.
- [ ] GET /ready returns HTTP 200 with PostgreSQL running.
- [ ] GET /ready returns HTTP 503 without PostgreSQL.

### Persistence

- [ ] SQLAlchemy database connectivity works.
- [ ] PostgreSQL starts through Docker Compose.
- [ ] Alembic upgrades a fresh database.
- [ ] Alembic reports revision 0001_pgvector.
- [ ] PostgreSQL vector extension is enabled.
- [ ] Migration repeatability is verified.

### Quality

- [ ] Ruff linting passes.
- [ ] Ruff formatting checks pass.
- [ ] All unit tests pass.
- [ ] PostgreSQL integration tests pass.
- [ ] GitHub Actions workflow passes.

### Repository

- [ ] README setup instructions are verified.
- [ ] A separate fresh-clone acceptance run succeeds.
- [ ] No unnecessary placeholder files remain.
- [ ] No unused future-phase dependencies exist.
- [ ] No future-phase functionality has been introduced.
- [ ] PROJECT_CONTEXT.md matches the implemented scope.
- [ ] Git worktree is clean after committing.

## 4. Verification Commands

### Toolchain and quality

```powershell
uv sync --frozen
uv run python --version
uv run ruff check .
uv run ruff format --check .
uv run pytest -m "not integration" -v
```

### Docker and migrations

```powershell
docker compose up -d --build
docker compose ps
docker compose exec api alembic upgrade head
docker compose exec api alembic current
```

### HTTP endpoints

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
```

### PostgreSQL extension

```sql
SELECT extname
FROM pg_extension
WHERE extname = 'vector';
```

### Integration tests

Run after configuring TEST_DATABASE_URL to reference
the isolated support_agent_test database:

```powershell
uv run pytest -m integration -v
uv run pytest -v
```

## 5. Results

Fill in this table after executing the checks.

| Check                        | Result  | Evidence |
| ---------------------------- | ------- | -------- |
| Python version               | Pending |          |
| uv dependency sync           | Pending |          |
| Ruff lint                    | Pending |          |
| Ruff format                  | Pending |          |
| Unit tests                   | Pending |          |
| PostgreSQL integration tests | Pending |          |
| Docker containers            | Pending |          |
| Alembic migration            | Pending |          |
| pgvector extension           | Pending |          |
| Health endpoint              | Pending |          |
| Readiness endpoint           | Pending |          |
| Fresh clone                  | Pending |          |
| GitHub Actions               | Pending |          |

Use PASS or FAIL for each result.

Record meaningful evidence such as test counts,
migration revision, actual responses, or a CI run URL.

## 6. Known Limitations

Phase 1 is infrastructure only.

The following functionality is intentionally not present:

- Knowledge ingestion
- Document embeddings and indexing
- Documentation semantic retrieval
- Historical support ticket intelligence
- LLM-based ticket classification
- LangGraph workflows
- Evidence sufficiency checks
- Citation validation
- Human escalation decisions
- AI evaluation and observability

These features belong to subsequent phases.

## 7. Acceptance Decision

**Decision:** PENDING

Change the decision to PASS only when all required
acceptance checks have succeeded.

Do not record a PASS with unresolved failures.

## 8. Next Phase

After Phase 1 acceptance and merge into main,
start Phase 2 — Knowledge Ingestion.

Use a new phase branch based on the latest main commit.

Continue implementation component by component,
with focused tests, reviews, and commits.
