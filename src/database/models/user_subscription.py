"""User subscription model for the application.

This module defines the UserSubscription model which tracks user subscription
status, including activation and expiration dates.
"""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..constants import USER_SUBSCRIPTIONS_TABLE, USERS_TABLE
from .base import Base


class UserSubscription(Base):
    """User subscription model for storing user subscription information.

    :param telegram_id: Telegram user ID (foreign key to User)
    :param subscription_type: Type of subscription (e.g., 'basic', 'premium')
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
    subscription_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationship
    user: Mapped["User"] = relationship(back_populates="subscription")
