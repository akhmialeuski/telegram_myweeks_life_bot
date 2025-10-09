"""Repository interfaces and implementations.

This package provides repository interfaces and their implementations
for different database backends.
"""

from .abstract import (
    AbstractBaseRepository,
    AbstractUserRepository,
    AbstractUserSettingsRepository,
    AbstractUserSubscriptionRepository,
)
from .sqlite import (
    SQLiteUserRepository,
    SQLiteUserSettingsRepository,
    SQLiteUserSubscriptionRepository,
)

__all__ = [
    # Abstract repositories
    "AbstractBaseRepository",
    "AbstractUserRepository",
    "AbstractUserSettingsRepository",
    "AbstractUserSubscriptionRepository",
    # SQLite implementations
    "SQLiteUserRepository",
    "SQLiteUserSettingsRepository",
    "SQLiteUserSubscriptionRepository",
]
