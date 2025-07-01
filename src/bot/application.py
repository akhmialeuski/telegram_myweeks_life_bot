"""Bot application setup and initialization.

This module provides the main bot application class that manages:
    - Bot initialization and configuration
    - Command handler registration
    - Application lifecycle management
    - Bot state management

The module uses a class-based approach to encapsulate all bot functionality
and provide a clean interface for bot management.
"""

from typing import Callable, Dict, Optional

from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from ..utils.config import BOT_NAME, TOKEN
from ..utils.logger import get_logger
from .handlers import (
    WAITING_BIRTH_DATE,
    command_cancel,
    command_help,
    command_start,
    command_start_handle_birth_date,
    command_visualize,
    command_weeks,
)

logger = get_logger(BOT_NAME)

# Command handlers mapping
COMMAND_HANDLERS: Dict[str, Callable] = {
    "weeks": command_weeks,
    "visualize": command_visualize,
    "help": command_help,
    "cancel": command_cancel,
}


class LifeWeeksBot:
    """Telegram bot for tracking and visualizing life weeks.

    This class manages the bot's functionality including:
        - Command handling for life weeks tracking
        - User interactions for week visualization
        - Bot state management
        - Application lifecycle

    The bot provides commands:
        - /start - User registration and setup
        - /weeks - Show current life weeks
        - /visualize - Generate week visualization
        - /help - Show help information

    :ivar _app: The telegram.ext.Application instance
    :type _app: Optional[Application]
    """

    def __init__(self) -> None:
        """Initialize the life weeks bot with default settings.

        Creates a new bot instance with default configuration.
        The actual application setup is deferred until setup() is called.

        :returns: None
        """
        self._app: Optional[Application] = None
        logger.info("Initializing LifeWeeksBot")

    def setup(self) -> None:
        """Set up the bot with command handlers for life weeks tracking.

        This method:
            - Creates the telegram.ext.Application instance
            - Registers all command handlers including conversation handler for /start
            - Configures the bot for operation

        :returns: None
        :raises RuntimeError: If application creation fails
        """
        logger.info("Setting up bot application")
        self._app = Application.builder().token(TOKEN).build()

        # Create conversation handler for /start command
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", command_start)],
            states={
                WAITING_BIRTH_DATE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, command_start_handle_birth_date
                    )
                ]
            },
            fallbacks=[CommandHandler("cancel", command_cancel)],
        )

        # Register conversation handler first
        self._app.add_handler(conv_handler)
        logger.debug("Registered conversation handler for /start command")

        # Register other command handlers from mapping
        for command, handler in COMMAND_HANDLERS.items():
            self._app.add_handler(CommandHandler(command, handler))
            logger.debug(f"Registered command handler: /{command}")

        logger.info(
            f"Command handlers registered: /start, {', '.join(f'/{cmd}' for cmd in COMMAND_HANDLERS.keys())}"
        )

    def start(self) -> None:
        """Start the life weeks bot in polling mode.

        This method:
            - Ensures the application is set up
            - Starts the bot in polling mode
            - Handles incoming updates

        :returns: None
        :raises RuntimeError: If application is not properly configured
        """
        if not self._app:
            self.setup()

        logger.info("Starting Life Weeks Bot")
        self._app.run_polling()
