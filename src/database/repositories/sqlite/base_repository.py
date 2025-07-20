"""Base SQLite repository with session management.

This module provides a base class for SQLite repositories with
common session management functionality following SQLAlchemy 2.0 best practices.
"""

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, List, Optional, Type, TypeVar

from sqlalchemy import create_engine, delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from ....utils.config import BOT_NAME
from ...constants import DEFAULT_DATABASE_PATH, SQLITE_ECHO, SQLITE_POOL_PRE_PING
from ...models.base import Base

logger = logging.getLogger(BOT_NAME)

# Type variable for SQLAlchemy models
ModelType = TypeVar("ModelType", bound=Base)


class BaseSQLiteRepository:
    """Base class for SQLite repositories with session management.

    This class implements common database operations and session management
    following SQLAlchemy 2.0 best practices. All SQLite repositories should
    inherit from this class.

    :param db_path: Path to SQLite database file
    """

    def __init__(self, db_path: str = DEFAULT_DATABASE_PATH):
        """Initialize SQLite repository.

        :param db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.engine = None
        self.SessionLocal = None

    def initialize(self) -> None:
        """Initialize database connection and create tables.

        Creates the database engine, session factory and tables if they don't exist.
        Should be called before any other operations.

        :returns: None
        :raises SQLAlchemyError: If database initialization fails
        """
        if not self.engine:
            try:
                self.engine = create_engine(
                    f"sqlite:///{self.db_path}",
                    echo=SQLITE_ECHO,
                    pool_pre_ping=SQLITE_POOL_PRE_PING,
                )
                Base.metadata.create_all(bind=self.engine)
                self.SessionLocal = sessionmaker(
                    bind=self.engine,
                    autocommit=False,
                    autoflush=False,
                    expire_on_commit=False,
                )
                logger.info(f"SQLite database initialized at {self.db_path}")
            except SQLAlchemyError as e:
                logger.error(f"Failed to initialize SQLite database: {e}")
                raise

    def close(self) -> None:
        """Close database connection and cleanup resources.

        :returns: None
        """
        if self.engine:
            self.engine.dispose()
            self.engine = None
            logger.info("SQLite database connection closed")

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
        if not self.SessionLocal:
            raise RuntimeError("Repository not initialized")

        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error in {self.__class__.__name__}: {e}")
            raise
        finally:
            session.close()

    def _detach_instance(self, session: Session, instance: Any) -> None:
        """Detach instance from session while keeping its state.

        :param session: Database session
        :param instance: SQLAlchemy model instance to detach
        :returns: None
        """
        if instance and instance in session:
            session.expunge(instance)

    def _create_entity(self, entity: ModelType, entity_name: str) -> bool:
        """Generic method to create an entity.

        :param entity: Entity object to create
        :param entity_name: Name of entity for logging
        :returns: True if successful, False otherwise
        """
        try:
            with self.session() as session:
                session.add(entity)
                logger.info(f"Created {entity_name}")
                return True

        except IntegrityError:
            logger.warning(f"{entity_name} already exists")
            return False
        except Exception as e:
            logger.error(f"Failed to create {entity_name}: {e}")
            return False

    def _get_entity_by_telegram_id(
        self, model_class: Type[ModelType], telegram_id: int, entity_name: str
    ) -> Optional[ModelType]:
        """Generic method to get entity by telegram_id.

        :param model_class: SQLAlchemy model class
        :param telegram_id: Telegram user ID
        :param entity_name: Name of entity for logging
        :returns: Entity object if found, None otherwise
        """
        try:
            with self.session() as session:
                stmt = select(model_class).where(model_class.telegram_id == telegram_id)
                result = session.execute(stmt)
                entity = result.scalar_one_or_none()
                if entity:
                    self._detach_instance(session, entity)
                return entity

        except Exception as e:
            logger.error(f"Failed to get {entity_name} {telegram_id}: {e}")
            return None

    def _delete_entity_by_telegram_id(
        self, model_class: Type[ModelType], telegram_id: int, entity_name: str
    ) -> bool:
        """Generic method to delete entity by telegram_id.

        :param model_class: SQLAlchemy model class
        :param telegram_id: Telegram user ID
        :param entity_name: Name of entity for logging
        :returns: True if successful, False otherwise
        """
        try:
            with self.session() as session:
                stmt = delete(model_class).where(model_class.telegram_id == telegram_id)
                result = session.execute(stmt)

                if result.rowcount > 0:
                    logger.info(f"Deleted {entity_name} for user {telegram_id}")
                    return True
                else:
                    logger.warning(f"{entity_name} for user {telegram_id} not found")
                    return False

        except Exception as e:
            logger.error(f"Failed to delete {entity_name}: {e}")
            return False

    def _get_all_entities(
        self, model_class: Type[ModelType], entity_name: str
    ) -> List[ModelType]:
        """Generic method to get all entities.

        :param model_class: SQLAlchemy model class
        :param entity_name: Name of entity for logging
        :returns: List of all entity objects
        """
        try:
            with self.session() as session:
                stmt = select(model_class)
                result = session.execute(stmt)
                entities = list(result.scalars().all())
                # Detach all objects from session
                for entity in entities:
                    self._detach_instance(session, entity)
                return entities

        except Exception as e:
            logger.error(f"Failed to get all {entity_name}: {e}")
            return []
