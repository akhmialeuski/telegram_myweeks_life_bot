"""User subscription model for the application.

This module defines the UserSubscription model which tracks user subscription
status, including activation and expiration dates.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..constants import USER_SUBSCRIPTIONS_TABLE, USERS_TABLE
from .base import Base


class SubscriptionType(StrEnum):
    """Subscription type enumeration.

    Defines available subscription types for users.

    :param BASIC: Basic subscription with limited features
    :param PREMIUM: Premium subscription with full features
    :param TRIAL: Trial subscription for new users
    """

    BASIC = "basic"
    PREMIUM = "premium"
    TRIAL = "trial"

    @classmethod
    def get_choices(cls) -> list[tuple[str, str]]:
        """Get list of choices for forms or validation.

        :returns: List of tuples containing (value, display_name) pairs
        """
        return [(choice.value, choice.value.title()) for choice in cls]

    @classmethod
    def is_valid(cls, value: Any) -> bool:
        """Check if a value is a valid subscription type.

        :param value: Value to check
        :returns: True if value is valid, False otherwise
        """
        return value in cls._value2member_map_


DEFAULT_SUBSCRIPTION_TYPE = SubscriptionType.BASIC
# Default subscription expiration days for free users is 100 years
DEFAULT_SUBSCRIPTION_EXPIRATION_DAYS = 36500


class UserSubscription(Base):
    """User subscription model for storing user subscription information.

    :param telegram_id: Telegram user ID (foreign key to User)
    :param subscription_type: Type of subscription (enum SubscriptionType)
    :param is_active: Whether the subscription is active
    :param created_at: Subscription creation date
    :param expires_at: Subscription expiration date
    """

    __tablename__ = USER_SUBSCRIPTIONS_TABLE

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(f"{USERS_TABLE}.telegram_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    subscription_type: Mapped[SubscriptionType] = mapped_column(
        Enum(SubscriptionType), nullable=False, default=DEFAULT_SUBSCRIPTION_TYPE
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationship
    user: Mapped["User"] = relationship(back_populates="subscription")


def create_user_subscription(
    telegram_id: int,
    subscription_type: SubscriptionType = DEFAULT_SUBSCRIPTION_TYPE,
    is_active: bool = True,
    expires_at: Optional[datetime] = None,
) -> UserSubscription:
    """Create a new user subscription.

    :param telegram_id: Telegram user ID
    :param subscription_type: Type of subscription (defaults to BASIC)
    :param is_active: Whether the subscription is active (defaults to True)
    :param expires_at: Subscription expiration date (optional)
    :returns: New UserSubscription instance
    :raises ValueError: If telegram_id is invalid or subscription_type is invalid
    """
    if not isinstance(telegram_id, int) or telegram_id <= 0:
        raise ValueError("telegram_id must be a positive integer")

    if not SubscriptionType.is_valid(subscription_type):
        raise ValueError(f"Invalid subscription_type: {subscription_type}")

    # Set default expiration for basic subscriptions if not specified
    if expires_at is None and subscription_type == SubscriptionType.BASIC:
        expires_at = datetime.now(UTC).replace(
            year=datetime.now(UTC).year + (DEFAULT_SUBSCRIPTION_EXPIRATION_DAYS // 365)
        )

    return UserSubscription(
        telegram_id=telegram_id,
        subscription_type=subscription_type,
        is_active=is_active,
        expires_at=expires_at,
    )
