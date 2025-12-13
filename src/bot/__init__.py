"""Bot package initialization.

This package contains the bot application and its handlers.

The bot application is responsible for:
    - Initializing the bot
    - Setting up the bot's handlers
    - Starting the bot in polling mode
"""

from .application import LifeWeeksBot
from .handlers import (
    BaseHandler,
    SettingsHandler,
    StartHandler,
    UnknownHandler,
    WeeksHandler,
)

# Initialize database service if available
try:
    from ..database.service import user_service

    pass
except ImportError:
    # During testing or when database service is not available
    user_service = None

__all__ = [
    "LifeWeeksBot",
    "user_service",
    "BaseHandler",
    "SettingsHandler",
    "StartHandler",
    "UnknownHandler",
    "WeeksHandler",
]
