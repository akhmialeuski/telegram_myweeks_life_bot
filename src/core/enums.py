"""Module for common enumerations used across the application."""

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
    def get_choices(cls) -> list[tuple[str, str]]:
        """Get subscription type choices as list of tuples.

        :returns: List of tuples with (value, display_name) for each subscription type
        :rtype: list[tuple[str, str]]
        """
        return [(member.value, member.value.capitalize()) for member in cls]

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
