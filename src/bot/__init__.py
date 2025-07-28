"""Bot package initialization.

This package contains the bot application and its handlers.

The bot application is responsible for:
    - Initializing the bot
    - Setting up the bot's handlers
    - Starting the bot in polling mode
"""

from ..database.service import user_service
from .application import LifeWeeksBot
from .handlers import (
    BaseHandler,
    SettingsHandler,
    StartHandler,
    UnknownHandler,
    WeeksHandler,
)

# Initialize database
user_service.initialize()

__all__ = [
    "LifeWeeksBot",
    "user_service",
    "BaseHandler",
    "SettingsHandler",
    "StartHandler",
    "UnknownHandler",
    "WeeksHandler",
]
