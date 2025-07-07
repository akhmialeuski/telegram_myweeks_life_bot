"""User settings model for the application.

This module defines the UserSettings model which stores user preferences
and configuration data, including notification settings and personal information.
"""

from datetime import UTC, date, datetime, time
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..constants import (
    MAX_NOTIFICATIONS_DAY_LENGTH,
    MAX_TIMEZONE_LENGTH,
    USER_SETTINGS_TABLE,
    USERS_TABLE,
)
from .base import Base


class UserSettings(Base):
    """User settings model for storing profile preferences and sensitive data.

    :param telegram_id: Telegram user ID (foreign key to User)
    :param birth_date: User's date of birth
    :param notifications_day: Day of the week for notifications (e.g., "Monday")
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
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notifications_day: Mapped[Optional[str]] = mapped_column(
        String(MAX_NOTIFICATIONS_DAY_LENGTH), nullable=True
    )
    life_expectancy: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(
        String(MAX_TIMEZONE_LENGTH), nullable=True
    )
    notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    notifications_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Relationship
    user: Mapped["User"] = relationship(back_populates="settings")
