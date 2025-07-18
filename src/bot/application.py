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
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from ..utils.config import BOT_NAME, TOKEN
from ..utils.logger import get_logger
from .handlers import (
    WAITING_USER_INPUT,
    command_cancel,
    command_help,
    command_language_callback,
    command_settings,
    command_settings_callback,
    command_start,
    command_start_handle_birth_date,
    command_subscription,
    command_subscription_callback,
    command_visualize,
    command_weeks,
    handle_settings_input,
    handle_unknown_message,
)
from .scheduler import (
    setup_user_notification_schedules,
    start_scheduler,
    stop_scheduler,
)

logger = get_logger(BOT_NAME)

# Command handlers mapping
COMMAND_HANDLERS: Dict[str, Callable] = {
    "weeks": command_weeks,
    "visualize": command_visualize,
    "help": command_help,
    "cancel": command_cancel,
    "settings": command_settings,
    "subscription": command_subscription,
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
        - /settings - Show user settings
        - /subscription - Show user subscription
        - /help - Show help information

    :ivar _app: The telegram.ext.Application instance
    :type _app: Optional[Application]
    :ivar _scheduler: The weekly notification scheduler
    :type _scheduler: Optional[AsyncIOScheduler]
    """

    def __init__(self) -> None:
        """Initialize the life weeks bot with default settings.

        Creates a new bot instance with default configuration.
        The actual application setup is deferred until setup() is called.

        :returns: None
        """
        self._app: Optional[Application] = None
        self._scheduler = None
        logger.info("Initializing LifeWeeksBot")

    def setup(self) -> None:
        """Set up the bot with command handlers for life weeks tracking.

        This method:
            - Creates the telegram.ext.Application instance
            - Registers all command handlers including conversation handler for /start
            - Configures the bot for operation
            - Sets up weekly notification scheduler

        :returns: None
        :raises RuntimeError: If application creation fails
        """
        if self._app is not None:
            return  # Already set up

        logger.info("Setting up bot application")
        self._app = Application.builder().token(TOKEN).build()

        # Create conversation handler for /start command
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", command_start)],
            states={
                WAITING_USER_INPUT: [
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

        # Register callback query handlers
        self._app.add_handler(
            CallbackQueryHandler(
                command_subscription_callback, pattern="^subscription_"
            )
        )
        logger.debug("Registered callback query handler for subscription")

        # Register settings callback handlers
        self._app.add_handler(
            CallbackQueryHandler(command_settings_callback, pattern="^settings_")
        )
        logger.debug("Registered callback query handler for settings")

        self._app.add_handler(
            CallbackQueryHandler(command_language_callback, pattern="^language_")
        )
        logger.debug("Registered callback query handler for language selection")

        # Register handler for settings text input (must be before unknown messages)
        self._app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_settings_input)
        )
        logger.debug("Registered handler for settings text input")

        # Register handler for unknown messages and commands (must be last)
        self._app.add_handler(MessageHandler(filters.ALL, handle_unknown_message))
        logger.debug("Registered handler for unknown messages")

        # Set up weekly notification scheduler
        success = setup_user_notification_schedules(self._app)
        if success:
            # Get the scheduler instance from the global variable
            from .scheduler import _scheduler_instance

            self._scheduler = _scheduler_instance
            logger.debug("Set up weekly notification scheduler")
        else:
            logger.error("Failed to set up weekly notification scheduler")

        logger.info(
            f"Command handlers registered: /start, "
            f"{', '.join(f'/{cmd}' for cmd in COMMAND_HANDLERS.keys())}"
        )

    def start(self) -> None:
        """Start the life weeks bot in polling mode.

        This method:
            - Ensures the application is set up
            - Starts the weekly notification scheduler
            - Starts the bot in polling mode
            - Handles incoming updates

        :returns: None
        :raises RuntimeError: If application is not properly configured
        """
        if not self._app:
            self.setup()

        # Start the weekly notification scheduler
        if self._scheduler:
            start_scheduler(self._scheduler)

        logger.info("Starting Life Weeks Bot")
        self._app.run_polling()

    def stop(self) -> None:
        """Stop the life weeks bot and cleanup resources.

        This method:
            - Stops the weekly notification scheduler
            - Performs any necessary cleanup

        :returns: None
        """
        if self._scheduler:
            stop_scheduler(self._scheduler)
            self._scheduler = None

        logger.info("Life Weeks Bot stopped")
