from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from app.config import get_settings


class HealthResponse(BaseModel):
    """Response returned by the process health endpoint."""

    status: Literal["ok"] = "ok"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    settings = get_settings()

    application = FastAPI(
        title=settings.name,
        version=settings.version,
        description="Evidence-driven AI support ticket resolution agent.",
    )

    @application.get(
        "/health",
        response_model=HealthResponse,
        tags=["health"],
    )
    async def health_check() -> HealthResponse:
        """Report whether the API process is running."""

        return HealthResponse()

    return application


app = create_app()
