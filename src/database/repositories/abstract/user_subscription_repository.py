"""Abstract repository interface for user subscription operations.

Defines the contract for user subscription storage operations
that can be implemented by different database backends.
"""

from abc import abstractmethod
from typing import Optional

from ...models import UserSubscription
from .base_repository import AbstractBaseRepository


class AbstractUserSubscriptionRepository(AbstractBaseRepository):
    """Abstract base class for user subscription repository operations.

    Defines the interface for user subscription storage that can be implemented
    by different database backends (SQLite, PostgreSQL, etc.)
    """

    @abstractmethod
    def create_subscription(self, subscription: UserSubscription) -> bool:
        """Create a new user subscription.

        :param subscription: UserSubscription object to create
        :returns: True if successful, False otherwise
        :raises: DatabaseError if subscription already exists or other database error
        """
        pass

    @abstractmethod
    def get_subscription(self, telegram_id: int) -> Optional[UserSubscription]:
        """Get user subscription by Telegram ID.

        :param telegram_id: Telegram user ID
        :returns: UserSubscription object if found, None otherwise
        """
        pass

    @abstractmethod
    def update_subscription(self, subscription: UserSubscription) -> bool:
        """Update user subscription.

        :param subscription: UserSubscription object with updated data
        :returns: True if successful, False otherwise
        :raises: DatabaseError if subscription not found or other database error
        """
        pass

    @abstractmethod
    def delete_subscription(self, telegram_id: int) -> bool:
        """Delete user subscription.

        :param telegram_id: Telegram user ID
        :returns: True if successful, False otherwise
        """
        pass
