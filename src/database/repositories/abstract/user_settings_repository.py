"""Abstract repository interface for user settings operations.

Defines the contract for user settings storage operations
that can be implemented by different database backends.
"""

from abc import abstractmethod
from typing import Optional

from .base_repository import AbstractBaseRepository
from ...models import UserSettings


class AbstractUserSettingsRepository(AbstractBaseRepository):
    """Abstract base class for user settings repository operations.

    Defines the interface for user settings storage that can be implemented
    by different database backends (SQLite, PostgreSQL, etc.)
    """

    @abstractmethod
    def create_user_settings(self, settings: UserSettings) -> bool:
        """Create user settings.

        :param settings: UserSettings object to create
        :returns: True if successful, False otherwise
        :raises: DatabaseError if settings already exist or other database error
        """
        pass

    @abstractmethod
    def get_user_settings(self, telegram_id: int) -> Optional[UserSettings]:
        """Get user settings by Telegram ID.

        :param telegram_id: Telegram user ID
        :returns: UserSettings object if found, None otherwise
        """
        pass

    @abstractmethod
    def update_user_settings(self, settings: UserSettings) -> bool:
        """Update user settings.

        :param settings: UserSettings object with updated data
        :returns: True if successful, False otherwise
        :raises: DatabaseError if settings not found or other database error
        """
        pass

    @abstractmethod
    def delete_user_settings(self, telegram_id: int) -> bool:
        """Delete user settings.

        :param telegram_id: Telegram user ID
        :returns: True if successful, False otherwise
        """
        pass
