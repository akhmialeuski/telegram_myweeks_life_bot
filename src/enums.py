"""Common enumerations used across the application.

This module contains shared enums to avoid circular dependencies
between core, config, and database modules.
"""

from enum import StrEnum, auto
from typing import Any


class WeekDay(StrEnum):
    """Week day enumeration.

    Defines days of the week for notifications and scheduling.
    """

    MONDAY = auto()
    TUESDAY = auto()
    WEDNESDAY = auto()
    THURSDAY = auto()
    FRIDAY = auto()
    SATURDAY = auto()
    SUNDAY = auto()


class SubscriptionType(StrEnum):
    """Subscription type enumeration.

    Defines available subscription types for users.
    """

    BASIC = auto()
    PREMIUM = auto()
    TRIAL = auto()

    @classmethod
    def is_valid(cls, value: Any) -> bool:
        """Check if a value is a valid subscription type.

        :param value: Value to check
        :type value: Any
        :returns: True if value is a valid subscription type, False otherwise
        :rtype: bool
        """
        if not isinstance(value, (str, cls)):
            return False

        if isinstance(value, cls):
            return True

        try:
            cls(value)
            return True
        except ValueError:
            return False


class SupportedLanguage(StrEnum):
    """Supported language enumeration."""

    RU = "ru"
    EN = "en"
    UA = "ua"
    BY = "by"
