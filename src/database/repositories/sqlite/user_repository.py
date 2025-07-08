"""SQLite implementation of user repository.

Provides SQLite-based implementation of AbstractUserRepository
for storing user data in SQLite database.
"""

import logging
from typing import List, Optional

from sqlalchemy import update
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
        return self._create_entity(user, f"user with telegram_id: {user.telegram_id}")

    def get_user(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID.

        :param telegram_id: Telegram user ID
        :returns: User object if found, None otherwise
        """
        return self._get_entity_by_telegram_id(User, telegram_id, "user")

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
        return self._delete_entity_by_telegram_id(User, telegram_id, "user")
