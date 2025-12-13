"""SQLite implementation of user repository.

Provides SQLite-based async implementation of AbstractUserRepository
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
    """SQLite async implementation of user repository.

    Handles all async database operations for user data using SQLite as the backend storage.
    """

    async def create_user(self, user: User) -> bool:
        """Create a new user in the database.

        :param user: User object to create
        :type user: User
        :returns: True if successful, False otherwise
        :rtype: bool
        """
        return await self._create_entity(
            entity=user,
            entity_name=f"user with telegram_id: {user.telegram_id}",
        )

    async def get_user(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :returns: User object if found, None otherwise
        :rtype: Optional[User]
        """
        return await self._get_entity_by_telegram_id(
            model_class=User,
            telegram_id=telegram_id,
            entity_name="user",
        )

    async def delete_user(self, telegram_id: int) -> bool:
        """Delete user and all associated data.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :returns: True if successful, False otherwise
        :rtype: bool
        """
        return await self._delete_entity_by_telegram_id(
            model_class=User,
            telegram_id=telegram_id,
            entity_name="user",
        )
