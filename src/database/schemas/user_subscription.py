"""User subscription schemas for data validation.

This module provides Pydantic models for user subscription data validation,
including schemas for creating, updating, and retrieving subscription data.
"""

from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import BaseSchema


class UserSubscriptionBase(BaseSchema):
    """Base schema for user subscription data."""

    telegram_id: int = Field(..., description="Telegram user ID")
    is_active: bool = Field(True, description="Whether the subscription is active")
    expires_at: Optional[datetime] = Field(
        None, description="Subscription expiration date"
    )


class UserSubscriptionCreate(UserSubscriptionBase):
    """Schema for creating a new subscription."""

    pass


class UserSubscriptionUpdate(BaseSchema):
    """Schema for updating an existing subscription."""

    is_active: Optional[bool] = Field(
        None, description="Whether the subscription is active"
    )
    expires_at: Optional[datetime] = Field(
        None, description="Subscription expiration date"
    )


class UserSubscriptionInDB(UserSubscriptionBase):
    """Schema for subscription data as stored in the database."""

    id: int = Field(..., description="Primary key")
    created_at: datetime = Field(..., description="Subscription creation date")


class UserSubscriptionResponse(UserSubscriptionInDB):
    """Schema for subscription data in API responses."""

    pass
