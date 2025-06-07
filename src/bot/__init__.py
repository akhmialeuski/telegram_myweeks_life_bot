"""Bot package initialization.

This package contains the bot application and its handlers.

The bot application is responsible for:
    - Initializing the bot
    - Setting up the bot's handlers
    - Starting the bot in polling mode

The bot handlers are responsible for:
    - Handling the /weeks command
    - Handling the /visualize command
"""

from .handlers import weeks, visualize
from .application import LifeWeeksBot

__all__ = ["LifeWeeksBot", "weeks", "visualize"]