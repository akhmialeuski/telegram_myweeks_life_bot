"""Abstract base repository interface.

This module provides abstract base class for repository implementations
with common async session management functionality.
"""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession


class AbstractBaseRepository(ABC):
    """Abstract base class for repositories with async session management.

    This class defines the interface for repository implementations
    and common async session management functionality. All repositories should
    inherit from this class and implement the abstract methods.

    :param db_path: Path to database file
    :type db_path: str
    """

    def __init__(self, db_path: str) -> None:
        """Initialize repository.

        :param db_path: Path to database file
        :type db_path: str
        """
        self.db_path = db_path

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize database connection and create tables.

        Creates the database engine, session factory and tables if they don't exist.
        Should be called before any other operations.

        :returns: None
        :rtype: None
        :raises Exception: If database initialization fails
        """

    @abstractmethod
    async def close(self) -> None:
        """Close database connection and cleanup resources.

        :returns: None
        :rtype: None
        """

    @abstractmethod
    @asynccontextmanager
    async def async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Create a new async session and handle its lifecycle.

        This async context manager ensures proper session handling:
        - Creates a new session
        - Handles commit/rollback automatically
        - Closes session after use
        - Provides error logging

        Usage::

            async with self.async_session() as session:
                result = await session.execute(stmt)
                # No need to commit - handled automatically

        :yields: Database session
        :rtype: AsyncGenerator[AsyncSession, None]
        :raises RuntimeError: If repository is not initialized
        """
        # This is needed to make the abstract method a generator
        yield  # type: ignore[misc]

    @abstractmethod
    def _detach_instance(self, session: AsyncSession, instance: Any) -> None:
        """Detach instance from session while keeping its state.

        :param session: Database session
        :type session: AsyncSession
        :param instance: SQLAlchemy model instance to detach
        :type instance: Any
        :returns: None
        :rtype: None
        """
