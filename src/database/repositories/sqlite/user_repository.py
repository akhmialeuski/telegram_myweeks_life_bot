"""SQLite implementation of user repository.

Provides SQLite-based implementation of AbstractUserRepository
for storing user data in SQLite database.
"""

import logging
from typing import Optional

from ....utils.config import BOT_NAME
from ...models.user import User
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

    def delete_user(self, telegram_id: int) -> bool:
        """Delete user and all associated data.

        :param telegram_id: Telegram user ID
        :returns: True if successful, False otherwise
        """
        return self._delete_entity_by_telegram_id(User, telegram_id, "user")
