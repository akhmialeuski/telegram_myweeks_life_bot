"""Abstract repository interface for user operations.

Defines the contract for user data storage operations
that can be implemented by different database backends.
"""

from abc import abstractmethod
from typing import Optional

from ...models.user import User
from .base_repository import AbstractBaseRepository


class AbstractUserRepository(AbstractBaseRepository):
    """Abstract base class for user repository operations.

    Defines the interface for user data storage that can be implemented
    by different database backends (SQLite, PostgreSQL, etc.)
    """

    @abstractmethod
    async def create_user(self, user: User) -> bool:
        """Create a new user in the database.

        :param user: User object to create
        :type user: User
        :returns: True if successful, False otherwise
        :rtype: bool
        :raises: DatabaseError if user already exists or other database error
        """

    @abstractmethod
    async def get_user(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :returns: User object if found, None otherwise
        :rtype: Optional[User]
        """

    @abstractmethod
    async def delete_user(self, telegram_id: int) -> bool:
        """Delete user and all associated data.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :returns: True if successful, False otherwise
        :rtype: bool
        """
