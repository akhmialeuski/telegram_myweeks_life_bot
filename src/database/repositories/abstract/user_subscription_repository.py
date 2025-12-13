"""Abstract repository interface for user subscription operations.

Defines the contract for user subscription storage operations
that can be implemented by different database backends.
"""

from abc import abstractmethod
from typing import Optional

from ...models.user_subscription import UserSubscription
from .base_repository import AbstractBaseRepository


class AbstractUserSubscriptionRepository(AbstractBaseRepository):
    """Abstract base class for user subscription repository operations.

    Defines the interface for user subscription storage that can be implemented
    by different database backends (SQLite, PostgreSQL, etc.)
    """

    @abstractmethod
    async def create_subscription(self, subscription: UserSubscription) -> bool:
        """Create a new user subscription.

        :param subscription: UserSubscription object to create
        :type subscription: UserSubscription
        :returns: True if successful, False otherwise
        :rtype: bool
        :raises: DatabaseError if subscription already exists or other database error
        """

    @abstractmethod
    async def get_subscription(self, telegram_id: int) -> Optional[UserSubscription]:
        """Get user subscription by Telegram ID.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :returns: UserSubscription object if found, None otherwise
        :rtype: Optional[UserSubscription]
        """

    @abstractmethod
    async def update_subscription(self, subscription: UserSubscription) -> bool:
        """Update user subscription.

        :param subscription: UserSubscription object with updated data
        :type subscription: UserSubscription
        :returns: True if successful, False otherwise
        :rtype: bool
        :raises: DatabaseError if subscription not found or other database error
        """

    @abstractmethod
    async def delete_subscription(self, telegram_id: int) -> bool:
        """Delete user subscription.

        :param telegram_id: Telegram user ID
        :type telegram_id: int
        :returns: True if successful, False otherwise
        :rtype: bool
        """
