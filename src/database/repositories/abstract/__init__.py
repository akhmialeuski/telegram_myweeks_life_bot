"""Abstract repository interfaces."""

from .user_repository import AbstractUserRepository
from .user_settings_repository import AbstractUserSettingsRepository
from .user_subscription_repository import AbstractUserSubscriptionRepository

__all__ = [
    "AbstractUserRepository",
    "AbstractUserSettingsRepository",
    "AbstractUserSubscriptionRepository",
]
