"""Core functionality for the LifeWeeksBot application.

This package contains the core business logic for life tracking,
statistics calculation, and data processing.
"""

from .life_calculator import LifeCalculatorEngine
from .messages import (
    BaseMessageGenerator,
    CancelMessages,
    RegistrationMessages,
    SettingsMessages,
    SubscriptionMessages,
    SystemMessages,
    VisualizeMessages,
    WeeksMessages,
    get_user_language,
)
from .subscription_messages import (
    generate_message_week_addition_basic,
    generate_message_week_addition_premium,
    get_subscription_addition_message,
)

__all__ = [
    "LifeCalculatorEngine",
    # Class-based public API
    "BaseMessageGenerator",
    "WeeksMessages",
    "VisualizeMessages",
    "SystemMessages",
    "RegistrationMessages",
    "CancelMessages",
    "SubscriptionMessages",
    "SettingsMessages",
    "get_user_language",
    # Subscription message functions
    "generate_message_week_addition_basic",
    "generate_message_week_addition_premium",
    "get_subscription_addition_message",
]
