"""Fake User Service implementation for testing.

This module provides an in-memory implementation of UserServiceProtocol
that can be used for testing without database dependencies.
"""

import copy
from datetime import UTC, date, datetime, time

from src.constants import (
    DEFAULT_LIFE_EXPECTANCY,
    DEFAULT_NOTIFICATIONS_DAY,
    DEFAULT_NOTIFICATIONS_ENABLED,
    DEFAULT_NOTIFICATIONS_TIME,
    DEFAULT_TIMEZONE,
)
from src.core.enums import SubscriptionType, WeekDay
from src.database.models.user import User
from src.database.models.user_settings import UserSettings
from src.database.models.user_subscription import UserSubscription

from .in_memory_user_repository import InMemoryUserRepository


class FakeUserService:
    """Fake user service for testing without database dependencies.

    This implementation uses in-memory storage for all user data,
    making it suitable for fast, isolated unit tests.

    Attributes:
        _repository: In-memory user repository
        _settings: Dictionary mapping telegram_id to UserSettings
        _subscriptions: Dictionary mapping telegram_id to UserSubscription

    Example:
        >>> service = FakeUserService()
        >>> service.create_user_profile(user_info=mock_user, birth_date=date(1990, 1, 1))
        User(...)
        >>> service.is_valid_user_profile(telegram_id=123456)
        True
    """

    def __init__(self) -> None:
        """Initialize the service with empty data stores.

        :returns: None
        """
        self._repository = InMemoryUserRepository()
        self._settings: dict[int, UserSettings] = {}
        self._subscriptions: dict[int, UserSubscription] = {}

    def get_user_profile(self, telegram_id: int) -> User | None:
        """Get complete user profile with settings and subscription.

        Returns a copy of the user to prevent mutation of stored data.

        :param telegram_id: Unique Telegram user identifier
        :type telegram_id: int
        :returns: User with settings and subscription if found, None otherwise
        :rtype: User | None
        """
        stored_user = self._repository.get_user(telegram_id=telegram_id)
        if stored_user is None:
            return None

        settings = self._settings.get(telegram_id)
        subscription = self._subscriptions.get(telegram_id)

        # Return None if settings or subscription are missing
        if settings is None or subscription is None:
            return None

        # Create a shallow copy to prevent mutation of stored data
        user = copy.copy(stored_user)
        user.settings = settings
        user.subscription = subscription

        return user

    def create_user_profile(
        self,
        user_info: object,
        birth_date: date,
        subscription_type: SubscriptionType | None = None,
        notifications: bool = DEFAULT_NOTIFICATIONS_ENABLED,
        notifications_day: WeekDay | None = None,
        notifications_time: time | None = None,
        life_expectancy: int = DEFAULT_LIFE_EXPECTANCY,
        timezone: str = DEFAULT_TIMEZONE,
    ) -> User | None:
        """Create new user with default settings.

        :param user_info: Object with id, username, first_name, last_name attributes
        :type user_info: object
        :param birth_date: User's date of birth
        :type birth_date: date
        :param subscription_type: Subscription type (defaults to BASIC)
        :type subscription_type: SubscriptionType | None
        :param notifications: Whether notifications are enabled
        :type notifications: bool
        :param notifications_day: Day of week for notifications
        :type notifications_day: WeekDay | None
        :param notifications_time: Time for notifications
        :type notifications_time: time | None
        :param life_expectancy: Expected lifespan in years
        :type life_expectancy: int
        :param timezone: User's timezone
        :type timezone: str
        :returns: Created user or None if creation fails
        :rtype: User | None
        """
        telegram_id = getattr(user_info, "id", 0)

        # Check if user already exists
        existing = self._repository.get_user(telegram_id=telegram_id)
        if existing is not None:
            return self.get_user_profile(telegram_id=telegram_id)

        # Create user
        user = User(
            telegram_id=telegram_id,
            username=getattr(user_info, "username", None),
            first_name=getattr(user_info, "first_name", None),
            last_name=getattr(user_info, "last_name", None),
            created_at=datetime.now(tz=UTC),
        )

        # Create settings
        if notifications_day is None:
            notifications_day = WeekDay(DEFAULT_NOTIFICATIONS_DAY)
        if notifications_time is None:
            notifications_time = datetime.strptime(
                DEFAULT_NOTIFICATIONS_TIME, "%H:%M:%S"
            ).time()

        settings = UserSettings(
            telegram_id=telegram_id,
            birth_date=birth_date,
            notifications=notifications,
            notifications_day=notifications_day,
            notifications_time=notifications_time,
            life_expectancy=life_expectancy,
            timezone=timezone,
            updated_at=datetime.now(tz=UTC),
        )

        # Create subscription
        if subscription_type is None:
            subscription_type = SubscriptionType.BASIC

        subscription = UserSubscription(
            telegram_id=telegram_id,
            subscription_type=subscription_type,
            is_active=True,
            created_at=datetime.now(tz=UTC),
            expires_at=None,
        )

        # Store everything
        self._repository.create_user(user=user)
        self._settings[telegram_id] = settings
        self._subscriptions[telegram_id] = subscription

        return self.get_user_profile(telegram_id=telegram_id)

    def is_valid_user_profile(self, telegram_id: int) -> bool:
        """Check if user has a valid profile with birth date.

        :param telegram_id: Unique Telegram user identifier
        :type telegram_id: int
        :returns: True if profile is valid with birth date, False otherwise
        :rtype: bool
        """
        settings = self._settings.get(telegram_id)
        return settings is not None and settings.birth_date is not None

    def update_user_settings(
        self,
        telegram_id: int,
        birth_date: date | None = None,
        life_expectancy: int | None = None,
        language: str | None = None,
    ) -> None:
        """Update user settings.

        :param telegram_id: Unique Telegram user identifier
        :type telegram_id: int
        :param birth_date: New birth date (optional)
        :type birth_date: date | None
        :param life_expectancy: New life expectancy (optional)
        :type life_expectancy: int | None
        :param language: New language preference (optional)
        :type language: str | None
        :returns: None
        :raises KeyError: If user settings not found
        """
        if telegram_id not in self._settings:
            raise KeyError(f"Settings not found for user {telegram_id}")

        settings = self._settings[telegram_id]
        if birth_date is not None:
            settings.birth_date = birth_date
        if life_expectancy is not None:
            settings.life_expectancy = life_expectancy
        if language is not None:
            settings.language = language

    def update_user_subscription(
        self,
        telegram_id: int,
        subscription_type: SubscriptionType,
    ) -> None:
        """Update user subscription type.

        :param telegram_id: Unique Telegram user identifier
        :type telegram_id: int
        :param subscription_type: New subscription type
        :type subscription_type: SubscriptionType
        :returns: None
        :raises KeyError: If user subscription not found
        """
        if telegram_id not in self._subscriptions:
            raise KeyError(f"Subscription not found for user {telegram_id}")

        self._subscriptions[telegram_id].subscription_type = subscription_type

    def delete_user_profile(self, telegram_id: int) -> None:
        """Delete user profile and all associated data.

        :param telegram_id: Unique Telegram user identifier
        :type telegram_id: int
        :returns: None
        :raises KeyError: If user not found
        """
        if not self._repository.delete_user(telegram_id=telegram_id):
            raise KeyError(f"User {telegram_id} not found")

        self._settings.pop(telegram_id, None)
        self._subscriptions.pop(telegram_id, None)

    def get_all_users(self) -> list[User]:
        """Get all users from the repository.

        Returns copies of users to prevent mutation of stored data.

        :returns: List of all users with their profiles
        :rtype: list[User]
        """
        users = []
        for stored_user in self._repository.get_all_users():
            # Create a shallow copy to prevent mutation of stored data
            user = copy.copy(stored_user)
            user.settings = self._settings.get(user.telegram_id)
            user.subscription = self._subscriptions.get(user.telegram_id)
            users.append(user)
        return users

    def clear(self) -> None:
        """Clear all stored data.

        :returns: None
        """
        self._repository.clear()
        self._settings.clear()
        self._subscriptions.clear()
