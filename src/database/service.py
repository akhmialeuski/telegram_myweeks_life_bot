"""Database service layer for LifeWeeksBot.

This module provides high-level business logic for database operations,
working with models and repositories to handle complex operations.
"""

import threading
from datetime import UTC, date, datetime, time, timedelta
from typing import Optional

from ..constants import (
    DEFAULT_LIFE_EXPECTANCY,
    DEFAULT_NOTIFICATIONS_DAY,
    DEFAULT_NOTIFICATIONS_ENABLED,
    DEFAULT_NOTIFICATIONS_TIME,
    DEFAULT_TIMEZONE,
)
from ..core.enums import SubscriptionType, WeekDay
from ..utils.config import BOT_NAME
from ..utils.logger import get_logger
from .models.user import User
from .models.user_settings import UserSettings
from .models.user_subscription import (
    DEFAULT_SUBSCRIPTION_EXPIRATION_DAYS,
    UserSubscription,
)
from .repositories.sqlite.user_repository import SQLiteUserRepository
from .repositories.sqlite.user_settings_repository import SQLiteUserSettingsRepository
from .repositories.sqlite.user_subscription_repository import (
    SQLiteUserSubscriptionRepository,
)

logger = get_logger(f"{BOT_NAME}.DatabaseService")


class DatabaseManager:
    """Manager for database repositories (repositories are already singletons)."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Prevent re-initialization in singleton
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.user_repository = SQLiteUserRepository()
        self.settings_repository = SQLiteUserSettingsRepository()
        self.subscription_repository = SQLiteUserSubscriptionRepository()

        # Initialize all repositories (they are singletons, so this only happens once)
        self.user_repository.initialize()
        self.settings_repository.initialize()
        self.subscription_repository.initialize()

        # Mark as initialized to prevent re-initialization on subsequent __init__ calls
        self._initialized = True

    def close(self):
        """Close all database connections."""
        self.user_repository.close()
        self.settings_repository.close()
        self.subscription_repository.close()

    @classmethod
    def reset_instance(cls):
        """Reset repository instances (for testing)."""
        SQLiteUserRepository.reset_instances()
        SQLiteUserSettingsRepository.reset_instances()
        SQLiteUserSubscriptionRepository.reset_instances()


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


class UserSettingsUpdateError(UserServiceError):
    """Exception raised when user settings update fails.

    This exception is raised when the system fails to update
    user settings in the database.
    """

    pass


class UserSubscriptionUpdateError(UserServiceError):
    """Exception raised when user subscription update fails.

    This exception is raised when the system fails to update
    user subscription in the database.
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
        # Use DatabaseManager to get singleton repositories
        db_manager = DatabaseManager()
        self.user_repository = user_repository or db_manager.user_repository
        self.settings_repository = settings_repository or db_manager.settings_repository
        self.subscription_repository = (
            subscription_repository or db_manager.subscription_repository
        )

    def initialize(self) -> None:
        """Initialize database connections."""
        # DatabaseManager already initializes repositories
        pass

    def close(self) -> None:
        """Close database connections."""
        # DatabaseManager handles closing
        pass

    def create_user_profile(
        self,
        user_info,
        birth_date: date,
        subscription_type: SubscriptionType = SubscriptionType.BASIC,
        notifications: bool = DEFAULT_NOTIFICATIONS_ENABLED,
        notifications_day: WeekDay = WeekDay(DEFAULT_NOTIFICATIONS_DAY),
        notifications_time: time = datetime.strptime(
            DEFAULT_NOTIFICATIONS_TIME, "%H:%M:%S"
        ).time(),
        life_expectancy: int = DEFAULT_LIFE_EXPECTANCY,
        timezone: str = DEFAULT_TIMEZONE,
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
                notifications=notifications,
                notifications_day=notifications_day,
                notifications_time=notifications_time,
                life_expectancy=life_expectancy,
                timezone=timezone,
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

            # Create user object
            new_user = User(
                telegram_id=user.telegram_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                created_at=user.created_at,
            )

            # Try to get settings (optional)
            try:
                settings = self.settings_repository.get_user_settings(telegram_id)
                new_user.settings = settings
            except Exception as e:
                logger.warning(f"Failed to get settings for user {telegram_id}: {e}")
                new_user.settings = None

            # Try to get subscription (optional)
            try:
                subscription = self.subscription_repository.get_subscription(
                    telegram_id
                )
                new_user.subscription = subscription
            except Exception as e:
                logger.warning(
                    f"Failed to get subscription for user {telegram_id}: {e}"
                )
                new_user.subscription = None

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

    def update_user_subscription(
        self, telegram_id: int, subscription_type: SubscriptionType
    ) -> None:
        """Update user subscription type.

        :param telegram_id: Telegram user ID
        :param subscription_type: New subscription type
        :raises UserSubscriptionUpdateError: If subscription update fails
        :raises UserNotFoundError: If user subscription not found
        """
        try:
            subscription = self.subscription_repository.get_subscription(telegram_id)
            if not subscription:
                logger.warning(f"Subscription not found for user {telegram_id}")
                raise UserNotFoundError(
                    f"Subscription not found for user {telegram_id}"
                )

            # Update subscription type
            subscription.subscription_type = subscription_type

            success = self.subscription_repository.update_subscription(subscription)
            if not success:
                logger.warning(f"Failed to update subscription for user {telegram_id}")
                raise UserSubscriptionUpdateError(
                    f"Failed to update subscription for user {telegram_id}"
                )

            logger.info(
                f"Updated subscription for user {telegram_id} to {subscription_type}"
            )

        except (UserNotFoundError, UserSubscriptionUpdateError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Error updating subscription for {telegram_id}: {e}")
            raise UserSubscriptionUpdateError(
                f"Error updating subscription for {telegram_id}: {e}"
            )

    def update_user_settings(
        self,
        telegram_id: int,
        birth_date: Optional[date] = None,
        life_expectancy: Optional[int] = None,
        language: Optional[str] = None,
    ) -> None:
        """Update user settings.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :param birth_date: New birth date (optional)
        :type birth_date: Optional[date]
        :param life_expectancy: New life expectancy (optional)
        :type life_expectancy: Optional[int]
        :param language: New language preference (optional)
        :type language: Optional[str]
        :raises UserSettingsUpdateError: If settings update fails
        :raises UserNotFoundError: If user settings not found
        """
        try:
            settings = self.settings_repository.get_user_settings(telegram_id)
            if not settings:
                logger.warning(f"Settings not found for user {telegram_id}")
                raise UserNotFoundError(f"Settings not found for user {telegram_id}")

            # Update only provided fields
            if birth_date is not None:
                settings.birth_date = birth_date
                logger.info(
                    f"Updated birth date for user {telegram_id} to {birth_date}"
                )

            if life_expectancy is not None:
                settings.life_expectancy = life_expectancy
                logger.info(
                    f"Updated life expectancy for user {telegram_id} to {life_expectancy}"
                )

            if language is not None:
                settings.language = language
                logger.info(f"Updated language for user {telegram_id} to {language}")

            success = self.settings_repository.update_user_settings(settings)
            if not success:
                logger.warning(f"Failed to update settings for user {telegram_id}")
                raise UserSettingsUpdateError(
                    f"Failed to update settings for user {telegram_id}"
                )

            logger.info(f"Successfully updated settings for user {telegram_id}")

        except (UserNotFoundError, UserSettingsUpdateError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Error updating settings for {telegram_id}: {e}")
            raise UserSettingsUpdateError(
                f"Error updating settings for {telegram_id}: {e}"
            )

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
            logger.info(f"Starting deletion of user profile for {telegram_id}")

            # First delete user settings
            settings_deleted = self.settings_repository.delete_user_settings(
                telegram_id
            )
            logger.info(
                f"Settings deletion result for {telegram_id}: {settings_deleted}"
            )

            if not settings_deleted:
                logger.warning(f"Settings not found for user {telegram_id}")

            # Then delete user subscription
            subscription_deleted = self.subscription_repository.delete_subscription(
                telegram_id
            )
            logger.info(
                f"Subscription deletion result for {telegram_id}: {subscription_deleted}"
            )

            if not subscription_deleted:
                logger.warning(f"Subscription not found for user {telegram_id}")

            # Finally delete user
            user_deleted = self.user_repository.delete_user(telegram_id)
            logger.info(f"User deletion result for {telegram_id}: {user_deleted}")

            if not user_deleted:
                raise UserDeletionError(f"User {telegram_id} not found")

            logger.info(f"Successfully deleted user profile for {telegram_id}")

        except Exception as e:
            logger.error(f"Failed to delete user profile for {telegram_id}: {e}")
            raise UserDeletionError(f"Failed to delete user profile: {e}")

    def get_all_users(self) -> list[User]:
        """Get all users from the database.

        This method retrieves all users with their settings and subscriptions
        for sending weekly notifications.

        :returns: List of all users with their profiles
        :rtype: list[User]
        """
        try:
            users = self.user_repository._get_all_entities(User, "users")
            complete_users = []

            for user in users:
                try:
                    # Get settings and subscription for each user
                    settings = self.settings_repository.get_user_settings(
                        user.telegram_id
                    )
                    subscription = self.subscription_repository.get_subscription(
                        user.telegram_id
                    )

                    # Create complete user profile
                    complete_user = User(
                        telegram_id=user.telegram_id,
                        username=user.username,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        created_at=user.created_at,
                    )
                    complete_user.settings = settings
                    complete_user.subscription = subscription
                    complete_users.append(complete_user)

                except Exception as e:
                    logger.warning(
                        f"Failed to get complete profile for user {user.telegram_id}: {e}"
                    )
                    continue

            logger.info(
                f"Retrieved {len(complete_users)} users for weekly notifications"
            )
            return complete_users

        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            return []


# Global service instance
user_service = UserService()
