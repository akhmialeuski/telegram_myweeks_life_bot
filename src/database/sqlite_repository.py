"""SQLAlchemy 2.0 implementation of user repository.

Provides SQLAlchemy-based implementation of AbstractUserRepository
for storing user data in SQLite database.
"""

import logging
from typing import Optional, List
from datetime import datetime, date, time, UTC
from pathlib import Path

from sqlalchemy import create_engine, select, update, delete
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .abstract_repository import AbstractUserRepository
from .models import Base, User, UserSettings
from .constants import DEFAULT_DATABASE_PATH, SQLITE_ECHO, SQLITE_POOL_PRE_PING


logger = logging.getLogger('myweeks_bot')


class SQLAlchemyUserRepository(AbstractUserRepository):
    """SQLAlchemy 2.0 implementation of user repository.

    Handles all database operations for user profiles and settings
    using SQLAlchemy ORM with SQLite as the backend storage.
    """

    def __init__(self, db_path: str = DEFAULT_DATABASE_PATH):
        """Initialize SQLAlchemy repository.

        :param db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.engine = None
        self.SessionLocal = None
        self._session: Optional[Session] = None

    def initialize(self) -> None:
        """Initialize database connection and create tables.

        Creates the database file and tables if they don't exist
        """
        try:
            # Create engine
            self.engine = create_engine(
                f"sqlite:///{self.db_path}",
                echo=SQLITE_ECHO,  # Use constant for SQL logging
                pool_pre_ping=SQLITE_POOL_PRE_PING
            )

            # Create session factory
            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )

            # Create tables
            Base.metadata.create_all(bind=self.engine)
            logger.info(f"SQLAlchemy database initialized at {self.db_path}")

        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize SQLAlchemy database: {e}")
            raise

    def close(self) -> None:
        """Close database connection."""
        if self._session:
            self._session.close()
            self._session = None

        if self.engine:
            self.engine.dispose()
            self.engine = None
            logger.info("SQLAlchemy database connection closed")

    def _get_session(self) -> Session:
        """Get database session.

        :returns: Database session
        """
        if not self._session:
            self._session = self.SessionLocal()
        return self._session

    def create_user(self, user: User) -> bool:
        """Create a new user in the database.

        :param user: User object to create
        :returns: True if successful, False otherwise
        """
        session = self._get_session()
        try:
            session.add(user)
            session.commit()
            logger.info(f"Created user with telegram_id: {user.telegram_id}")
            return True

        except IntegrityError:
            session.rollback()
            logger.warning(f"User with telegram_id {user.telegram_id} already exists")
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to create user: {e}")
            return False

    def get_user(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID.

        :param telegram_id: Telegram user ID
        :returns: User object if found, None otherwise
        """
        session = self._get_session()
        try:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = session.execute(stmt)
            user = result.scalar_one_or_none()
            return user

        except SQLAlchemyError as e:
            logger.error(f"Failed to get user {telegram_id}: {e}")
            return None

    def update_user(self, user: User) -> bool:
        """Update existing user information.

        :param user: User object with updated data
        :returns: True if successful, False otherwise
        """
        session = self._get_session()
        try:
            stmt = (
                update(User)
                .where(User.telegram_id == user.telegram_id)
                .values(
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
            )
            result = session.execute(stmt)
            session.commit()

            if result.rowcount > 0:
                logger.info(f"Updated user with telegram_id: {user.telegram_id}")
                return True
            else:
                logger.warning(f"User with telegram_id {user.telegram_id} not found")
                return False

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to update user: {e}")
            return False

    def delete_user(self, telegram_id: int) -> bool:
        """Delete user and all associated settings.

        :param telegram_id: Telegram user ID
        :returns: True if successful, False otherwise
        """
        session = self._get_session()
        try:
            stmt = delete(User).where(User.telegram_id == telegram_id)
            result = session.execute(stmt)
            session.commit()

            if result.rowcount > 0:
                logger.info(f"Deleted user with telegram_id: {telegram_id}")
                return True
            else:
                logger.warning(f"User with telegram_id {telegram_id} not found")
                return False

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to delete user: {e}")
            return False

    def get_all_users(self) -> List[User]:
        """Get all users from database.

        :returns: List of all User objects
        """
        session = self._get_session()
        try:
            stmt = select(User)
            result = session.execute(stmt)
            users = result.scalars().all()
            return list(users)

        except SQLAlchemyError as e:
            logger.error(f"Failed to get all users: {e}")
            return []

    def create_user_settings(self, settings: UserSettings) -> bool:
        """Create user settings.

        :param settings: UserSettings object to create
        :returns: True if successful, False otherwise
        """
        session = self._get_session()
        try:
            session.add(settings)
            session.commit()
            logger.info(f"Created settings for user {settings.telegram_id}")
            return True

        except IntegrityError:
            session.rollback()
            logger.warning(f"Settings for user {settings.telegram_id} already exist")
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to create user settings: {e}")
            return False

    def get_user_settings(self, telegram_id: int) -> Optional[UserSettings]:
        """Get user settings by Telegram ID.

        :param telegram_id: Telegram user ID
        :returns: UserSettings object if found, None otherwise
        """
        session = self._get_session()
        try:
            stmt = select(UserSettings).where(UserSettings.telegram_id == telegram_id)
            result = session.execute(stmt)
            settings = result.scalar_one_or_none()
            return settings

        except SQLAlchemyError as e:
            logger.error(f"Failed to get user settings {telegram_id}: {e}")
            return None

    def update_user_settings(self, settings: UserSettings) -> bool:
        """Update user settings.

        :param settings: UserSettings object with updated data
        :returns: True if successful, False otherwise
        """
        session = self._get_session()
        try:
            stmt = (
                update(UserSettings)
                .where(UserSettings.telegram_id == settings.telegram_id)
                .values(
                    birth_date=settings.birth_date,
                    notifications_day=settings.notifications_day,
                    life_expectancy=settings.life_expectancy,
                    timezone=settings.timezone,
                    notifications=settings.notifications,
                    notifications_time=settings.notifications_time,
                    updated_at=datetime.now(UTC)
                )
            )
            result = session.execute(stmt)
            session.commit()

            if result.rowcount > 0:
                logger.info(f"Updated settings for user {settings.telegram_id}")
                return True
            else:
                logger.warning(f"Settings for user {settings.telegram_id} not found")
                return False

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to update user settings: {e}")
            return False

    def delete_user_settings(self, telegram_id: int) -> bool:
        """Delete user settings.

        :param telegram_id: Telegram user ID
        :returns: True if successful, False otherwise
        """
        session = self._get_session()
        try:
            stmt = delete(UserSettings).where(UserSettings.telegram_id == telegram_id)
            result = session.execute(stmt)
            session.commit()

            if result.rowcount > 0:
                logger.info(f"Deleted settings for user {telegram_id}")
                return True
            else:
                logger.warning(f"Settings for user {telegram_id} not found")
                return False

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to delete user settings: {e}")
            return False

    def get_user_profile(self, telegram_id: int) -> Optional[User]:
        """Get complete user profile with settings.

        :param telegram_id: Telegram user ID
        :returns: User object with settings if found, None otherwise
        """
        user = self.get_user(telegram_id)
        if not user:
            return None

        # Load settings relationship
        session = self._get_session()
        try:
            session.refresh(user, ['settings'])
            return user
        except SQLAlchemyError as e:
            logger.error(f"Failed to load user profile {telegram_id}: {e}")
            return None

    def create_user_profile(self, user: User, settings: UserSettings) -> bool:
        """Create complete user profile with settings.

        :param user: User object to create
        :param settings: UserSettings object to create
        :returns: True if successful, False otherwise
        """
        session = self._get_session()
        try:
            # Create user first
            session.add(user)
            session.flush()  # Get the user ID

            # Create settings
            session.add(settings)
            session.commit()

            logger.info(f"Created user profile with telegram_id: {user.telegram_id}")
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to create user profile: {e}")
            return False

    def update_user_profile(self, user: User, settings: UserSettings) -> bool:
        """Update complete user profile with settings.

        :param user: User object with updated data
        :param settings: UserSettings object with updated data
        :returns: True if successful, False otherwise
        """
        try:
            # Update user
            if not self.update_user(user):
                return False

            # Update or create settings
            existing_settings = self.get_user_settings(settings.telegram_id)
            if existing_settings:
                return self.update_user_settings(settings)
            else:
                return self.create_user_settings(settings)

        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            return False

    def set_birth_date(self, telegram_id: int, birth_date: date) -> bool:
        """Set user birth date.

        :param telegram_id: Telegram user ID
        :param birth_date: Birth date to set
        :returns: True if successful, False otherwise
        """
        session = self._get_session()
        try:
            # Check if settings exist
            existing_settings = self.get_user_settings(telegram_id)
            if existing_settings:
                existing_settings.birth_date = birth_date
                existing_settings.updated_at = datetime.now(UTC)
                session.commit()
                return True
            else:
                # Create new settings with birth date
                new_settings = UserSettings(
                    telegram_id=telegram_id,
                    birth_date=birth_date,
                    updated_at=datetime.now(UTC)
                )
                return self.create_user_settings(new_settings)

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to set birth date: {e}")
            return False

    def get_birth_date(self, telegram_id: int) -> Optional[date]:
        """Get user birth date.

        :param telegram_id: Telegram user ID
        :returns: Birth date if set, None otherwise
        """
        settings = self.get_user_settings(telegram_id)
        return settings.birth_date if settings else None

    def set_notification_settings(
        self,
        telegram_id: int,
        notifications: bool,
        notifications_day: Optional[str] = None,
        notifications_time: Optional[time] = None
    ) -> bool:
        """Set notification settings.

        :param telegram_id: Telegram user ID
        :param notifications: Whether notifications are enabled
        :param notifications_day: Day of week for notifications
        :param notifications_time: Time for notifications
        :returns: True if successful, False otherwise
        """
        session = self._get_session()
        try:
            # Check if settings exist
            existing_settings = self.get_user_settings(telegram_id)
            if existing_settings:
                existing_settings.notifications = notifications
                existing_settings.notifications_day = notifications_day
                existing_settings.notifications_time = notifications_time
                existing_settings.updated_at = datetime.now(UTC)
                session.commit()
                return True
            else:
                # Create new settings with notification settings
                new_settings = UserSettings(
                    telegram_id=telegram_id,
                    notifications=notifications,
                    notifications_day=notifications_day,
                    notifications_time=notifications_time,
                    updated_at=datetime.now(UTC)
                )
                return self.create_user_settings(new_settings)

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to set notification settings: {e}")
            return False

    def get_users_with_notifications(self) -> List[User]:
        """Get all users who have notifications enabled.

        :returns: List of User objects with notifications enabled
        """
        session = self._get_session()
        try:
            stmt = (
                select(User)
                .join(UserSettings)
                .where(UserSettings.notifications == True)
            )
            result = session.execute(stmt)
            users = result.scalars().all()

            # Load settings for each user
            for user in users:
                session.refresh(user, ['settings'])

            return list(users)

        except SQLAlchemyError as e:
            logger.error(f"Failed to get users with notifications: {e}")
            return []
