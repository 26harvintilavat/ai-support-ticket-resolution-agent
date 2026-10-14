# AI Support Ticket Resolution Agent

An evidence-driven AI support ticket resolution system built using
Retrieval-Augmented Generation (RAG) and agentic workflows.

The goal is to help support teams resolve customer issues using
trusted product documentation and previously resolved support tickets.

The planned system will retrieve evidence, generate a suggested
resolution with citations, and recommend human escalation when
the available evidence is insufficient or conflicting.

## Development Status

**Current milestone:** Phase 1 — Project Foundation.

Phase 1 establishes the backend infrastructure required for
future AI development.

The following capabilities are implemented:

- Python 3.12 project managed with uv
- FastAPI application foundation
- Pydantic-based application configuration
- PostgreSQL database connectivity
- SQLAlchemy 2.x asynchronous sessions
- Alembic database migrations
- PostgreSQL pgvector extension
- Docker Compose development environment
- Health and readiness endpoints
- Unit and PostgreSQL integration tests
- Ruff linting and formatting
- GitHub Actions continuous integration

The AI features, including document ingestion, embeddings,
RAG retrieval, ticket classification, agentic workflows, and
resolution generation, are planned for later phases.

This project is not yet a functioning AI ticket-resolution agent.

## Technology Stack

| Layer                   | Technology                     |
| ----------------------- | ------------------------------ |
| Language                | Python 3.12                    |
| API                     | FastAPI                        |
| Validation and settings | Pydantic v2, pydantic-settings |
| ORM                     | SQLAlchemy 2.x (async)         |
| Database                | PostgreSQL 17                  |
| Vector support          | pgvector                       |
| Database driver         | asyncpg                        |
| Migrations              | Alembic                        |
| Environment management  | uv                             |
| Containerization        | Docker and Docker Compose      |
| Testing                 | pytest                         |
| Code quality            | Ruff                           |
| CI                      | GitHub Actions                 |

Future AI components may use LangChain, LangGraph, and Langfuse.
They are not required to run the current foundation.

## Prerequisites

Install:

1. Git
2. Python 3.12, or allow uv to manage Python
3. uv
4. Docker Desktop with Docker Compose

Development has been configured for Windows and PowerShell.
The Docker environment runs Linux containers.

Ensure Docker Desktop is running before using Docker commands.

## Getting Started

### 1. Clone the repository

While Phase 1 development remains on its phase branch:

```powershell
git clone --branch phase/1-project-foundation https://github.com/26harvintilavat/ai-support-ticket-resolution-agent.git

cd ai-support-ticket-resolution-agent
```

After Phase 1 is merged into main, a normal clone can be used.

### 2. Install dependencies

```powershell
uv sync --frozen
```

This installs dependencies from the committed lockfile.

Verify the Python version:

```powershell
uv run python --version
```

The project requires Python 3.12.

### 3. Configure the environment

Copy the environment example:

```powershell
Copy-Item .env.example .env
```

The default development configuration is:

```dotenv
APP_ENVIRONMENT=development
API_PORT=8000

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=support_agent
POSTGRES_PORT=5433

APP_DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/support_agent
```

If PostgreSQL port 5433 is already occupied, change
POSTGRES_PORT to an available port such as 5434.

Also update the port inside APP_DATABASE_URL:

```dotenv
POSTGRES_PORT=5434

APP_DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5434/support_agent
```

The APP_DATABASE_URL shown above is for commands running
directly on the host machine.

Inside Docker Compose, the API uses the PostgreSQL service
hostname `postgres` and internal port 5432 automatically.

The default credentials are for local development only.
Use different credentials outside a local development environment.

The `.env` file is ignored by Git and must not be committed.

## Running with Docker Compose

The easiest way to run the entire foundation is Docker Compose.

### 1. Build and start services

```powershell
docker compose up -d --build
```

This starts:

- postgres: PostgreSQL with pgvector installed
- api: FastAPI backend

### 2. Check container status

```powershell
docker compose ps
```

Both containers should become healthy.

### 3. Apply database migrations

```powershell
docker compose exec api alembic upgrade head
```

Check the migration revision:

```powershell
docker compose exec api alembic current
```

Expected revision:

```text
0001_pgvector (head)
```

### 4. Verify PostgreSQL vector support

```powershell
docker compose exec postgres psql -U postgres -d support_agent -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

Expected extension:

```text
vector
```

### 5. Check API endpoints

Health check:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

Readiness check:

```powershell
Invoke-RestMethod http://localhost:8000/ready
```

Expected response:

```json
{
  "status": "ready"
}
```

API documentation is available at:

http://localhost:8000/docs

### 6. Stop the environment

```powershell
docker compose down
```

This stops the containers and preserves the PostgreSQL
named volume.

Do not add `-v` unless you intentionally want to delete
the database volume and its contents.

## Running FastAPI Directly on Windows

Alternatively, run only PostgreSQL in Docker and run
FastAPI on your host machine.

Start PostgreSQL:

```powershell
docker compose up -d postgres
```

Apply migrations using your host's APP_DATABASE_URL:

```powershell
uv run alembic upgrade head
```

Start FastAPI:

```powershell
uv run uvicorn app.main:app --reload
```

Open:

http://127.0.0.1:8000/docs

Do not run the Docker API container and local Uvicorn
server on the same host port simultaneously.

## Health and Readiness Endpoints

### GET /health

Confirms the API process is running.

Successful response:

```json
{
  "status": "ok"
}
```

HTTP status: 200.

This endpoint does not require PostgreSQL to be available.

### GET /ready

Checks whether the application can connect to PostgreSQL.

Successful response:

```json
{
  "status": "ready"
}
```

HTTP status: 200.

When PostgreSQL is unavailable:

```json
{
  "status": "not_ready"
}
```

HTTP status: 503.

These endpoints can be used by Docker and deployment systems
to monitor application health.

## Database Migrations

Alembic manages database schema changes.

Apply migrations:

```powershell
uv run alembic upgrade head
```

Check the current revision:

```powershell
uv run alembic current
```

For the containerized API, use:

```powershell
docker compose exec api alembic upgrade head
```

The first migration enables PostgreSQL's `vector` extension.

Revision:

```text
0001_pgvector
```

Future domain tables should be introduced through their
own Alembic migrations.

## Testing

### Run unit tests

```powershell
uv run pytest -m "not integration" -v
```

### Run all available tests

```powershell
uv run pytest -v
```

Database integration tests are skipped automatically if
TEST_DATABASE_URL is not configured.

### PostgreSQL integration tests

Integration tests require an isolated database named:

```text
support_agent_test
```

With PostgreSQL running, create this database once:

```powershell
docker compose exec postgres psql -U postgres -d postgres -c "CREATE DATABASE support_agent_test;"
```

If the database already exists, do not create it again.

For a PostgreSQL host port of 5434, set:

```powershell
$env:TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5434/support_agent_test"

$env:APP_DATABASE_URL = $env:TEST_DATABASE_URL
```

Apply migrations to the isolated test database:

```powershell
uv run alembic upgrade head
```

Run integration tests:

```powershell
uv run pytest -m integration -v
```

Run the complete test suite:

```powershell
uv run pytest -v
```

Remove the temporary environment variables afterward:

```powershell
Remove-Item Env:\TEST_DATABASE_URL
Remove-Item Env:\APP_DATABASE_URL
```

The integration tests check:

- PostgreSQL and pgvector availability
- Initial migration revision
- Vector distance calculations
- SQLAlchemy asynchronous sessions
- FastAPI readiness against real PostgreSQL

Never configure TEST_DATABASE_URL to point at a production
or normal development database.

## Code Quality

Ruff handles linting and formatting.

Check linting:

```powershell
uv run ruff check .
```

Check formatting:

```powershell
uv run ruff format --check .
```

Apply formatting when needed:

```powershell
uv run ruff format .
```

Run the complete local quality checks:

```powershell
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run pytest
git diff --check
```

## Continuous Integration

GitHub Actions runs the foundation quality gates.

Workflow file:

```text
.github/workflows/ci.yml
```

Workflow name:

```text
Foundation CI
```

The workflow is triggered by pushes and pull requests
for main and phase branches.

It performs:

1. Repository checkout
2. Python 3.12 setup
3. uv dependency installation from the lockfile
4. Ruff linting
5. Ruff formatting verification
6. PostgreSQL/pgvector service startup
7. Alembic migration upgrade
8. Migration repeatability check
9. Full pytest suite

The CI database is isolated from the local development
database.

GitHub Actions results can be viewed under the
repository's Actions tab.

## Project Structure

```text
ai-support-ticket-resolution-agent/
├── .github/
│   └── workflows/
│       └── ci.yml
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   └── main.py
├── docs/
│   └── phase-1/
│       ├── PHASE_1_PLAN.md
│       └── PHASE_1_ACCEPTANCE.md
├── migrations/
│   ├── versions/
│   │   └── 0001_enable_pgvector_extension.py
│   ├── env.py
│   └── script.py.mako
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_database.py
│   ├── test_health.py
│   ├── test_migrations.py
│   ├── test_postgres_integration.py
│   ├── test_readiness.py
│   └── test_toolchain.py
├── .dockerignore
├── .env.example
├── .gitignore
├── .python-version
├── alembic.ini
├── compose.yaml
├── Dockerfile
├── PROJECT_CONTEXT.md
├── pyproject.toml
├── README.md
└── uv.lock
```

## Development Workflow

Development is organized by phases and components.

For each component:

1. Read PROJECT_CONTEXT.md.
2. Review the relevant phase plan.
3. Implement the component.
4. Add focused tests.
5. Run pytest and Ruff.
6. Review the changes.
7. Commit the component.
8. Push to GitHub.
9. Verify relevant GitHub Actions checks.

PROJECT_CONTEXT.md is the primary architecture and scope
reference for the repository.

Avoid introducing unused modules, placeholder files, or
future-phase dependencies.

## Next Phase — Knowledge Ingestion

Phase 2 will introduce the first AI data-processing
capabilities.

Planned functionality includes:

- Loading product documentation
- Validating and cleaning source content
- Splitting documents into chunks
- Generating embeddings
- Storing document chunks and source metadata
- Using PostgreSQL with pgvector for future retrieval
- Testing ingestion correctness and repeatability

Actual ticket retrieval and agentic resolution workflows
will be introduced in subsequent phases.

## Project Scope

The project's priority is AI engineering, retrieval
quality, grounded generation, and reliable escalation.

It is not intended to become a full help-desk SaaS product.

The initial scope excludes:

- Complex multi-tenant architecture
- Enterprise authentication and RBAC
- Billing and payments
- Full CRM or help-desk integrations
- Autonomous customer communication
- Mobile applications

## Additional Documentation

- [Project Context](PROJECT_CONTEXT.md)
- [Phase 1 Plan](docs/phase-1/PHASE_1_PLAN.md)
- [Phase 1 Acceptance](docs/phase-1/PHASE_1_ACCEPTANCE.md)

## License

No license has been selected yet.
