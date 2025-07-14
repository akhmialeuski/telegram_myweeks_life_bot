"""Core functionality for the LifeWeeksBot application.

This package contains the core business logic for life tracking,
statistics calculation, and data processing.
"""

from .life_calculator import LifeCalculatorEngine
from .messages import (
    generate_message_birth_date_format_error,
    generate_message_birth_date_future_error,
    generate_message_birth_date_old_error,
    generate_message_cancel_error,
    generate_message_cancel_success,
    generate_message_help,
    generate_message_registration_error,
    generate_message_registration_success,
    generate_message_start_welcome_existing,
    generate_message_start_welcome_new,
    generate_message_subscription_already_active,
    generate_message_subscription_change_error,
    generate_message_subscription_change_failed,
    generate_message_subscription_change_success,
    generate_message_subscription_current,
    generate_message_subscription_invalid_type,
    generate_message_subscription_profile_error,
    generate_message_unknown_command,
    generate_message_visualize,
    generate_message_week,
)
from .subscription_messages import (
    generate_message_week_addition_basic,
    generate_message_week_addition_premium,
    get_subscription_addition_message,
)

__all__ = [
    "LifeCalculatorEngine",
    # Message generation functions
    "generate_message_birth_date_format_error",
    "generate_message_birth_date_future_error",
    "generate_message_birth_date_old_error",
    "generate_message_cancel_error",
    "generate_message_cancel_success",
    "generate_message_help",
    "generate_message_registration_error",
    "generate_message_registration_success",
    "generate_message_start_welcome_existing",
    "generate_message_start_welcome_new",
    "generate_message_subscription_already_active",
    "generate_message_subscription_change_error",
    "generate_message_subscription_change_failed",
    "generate_message_subscription_change_success",
    "generate_message_subscription_current",
    "generate_message_subscription_invalid_type",
    "generate_message_subscription_profile_error",
    "generate_message_unknown_command",
    "generate_message_visualize",
    "generate_message_week",
    # Subscription message functions
    "generate_message_week_addition_basic",
    "generate_message_week_addition_premium",
    "get_subscription_addition_message",
]
