# Phase 1 — Project Foundation Plan

## AI Support Ticket Resolution Agent

**Repository:** `26harvintilavat/ai-support-ticket-resolution-agent`  
**Phase branch:** `phase/1-project-foundation`  
**Phase goal:** Establish a clean, reproducible, testable backend foundation for the AI Support Ticket Resolution Agent without implementing RAG, ingestion, agentic workflows, or other later-phase features.

---

## 1. Current Repository Baseline

At the start of Phase 1, the repository contains the initial project context and a minimal repository bootstrap.

Observed baseline:

```text
.
├── .gitignore
├── PROJECT_CONTEXT.md
├── README.md
├── app/
│   └── __init__.py
├── pyproject.toml
├── tests/
│   └── __init__.py
└── uv.lock
```

Current notes:

- `PROJECT_CONTEXT.md` is the primary source of truth for project scope and architecture.
- `pyproject.toml` currently contains only a minimal development dependency setup.
- `.gitignore`, `README.md`, `app/__init__.py`, and `tests/__init__.py` are currently empty placeholders.
- Phase 1 will not expand the repository with speculative directories or placeholder files.
- Existing empty placeholders should either be populated when they become useful or removed until the component that needs them is implemented.

---

# 2. Phase 1 Objectives

Phase 1 should leave the project with a reliable foundation that supports all later AI/RAG development.

By the end of the phase, the repository should provide:

1. A reproducible Python 3.12 environment managed with `uv`.
2. A working FastAPI application.
3. Typed application configuration.
4. PostgreSQL connectivity through SQLAlchemy 2.x.
5. `pgvector` enabled in PostgreSQL.
6. Alembic database migrations.
7. A Docker-based local development environment.
8. Health and readiness checks.
9. Automated tests.
10. Ruff linting and formatting configuration.
11. GitHub CI quality gates.
12. Clear local-development documentation.

Phase 1 should establish infrastructure only. It should not prematurely implement business or AI features belonging to later phases.

---

# 3. Phase 1 Development Rules

## 3.1 Build only what is currently needed

Do **not** create empty directories, placeholder modules, future service classes, empty schemas, unused interfaces, or speculative abstractions.

A directory or file should be added only when the current component contains real implementation that requires it.

Examples:

- Do not create `app/rag/` during Phase 1.
- Do not create `app/agents/` before the LangGraph phase.
- Do not create `app/ingestion/` before knowledge ingestion begins.
- Do not create empty database model modules for future tickets or documents.
- Do not create unused repository/service layers just because they may be useful later.

The repository structure should grow together with working functionality.

## 3.2 Add dependencies when they become necessary

Use `uv` for all environment and dependency operations.

Do not install the complete future stack in Phase 1.

For example:

- FastAPI dependencies are added when the API foundation is implemented.
- SQLAlchemy and PostgreSQL dependencies are added when database support is implemented.
- Alembic is added when migrations are introduced.
- LangChain is added during the phase that first uses it.
- LangGraph is added when the agentic workflow is implemented.
- Langfuse is added when observability is implemented.

This keeps the dependency graph small and makes every dependency explainable.

## 3.3 Every component must be independently usable

Each component should finish with:

1. Working production code for that component.
2. Relevant automated tests.
3. Ruff passing for changed code.
4. No known broken behavior.
5. A focused Git commit.

Do not combine several unfinished components into one large commit.

## 3.4 `PROJECT_CONTEXT.md` remains authoritative

Implementation decisions should stay consistent with `PROJECT_CONTEXT.md`.

If the implementation intentionally changes the architecture or scope, update `PROJECT_CONTEXT.md` in the same component that introduces the change.

---

# 4. Phase 1 Components

## Component 1.1 — Python Toolchain and Repository Baseline

### Goal

Turn the initial repository bootstrap into a clean Python 3.12 project with a reproducible `uv` workflow and useful repository-level configuration.

### Work

- Standardize the project on Python 3.12.
- Add normal project metadata to `pyproject.toml`.
- Configure Ruff.
- Configure pytest basics.
- Add `.python-version` if useful for the local `uv` workflow.
- Populate `.gitignore` with actual Python, virtual-environment, test-cache, IDE, local-env, and build exclusions.
- Remove or defer existing empty placeholder files that are not yet required.
- Keep `uv.lock` synchronized with `pyproject.toml`.
- Establish the project commands that later components will use.

### Dependency policy

Only development/tooling dependencies that are genuinely used at this point should be present.

No AI-framework dependencies should be added.

### Expected repository changes

Examples of files that may become real in this component:

```text
pyproject.toml
uv.lock
.python-version
.gitignore
```

Do not create application subpackages yet unless Component 1.1 itself needs them.

### Verification

At minimum:

```powershell
uv sync
uv run python --version
uv run ruff check .
uv run pytest
```

`pytest` may report no tests yet if application functionality has not been introduced. That is acceptable for this component, provided the test configuration itself is valid.

### Suggested commit

```text
chore: establish python toolchain and repository baseline
```

---

## Component 1.2 — FastAPI Application Foundation

### Goal

Create the smallest production-quality FastAPI application that can start successfully and expose an operational health endpoint.

### Work

- Add FastAPI.
- Add an ASGI server such as Uvicorn.
- Add `pydantic-settings` for typed configuration.
- Create the application package only now, because it contains real code.
- Add the FastAPI application entry point.
- Add typed application settings.
- Add a basic application health endpoint.
- Add application tests using FastAPI-compatible HTTP test tooling.
- Define a clear development startup command.

### Initial API behavior

A simple operational route is enough:

```text
GET /health
```

Expected purpose:

- confirm the process is running;
- return a stable machine-readable response;
- avoid checking external dependencies yet.

Example shape:

```json
{
  "status": "ok"
}
```

The exact schema can be finalized during implementation.

### Scope limits

Do not add:

- support-ticket submission endpoints;
- RAG routes;
- LLM clients;
- document ingestion;
- authentication;
- complex API versioning infrastructure unless it is already needed.

### Verification

Example checks:

```powershell
uv run ruff check .
uv run pytest
uv run uvicorn app.main:app --reload
```

Then verify:

```text
GET /health -> 200
```

### Suggested commit

```text
feat: add fastapi application foundation
```

---

## Component 1.3 — PostgreSQL and SQLAlchemy Foundation

### Goal

Give the FastAPI application a clean, testable PostgreSQL persistence foundation without introducing premature domain models.

### Work

- Add SQLAlchemy 2.x.
- Add an async PostgreSQL driver such as `asyncpg`.
- Add database configuration to the typed settings model.
- Create the SQLAlchemy async engine/session infrastructure.
- Add safe session lifecycle handling.
- Add a small database connectivity abstraction needed by the application.
- Add a readiness endpoint that checks whether required infrastructure is reachable.
- Add focused tests for configuration and database connectivity behavior.

### Operational routes

Keep `/health` process-only.

Add:

```text
GET /ready
```

Purpose:

- verify the application is able to reach PostgreSQL;
- return failure when a required dependency is unavailable.

This separation makes the service suitable for later container health checks and deployment environments.

### Domain-model policy

Do **not** create ticket, document, chunk, embedding, evaluation, or trace tables in this component.

Those schemas should be introduced only when their owning features are implemented.

### Verification

At minimum:

```powershell
uv run ruff check .
uv run pytest
```

With PostgreSQL available:

```text
GET /health -> 200
GET /ready  -> 200
```

With PostgreSQL unavailable:

```text
GET /health -> 200
GET /ready  -> non-ready response
```

### Suggested commit

```text
feat: add postgresql persistence foundation
```

---

## Component 1.4 — Alembic and pgvector Bootstrap

### Goal

Establish controlled database migrations and prove that the PostgreSQL instance supports vector storage for later RAG phases.

### Work

- Add Alembic.
- Configure Alembic to use the project database settings correctly.
- Add the Python `pgvector` integration only when required by the implementation.
- Create the first real migration.
- Enable the PostgreSQL `vector` extension through migration-controlled database state.
- Verify upgrade behavior from a fresh database.
- Verify repeatability/idempotent environment setup where appropriate.

### Initial migration scope

The first migration should focus on foundation state, for example:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Do not create future document or ticket tables just to make the migration look larger.

### Verification

From a clean database:

```powershell
uv run alembic upgrade head
uv run alembic current
uv run ruff check .
uv run pytest
```

Verify PostgreSQL reports the vector extension as installed.

### Suggested commit

```text
feat: add alembic migrations and pgvector bootstrap
```

---

## Component 1.5 — Docker Development Environment

### Goal

Make the complete Phase 1 application reproducible on a developer machine through Docker Compose.

### Work

- Add a production-sensible API `Dockerfile`.
- Add `.dockerignore`.
- Add a Compose configuration.
- Add a PostgreSQL image that includes pgvector.
- Run the FastAPI service and PostgreSQL together.
- Add container health checks where useful.
- Wire application configuration through environment variables.
- Add persistent local database storage through a named volume.
- Ensure migrations can be applied predictably.
- Keep secrets out of committed files.

### Initial Compose services

Phase 1 should require only what Phase 1 actually uses:

```text
api
postgres
```

Do not add Redis, Langfuse, worker services, vector-database alternatives, or other future infrastructure until a later component actually needs them.

### Verification

Example acceptance flow:

```powershell
docker compose build
docker compose up -d
docker compose ps
```

Then verify:

```text
API container: healthy/running
PostgreSQL container: healthy/running
GET /health: 200
GET /ready: 200
```

Apply migrations and confirm pgvector is enabled.

Finally:

```powershell
docker compose down
```

### Suggested commit

```text
build: add docker development environment
```

---

## Component 1.6 — Test Infrastructure and GitHub Quality Gates

### Goal

Make repository correctness automatically verifiable before later AI complexity is added.

### Work

- Finalize pytest configuration.
- Add reusable test fixtures only where they are actually needed.
- Add API tests.
- Add configuration tests.
- Add database/readiness tests.
- Add migration smoke validation if practical.
- Finalize Ruff linting/formatting rules.
- Add a GitHub Actions workflow.
- Use `uv` inside CI.
- Ensure CI uses the lockfile rather than silently resolving a different environment.

### CI quality gates

The workflow should at minimum check:

```text
dependency sync
lint
tests
```

If database integration tests require PostgreSQL, CI should provide a real PostgreSQL/pgvector service rather than mocking every persistence boundary.

### Quality philosophy

Phase 1 CI should stay small and deterministic.

Do not add:

- deployment pipelines;
- release automation;
- complex security scanning suites;
- coverage thresholds with no meaningful test baseline;
- matrix combinations that provide little value for a portfolio project.

These can be introduced later if the project actually needs them.

### Verification

Local:

```powershell
uv sync --frozen
uv run ruff check .
uv run pytest
```

GitHub:

```text
Phase 1 CI workflow -> passing
```

### Suggested commit

```text
ci: add foundation quality gates
```

---

## Component 1.7 — Documentation and Phase 1 Acceptance

### Goal

Finish Phase 1 with documentation that allows the project to be cloned and run from scratch without relying on undocumented local knowledge.

### Work

Populate the repository README with the actual implemented foundation.

Document:

- project purpose;
- current development status;
- prerequisites;
- Python version;
- `uv` setup;
- dependency installation;
- local FastAPI startup;
- Docker startup;
- environment configuration;
- migration commands;
- test commands;
- Ruff commands;
- health/readiness endpoints;
- current repository structure;
- next phase.

Update `PROJECT_CONTEXT.md` only if Phase 1 implementation changed any originally documented architectural decision.

### Fresh-clone acceptance

Validate the project as if another developer were cloning it for the first time.

Expected flow should be approximately:

```powershell
git clone <repository>
cd ai-support-ticket-resolution-agent

uv sync
uv run pytest
uv run ruff check .

docker compose up -d --build
uv run alembic upgrade head
```

Then verify:

```text
GET /health -> healthy
GET /ready  -> ready
PostgreSQL reachable
pgvector extension enabled
```

### Final repository check

Before Phase 1 is considered complete:

- no empty placeholder files remain unless technically required;
- no unused future-feature packages are installed;
- no committed `.env` secrets exist;
- no dead modules exist;
- no future-phase skeleton directories exist;
- lockfile matches project dependencies;
- tests pass;
- Ruff passes;
- Docker environment starts cleanly;
- migrations apply from a fresh database;
- GitHub CI passes;
- README matches the real commands.

### Suggested commit

```text
docs: finalize phase 1 project foundation
```

---

# 5. Expected Repository Shape at the End of Phase 1

This is an architectural target, **not a request to create every path immediately**.

Each path should appear only when its component is implemented.

A likely final Phase 1 structure is:

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── alembic/
│   ├── versions/
│   │   └── <initial_pgvector_migration>.py
│   └── env.py
├── app/
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   └── session.py
│   ├── __init__.py
│   └── main.py
├── tests/
│   ├── <api tests>
│   ├── <configuration tests>
│   └── <database/readiness tests>
├── .dockerignore
├── .env.example
├── .gitignore
├── .python-version
├── alembic.ini
├── compose.yaml
├── Dockerfile
├── PROJECT_CONTEXT.md
├── README.md
├── pyproject.toml
└── uv.lock
```

The exact structure may be smaller if some modules do not need their own files yet.

Avoid creating package layers only to match this diagram.

---

# 6. Phase 1 Dependency Boundary

A likely Phase 1 dependency set will eventually include only foundation packages such as:

### Runtime

```text
fastapi
uvicorn
pydantic-settings
sqlalchemy
asyncpg
alembic
pgvector
```

### Development

```text
pytest
pytest-asyncio
httpx
ruff
```

Exact versions should be resolved and locked by `uv` during implementation.

Do not add the following merely because they appear in the complete project stack:

```text
langchain
langgraph
langfuse
embedding-model integrations
reranking libraries
LLM provider SDKs
```

They belong to later phases when production code begins using them.

---

# 7. Explicitly Out of Scope for Phase 1

Phase 1 must not implement:

- knowledge ingestion;
- document loaders;
- text chunking;
- embeddings;
- document vector search;
- historical ticket retrieval;
- support-ticket classification;
- LLM calls;
- prompt templates;
- LangChain chains;
- LangGraph state machines;
- reranking;
- evidence sufficiency logic;
- response generation;
- citation validation;
- human escalation logic;
- Langfuse tracing;
- evaluation datasets;
- frontend UI;
- authentication/RBAC;
- help-desk integrations;
- Redis or worker queues unless a real Phase 1 requirement appears.

This prevents Phase 1 from becoming a disguised implementation of future phases.

---

# 8. Component Execution Workflow

For every Phase 1 component:

```text
Read PROJECT_CONTEXT.md
        ↓
Inspect current branch/worktree
        ↓
Implement only current component
        ↓
Add/update focused tests
        ↓
Run focused tests
        ↓
Run full Phase 1 tests available so far
        ↓
Run Ruff
        ↓
Inspect git diff
        ↓
Perform component code review
        ↓
Commit the completed component
        ↓
Start next component
```

Recommended rule:

> Never begin the next component while the current component has known failing tests, unresolved review findings, or uncommitted implementation changes.

---

# 9. Commit Strategy

Development remains on:

```text
phase/1-project-foundation
```

Use one focused commit per completed component.

Suggested sequence:

```text
docs: add phase 1 project foundation plan
chore: establish python toolchain and repository baseline
feat: add fastapi application foundation
feat: add postgresql persistence foundation
feat: add alembic migrations and pgvector bootstrap
build: add docker development environment
ci: add foundation quality gates
docs: finalize phase 1 project foundation
```

Do not squash unrelated component work together while Phase 1 is being actively developed. The component history should remain easy to review.

---

# 10. Phase 1 Definition of Done

Phase 1 is complete only when all of the following are true:

- [ ] Python 3.12 is the documented project runtime.
- [ ] `uv` fully manages dependency installation and locking.
- [ ] `uv sync --frozen` succeeds.
- [ ] FastAPI starts successfully.
- [ ] `/health` succeeds independently of PostgreSQL.
- [ ] `/ready` accurately represents PostgreSQL readiness.
- [ ] SQLAlchemy 2.x database sessions work correctly.
- [ ] PostgreSQL runs locally through Docker Compose.
- [ ] pgvector is enabled through Alembic-managed database state.
- [ ] Alembic upgrades a fresh database successfully.
- [ ] Automated tests pass.
- [ ] Ruff passes.
- [ ] GitHub CI passes.
- [ ] `.env` secrets are not committed.
- [ ] README setup commands work from a fresh clone.
- [ ] No unnecessary placeholder files/directories remain.
- [ ] No future-phase implementation has leaked into Phase 1.
- [ ] `PROJECT_CONTEXT.md` still matches the implemented architecture.

---

# 11. Phase 1 Deliverable

The final Phase 1 deliverable is **not** an AI support agent yet.

It is a dependable application foundation on which the AI system can be built safely:

```text
FastAPI
   ↓
Typed Configuration
   ↓
SQLAlchemy
   ↓
PostgreSQL + pgvector
   ↓
Alembic
   ↓
Docker
   ↓
Tests + Ruff + CI
```

Once this foundation is stable, Phase 2 can introduce the first actual AI-data capability: **Knowledge Ingestion**.
