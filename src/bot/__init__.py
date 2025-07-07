"""Bot package initialization.

This package contains the bot application and its handlers.

The bot application is responsible for:
    - Initializing the bot
    - Setting up the bot's handlers
    - Starting the bot in polling mode

The bot handlers are responsible for:
    - Handling the /start command (user registration)
    - Handling the /weeks command
    - Handling the /visualize command
    - Handling the /help command
"""

from ..database.service import user_service
from .application import LifeWeeksBot
from .handlers import (
    command_cancel,
    command_help,
    command_start,
    command_visualize,
    command_weeks,
)

# Initialize database
user_service.initialize()

__all__ = [
    "LifeWeeksBot",
    "user_service",
]
