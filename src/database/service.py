"""Database service layer for LifeWeeksBot.

This module provides high-level business logic for database operations,
working with models and repositories to handle complex operations.
"""

from datetime import UTC, date, datetime
from typing import Optional, Tuple

from ..utils.config import BOT_NAME
from ..utils.logger import get_logger
from .models import User, UserSettings
from .sqlite_repository import SQLAlchemyUserRepository

logger = get_logger(f"{BOT_NAME}.DatabaseService")


class UserService:
    """Service for user-related database operations.

    This service provides high-level business logic for user management,
    including user registration, profile updates, and settings management.
    """

    def __init__(self, repository: Optional[SQLAlchemyUserRepository] = None):
        """Initialize user service.

        :param repository: Database repository instance (optional)
        :type repository: Optional[SQLAlchemyUserRepository]
        """
        self.repository = repository or SQLAlchemyUserRepository()

    def create_user_with_settings(
        self,
        telegram_id: int,
        username: Optional[str],
        first_name: str,
        last_name: Optional[str],
        birth_date: date,
        notifications_enabled: bool = True,
        timezone: str = "UTC",
        notifications_day: str = "monday",
        notifications_time: str = "09:00:00",
    ) -> Tuple[bool, Optional[str]]:
        """Create a new user with settings.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :param username: Telegram username
        :type username: Optional[str]
        :param first_name: User's first name
        :type first_name: str
        :param last_name: User's last name
        :type last_name: Optional[str]
        :param birth_date: User's birth date
        :type birth_date: date
        :param notifications_enabled: Whether notifications are enabled
        :type notifications_enabled: bool
        :param timezone: User's timezone
        :type timezone: str
        :param notifications_day: Day for notifications
        :type notifications_day: str
        :param notifications_time: Time for notifications
        :type notifications_time: str
        :returns: Tuple of (success, error_message)
        :rtype: Tuple[bool, Optional[str]]
        """
        try:
            # Parse notifications time
            parsed_time = datetime.strptime(notifications_time, "%H:%M:%S").time()

            # Create user object
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                created_at=datetime.now(UTC),
            )

            # Create settings object
            settings = UserSettings(
                telegram_id=telegram_id,
                birth_date=birth_date,
                notifications=notifications_enabled,
                timezone=timezone,
                notifications_day=notifications_day,
                notifications_time=parsed_time,
                updated_at=datetime.now(UTC),
            )

            # Save to database
            success = self.repository.create_user_profile(user, settings)

            if success:
                logger.info(f"Created user profile for telegram_id: {telegram_id}")
                return True, None
            else:
                error_msg = "Failed to create user profile in database"
                logger.error(f"{error_msg} for telegram_id: {telegram_id}")
                return False, error_msg

        except Exception as e:
            error_msg = f"Error creating user profile: {str(e)}"
            logger.error(f"{error_msg} for telegram_id: {telegram_id}")
            return False, error_msg

    def get_user_profile(self, telegram_id: int) -> Optional[User]:
        """Get user profile with settings.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :returns: User object with settings if found, None otherwise
        :rtype: Optional[User]
        """
        try:
            return self.repository.get_user_profile(telegram_id)
        except Exception as e:
            logger.error(f"Error getting user profile for {telegram_id}: {e}")
            return None

    def is_valid_user_profile(self, telegram_id: int) -> bool:
        """Check if user has a valid profile with birth date.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :returns: True if user has valid profile with birth date, False otherwise
        :rtype: bool
        """
        try:
            user_profile = self.repository.get_user_profile(telegram_id)
            return (
                user_profile is not None
                and user_profile.settings is not None
                and user_profile.settings.birth_date is not None
            )
        except Exception as e:
            logger.error(f"Error checking user profile validity for {telegram_id}: {e}")
            return False

    def update_user_birth_date(self, telegram_id: int, birth_date: date) -> bool:
        """Update user's birth date.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :param birth_date: New birth date
        :type birth_date: date
        :returns: True if successful, False otherwise
        :rtype: bool
        """
        try:
            success = self.repository.set_birth_date(telegram_id, birth_date)
            if success:
                logger.info(f"Updated birth date for user {telegram_id}")
            else:
                logger.warning(f"Failed to update birth date for user {telegram_id}")
            return success
        except Exception as e:
            logger.error(f"Error updating birth date for user {telegram_id}: {e}")
            return False

    def update_notification_settings(
        self,
        telegram_id: int,
        notifications_enabled: bool,
        notifications_day: Optional[str] = None,
        notifications_time: Optional[str] = None,
    ) -> bool:
        """Update user's notification settings.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :param notifications_enabled: Whether notifications are enabled
        :type notifications_enabled: bool
        :param notifications_day: Day for notifications
        :type notifications_day: Optional[str]
        :param notifications_time: Time for notifications
        :type notifications_time: Optional[str]
        :returns: True if successful, False otherwise
        :rtype: bool
        """
        try:
            parsed_time = None
            if notifications_time:
                parsed_time = datetime.strptime(notifications_time, "%H:%M:%S").time()

            success = self.repository.set_notification_settings(
                telegram_id, notifications_enabled, notifications_day, parsed_time
            )

            if success:
                logger.info(f"Updated notification settings for user {telegram_id}")
            else:
                logger.warning(
                    f"Failed to update notification settings for user {telegram_id}"
                )
            return success
        except Exception as e:
            logger.error(
                f"Error updating notification settings for user {telegram_id}: {e}"
            )
            return False

    def get_users_with_notifications(self) -> list[User]:
        """Get all users with notifications enabled.

        :returns: List of users with notifications enabled
        :rtype: list[User]
        """
        try:
            return self.repository.get_users_with_notifications()
        except Exception as e:
            logger.error(f"Error getting users with notifications: {e}")
            return []

    def delete_user(self, telegram_id: int) -> bool:
        """Delete user and all associated data.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :returns: True if successful, False otherwise
        :rtype: bool
        """
        try:
            success = self.repository.delete_user(telegram_id)
            if success:
                logger.info(f"Deleted user {telegram_id}")
            else:
                logger.warning(f"Failed to delete user {telegram_id}")
            return success
        except Exception as e:
            logger.error(f"Error deleting user {telegram_id}: {e}")
            return False

    def delete_user_profile(self, telegram_id: int) -> bool:
        """Delete user profile by first removing settings, then user.

        This method ensures complete removal of user data by:
        1. First deleting all user settings
        2. Then deleting the user record itself

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :returns: True if successful, False otherwise
        :rtype: bool
        """
        try:
            logger.info(f"Starting complete profile deletion for user {telegram_id}")

            # Step 1: Delete user settings first
            settings_deleted = self.repository.delete_user_settings(telegram_id)
            if settings_deleted:
                logger.info(f"Deleted settings for user {telegram_id}")
            else:
                logger.warning(
                    f"No settings found for user {telegram_id} (this is OK if user was not fully registered)"
                )

            # Step 2: Delete user record
            user_deleted = self.repository.delete_user(telegram_id)
            if user_deleted:
                logger.info(f"Deleted user record for {telegram_id}")
            else:
                logger.warning(f"No user record found for {telegram_id}")

            # Consider success if at least user was deleted (settings might not exist)
            if user_deleted:
                logger.info(
                    f"Successfully completed profile deletion for user {telegram_id}"
                )
                return True
            else:
                logger.warning(f"Failed to delete user record for {telegram_id}")
                return False

        except Exception as e:
            logger.error(
                f"Error during complete profile deletion for user {telegram_id}: {e}"
            )
            return False

    def close(self) -> None:
        """Close database connection."""
        if self.repository:
            self.repository.close()
            logger.info("Database service connection closed")


# Global service instance
user_service = UserService()
