"""SQLite implementation of user subscription repository.

Provides SQLite-based implementation of AbstractUserSubscriptionRepository
for storing user subscriptions in SQLite database.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from ....utils.config import BOT_NAME
from ...models import UserSubscription
from ..abstract.user_subscription_repository import AbstractUserSubscriptionRepository
from .base_repository import BaseSQLiteRepository

logger = logging.getLogger(BOT_NAME)


class SQLiteUserSubscriptionRepository(
    BaseSQLiteRepository, AbstractUserSubscriptionRepository
):
    """SQLite implementation of user subscription repository.

    Handles all database operations for user subscriptions using SQLite as the backend storage.
    """

    def create_subscription(self, subscription: UserSubscription) -> bool:
        """Create a new user subscription.

        :param subscription: UserSubscription object to create
        :returns: True if successful, False otherwise
        """
        try:
            with self.session() as session:
                session.add(subscription)
                logger.info(f"Created subscription for user {subscription.telegram_id}")
                return True

        except IntegrityError:
            logger.warning(
                f"Subscription for user {subscription.telegram_id} already exists"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to create user subscription: {e}")
            return False

    def get_subscription(self, telegram_id: int) -> Optional[UserSubscription]:
        """Get user subscription by Telegram ID.

        :param telegram_id: Telegram user ID
        :returns: UserSubscription object if found, None otherwise
        """
        try:
            with self.session() as session:
                stmt = select(UserSubscription).where(
                    UserSubscription.telegram_id == telegram_id
                )
                result = session.execute(stmt)
                subscription = result.scalar_one_or_none()
                if subscription:
                    self._detach_instance(session, subscription)
                return subscription

        except Exception as e:
            logger.error(f"Failed to get user subscription {telegram_id}: {e}")
            return None

    def update_subscription(self, subscription: UserSubscription) -> bool:
        """Update user subscription.

        :param subscription: UserSubscription object with updated data
        :returns: True if successful, False otherwise
        """
        try:
            with self.session() as session:
                stmt = (
                    update(UserSubscription)
                    .where(UserSubscription.telegram_id == subscription.telegram_id)
                    .values(
                        subscription_type=subscription.subscription_type,
                        is_active=subscription.is_active,
                        expires_at=subscription.expires_at,
                    )
                )
                result = session.execute(stmt)

                if result.rowcount > 0:
                    logger.info(
                        f"Updated subscription for user {subscription.telegram_id}"
                    )
                    return True
                else:
                    logger.warning(
                        f"Subscription for user {subscription.telegram_id} not found"
                    )
                    return False

        except Exception as e:
            logger.error(f"Failed to update user subscription: {e}")
            return False

    def delete_subscription(self, telegram_id: int) -> bool:
        """Delete user subscription.

        :param telegram_id: Telegram user ID
        :returns: True if successful, False otherwise
        """
        try:
            with self.session() as session:
                stmt = delete(UserSubscription).where(
                    UserSubscription.telegram_id == telegram_id
                )
                result = session.execute(stmt)

                if result.rowcount > 0:
                    logger.info(f"Deleted subscription for user {telegram_id}")
                    return True
                else:
                    logger.warning(f"Subscription for user {telegram_id} not found")
                    return False

        except Exception as e:
            logger.error(f"Failed to delete user subscription: {e}")
            return False

    def get_active_subscriptions(self) -> List[UserSubscription]:
        """Get all active user subscriptions.

        :returns: List of active UserSubscription objects
        """
        try:
            with self.session() as session:
                now = datetime.now(UTC)
                stmt = (
                    select(UserSubscription)
                    .where(UserSubscription.is_active == True)  # noqa: E712
                    .where(UserSubscription.expires_at > now)
                )
                result = session.execute(stmt)
                subscriptions = list(result.scalars().all())
                for subscription in subscriptions:
                    self._detach_instance(session, subscription)
                return subscriptions

        except Exception as e:
            logger.error(f"Failed to get active subscriptions: {e}")
            return []

    def get_expired_subscriptions(self) -> List[UserSubscription]:
        """Get all expired user subscriptions.

        :returns: List of expired UserSubscription objects
        """
        try:
            with self.session() as session:
                now = datetime.now(UTC)
                stmt = (
                    select(UserSubscription)
                    .where(UserSubscription.is_active == True)  # noqa: E712
                    .where(UserSubscription.expires_at <= now)
                )
                result = session.execute(stmt)
                subscriptions = list(result.scalars().all())
                for subscription in subscriptions:
                    self._detach_instance(session, subscription)
                return subscriptions

        except Exception as e:
            logger.error(f"Failed to get expired subscriptions: {e}")
            return []

    def extend_subscription(self, telegram_id: int, days: int) -> bool:
        """Extend user subscription by specified number of days.

        :param telegram_id: Telegram user ID
        :param days: Number of days to extend subscription
        :returns: True if successful, False otherwise
        """
        try:
            with self.session() as session:
                stmt = select(UserSubscription).where(
                    UserSubscription.telegram_id == telegram_id
                )
                result = session.execute(stmt)
                subscription = result.scalar_one_or_none()

                if not subscription:
                    logger.warning(f"Subscription for user {telegram_id} not found")
                    return False

                now = datetime.now(UTC)
                if subscription.expires_at and subscription.expires_at > now:
                    # Extend from current expiration date
                    subscription.expires_at += timedelta(days=days)
                else:
                    # Start new subscription period from now
                    subscription.expires_at = now + timedelta(days=days)
                    subscription.is_active = True

                return True

        except Exception as e:
            logger.error(f"Failed to extend user subscription: {e}")
            return False

    def is_subscription_active(self, telegram_id: int) -> bool:
        """Check if user has active subscription.

        :param telegram_id: Telegram user ID
        :returns: True if subscription is active, False otherwise
        """
        subscription = self.get_subscription(telegram_id)
        if not subscription:
            return False

        now = datetime.now(UTC)
        return subscription.is_active and (
            subscription.expires_at is None or subscription.expires_at > now
        )
