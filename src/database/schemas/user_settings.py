"""User settings schemas for data validation.

This module provides Pydantic models for user settings data validation,
including schemas for creating, updating, and retrieving user settings.
"""

from datetime import date, datetime, time
from typing import Optional

from pydantic import Field

from .base import BaseSchema


class UserSettingsBase(BaseSchema):
    """Base schema for user settings data."""

    telegram_id: int = Field(..., description="Telegram user ID")
    birth_date: Optional[date] = Field(None, description="User's date of birth")
    notifications_day: Optional[str] = Field(
        None, description="Day of the week for notifications"
    )
    life_expectancy: Optional[int] = Field(
        None, description="Expected life expectancy in years"
    )
    timezone: Optional[str] = Field(None, description="User's timezone")
    notifications: bool = Field(True, description="Whether notifications are enabled")
    notifications_time: Optional[time] = Field(
        None, description="Time of day for notifications"
    )


class UserSettingsCreate(UserSettingsBase):
    """Schema for creating new user settings."""

    pass


class UserSettingsUpdate(BaseSchema):
    """Schema for updating existing user settings."""

    birth_date: Optional[date] = Field(None, description="User's date of birth")
    notifications_day: Optional[str] = Field(
        None, description="Day of the week for notifications"
    )
    life_expectancy: Optional[int] = Field(
        None, description="Expected life expectancy in years"
    )
    timezone: Optional[str] = Field(None, description="User's timezone")
    notifications: Optional[bool] = Field(
        None, description="Whether notifications are enabled"
    )
    notifications_time: Optional[time] = Field(
        None, description="Time of day for notifications"
    )


class UserSettingsInDB(UserSettingsBase):
    """Schema for user settings data as stored in the database."""

    id: int = Field(..., description="Primary key")
    updated_at: datetime = Field(..., description="Last update timestamp")


class UserSettingsResponse(UserSettingsInDB):
    """Schema for user settings data in API responses."""

    pass
