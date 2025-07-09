"""User settings model for the application.

This module defines the UserSettings model which stores user preferences
and configuration data, including notification settings and personal information.
"""

from datetime import UTC, date, datetime, time
from enum import StrEnum
from typing import Any, Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..constants import (
    MAX_TIMEZONE_LENGTH,
    USER_SETTINGS_TABLE,
    USERS_TABLE,
)
from .base import Base


class WeekDay(StrEnum):
    """Week day enumeration.

    Defines days of the week for notifications and scheduling.

    :param MONDAY: Monday
    :param TUESDAY: Tuesday
    :param WEDNESDAY: Wednesday
    :param THURSDAY: Thursday
    :param FRIDAY: Friday
    :param SATURDAY: Saturday
    :param SUNDAY: Sunday
    """

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

    @classmethod
    def get_choices(cls) -> list[tuple[str, str]]:
        """Get list of choices for forms or validation.

        :returns: List of tuples containing (value, display_name) pairs
        """
        return [(choice.value, choice.value.title()) for choice in cls]

    @classmethod
    def is_valid(cls, value: Any) -> bool:
        """Check if a value is a valid week day.

        :param value: Value to check
        :returns: True if value is valid, False otherwise
        """
        return value in cls._value2member_map_

    @classmethod
    def get_weekday_number(cls, day: "WeekDay") -> int:
        """Get weekday number (Monday = 0, Sunday = 6).

        :param day: WeekDay enum value
        :returns: Weekday number (0-6)
        """
        day_mapping = {
            cls.MONDAY: 0,
            cls.TUESDAY: 1,
            cls.WEDNESDAY: 2,
            cls.THURSDAY: 3,
            cls.FRIDAY: 4,
            cls.SATURDAY: 5,
            cls.SUNDAY: 6,
        }
        return day_mapping[day]

    @classmethod
    def from_weekday_number(cls, weekday: int) -> "WeekDay":
        """Get WeekDay from weekday number (Monday = 0, Sunday = 6).

        :param weekday: Weekday number (0-6)
        :returns: WeekDay enum value
        :raises ValueError: If weekday number is invalid
        """
        day_mapping = {
            0: cls.MONDAY,
            1: cls.TUESDAY,
            2: cls.WEDNESDAY,
            3: cls.THURSDAY,
            4: cls.FRIDAY,
            5: cls.SATURDAY,
            6: cls.SUNDAY,
        }
        if weekday not in day_mapping:
            raise ValueError(f"Invalid weekday number: {weekday}. Must be 0-6.")
        return day_mapping[weekday]


class UserSettings(Base):
    """User settings model for storing profile preferences and sensitive data.

    :param telegram_id: Telegram user ID (foreign key to User)
    :param birth_date: User's date of birth
    :param notifications_day: Day of the week for notifications (enum WeekDay)
    :param life_expectancy: Expected life expectancy in years
    :param timezone: User's timezone (e.g., "Europe/Warsaw")
    :param notifications: Whether notifications are enabled
    :param notifications_time: Time of day for notifications
    :param updated_at: Last update timestamp
    """

    __tablename__ = USER_SETTINGS_TABLE

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{USERS_TABLE}.telegram_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Personal information
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Notifications
    notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    notifications_day: Mapped[Optional[WeekDay]] = mapped_column(
        Enum(WeekDay), nullable=True
    )
    notifications_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    # Life expectancy and timezone
    life_expectancy: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(
        String(MAX_TIMEZONE_LENGTH), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="settings")
