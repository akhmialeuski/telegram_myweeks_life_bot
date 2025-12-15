"""Handlers package for Telegram bot command processing.

This package contains all command handlers for the LifeWeeksBot Telegram bot.
Each handler is responsible for processing specific user commands and managing
the conversation flow.

The package includes:
- BaseHandler: Base class with common functionality
- StartHandler: Handles /start command and user registration
- WeeksHandler: Handles /weeks command for life statistics
- SettingsHandler: Handles /settings command and related callbacks
- VisualizeHandler: Handles /visualize command for life weeks visualization
- HelpHandler: Handles /help command for bot assistance
- SubscriptionHandler: Handles /subscription command for subscription management
- CancelHandler: Handles /cancel command for operation cancellation
- UnknownHandler: Handles unrecognized messages

All handlers inherit from BaseHandler and provide consistent error handling,
logging, and user experience.
"""

from .base_handler import BaseHandler
from .cancel_handler import CancelHandler
from .help_handler import HelpHandler
from .settings import (
    BirthDateHandler,
    LanguageHandler,
    LifeExpectancyHandler,
    SettingsDispatcher,
)
from .start_handler import StartHandler
from .subscription_handler import SubscriptionHandler
from .unknown_handler import UnknownHandler
from .visualize_handler import VisualizeHandler
from .weeks_handler import WeeksHandler

__all__ = [
    "BaseHandler",
    "StartHandler",
    "WeeksHandler",
    "SettingsDispatcher",
    "BirthDateHandler",
    "LanguageHandler",
    "LifeExpectancyHandler",
    "VisualizeHandler",
    "HelpHandler",
    "SubscriptionHandler",
    "CancelHandler",
    "UnknownHandler",
]
