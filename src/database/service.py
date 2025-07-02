"""Database service layer for LifeWeeksBot.

This module provides high-level business logic for database operations,
working with models and repositories to handle complex operations.
"""

from datetime import UTC, date, datetime
from typing import Optional

from telegram import User as TelegramUser

from ..utils.config import BOT_NAME
from ..utils.logger import get_logger
from .models import User, UserSettings
from .sqlite_repository import SQLAlchemyUserRepository

logger = get_logger(f"{BOT_NAME}.DatabaseService")


class UserServiceError(Exception):
    """Base exception for user service operations.

    This exception is raised when user service operations fail
    due to database errors, validation issues, or other problems.
    """

    pass


class UserNotFoundError(UserServiceError):
    """Exception raised when a user is not found in the database.

    This exception is raised when trying to perform operations
    on a user that doesn't exist in the database.
    """

    pass


class UserDeletionError(UserServiceError):
    """Exception raised when user deletion fails.

    This exception is raised when the system fails to delete
    a user profile from the database.
    """

    pass


class UserProfileError(UserServiceError):
    """Exception raised when user profile operations fail.

    This exception is raised when operations on user profiles
    fail due to database errors or invalid data.
    """

    pass


class UserRegistrationError(UserServiceError):
    """Exception raised when user registration fails.

    This exception is raised when the system fails to register
    a new user in the database.
    """

    pass


class UserAlreadyExistsError(UserServiceError):
    """Exception raised when trying to register an existing user.

    This exception is raised when attempting to register a user
    that already exists in the database.
    """

    pass


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
        user_info: TelegramUser,
        birth_date: date,
        notifications_enabled: bool = True,
        timezone: str = "UTC",
        notifications_day: str = "monday",
        notifications_time: str = "09:00:00",
    ) -> None:
        """Create a new user with settings.

        :param user_info: Telegram user object
        :type user_info: TelegramUser
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
        :raises UserRegistrationError: If user registration fails
        :raises UserAlreadyExistsError: If user already exists
        :raises UserServiceError: If any other service operation fails
        """
        try:
            # Check if user already exists
            existing_user = self.repository.get_user_profile(user_info.id)
            if existing_user:
                error_msg = f"User with telegram_id {user_info.id} already exists"
                logger.warning(error_msg)
                raise UserAlreadyExistsError(error_msg)

            # Parse notifications time
            parsed_time = datetime.strptime(notifications_time, "%H:%M:%S").time()

            # Create user object
            user = User(
                telegram_id=user_info.id,
                username=user_info.username,
                first_name=user_info.first_name,
                last_name=user_info.last_name,
                created_at=datetime.now(UTC),
            )

            # Create settings object
            settings = UserSettings(
                telegram_id=user_info.id,
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
                logger.info(f"Created user profile for telegram_id: {user_info.id}")
            else:
                error_msg = f"Failed to create user profile in database for telegram_id: {user_info.id}"
                logger.error(error_msg)
                raise UserRegistrationError(error_msg)

        except UserAlreadyExistsError:
            # Re-raise UserAlreadyExistsError as-is
            raise
        except UserRegistrationError:
            # Re-raise UserRegistrationError as-is
            raise
        except Exception as error:
            error_msg = f"Error creating user profile for telegram_id {user_info.id}: {str(error)}"
            logger.error(error_msg)
            raise UserServiceError(error_msg) from error

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

    def delete_user_profile(self, telegram_id: int) -> None:
        """Delete user profile by first removing settings, then user.

        This method ensures complete removal of user data by:
        1. First deleting all user settings
        2. Then deleting the user record itself

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :raises UserDeletionError: If user deletion fails
        :raises UserServiceError: If any other service operation fails
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
            else:
                error_msg = f"Failed to delete user record for {telegram_id}"
                logger.error(error_msg)
                raise UserDeletionError(error_msg)

        except UserDeletionError:
            # Re-raise UserDeletionError as-is
            raise
        except Exception as e:
            error_msg = (
                f"Error during complete profile deletion for user {telegram_id}: {e}"
            )
            logger.error(error_msg)
            raise UserServiceError(error_msg) from e

    def close(self) -> None:
        """Close database connection."""
        if self.repository:
            self.repository.close()
            logger.info("Database service connection closed")


# Global service instance
user_service = UserService()
