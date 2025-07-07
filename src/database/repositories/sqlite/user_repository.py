"""SQLite implementation of user repository.

Provides SQLite-based implementation of AbstractUserRepository
for storing user data in SQLite database.
"""

import logging
from typing import List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from ....utils.config import BOT_NAME
from ...models import User
from ..abstract.user_repository import AbstractUserRepository
from .base_repository import BaseSQLiteRepository

logger = logging.getLogger(BOT_NAME)


class SQLiteUserRepository(BaseSQLiteRepository, AbstractUserRepository):
    """SQLite implementation of user repository.

    Handles all database operations for user data using SQLite as the backend storage.
    """

    def create_user(self, user: User) -> bool:
        """Create a new user in the database.

        :param user: User object to create
        :returns: True if successful, False otherwise
        """
        try:
            with self.session() as session:
                session.add(user)
                logger.info(f"Created user with telegram_id: {user.telegram_id}")
                return True

        except IntegrityError:
            logger.warning(f"User with telegram_id {user.telegram_id} already exists")
            return False
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return False

    def get_user(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID.

        :param telegram_id: Telegram user ID
        :returns: User object if found, None otherwise
        """
        try:
            with self.session() as session:
                stmt = select(User).where(User.telegram_id == telegram_id)
                result = session.execute(stmt)
                user = result.scalar_one_or_none()
                if user:
                    self._detach_instance(session, user)
                return user

        except Exception as e:
            logger.error(f"Failed to get user {telegram_id}: {e}")
            return None

    def update_user(self, user: User) -> bool:
        """Update existing user information.

        :param user: User object with updated data
        :returns: True if successful, False otherwise
        """
        try:
            with self.session() as session:
                stmt = (
                    update(User)
                    .where(User.telegram_id == user.telegram_id)
                    .values(
                        username=user.username,
                        first_name=user.first_name,
                        last_name=user.last_name,
                    )
                )
                result = session.execute(stmt)

                if result.rowcount > 0:
                    logger.info(f"Updated user with telegram_id: {user.telegram_id}")
                    return True
                else:
                    logger.warning(
                        f"User with telegram_id {user.telegram_id} not found"
                    )
                    return False

        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            return False

    def delete_user(self, telegram_id: int) -> bool:
        """Delete user and all associated data.

        :param telegram_id: Telegram user ID
        :returns: True if successful, False otherwise
        """
        try:
            with self.session() as session:
                stmt = delete(User).where(User.telegram_id == telegram_id)
                result = session.execute(stmt)

                if result.rowcount > 0:
                    logger.info(f"Deleted user with telegram_id: {telegram_id}")
                    return True
                else:
                    logger.warning(f"User with telegram_id {telegram_id} not found")
                    return False

        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            return False

    def get_all_users(self) -> List[User]:
        """Get all users from database.

        :returns: List of all User objects
        """
        try:
            with self.session() as session:
                stmt = select(User)
                result = session.execute(stmt)
                users = list(result.scalars().all())
                # Отсоединяем все объекты от сессии
                for user in users:
                    self._detach_instance(session, user)
                return users

        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            return []
