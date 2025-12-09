"""In-memory User Repository implementation for testing.

This module provides an in-memory implementation of UserRepositoryProtocol
that stores users in a dictionary for fast, isolated testing without
database dependencies.
"""

from datetime import UTC, datetime

from src.database.models.user import User


class InMemoryUserRepository:
    """In-memory implementation of UserRepositoryProtocol for testing.

    This implementation stores all user data in memory using a dictionary.
    It is suitable for unit tests where database isolation is required.

    Attributes:
        _users: Dictionary mapping telegram_id to User objects

    Example:
        >>> repo = InMemoryUserRepository()
        >>> repo.create_user(user=test_user)
        True
        >>> repo.get_user(telegram_id=123456)
        User(telegram_id=123456, ...)
    """

    def __init__(self) -> None:
        """Initialize the repository with an empty user store.

        :returns: None
        """
        self._users: dict[int, User] = {}

    def get_user(self, telegram_id: int) -> User | None:
        """Retrieve user by Telegram ID.

        :param telegram_id: Unique Telegram user identifier
        :type telegram_id: int
        :returns: User object if found, None otherwise
        :rtype: User | None
        """
        return self._users.get(telegram_id)

    def create_user(self, user: User) -> bool:
        """Create a new user record.

        :param user: User object to persist
        :type user: User
        :returns: True if creation successful, False if user already exists
        :rtype: bool
        """
        if user.telegram_id in self._users:
            return False
        self._users[user.telegram_id] = user
        return True

    def delete_user(self, telegram_id: int) -> bool:
        """Delete user by Telegram ID.

        :param telegram_id: Unique Telegram user identifier
        :type telegram_id: int
        :returns: True if deletion successful, False if user not found
        :rtype: bool
        """
        if telegram_id in self._users:
            del self._users[telegram_id]
            return True
        return False

    def update_user(self, user: User) -> bool:
        """Update an existing user record.

        :param user: User object with updated data
        :type user: User
        :returns: True if update successful, False if user not found
        :rtype: bool
        """
        if user.telegram_id not in self._users:
            return False
        self._users[user.telegram_id] = user
        return True

    def get_all_users(self) -> list[User]:
        """Get all users in the repository.

        :returns: List of all users
        :rtype: list[User]
        """
        return list(self._users.values())

    def initialize(self) -> None:
        """Initialize the repository (no-op for in-memory).

        :returns: None
        """
        pass

    def close(self) -> None:
        """Close the repository (clears all data).

        :returns: None
        """
        self._users.clear()

    def clear(self) -> None:
        """Clear all stored users.

        :returns: None
        """
        self._users.clear()

    def seed_user(
        self,
        telegram_id: int,
        username: str = "testuser",
        first_name: str = "Test",
        last_name: str = "User",
    ) -> User:
        """Seed a test user into the repository.

        Convenience method for test setup that creates a user with
        default values and returns it.

        :param telegram_id: Unique Telegram user identifier
        :type telegram_id: int
        :param username: Username for the test user
        :type username: str
        :param first_name: First name for the test user
        :type first_name: str
        :param last_name: Last name for the test user
        :type last_name: str
        :returns: The created user object
        :rtype: User
        """
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            created_at=datetime.now(tz=UTC),
        )
        self._users[telegram_id] = user
        return user
