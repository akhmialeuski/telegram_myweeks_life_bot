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

from .application import LifeWeeksBot
from .handlers import (
    cancel,
    handle_birth_date,
    help_command,
    repository,
    start,
    visualize,
    weeks,
)

# Initialize database when module is imported
repository.initialize()

__all__ = [
    "LifeWeeksBot",
    "start",
    "handle_birth_date",
    "cancel",
    "weeks",
    "visualize",
    "help_command",
    "repository",
]
