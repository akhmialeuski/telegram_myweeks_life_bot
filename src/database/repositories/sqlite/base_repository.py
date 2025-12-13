"""Base SQLite repository with async session management.

This module provides a base class for SQLite repositories with
common async session management functionality following SQLAlchemy 2.0 best practices.
"""

import asyncio
import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Optional, Type

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from typing_extensions import TypeVar

from ....utils.config import BOT_NAME
from ...constants import DEFAULT_DATABASE_PATH, SQLITE_ECHO, SQLITE_POOL_PRE_PING
from ...models.base import Base

logger = logging.getLogger(BOT_NAME)

# Type variable for SQLAlchemy models
ModelType = TypeVar("ModelType", bound=Base, default=Base)


class BaseSQLiteRepository:
    """Base class for SQLite repositories with async session management.

    Provides a shared SQLAlchemy async engine and session factory per ``db_path``
    across all subclasses to avoid duplicate initializations and logs.

    :param db_path: Path to SQLite database file
    :type db_path: str
    """

    # Shared registries across ALL subclasses (keyed by db_path absolute string)
    _engines: dict[str, AsyncEngine] = {}
    _sessions: dict[str, async_sessionmaker[AsyncSession]] = {}
    _initialized_once_logged: set[str] = set()
    _instances: dict[str, "BaseSQLiteRepository"] = {}
    _initialized: dict[str, bool] = {}
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, db_path: str = DEFAULT_DATABASE_PATH) -> "BaseSQLiteRepository":
        """Create singleton instance per (class, db_path).

        :param db_path: Path to SQLite database file
        :type db_path: str
        :returns: Singleton instance for class+db_path
        :rtype: BaseSQLiteRepository
        """
        key = f"{cls.__name__}_{db_path}"
        instance = cls._instances.get(key)
        if instance is None:
            with cls._lock:
                instance = cls._instances.get(key)
                if instance is None:
                    instance = super().__new__(cls)
                    cls._instances[key] = instance
        return instance

    def __init__(self, db_path: str = DEFAULT_DATABASE_PATH) -> None:
        """Initialize repository instance minimal state.

        :param db_path: Path to SQLite database file
        :type db_path: str
        """
        key = f"{self.__class__.__name__}_{db_path}"

        # Fast path: already initialized
        if key in self._initialized:
            return

        # Acquire lock for thread-safe initialization
        with self._lock:
            # Double-check after acquiring lock
            if key in self._initialized:
                return

            self.db_path = Path(db_path)
            self.engine: Optional[AsyncEngine] = None
            self.SessionLocal: Optional[async_sessionmaker[AsyncSession]] = None
            self._initialized[key] = True

    async def initialize(self) -> None:
        """Initialize database connection and create tables.

        Ensures a single SQLAlchemy async engine/sessionmaker per ``db_path`` for all
        repository subclasses. Subsequent calls reuse the shared engine/session
        without re-initializing or re-logging.

        :returns: None
        :rtype: None
        :raises SQLAlchemyError: If database initialization fails
        """
        db_key: str = str(self.db_path.resolve())

        # Fast path: already bound for this instance
        if self.engine is not None and self.SessionLocal is not None:
            return

        with self._lock:
            # Reuse shared engine/sessionmaker if already created for this db_path
            if db_key in self._engines and db_key in self._sessions:
                self.engine = self._engines[db_key]
                self.SessionLocal = self._sessions[db_key]
                return

            # Create new async engine/sessionmaker for this db_path
            try:
                engine = create_async_engine(
                    url=f"sqlite+aiosqlite:///{self.db_path}",
                    echo=SQLITE_ECHO,
                    pool_pre_ping=SQLITE_POOL_PRE_PING,
                )

                # Create tables using run_sync
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                session_local: async_sessionmaker[AsyncSession] = async_sessionmaker(
                    bind=engine,
                    autocommit=False,
                    autoflush=False,
                    expire_on_commit=False,
                )

                # Store in shared registries
                self._engines[db_key] = engine
                self._sessions[db_key] = session_local

                # Bind to this instance
                self.engine = engine
                self.SessionLocal = session_local

                # Log only once per db_path
                if db_key not in self._initialized_once_logged:
                    logger.info(f"SQLite database initialized at {self.db_path}")
                    self._initialized_once_logged.add(db_key)

            except SQLAlchemyError as e:
                logger.error(f"Failed to initialize SQLite database: {e}")
                # Ensure partial initialization does not leave invalid state
                if db_key in self._engines:
                    try:
                        await self._engines[db_key].dispose()
                    except Exception:
                        pass
                    finally:
                        self._engines.pop(db_key, None)
                self._sessions.pop(db_key, None)
                self.engine = None
                self.SessionLocal = None
                raise

    async def close(self) -> None:
        """Close database connection and cleanup resources.

        Note: The engine/session are shared across repositories for the same
        ``db_path``. This method disposes the shared engine and clears the
        registries for that path. Use cautiously (primarily in tests).

        :returns: None
        :rtype: None
        """
        db_key: str = str(self.db_path.resolve())
        if db_key in self._engines:
            try:
                await self._engines[db_key].dispose()
            finally:
                self._engines.pop(db_key, None)
                self._sessions.pop(db_key, None)
                self._initialized_once_logged.discard(db_key)
                self.engine = None
                self.SessionLocal = None
                logger.info("SQLite database connection closed")

    @classmethod
    def reset_instances(cls) -> None:
        """Reset all singleton instances and shared registries (for testing).

        :returns: None
        :rtype: None
        """
        with cls._lock:
            # Dispose all engines - need to run in event loop
            for engine in list(cls._engines.values()):
                try:
                    # Run dispose in a new event loop if not in async context
                    try:
                        loop = asyncio.get_running_loop()
                        # Already in async context - schedule for later
                        loop.create_task(engine.dispose())
                    except RuntimeError:
                        # No running loop - create one
                        asyncio.run(engine.dispose())
                except Exception:
                    pass
            cls._engines.clear()
            cls._sessions.clear()
            cls._initialized_once_logged.clear()

            # Close and clear per-instance caches
            for instance in cls._instances.values():
                instance.engine = None
                instance.SessionLocal = None
            cls._instances.clear()
            cls._initialized.clear()

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
        if not self.SessionLocal:
            raise RuntimeError("Repository not initialized")

        async with self.SessionLocal() as session:
            try:
                yield session
                await session.commit()
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Database error in {self.__class__.__name__}: {e}")
                raise

    def _detach_instance(self, session: AsyncSession, instance: Any) -> None:
        """Detach instance from session while keeping its state.

        :param session: Database session
        :type session: AsyncSession
        :param instance: SQLAlchemy model instance to detach
        :type instance: Any
        :returns: None
        :rtype: None
        """
        if instance and instance in session:
            session.expunge(instance)

    async def _create_entity(self, entity: ModelType, entity_name: str) -> bool:
        """Generic async method to create an entity.

        :param entity: Entity object to create
        :type entity: ModelType
        :param entity_name: Name of entity for logging
        :type entity_name: str
        :returns: True if successful, False otherwise
        :rtype: bool
        """
        try:
            async with self.async_session() as session:
                session.add(entity)
                logger.info(f"Created {entity_name}")
                return True

        except IntegrityError:
            logger.warning(f"{entity_name} already exists")
            return False
        except Exception as e:
            logger.error(f"Failed to create {entity_name}: {e}")
            return False

    async def _get_entity_by_telegram_id(
        self, model_class: Type[ModelType], telegram_id: int, entity_name: str
    ) -> Optional[ModelType]:
        """Generic async method to get entity by telegram_id.

        :param model_class: SQLAlchemy model class
        :type model_class: Type[ModelType]
        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :param entity_name: Name of entity for logging
        :type entity_name: str
        :returns: Entity object if found, None otherwise
        :rtype: Optional[ModelType]
        """
        try:
            async with self.async_session() as session:
                stmt = select(model_class).where(model_class.telegram_id == telegram_id)
                result = await session.execute(stmt)
                entity = result.scalar_one_or_none()
                if entity:
                    self._detach_instance(session, entity)
                return entity

        except Exception as e:
            logger.error(f"Failed to get {entity_name} {telegram_id}: {e}")
            return None

    async def _delete_entity_by_telegram_id(
        self, model_class: Type[ModelType], telegram_id: int, entity_name: str
    ) -> bool:
        """Generic async method to delete entity by telegram_id.

        :param model_class: SQLAlchemy model class
        :type model_class: Type[ModelType]
        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :param entity_name: Name of entity for logging
        :type entity_name: str
        :returns: True if successful, False otherwise
        :rtype: bool
        """
        try:
            async with self.async_session() as session:
                stmt = delete(model_class).where(model_class.telegram_id == telegram_id)
                result = await session.execute(stmt)

                if result.rowcount > 0:
                    logger.info(f"Deleted {entity_name} for user {telegram_id}")
                    return True
                else:
                    logger.warning(f"{entity_name} for user {telegram_id} not found")
                    return False

        except Exception as e:
            logger.error(f"Failed to delete {entity_name}: {e}")
            return False

    async def _get_all_entities(
        self, model_class: Type[ModelType], entity_name: str
    ) -> list[ModelType]:
        """Generic async method to get all entities.

        :param model_class: SQLAlchemy model class
        :type model_class: Type[ModelType]
        :param entity_name: Name of entity for logging
        :type entity_name: str
        :returns: List of all entity objects
        :rtype: list[ModelType]
        """
        try:
            async with self.async_session() as session:
                stmt = select(model_class)
                result = await session.execute(stmt)
                entities = list(result.scalars().all())
                # Detach all objects from session
                for entity in entities:
                    self._detach_instance(session, entity)
                return entities

        except Exception as e:
            logger.error(f"Failed to get all {entity_name}: {e}")
            return []
