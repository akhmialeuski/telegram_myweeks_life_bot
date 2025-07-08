"""Abstract repository interface for user operations.

Defines the contract for user data storage operations
that can be implemented by different database backends.
"""

from abc import abstractmethod
from typing import List, Optional

from ...models import User
from .base_repository import AbstractBaseRepository


class AbstractUserRepository(AbstractBaseRepository):
    """Abstract base class for user repository operations.

    Defines the interface for user data storage that can be implemented
    by different database backends (SQLite, PostgreSQL, etc.)
    """

    @abstractmethod
    def create_user(self, user: User) -> bool:
        """Create a new user in the database.

        :param user: User object to create
        :returns: True if successful, False otherwise
        :raises: DatabaseError if user already exists or other database error
        """
        pass

    @abstractmethod
    def get_user(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID.

        :param telegram_id: Telegram user ID
        :returns: User object if found, None otherwise
        """
        pass

    @abstractmethod
    def update_user(self, user: User) -> bool:
        """Update existing user information.

        :param user: User object with updated data
        :returns: True if successful, False otherwise
        :raises: DatabaseError if user not found or other database error
        """
        pass

    @abstractmethod
    def delete_user(self, telegram_id: int) -> bool:
        """Delete user and all associated data.

        :param telegram_id: Telegram user ID
        :returns: True if successful, False otherwise
        """
