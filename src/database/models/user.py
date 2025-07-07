"""User model for the application.

This module defines the User model which represents a Telegram user
in the database, including their basic information and relationships.
"""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..constants import (
    MAX_FIRST_NAME_LENGTH,
    MAX_LAST_NAME_LENGTH,
    MAX_USERNAME_LENGTH,
    USERS_TABLE,
)
from .base import Base


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
    username: Mapped[Optional[str]] = mapped_column(
        String(MAX_USERNAME_LENGTH), nullable=True
    )
    first_name: Mapped[Optional[str]] = mapped_column(
        String(MAX_FIRST_NAME_LENGTH), nullable=True
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(MAX_LAST_NAME_LENGTH), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )

    # Relationship
    settings: Mapped["UserSettings"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    subscription: Mapped["UserSubscription"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
