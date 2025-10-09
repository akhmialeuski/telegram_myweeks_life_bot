"""User subscription model for subscription management.

This module defines the UserSubscription model which handles user subscription
information including subscription type, status, and expiration dates.
"""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.enums import SubscriptionType
from ..constants import USER_SUBSCRIPTIONS_TABLE, USERS_TABLE
from .base import Base

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
        Enum(SubscriptionType), nullable=False, default=SubscriptionType.TRIAL
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationship
    user: Mapped["User"] = relationship(back_populates="subscription")
