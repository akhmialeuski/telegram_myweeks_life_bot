"""Bot application setup and initialization.

This module provides the main bot application class that manages:
    - Bot initialization and configuration
    - Command handler registration
    - Application lifecycle management
    - Bot state management

The module uses a class-based approach to encapsulate all bot functionality
and provide a clean interface for bot management.
"""

from typing import Optional

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from ..utils.config import BOT_NAME, TOKEN
from ..utils.logger import get_logger
from .constants import (
    COMMAND_CANCEL,
    COMMAND_HELP,
    COMMAND_SETTINGS,
    COMMAND_START,
    COMMAND_SUBSCRIPTION,
    COMMAND_UNKNOWN,
    COMMAND_VISUALIZE,
    COMMAND_WEEKS,
)
from .handlers import (
    CancelHandler,
    HelpHandler,
    SettingsHandler,
    StartHandler,
    SubscriptionHandler,
    UnknownHandler,
    VisualizeHandler,
    WeeksHandler,
)
from .scheduler import (
    SchedulerSetupError,
    _scheduler_instance,
    setup_user_notification_schedules,
    start_scheduler,
    stop_scheduler,
)

logger = get_logger(BOT_NAME)


# Unified handlers mapping
HANDLERS = {
    COMMAND_START: {
        "class": StartHandler,
        "callbacks": [],
        "text_input": "handle_birth_date_input",
    },
    COMMAND_WEEKS: {"class": WeeksHandler, "callbacks": []},
    COMMAND_SETTINGS: {
        "class": SettingsHandler,
        "callbacks": [
            {"method": "handle_settings_callback", "pattern": "^settings_"},
            {"method": "handle_language_callback", "pattern": "^language_"},
        ],
        "text_input": "handle_settings_input",
    },
    COMMAND_VISUALIZE: {"class": VisualizeHandler, "callbacks": []},
    COMMAND_HELP: {"class": HelpHandler, "callbacks": []},
    COMMAND_SUBSCRIPTION: {
        "class": SubscriptionHandler,
        "callbacks": [
            {"method": "handle_subscription_callback", "pattern": "^subscription_"}
        ],
    },
    COMMAND_CANCEL: {"class": CancelHandler, "callbacks": []},
    COMMAND_UNKNOWN: {"class": UnknownHandler, "callbacks": []},
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
        - /cancel - Cancel current conversation

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

        # Automatically register all handlers from HANDLERS
        self._register_handlers()

        # Register unknown handler separately
        self._register_unknown_handler()

        # Set up weekly notification scheduler
        self._setup_scheduler()

    def start(self) -> None:
        """Start the life weeks bot in polling mode.

        This method:
            - Ensures the application is set up (calls setup() if needed)
            - Starts the weekly notification scheduler if it is configured
            - Runs the bot in polling mode to process incoming updates

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

    def _register_handlers(self) -> None:
        """Register all command handlers, callbacks, and text input handlers.

        This private method automatically registers all handlers defined in the
        HANDLERS dictionary. It processes each handler configuration and creates
        the appropriate handler instances for commands, callbacks, and text input.

        The registration process performs the following actions:
        - Registers a command handler for each command defined in HANDLERS
        - Registers callback query handlers for each callback specified in the handler configuration
        - Registers text input handlers if specified in the handler configuration
        - Registers a message handler for unknown messages if indicated in the handler configuration

        :returns: None
        """
        registered_commands = []
        registered_callbacks = []
        registered_text_handlers = []

        for command, config in HANDLERS.items():
            # Get handler class and create instance
            handler_class = config["class"]
            handler_instance = handler_class()

            # Register command handler
            self._app.add_handler(CommandHandler(command, handler_instance.handle))
            logger.debug(f"Registered command handler: /{command}")
            registered_commands.append(command)
            logger.info(f"Command handlers registered: /{command}")

            # Register callbacks if any
            for callback in config.get("callbacks", []):
                callback_method = getattr(handler_instance, callback["method"])
                self._app.add_handler(
                    CallbackQueryHandler(callback_method, pattern=callback["pattern"])
                )
                logger.debug(
                    f"Registered callback: {callback['method']} for /{command}"
                )
                registered_callbacks.append(f"{command}_{callback['method']}")
                logger.info(
                    f"Callback handlers registered: {', '.join(f'/{cmd}' for cmd in registered_callbacks)}"
                )

            # Register text input handler if specified
            if "text_input" in config:
                text_input_method = getattr(handler_instance, config["text_input"])
                self._app.add_handler(
                    MessageHandler(filters.TEXT & ~filters.COMMAND, text_input_method)
                )
                logger.debug(
                    f"Registered text input: {config['text_input']} for /{command}"
                )
                registered_text_handlers.append(f"{command}_{config['text_input']}")
                logger.info(
                    f"Text input handlers registered: {', '.join(f'/{cmd}' for cmd in registered_text_handlers)}"
                )

            # Register message handler if specified (for unknown messages)
            if config.get("message_handler", False):
                self._app.add_handler(
                    MessageHandler(filters.ALL, handler_instance.handle)
                )
                logger.debug(f"Registered message handler: {command}")
                registered_text_handlers.append(f"{command}_message_handler")
                logger.info(
                    f"Message handlers registered: {', '.join(f'/{cmd}' for cmd in registered_text_handlers)}"
                )

    def _register_unknown_handler(self) -> None:
        """Register the unknown handler for handling unknown messages and commands.

        This private method registers the UnknownHandler as a MessageHandler
        with filters.ALL to catch all messages and commands that are not handled
        by other handlers. This handler must be registered last to act as a fallback
        for any unrecognized input.

        The handler will:
        - Catch all unknown commands (e.g., /invalid_command)
        - Catch all unknown text messages
        - Catch all other message types (photos, documents, etc.)
        - Route text input to appropriate handlers based on context.user_data["waiting_for"]
        - Provide error message and help suggestion for truly unknown input

        :returns: None
        """
        unknown_handler = UnknownHandler()

        # Register universal handler for all messages and commands
        # This will catch everything that wasn't handled by other handlers
        self._app.add_handler(MessageHandler(filters.ALL, unknown_handler.handle))

        logger.debug(
            "Registered universal unknown handler for all messages and commands"
        )
        logger.info(
            "Unknown handler registered as universal fallback with routing capability"
        )

    def _setup_scheduler(self) -> None:
        """Set up the weekly notification scheduler.

        This method:
            - Sets up the weekly notification scheduler
            - Sets up the scheduler instance
            - Logs the setup status
        """
        try:
            setup_user_notification_schedules(self._app)
            self._scheduler = _scheduler_instance
            logger.debug("Set up weekly notification scheduler")
        except SchedulerSetupError as error:
            logger.error(
                f"Failed to set up weekly notification scheduler: {error.message}"
            )
