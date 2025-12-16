"""Data Transfer Objects for the application.

This module defines immutable DTOs used across the application to represent
domain entities. They are implemented as frozen dataclasses to ensure
immutability and type safety.
"""

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Optional

from src.enums import SubscriptionType, WeekDay


@dataclass(frozen=True, slots=True, kw_only=True)
class UserSettingsDTO:
    """Immutable DTO for user settings.

    :param birth_date: User's date of birth
    :param notifications: Whether notifications are enabled
    :param notifications_day: Day of the week for notifications
    :param notifications_time: Time of day for notifications
    :param life_expectancy: Expected life expectancy in years
    :param timezone: User's timezone
    :param language: User's language preference
    """

    birth_date: Optional[date]
    notifications: bool
    notifications_day: Optional[WeekDay]
    notifications_time: Optional[time]
    life_expectancy: Optional[int]
    timezone: Optional[str]
    language: Optional[str]


@dataclass(frozen=True, slots=True, kw_only=True)
class UserSubscriptionDTO:
    """Immutable DTO for user subscription.

    :param subscription_type: Type of subscription
    :param is_active: Whether the subscription is active
    :param expires_at: Subscription expiration date
    """

    subscription_type: SubscriptionType
    is_active: bool
    expires_at: Optional[datetime]


@dataclass(frozen=True, slots=True, kw_only=True)
class UserProfileDTO:
    """Immutable DTO for complete user profile.

    Contains basic user info, settings, and subscription details.
    This serves as the main domain object for the application logic.

    :param telegram_id: Unique Telegram user ID
    :param username: Telegram username
    :param first_name: User's first name
    :param last_name: User's last name
    :param created_at: Registration date
    :param settings: User settings DTO
    :param subscription: User subscription DTO
    """

    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    created_at: datetime
    settings: UserSettingsDTO
    subscription: UserSubscriptionDTO
