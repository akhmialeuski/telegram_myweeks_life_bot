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

from telegram import Update
from telegram.error import NetworkError, RetryAfter, TimedOut
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ..services.container import ServiceContainer
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
        "waiting_states": ["start_birth_date"],
    },
    COMMAND_WEEKS: {"class": WeeksHandler, "callbacks": []},
    COMMAND_SETTINGS: {
        "class": SettingsHandler,
        "callbacks": [
            {"method": "handle_settings_callback", "pattern": "settings_birth_date"},
            {"method": "handle_settings_callback", "pattern": "settings_language"},
            {
                "method": "handle_settings_callback",
                "pattern": "settings_life_expectancy",
            },
            {"method": "handle_language_callback", "pattern": "language_ru"},
            {"method": "handle_language_callback", "pattern": "language_en"},
            {"method": "handle_language_callback", "pattern": "language_ua"},
            {"method": "handle_language_callback", "pattern": "language_by"},
        ],
        "text_input": "handle_settings_input",
        "waiting_states": ["settings_birth_date", "settings_life_expectancy"],
    },
    COMMAND_VISUALIZE: {"class": VisualizeHandler, "callbacks": []},
    COMMAND_HELP: {"class": HelpHandler, "callbacks": []},
    COMMAND_SUBSCRIPTION: {
        "class": SubscriptionHandler,
        "callbacks": [
            {"method": "handle_subscription_callback", "pattern": "subscription_basic"},
            {
                "method": "handle_subscription_callback",
                "pattern": "subscription_premium",
            },
            {"method": "handle_subscription_callback", "pattern": "subscription_trial"},
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
        self._handler_instances = {}
        self._text_input_handlers = {}
        self._waiting_states = {}
        self.services = ServiceContainer()
        logger.info("Initializing LifeWeeksBot")

    def setup(self) -> None:
        """Set up the bot with command handlers for life weeks tracking.

        This method:
            - Creates the telegram.ext.Application instance
            - Registers post_init callback for scheduler startup
            - Registers global error handler for network and other errors
            - Registers all command handlers including conversation handler for /start
            - Configures the bot for operation
            - Sets up weekly notification scheduler

        :returns: None
        :raises RuntimeError: If application creation fails
        """
        if self._app is not None:
            return  # Already set up

        logger.info("Setting up bot application")
        builder = Application.builder().token(TOKEN)

        # Register post_init callback to start scheduler after event loop is created
        # This ensures APScheduler AsyncIOScheduler has access to running event loop
        builder.post_init(self._post_init_scheduler_start)

        self._app = builder.build()

        # Register global error handler for network and other errors
        self._app.add_error_handler(self._error_handler)

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
            - Runs the bot in polling mode to process incoming updates

        The scheduler is started via post_init callback registered in setup().
        This ensures APScheduler AsyncIOScheduler has access to running event loop.

        :returns: None
        :raises RuntimeError: If application is not properly configured
        """
        if not self._app:
            self.setup()

        logger.info("Starting Life Weeks Bot")
        self._app.run_polling()

    def stop(self) -> None:
        """Stop the life weeks bot and cleanup resources.

        This method:
            - Stops the weekly notification scheduler
            - Cleans up service container resources (database connections)
            - Performs any necessary cleanup

        :returns: None
        """
        if self._scheduler:
            stop_scheduler(self._scheduler)
            self._scheduler = None

        # Clean up service container resources
        if hasattr(self, "services"):
            self.services.cleanup()

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

        # Collect all handler instances and text input methods automatically from HANDLERS
        for command, config in HANDLERS.items():
            # Get handler class and create instance with services
            handler_class = config["class"]
            handler_instance = handler_class(self.services)
            self._handler_instances[command] = handler_instance

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

            # Collect text input handlers and waiting states if specified
            if "text_input" in config:
                text_input_method = getattr(handler_instance, config["text_input"])
                self._text_input_handlers[command] = text_input_method

                # Collect waiting states from config
                if "waiting_states" in config:
                    for state in config["waiting_states"]:
                        self._waiting_states[state] = command

                logger.debug(
                    f"Collected text input: {config['text_input']} for /{command}"
                )

        # Register the universal text handler
        self._app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, self._universal_text_handler
            )
        )
        logger.info("Registered universal text handler for routing text input")

        # Register message handler if specified (for unknown messages)
        for command, config in HANDLERS.items():
            if config.get("message_handler", False):
                handler_instance = self._handler_instances[command]
                self._app.add_handler(
                    MessageHandler(filters.ALL, handler_instance.handle)
                )
                logger.debug(f"Registered message handler: {command}")
                registered_text_handlers.append(f"{command}_message_handler")
                logger.info(
                    f"Message handlers registered: {', '.join(f'/{cmd}' for cmd in registered_text_handlers)}"
                )

    async def _universal_text_handler(self, update, context):
        """Universal text handler that routes messages to appropriate handlers.

        This method routes incoming text messages to the appropriate handler based on
        the user's current waiting state. It includes comprehensive error handling to
        prevent unhandled exceptions from propagating and ensure bot stability.

        :param update: Telegram update object containing the message
        :param context: Telegram context object containing user data and bot instance
        :returns: None
        :raises Exception: Only if all error handling fails and fallback also fails
        """
        waiting_for = context.user_data.get("waiting_for")

        if waiting_for in self._waiting_states:
            await self._handle_waiting_state(update, context, waiting_for)
        else:
            await self._handle_no_waiting_state(update, context)

    async def _handle_waiting_state(self, update, context, waiting_for: str) -> None:
        """Handle message when user is in a waiting state.

        :param update: Telegram update object containing the message
        :param context: Telegram context object containing user data and bot instance
        :param waiting_for: The waiting state identifier
        :returns: None
        """
        target_command = self._waiting_states[waiting_for]
        error_occurred = await self._try_text_input_handler(
            update, context, target_command
        )

        if error_occurred:
            fallback_error = await self._try_unknown_handler_fallback(
                update, context, waiting_for
            )
            if fallback_error:
                await self._send_error_message(update, context)

    async def _handle_no_waiting_state(self, update, context) -> None:
        """Handle message when user is not in any waiting state.

        :param update: Telegram update object containing the message
        :param context: Telegram context object containing user data and bot instance
        :returns: None
        """
        try:
            await self._handler_instances[COMMAND_UNKNOWN].handle(update, context)
        except Exception as error:
            logger.error(
                f"Error in unknown handler for no waiting state: {error}",
                exc_info=True,
            )

    async def _try_text_input_handler(
        self, update, context, target_command: str
    ) -> bool:
        """Try to execute text input handler for the target command.

        :param update: Telegram update object containing the message
        :param context: Telegram context object containing user data and bot instance
        :param target_command: The command to handle
        :returns: True if error occurred, False otherwise
        """
        if target_command not in self._text_input_handlers:
            return True

        try:
            await self._text_input_handlers[target_command](update, context)
            return False
        except Exception as error:
            logger.error(
                f"Error in text input handler for command '{target_command}': {error}",
                exc_info=True,
            )
            return True

    async def _try_unknown_handler_fallback(
        self, update, context, waiting_for: str
    ) -> bool:
        """Try to execute unknown handler as fallback.

        :param update: Telegram update object containing the message
        :param context: Telegram context object containing user data and bot instance
        :param waiting_for: The waiting state identifier for logging
        :returns: True if error occurred, False otherwise
        """
        try:
            await self._handler_instances[COMMAND_UNKNOWN].handle(update, context)
            return False
        except Exception as error:
            logger.error(
                f"Error in unknown handler fallback for waiting state '{waiting_for}': {error}",
                exc_info=True,
            )
            return True

    async def _send_error_message(self, update, context) -> None:
        """Send user-friendly error message when all handlers fail.

        :param update: Telegram update object containing the message
        :param context: Telegram context object containing user data and bot instance
        :returns: None
        """
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Sorry, something went wrong. Please try again or use /help for assistance.",
            )
        except Exception as final_error:
            logger.error(
                f"Failed to send error message to user: {final_error}",
                exc_info=True,
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
        - Provide error message and help suggestion for truly unknown input

        :returns: None
        """
        unknown_handler = UnknownHandler(self.services)

        # Register universal handler for all messages and commands
        # This will catch everything that wasn't handled by other handlers
        self._app.add_handler(MessageHandler(filters.ALL, unknown_handler.handle))

        logger.debug(
            "Registered universal unknown handler for all messages and commands"
        )
        logger.info("Unknown handler registered as universal fallback")

    async def _error_handler(
        self, update: Optional[Update], context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle errors that occur during bot operation.

        This global error handler catches all unhandled exceptions including:
            - Network errors (connection issues, timeouts, read errors)
            - Rate limiting errors (RetryAfter)
            - Other unexpected errors

        The handler logs errors appropriately and prevents bot crashes
        from network issues or other transient errors.

        :param update: Telegram update object, may be None for non-update errors
        :type update: Optional[Update]
        :param context: Telegram context object containing error information
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        error = context.error

        # Handle rate limiting - Telegram API rate limit exceeded
        # Check RetryAfter before NetworkError as it may inherit from it
        if isinstance(error, RetryAfter):
            logger.warning(
                f"Rate limit exceeded. Retry after {error.retry_after} seconds."
            )
            return

        # Handle timeout errors
        # Check TimedOut before NetworkError as it inherits from NetworkError
        if isinstance(error, TimedOut):
            logger.warning(
                f"Request timeout occurred: {error}. "
                "This is usually a temporary network issue."
            )
            return

        # Handle network errors - these are usually transient and should not crash the bot
        # Check NetworkError last as it's the base class for TimedOut
        if isinstance(error, NetworkError):
            logger.warning(
                f"Network error occurred: {error}. "
                "This is usually a temporary issue and will be retried automatically."
            )
            return

        # Log all other errors with full context
        logger.error(
            f"Unhandled exception occurred: {error}",
            exc_info=error,
        )

        # Try to notify user if update is available
        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        "Sorry, an unexpected error occurred. "
                        "Please try again later or use /help for assistance."
                    ),
                )
            except Exception as send_error:
                logger.error(
                    f"Failed to send error notification to user: {send_error}",
                    exc_info=True,
                )

    def _setup_scheduler(self) -> None:
        """Set up the weekly notification scheduler.

        This method:
            - Sets up the weekly notification scheduler
            - Sets up the scheduler instance
            - Logs the setup status
            - Stores scheduler in bot_data for access by handlers
        """
        try:
            self._scheduler = setup_user_notification_schedules(self._app)
            # Store scheduler in bot_data for access by handlers
            self._app.bot_data["scheduler"] = self._scheduler
            logger.debug("Set up weekly notification scheduler")
        except SchedulerSetupError as error:
            logger.error(
                f"Failed to set up weekly notification scheduler: {error.message}"
            )

    async def _post_init_scheduler_start(self, application: Application) -> None:
        """Post-initialization callback to start scheduler after event loop is created.

        This callback is registered via Application.post_init() and is called after
        the event loop is created and running. This ensures APScheduler AsyncIOScheduler
        can access the running event loop when it starts.

        The callback is called automatically by python-telegram-bot after the
        application is initialized and the event loop is running.

        :param application: The Application instance (unused, kept for signature compatibility)
        :type application: Application
        :returns: None
        """
        if self._scheduler:
            logger.info("Starting scheduler via post_init callback")
            start_scheduler(self._scheduler)
        else:
            logger.warning("Scheduler not configured, skipping start")
