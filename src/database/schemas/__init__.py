"""Schemas package for data validation.

This package contains Pydantic models for validating data
at different layers of the application. Each module corresponds
to a specific domain model and provides schemas for various operations.
"""

from .base import BaseSchema
from .user import UserBase, UserCreate, UserInDB, UserResponse, UserUpdate
from .user_settings import (
    UserSettingsBase,
    UserSettingsCreate,
    UserSettingsInDB,
    UserSettingsResponse,
    UserSettingsUpdate,
)
from .user_subscription import (
    UserSubscriptionBase,
    UserSubscriptionCreate,
    UserSubscriptionInDB,
    UserSubscriptionResponse,
    UserSubscriptionUpdate,
)

__all__ = [
    # Base
    "BaseSchema",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserResponse",
    # User Settings
    "UserSettingsBase",
    "UserSettingsCreate",
    "UserSettingsUpdate",
    "UserSettingsInDB",
    "UserSettingsResponse",
    # User Subscription
    "UserSubscriptionBase",
    "UserSubscriptionCreate",
    "UserSubscriptionUpdate",
    "UserSubscriptionInDB",
    "UserSubscriptionResponse",
]
