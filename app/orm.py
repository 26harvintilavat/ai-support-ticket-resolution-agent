"""Shared SQLAlchemy declarative base for application ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Metadata registry shared by domain models and Alembic."""
