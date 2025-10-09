"""User schemas for data validation.

This module provides Pydantic models for user data validation,
including schemas for creating, updating, and retrieving user data.
"""

from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import BaseSchema
from .user_settings import UserSettingsResponse
from .user_subscription import UserSubscriptionResponse


class UserBase(BaseSchema):
    """Base schema for user data."""

    telegram_id: int = Field(..., description="Unique Telegram user ID")
    username: Optional[str] = Field(None, description="Telegram username")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")


class UserCreate(UserBase):
    """Schema for creating a new user."""

    pass


class UserUpdate(BaseSchema):
    """Schema for updating an existing user."""

    username: Optional[str] = Field(None, description="Telegram username")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")


class UserInDB(UserBase):
    """Schema for user data as stored in the database."""

    created_at: datetime = Field(..., description="Registration date in the system")
    settings: Optional[UserSettingsResponse] = Field(None, description="User settings")
    subscription: Optional[UserSubscriptionResponse] = Field(
        None, description="User subscription"
    )


class UserResponse(UserInDB):
    """Schema for user data in API responses."""

    pass
