"""Database service layer for LifeWeeksBot.

This module provides high-level business logic for database operations,
working with models and repositories to handle complex operations.
"""

from datetime import UTC, date, datetime, timedelta
from typing import Optional

from ..utils.config import BOT_NAME
from ..utils.logger import get_logger
from .models import (
    User,
    UserSettings,
    UserSubscription,
    SubscriptionType,
    DEFAULT_SUBSCRIPTION_EXPIRATION_DAYS,
)
from .repositories.sqlite.user_repository import SQLiteUserRepository
from .repositories.sqlite.user_settings_repository import SQLiteUserSettingsRepository
from .repositories.sqlite.user_subscription_repository import (
    SQLiteUserSubscriptionRepository,
)

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
    """Service for managing user data in the database."""

    def __init__(
        self,
        user_repository: Optional[SQLiteUserRepository] = None,
        settings_repository: Optional[SQLiteUserSettingsRepository] = None,
        subscription_repository: Optional[SQLiteUserSubscriptionRepository] = None,
    ):
        """Initialize user service.

        :param user_repository: User repository instance
        :param settings_repository: User settings repository instance
        :param subscription_repository: User subscription repository instance
        """
        self.user_repository = user_repository or SQLiteUserRepository()
        self.settings_repository = settings_repository or SQLiteUserSettingsRepository()
        self.subscription_repository = (
            subscription_repository or SQLiteUserSubscriptionRepository()
        )

    def initialize(self) -> None:
        """Initialize database connections."""
        self.user_repository.initialize()
        self.settings_repository.initialize()
        self.subscription_repository.initialize()

    def close(self) -> None:
        """Close database connections."""
        self.user_repository.close()
        self.settings_repository.close()
        self.subscription_repository.close()

    def create_user_with_settings(
        self,
        user_info,
        birth_date: date,
        subscription_type: SubscriptionType,
    ) -> Optional[User]:
        """Create new user with default settings.

        :param user_info: Telegram User object
        :param birth_date: User's birth date
        :param subscription_type: User's subscription type
        :returns: Created user object if successful, None otherwise
        """
        try:
            # Check if user already exists
            existing_user = self.get_user_profile(user_info.id)
            if existing_user:
                logger.warning(f"User with telegram_id {user_info.id} already exists")
                return existing_user

            # Create user
            user = User(
                telegram_id=user_info.id,
                username=user_info.username,
                first_name=user_info.first_name,
                last_name=user_info.last_name,
                created_at=datetime.now(UTC),
            )

            # Create default settings with birth date if provided
            settings = UserSettings(
                telegram_id=user_info.id,
                birth_date=birth_date,
                updated_at=datetime.now(UTC),
            )

            # Set subscription type
            subscription = UserSubscription(
                telegram_id=user_info.id,
                subscription_type=subscription_type,
                is_active=True,
                created_at=datetime.now(UTC),
                expires_at=datetime.now(UTC)
                + timedelta(days=DEFAULT_SUBSCRIPTION_EXPIRATION_DAYS),
            )

            # Save to database
            if self.user_repository.create_user(user):
                # Try to create settings
                if not self.settings_repository.create_user_settings(settings):
                    # Rollback user creation if settings creation failed
                    self.user_repository.delete_user(user_info.id)
                    logger.error(f"Failed to create settings for {user_info.id}")
                    return None

                # Try to create subscription
                if not self.subscription_repository.create_subscription(subscription):
                    # Rollback user and settings creation if subscription creation failed
                    self.settings_repository.delete_user_settings(user_info.id)
                    self.user_repository.delete_user(user_info.id)
                    logger.error(f"Failed to create subscription for {user_info.id}")
                    return None

                # All operations successful
                logger.info(f"Created complete user profile for {user_info.id}")
                return self.get_user_profile(user_info.id)
            else:
                logger.error(f"Failed to create user {user_info.id}")
                return None

        except Exception as error:
            logger.error(f"Error creating user profile: {error}")
            return None

    def get_user_profile(self, telegram_id: int) -> Optional[User]:
        """Get complete user profile with settings and subscription.

        :param telegram_id: Telegram user ID
        :returns: User object with settings and subscription if found, None otherwise
        """
        try:
            user = self.user_repository.get_user(telegram_id)
            if not user:
                logger.warning(f"User {telegram_id} not found")
                return None

            settings = self.settings_repository.get_user_settings(telegram_id)
            if not settings:
                logger.warning(f"Settings not found for user {telegram_id}")
                return None

            subscription = self.subscription_repository.get_subscription(telegram_id)
            if not subscription:
                logger.warning(f"Subscription not found for user {telegram_id}")
                return None

            new_user = User(
                telegram_id=user.telegram_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                created_at=user.created_at,
            )
            new_user.settings = settings
            new_user.subscription = subscription
            return new_user

        except Exception as e:
            logger.error(f"Error getting user profile for {telegram_id}: {e}")
            return None

    def user_exists(self, telegram_id: int) -> bool:
        """Check if user exists.

        :param telegram_id: Telegram user ID
        :returns: True if user exists, False otherwise
        """
        try:
            user = self.get_user_profile(telegram_id)
            return user is not None and user.settings is not None
        except Exception as e:
            logger.error(f"Error checking user existence for {telegram_id}: {e}")
            return False

    def is_valid_user_profile(self, telegram_id: int) -> bool:
        """Check if user has a valid profile with birth date.

        :param telegram_id: Telegram user ID
        :returns: True if profile is valid, False otherwise
        """
        try:
            settings = self.settings_repository.get_user_settings(telegram_id)
            return settings is not None and settings.birth_date is not None
        except Exception as e:
            logger.error(f"Error checking user profile validity for {telegram_id}: {e}")
            return False

    def delete_user(self, telegram_id: int) -> bool:
        """Delete user and all associated data.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :returns: True if successful, False otherwise
        :rtype: bool
        """
        try:
            success = self.user_repository.delete_user(telegram_id)
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
            settings_deleted = self.settings_repository.delete_user_settings(
                telegram_id
            )
            if settings_deleted:
                logger.info(f"Deleted settings for user {telegram_id}")
            else:
                logger.warning(
                    f"No settings found for user {telegram_id} (this is OK if user was not fully registered)"
                )

            # Step 2: Delete user record
            user_deleted = self.user_repository.delete_user(telegram_id)
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


# Global service instance
user_service = UserService()
