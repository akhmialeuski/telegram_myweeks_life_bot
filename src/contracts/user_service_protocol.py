"""User Service Protocol for user management operations.

This module defines the contract for user management services.
The UserService implementation provides business logic for user
operations including registration, profile management, and settings.
"""

from collections.abc import Coroutine
from datetime import date, time
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from src.core.dtos import UserProfileDTO
    from src.enums import SubscriptionType, WeekDay

    from ..database.models.user import User


@runtime_checkable
class UserServiceProtocol(Protocol):
    """Service contract for user management operations.

    This protocol defines the interface for all user-related business logic.
    Implementations coordinate between repositories and provide higher-level
    operations like profile creation with default settings.

    Implementations:
        - UserService: Production implementation with SQLite repositories
        - FakeUserService: In-memory implementation for testing
    """

    async def get_user_profile(self, telegram_id: int) -> "UserProfileDTO | None":
        """Get complete user profile with settings and subscription.

        :param telegram_id: Unique Telegram user identifier
        :type telegram_id: int
        :returns: User DTO with settings and subscription if found, None otherwise
        :rtype: Coroutine[Any, Any, UserProfileDTO | None]
        """
        ...

    async def create_user_profile(
        self,
        user_info: object,
        birth_date: date,
        subscription_type: "SubscriptionType | None" = None,
        notifications: bool = True,
        notifications_day: "WeekDay | None" = None,
        notifications_time: time | None = None,
        life_expectancy: int = 80,
        timezone: str = "UTC",
    ) -> Coroutine[Any, Any, "UserProfileDTO | None"]:
        """Create new user with default settings.

        :param user_info: Telegram User object containing user details
        :type user_info: object
        :param birth_date: User's date of birth
        :type birth_date: date
        :param subscription_type: User's subscription type
        :type subscription_type: SubscriptionType | None
        :param notifications: Whether notifications are enabled
        :type notifications: bool
        :param notifications_day: Day of week for notifications
        :type notifications_day: WeekDay | None
        :param notifications_time: Time of day for notifications
        :type notifications_time: time | None
        :param life_expectancy: Expected life span in years
        :type life_expectancy: int
        :param timezone: User's timezone
        :type timezone: str
        :returns: Created user DTO if successful, None otherwise
        :rtype: Coroutine[Any, Any, UserProfileDTO | None]
        """
        ...

    async def is_valid_user_profile(self, telegram_id: int) -> bool:
        """Check if user has a valid profile with birth date.

        :param telegram_id: Unique Telegram user identifier
        :type telegram_id: int
        :returns: True if profile is valid, False otherwise
        :rtype: Coroutine[Any, Any, bool]
        """
        ...

    async def update_user_settings(
        self,
        telegram_id: int,
        birth_date: date | None = None,
        life_expectancy: int | None = None,
        language: str | None = None,
    ) -> Coroutine[Any, Any, None]:
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
        :raises UserSettingsUpdateError: If settings update fails
        :raises UserNotFoundError: If user settings not found
        """
        ...

    async def update_user_subscription(
        self,
        telegram_id: int,
        subscription_type: "SubscriptionType",
    ) -> Coroutine[Any, Any, None]:
        """Update user subscription type.

        :param telegram_id: Unique Telegram user identifier
        :type telegram_id: int
        :param subscription_type: New subscription type
        :type subscription_type: SubscriptionType
        :returns: None
        :raises UserSubscriptionUpdateError: If subscription update fails
        :raises UserNotFoundError: If user subscription not found
        """
        ...

    async def delete_user_profile(self, telegram_id: int) -> None:
        """Delete user profile and all associated data.

        :param telegram_id: Unique Telegram user identifier
        :type telegram_id: int
        :returns: None
        :raises UserDeletionError: If user deletion fails
        """
        ...

    async def get_all_users(self) -> list["User"]:
        """Get all users from the repository.

        :returns: List of all users with their profiles
        :rtype: list[User]
        """
        ...
