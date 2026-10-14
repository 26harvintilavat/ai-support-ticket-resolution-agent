from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Response, status
from pydantic import BaseModel

from app.config import get_settings
from app.database import check_database_connection, engine


class HealthResponse(BaseModel):
    """Response returned by the process health endpoint."""

    status: Literal["ok"] = "ok"


class ReadinessResponse(BaseModel):
    """Response returned by the application readiness endpoint."""

    status: Literal["ready", "not_ready"]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Release application resources during shutdown."""

    yield

    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    settings = get_settings()

    application = FastAPI(
        title=settings.name,
        version=settings.version,
        description="Evidence-driven AI support ticket resolution agent.",
        lifespan=lifespan,
    )

    @application.get(
        "/health",
        response_model=HealthResponse,
        tags=["health"],
    )
    async def health_check() -> HealthResponse:
        """Report whether the API process is running."""

        return HealthResponse()

    @application.get(
        "/ready",
        response_model=ReadinessResponse,
        tags=["health"],
    )
    async def readiness_check(response: Response) -> ReadinessResponse:
        """Report whether required infrastructure is available."""

        if not await check_database_connection():
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return ReadinessResponse(status="not_ready")

        return ReadinessResponse(status="ready")

    return application


app = create_app()
