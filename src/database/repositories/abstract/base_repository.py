"""Abstract base repository interface.

This module provides abstract base class for repository implementations
with common session management functionality.
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Generator

from sqlalchemy.orm import Session


class AbstractBaseRepository(ABC):
    """Abstract base class for repositories with session management.

    This class defines the interface for repository implementations
    and common session management functionality. All repositories should
    inherit from this class and implement the abstract methods.

    :param db_path: Path to database file
    """

    def __init__(self, db_path: str):
        """Initialize repository.

        :param db_path: Path to database file
        """
        self.db_path = db_path

    @abstractmethod
    def initialize(self) -> None:
        """Initialize database connection and create tables.

        Creates the database engine, session factory and tables if they don't exist.
        Should be called before any other operations.

        :returns: None
        :raises Exception: If database initialization fails
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connection and cleanup resources.

        :returns: None
        """
        pass

    @abstractmethod
    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Create a new session and handle its lifecycle.

        This context manager ensures proper session handling:
        - Creates a new session
        - Handles commit/rollback automatically
        - Closes session after use
        - Provides error logging

        Usage:
            with self.session() as session:
                result = session.execute(stmt)
                # No need to commit - handled automatically

        :yields: Database session
        :raises RuntimeError: If repository is not initialized
        """
        pass

    @abstractmethod
    def _detach_instance(self, session: Session, instance: Any) -> None:
        """Detach instance from session while keeping its state.

        :param session: Database session
        :param instance: SQLAlchemy model instance to detach
        :returns: None
        """
        pass