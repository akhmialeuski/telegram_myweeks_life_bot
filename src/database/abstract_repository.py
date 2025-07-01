"""Abstract repository interface for database operations

Defines the contract for user data storage operations
that can be implemented by different database backends.
"""

from abc import ABC, abstractmethod
from datetime import date, time
from typing import List, Optional

from .models import User, UserSettings


class AbstractUserRepository(ABC):
    """Abstract base class for user repository operations

    Defines the interface for user data storage that can be implemented
    by different database backends (SQLite, PostgreSQL, etc.)
    """

    @abstractmethod
    def initialize(self) -> None:
        """Initialize database connection and create tables if needed

        Should be called before any other operations
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connection and cleanup resources"""
        pass

    # User operations
    @abstractmethod
    def create_user(self, user: User) -> bool:
        """Create a new user in the database

        :param user: User object to create
        :returns: True if successful, False otherwise
        :raises: DatabaseError if user already exists or other database error
        """
        pass

    @abstractmethod
    def get_user(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID

        :param telegram_id: Telegram user ID
        :returns: User object if found, None otherwise
        """
        pass

    @abstractmethod
    def update_user(self, user: User) -> bool:
        """Update existing user information

        :param user: User object with updated data
        :returns: True if successful, False otherwise
        :raises: DatabaseError if user not found or other database error
        """
        pass

    @abstractmethod
    def delete_user(self, telegram_id: int) -> bool:
        """Delete user and all associated settings

        :param telegram_id: Telegram user ID
        :returns: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_all_users(self) -> List[User]:
        """Get all users from database

        :returns: List of all User objects
        """
        pass

    # User settings operations
    @abstractmethod
    def create_user_settings(self, settings: UserSettings) -> bool:
        """Create user settings

        :param settings: UserSettings object to create
        :returns: True if successful, False otherwise
        :raises: DatabaseError if settings already exist or other database error
        """
        pass

    @abstractmethod
    def get_user_settings(self, telegram_id: int) -> Optional[UserSettings]:
        """Get user settings by Telegram ID

        :param telegram_id: Telegram user ID
        :returns: UserSettings object if found, None otherwise
        """
        pass

    @abstractmethod
    def update_user_settings(self, settings: UserSettings) -> bool:
        """Update user settings

        :param settings: UserSettings object with updated data
        :returns: True if successful, False otherwise
        :raises: DatabaseError if settings not found or other database error
        """
        pass

    @abstractmethod
    def delete_user_settings(self, telegram_id: int) -> bool:
        """Delete user settings

        :param telegram_id: Telegram user ID
        :returns: True if successful, False otherwise
        """
        pass

    # Combined operations
    @abstractmethod
    def get_user_profile(self, telegram_id: int) -> Optional[User]:
        """Get complete user profile with settings

        :param telegram_id: Telegram user ID
        :returns: User object with settings if found, None otherwise
        """
        pass

    @abstractmethod
    def create_user_profile(self, user: User, settings: UserSettings) -> bool:
        """Create complete user profile with settings

        :param user: User object to create
        :param settings: UserSettings object to create
        :returns: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def update_user_profile(self, user: User, settings: UserSettings) -> bool:
        """Update complete user profile with settings

        :param user: User object with updated data
        :param settings: UserSettings object with updated data
        :returns: True if successful, False otherwise
        """
        pass

    # Specific settings operations
    @abstractmethod
    def set_birth_date(self, telegram_id: int, birth_date: date) -> bool:
        """Set user birth date

        :param telegram_id: Telegram user ID
        :param birth_date: Birth date to set
        :returns: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_birth_date(self, telegram_id: int) -> Optional[date]:
        """Get user birth date

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
        """Set notification settings

        :param telegram_id: Telegram user ID
        :param notifications: Whether notifications are enabled
        :param notifications_day: Day of week for notifications
        :param notifications_time: Time for notifications
        :returns: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_users_with_notifications(self) -> List[User]:
        """Get all users who have notifications enabled

        :returns: List of User objects with notifications enabled
        """
        pass
