"""Abstract repository interface for user settings operations.

Defines the contract for user settings storage operations
that can be implemented by different database backends.
"""

from abc import ABC, abstractmethod
from datetime import date, time
from typing import Optional

from ...models import UserSettings


class AbstractUserSettingsRepository(ABC):
    """Abstract base class for user settings repository operations.

    Defines the interface for user settings storage that can be implemented
    by different database backends (SQLite, PostgreSQL, etc.)
    """

    @abstractmethod
    def initialize(self) -> None:
        """Initialize database connection and create tables.

        :returns: None
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connection.

        :returns: None
        """
        pass

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

    @abstractmethod
    def set_birth_date(self, telegram_id: int, birth_date: date) -> bool:
        """Set user birth date.

        :param telegram_id: Telegram user ID
        :param birth_date: Birth date to set
        :returns: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_birth_date(self, telegram_id: int) -> Optional[date]:
        """Get user birth date.

        :param telegram_id: Telegram user ID
        :returns: Birth date if set, None otherwise
        """
        pass

    @abstractmethod
    def set_notification_settings(
        self,
        telegram_id: int,
        notifications: bool,
        notifications_day: Optional[str] = None,
        notifications_time: Optional[time] = None,
    ) -> bool:
        """Set notification settings.

        :param telegram_id: Telegram user ID
        :param notifications: Whether notifications are enabled
        :param notifications_day: Day of week for notifications
        :param notifications_time: Time for notifications
        :returns: True if successful, False otherwise
        """
        pass
