"""Base model for SQLAlchemy declarative models.

This module provides the base class for all SQLAlchemy models
in the application, ensuring consistent configuration and behavior.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass
