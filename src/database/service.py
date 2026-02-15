"""Database service layer for LifeWeeksBot.

This module provides high-level business logic for database operations,
working with models and repositories to handle complex operations.
"""

import threading
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Optional

from src.enums import NotificationFrequency, SubscriptionType, WeekDay

from ..constants import (
    DEFAULT_LIFE_EXPECTANCY,
    DEFAULT_NOTIFICATION_FREQUENCY,
    DEFAULT_NOTIFICATIONS_DAY,
    DEFAULT_NOTIFICATIONS_ENABLED,
    DEFAULT_NOTIFICATIONS_TIME,
    DEFAULT_TIMEZONE,
)
from ..core.dtos import UserProfileDTO, UserSettingsDTO, UserSubscriptionDTO
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
    """Manager for database repositories (repositories are already singletons).

    :param db_path: Optional path to SQLite database file. If None, uses default.
    :type db_path: str | None
    """

    _instance: Optional["DatabaseManager"] = None
    _lock: threading.Lock = threading.Lock()
    _initialized: bool = False

    def __new__(
        cls,
        db_path: str | None = None,
    ) -> "DatabaseManager":
        """Create singleton instance of DatabaseManager.

        :param db_path: Optional path to SQLite database file
        :type db_path: str | None
        :returns: DatabaseManager instance
        :rtype: DatabaseManager
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize DatabaseManager with repositories.

        :param db_path: Optional path to SQLite database file. If None, uses default.
        :type db_path: str | None
        :returns: None
        """
        # Prevent re-initialization in singleton
        if hasattr(self, "_initialized") and self._initialized:
            return

        # Store db_path for later use
        self._db_path = db_path

        # Initialize repositories with custom db_path if provided
        if db_path:
            self.user_repository = SQLiteUserRepository(db_path=db_path)
            self.settings_repository = SQLiteUserSettingsRepository(db_path=db_path)
            self.subscription_repository = SQLiteUserSubscriptionRepository(
                db_path=db_path
            )
        else:
            self.user_repository = SQLiteUserRepository()
            self.settings_repository = SQLiteUserSettingsRepository()
            self.subscription_repository = SQLiteUserSubscriptionRepository()

        # Mark as initialized to prevent re-initialization on subsequent __init__ calls
        self._initialized = True

    async def initialize(self) -> None:
        """Initialize all repositories asynchronously.

        :returns: None
        :rtype: None
        """
        await self.user_repository.initialize()
        await self.settings_repository.initialize()
        await self.subscription_repository.initialize()

    async def close(self) -> None:
        """Close all database connections.

        :returns: None
        :rtype: None
        """
        await self.user_repository.close()
        await self.settings_repository.close()
        await self.subscription_repository.close()

    @classmethod
    def reset_instance(cls) -> None:
        """Reset repository instances (for testing).

        :returns: None
        :rtype: None
        """
        SQLiteUserRepository.reset_instances()
        SQLiteUserSettingsRepository.reset_instances()
        SQLiteUserSubscriptionRepository.reset_instances()
        cls._instance = None


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
    ) -> None:
        """Initialize user service.

        :param user_repository: User repository instance
        :type user_repository: Optional[SQLiteUserRepository]
        :param settings_repository: User settings repository instance
        :type settings_repository: Optional[SQLiteUserSettingsRepository]
        :param subscription_repository: User subscription repository instance
        :type subscription_repository: Optional[SQLiteUserSubscriptionRepository]
        """
        # Use DatabaseManager to get singleton repositories
        db_manager = DatabaseManager()
        self.user_repository = user_repository or db_manager.user_repository
        self.settings_repository = settings_repository or db_manager.settings_repository
        self.subscription_repository = (
            subscription_repository or db_manager.subscription_repository
        )

    async def initialize(self) -> None:
        """Initialize database connections.

        :returns: None
        :rtype: None
        """
        db_manager = DatabaseManager()
        await db_manager.initialize()

    async def close(self) -> None:
        """Close database connections.

        :returns: None
        :rtype: None
        """
        db_manager = DatabaseManager()
        await db_manager.close()

    async def create_user_profile(
        self,
        user_info: Any,  # Usually a telegram.User or mock
        birth_date: date,
        subscription_type: SubscriptionType = SubscriptionType.BASIC,
        notifications: bool = DEFAULT_NOTIFICATIONS_ENABLED,
        notifications_day: WeekDay = WeekDay(DEFAULT_NOTIFICATIONS_DAY),
        notifications_time: time = datetime.strptime(
            DEFAULT_NOTIFICATIONS_TIME, "%H:%M:%S"
        ).time(),
        life_expectancy: int = DEFAULT_LIFE_EXPECTANCY,
        timezone: str = DEFAULT_TIMEZONE,
        notification_frequency: NotificationFrequency = DEFAULT_NOTIFICATION_FREQUENCY,
        notifications_month_day: Optional[int] = None,
    ) -> Optional[UserProfileDTO]:
        """Create new user with default settings.

        :param user_info: Telegram User object
        :param birth_date: User's birth date
        :type birth_date: date
        :param subscription_type: User's subscription type
        :type subscription_type: SubscriptionType
        :param notifications: Whether notifications are enabled
        :type notifications: bool
        :param notifications_day: Day of week for notifications
        :type notifications_day: WeekDay
        :param notifications_time: Time of day for notifications
        :type notifications_time: time
        :param life_expectancy: User's life expectancy in years
        :type life_expectancy: int
        :param timezone: User's timezone
        :type timezone: str
        :param notification_frequency: Notification frequency
        :type notification_frequency: NotificationFrequency
        :param notifications_month_day: Day of month for monthly notifications
        :type notifications_month_day: int
        :returns: Created user object if successful, None otherwise
        :rtype: Optional[UserProfileDTO]
        """
        try:
            # Check if user already exists
            existing_user = await self.get_user_profile(telegram_id=user_info.id)
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
                notification_frequency=notification_frequency,
                notifications_month_day=notifications_month_day,
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
            if await self.user_repository.create_user(user=user):
                # Try to create settings
                if not await self.settings_repository.create_user_settings(
                    settings=settings
                ):
                    # Rollback user creation if settings creation failed
                    await self.user_repository.delete_user(telegram_id=user_info.id)
                    logger.error(f"Failed to create settings for {user_info.id}")
                    return None

                # Try to create subscription
                if not await self.subscription_repository.create_subscription(
                    subscription=subscription
                ):
                    # Rollback user and settings creation if subscription creation failed
                    await self.settings_repository.delete_user_settings(
                        telegram_id=user_info.id
                    )
                    await self.user_repository.delete_user(telegram_id=user_info.id)
                    logger.error(f"Failed to create subscription for {user_info.id}")
                    return None

                # All operations successful
                logger.info(f"Created complete user profile for {user_info.id}")
                return await self.get_user_profile(telegram_id=user_info.id)
            else:
                logger.error(f"Failed to create user {user_info.id}")
                return None

        except Exception as error:
            logger.error(f"Error creating user profile: {error}")
            return None

    def _to_dto(self, user: User) -> UserProfileDTO:
        """Convert User model to UserProfileDTO.

        :param user: User model instance
        :type user: User
        :returns: User profile DTO
        :rtype: UserProfileDTO
        :raises UserServiceError: If user data is incomplete
        """
        if not user.settings or not user.subscription:
            raise UserServiceError(f"Incomplete user data for {user.telegram_id}")

        settings_dto = UserSettingsDTO(
            birth_date=user.settings.birth_date,
            notifications=user.settings.notifications,
            notifications_day=user.settings.notifications_day,
            notifications_time=user.settings.notifications_time,
            life_expectancy=user.settings.life_expectancy,
            timezone=user.settings.timezone,
            notification_frequency=user.settings.notification_frequency,
            notifications_month_day=user.settings.notifications_month_day,
            language=user.settings.language,
        )

        subscription_dto = UserSubscriptionDTO(
            subscription_type=user.subscription.subscription_type,
            is_active=user.subscription.is_active,
            expires_at=user.subscription.expires_at,
        )

        return UserProfileDTO(
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            created_at=user.created_at,
            settings=settings_dto,
            subscription=subscription_dto,
        )

    async def get_user_profile(self, telegram_id: int) -> Optional[UserProfileDTO]:
        """Get complete user profile with settings and subscription.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :returns: User DTO with complete settings and subscription if found,
            None if user, settings, or subscription are missing
        :rtype: Optional[UserProfileDTO]
        """
        try:
            user = await self.user_repository.get_user(telegram_id=telegram_id)
            if not user:
                logger.warning(f"User {telegram_id} not found")
                return None

            # Create user object (temporarily for fetching relationships)
            # In a real ORM scenario, eager loading would be better
            new_user = User(
                telegram_id=user.telegram_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                created_at=user.created_at,
            )

            # Try to get settings (required for complete profile)
            try:
                settings = await self.settings_repository.get_user_settings(
                    telegram_id=telegram_id
                )
                if settings is None:
                    logger.warning(f"Settings not found for user {telegram_id}")
                    return None
                new_user.settings = settings
            except Exception as e:
                logger.warning(f"Failed to get settings for user {telegram_id}: {e}")
                return None

            # Try to get subscription (required for complete profile)
            try:
                subscription = await self.subscription_repository.get_subscription(
                    telegram_id=telegram_id
                )
                if subscription is None:
                    logger.warning(f"Subscription not found for user {telegram_id}")
                    return None
                new_user.subscription = subscription
            except Exception as e:
                logger.warning(
                    f"Failed to get subscription for user {telegram_id}: {e}"
                )
                return None

            return self._to_dto(new_user)

        except Exception as e:
            logger.error(f"Error getting user profile for {telegram_id}: {e}")
            return None

    async def is_valid_user_profile(self, telegram_id: int) -> bool:
        """Check if user has a valid profile with birth date.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :returns: True if profile is valid, False otherwise
        :rtype: bool
        """
        try:
            settings = await self.settings_repository.get_user_settings(
                telegram_id=telegram_id
            )
            return settings is not None and settings.birth_date is not None
        except Exception as e:
            logger.error(f"Error checking user profile validity for {telegram_id}: {e}")
            return False

    async def update_user_subscription(
        self, telegram_id: int, subscription_type: SubscriptionType
    ) -> None:
        """Update user subscription type.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :param subscription_type: New subscription type
        :type subscription_type: SubscriptionType
        :raises UserSubscriptionUpdateError: If subscription update fails
        :raises UserNotFoundError: If user subscription not found
        """
        try:
            subscription = await self.subscription_repository.get_subscription(
                telegram_id=telegram_id
            )
            if not subscription:
                logger.warning(f"Subscription not found for user {telegram_id}")
                raise UserNotFoundError(
                    f"Subscription not found for user {telegram_id}"
                )

            # Update subscription type
            subscription.subscription_type = subscription_type

            success = await self.subscription_repository.update_subscription(
                subscription=subscription
            )
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

    async def update_user_settings(
        self,
        telegram_id: int,
        birth_date: Optional[date] = None,
        life_expectancy: Optional[int] = None,
        language: Optional[str] = None,
        notifications_day: Optional[WeekDay] = None,
        notifications_time: Optional[time] = None,
        notification_frequency: Optional[NotificationFrequency] = None,
        notifications_month_day: Optional[int] = None,
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
        :param notifications_day: New notifications weekday (for weekly mode)
        :type notifications_day: Optional[WeekDay]
        :param notifications_time: New notifications time
        :type notifications_time: Optional[time]
        :param notification_frequency: New notification frequency
        :type notification_frequency: Optional[NotificationFrequency]
        :param notifications_month_day: New day of month for monthly notifications
        :type notifications_month_day: Optional[int]
        :raises UserSettingsUpdateError: If settings update fails
        :raises UserNotFoundError: If user settings not found
        """
        try:
            settings = await self.settings_repository.get_user_settings(
                telegram_id=telegram_id
            )
            if not settings:
                logger.warning(f"Settings not found for user {telegram_id}")
                raise UserNotFoundError(f"Settings not found for user {telegram_id}")

            # Update only provided fields
            self._apply_settings_updates(
                settings=settings,
                birth_date=birth_date,
                life_expectancy=life_expectancy,
                language=language,
                notifications_day=notifications_day,
                notifications_time=notifications_time,
                notification_frequency=notification_frequency,
                notifications_month_day=notifications_month_day,
                telegram_id=telegram_id,
            )

            success = await self.settings_repository.update_user_settings(
                settings=settings
            )
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

    async def delete_user(self, telegram_id: int) -> bool:
        """Delete user and all associated data.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :returns: True if successful, False otherwise
        :rtype: bool
        """
        try:
            success = await self.user_repository.delete_user(telegram_id=telegram_id)
            if success:
                logger.info(f"Deleted user {telegram_id}")
            else:
                logger.warning(f"Failed to delete user {telegram_id}")
            return success
        except Exception as e:
            logger.error(f"Error deleting user {telegram_id}: {e}")
            return False

    async def delete_user_profile(self, telegram_id: int) -> None:
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
            settings_deleted = await self.settings_repository.delete_user_settings(
                telegram_id=telegram_id
            )
            logger.info(
                f"Settings deletion result for {telegram_id}: {settings_deleted}"
            )

            if not settings_deleted:
                logger.warning(f"Settings not found for user {telegram_id}")

            # Then delete user subscription
            subscription_deleted = (
                await self.subscription_repository.delete_subscription(
                    telegram_id=telegram_id
                )
            )
            logger.info(
                f"Subscription deletion result for {telegram_id}: {subscription_deleted}"
            )

            if not subscription_deleted:
                logger.warning(f"Subscription not found for user {telegram_id}")

            # Finally delete user
            user_deleted = await self.user_repository.delete_user(
                telegram_id=telegram_id
            )
            logger.info(f"User deletion result for {telegram_id}: {user_deleted}")

            if not user_deleted:
                raise UserDeletionError(f"User {telegram_id} not found")

            logger.info(f"Successfully deleted user profile for {telegram_id}")

        except Exception as e:
            logger.error(f"Failed to delete user profile for {telegram_id}: {e}")
            raise UserDeletionError(f"Failed to delete user profile: {e}")

    async def get_all_users(self) -> list[UserProfileDTO]:
        """Get all users from the database.

        This method retrieves all users with their settings and subscriptions
        for sending weekly notifications.

        :returns: List of all users with their profiles
        :rtype: list[UserProfileDTO]
        """
        try:
            users = await self.user_repository._get_all_entities(
                model_class=User,
                entity_name="users",
            )
            complete_users: list[UserProfileDTO] = []

            for user in users:
                try:
                    # Get settings and subscription for each user
                    settings = await self.settings_repository.get_user_settings(
                        telegram_id=user.telegram_id
                    )
                    subscription = await self.subscription_repository.get_subscription(
                        telegram_id=user.telegram_id
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
                    complete_users.append(self._to_dto(complete_user))

                except Exception as e:
                    logger.warning(
                        f"Failed to get complete profile for user {user.telegram_id}: {e}"
                    )
                    continue

            logger.info(f"Retrieved {len(complete_users)} users for scheduled jobs")
            return complete_users

        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            return []

    def _apply_settings_updates(
        self,
        settings: UserSettings,
        birth_date: Optional[date],
        life_expectancy: Optional[int],
        language: Optional[str],
        notifications_day: Optional[WeekDay],
        notifications_time: Optional[time],
        notification_frequency: Optional[NotificationFrequency],
        notifications_month_day: Optional[int],
        telegram_id: int,
    ) -> None:
        """Apply individual field updates to user settings.

        This helper method reduces the complexity of update_user_settings
        by handling each field update independently.

        :param settings: UserSettings model instance to update
        :type settings: UserSettings
        :param birth_date: New birth date
        :type birth_date: Optional[date]
        :param life_expectancy: New life expectancy
        :type life_expectancy: Optional[int]
        :param language: New language preference
        :type language: Optional[str]
        :param notifications_day: New notifications weekday
        :type notifications_day: Optional[WeekDay]
        :param notifications_time: New notifications time
        :type notifications_time: Optional[time]
        :param notification_frequency: New notification frequency
        :type notification_frequency: Optional[NotificationFrequency]
        :param notifications_month_day: New day of month
        :type notifications_month_day: Optional[int]
        :param telegram_id: User's telegram ID (for logging)
        :type telegram_id: int
        """
        if birth_date is not None:
            settings.birth_date = birth_date
            logger.info(f"Updated birth date for user {telegram_id} to {birth_date}")

        if life_expectancy is not None:
            settings.life_expectancy = life_expectancy
            logger.info(
                f"Updated life expectancy for user {telegram_id} to {life_expectancy}"
            )

        if language is not None:
            settings.language = language
            logger.info(f"Updated language for user {telegram_id} to {language}")

        if notifications_day is not None:
            settings.notifications_day = notifications_day
            logger.info(
                f"Updated notifications day for user {telegram_id} to {notifications_day}"
            )

        if notifications_time is not None:
            settings.notifications_time = notifications_time
            logger.info(
                f"Updated notifications time for user {telegram_id} to {notifications_time}"
            )

        if notification_frequency is not None:
            settings.notification_frequency = notification_frequency
            logger.info(
                f"Updated notification frequency for user {telegram_id} to {notification_frequency}"
            )

        if notifications_month_day is not None:
            settings.notifications_month_day = notifications_month_day
            logger.info(
                f"Updated notifications month day for user {telegram_id} to {notifications_month_day}"
            )


# Global service instance
user_service = UserService()
