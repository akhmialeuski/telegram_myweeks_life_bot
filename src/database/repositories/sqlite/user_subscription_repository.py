"""SQLite implementation of user subscription repository.

Provides SQLite-based implementation of AbstractUserSubscriptionRepository
for storing user subscriptions in SQLite database.
"""

import logging
from typing import Optional

from sqlalchemy import update

from ....utils.config import BOT_NAME
from ...models.user_subscription import UserSubscription
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
        return self._create_entity(
            subscription, f"subscription for user {subscription.telegram_id}"
        )

    def get_subscription(self, telegram_id: int) -> Optional[UserSubscription]:
        """Get user subscription by Telegram ID.

        :param telegram_id: Telegram user ID
        :returns: UserSubscription object if found, None otherwise
        """
        return self._get_entity_by_telegram_id(
            UserSubscription, telegram_id, "user subscription"
        )

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
                    logger.debug(
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
        return self._delete_entity_by_telegram_id(
            UserSubscription, telegram_id, "subscription"
        )
