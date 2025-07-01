"""Data models for user profile and settings.

Defines the data structures for user information and user settings
used by the storage and service layers of the LifeWeeksBot project.
"""

from datetime import datetime, date, time, UTC
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, Date, Time, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .constants import (
    USERS_TABLE, USER_SETTINGS_TABLE,
    MAX_USERNAME_LENGTH, MAX_FIRST_NAME_LENGTH, MAX_LAST_NAME_LENGTH,
    MAX_NOTIFICATIONS_DAY_LENGTH, MAX_TIMEZONE_LENGTH
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class User(Base):
    """User model representing a Telegram user.

    :param telegram_id: Unique Telegram user ID
    :param username: Telegram username (if available)
    :param first_name: User's first name
    :param last_name: User's last name (if available)
    :param created_at: Registration date in the system
    """
    __tablename__ = USERS_TABLE

    telegram_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(MAX_USERNAME_LENGTH), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(MAX_FIRST_NAME_LENGTH), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(MAX_LAST_NAME_LENGTH), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Relationship
    settings: Mapped["UserSettings"] = relationship(back_populates="user", uselist=False)


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
    telegram_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{USERS_TABLE}.telegram_id", ondelete="CASCADE"), nullable=False, unique=True)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notifications_day: Mapped[Optional[str]] = mapped_column(String(MAX_NOTIFICATIONS_DAY_LENGTH), nullable=True)
    life_expectancy: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(MAX_TIMEZONE_LENGTH), nullable=True)
    notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    notifications_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationship
    user: Mapped["User"] = relationship(back_populates="settings")
