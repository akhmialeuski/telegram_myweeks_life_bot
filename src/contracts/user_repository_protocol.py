"""User Repository Protocol for data access abstraction.

This module defines the contract for user data access operations.
Implementations include SQLiteUserRepository (production) and
InMemoryUserRepository (testing).
"""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..database.models.user import User


@runtime_checkable
class UserRepositoryProtocol(Protocol):
    """Repository contract for user data access.

    This protocol defines the interface for user persistence operations.
    Implementations should handle the actual data storage and retrieval.

    Implementations:
        - SQLiteUserRepository: Production SQLite implementation
        - InMemoryUserRepository: In-memory implementation for testing
    """

    def get_user(self, telegram_id: int) -> "User | None":
        """Retrieve user by Telegram ID.

        :param telegram_id: Unique Telegram user identifier
        :type telegram_id: int
        :returns: User object if found, None otherwise
        :rtype: User | None
        """
        ...

    def create_user(self, user: "User") -> bool:
        """Create a new user record.

        :param user: User object to persist
        :type user: User
        :returns: True if creation successful, False otherwise
        :rtype: bool
        """
        ...

    def delete_user(self, telegram_id: int) -> bool:
        """Delete user by Telegram ID.

        :param telegram_id: Unique Telegram user identifier
        :type telegram_id: int
        :returns: True if deletion successful, False otherwise
        :rtype: bool
        """
        ...

    def initialize(self) -> None:
        """Initialize the repository (e.g., create tables).

        :returns: None
        """
        ...

    def close(self) -> None:
        """Close any open connections.

        :returns: None
        """
        ...
