"""Telegram bot application for tracking and visualizing life weeks.

This module provides the LifeWeeksBot class which serves as a thin bootstrapper
for the Telegram bot application. It delegates handler registration to the
plugin system and uses HandlerRegistry for centralized handler management.
"""

import asyncio
import multiprocessing
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

from ..bot.event_listeners import register_event_listeners
from ..scheduler.client import SchedulerClient
from ..scheduler.worker import SchedulerWorker
from ..services.container import ServiceContainer
from ..utils.config import BOT_NAME, TOKEN
from ..utils.logger import get_logger
from .constants import COMMAND_UNKNOWN
from .conversations.states import STATE_TO_COMMAND, ConversationState
from .plugins.loader import HandlerConfig, PluginLoader
from .registry import HandlerRegistry

logger = get_logger(BOT_NAME)


class LifeWeeksBot:
    """Telegram bot for tracking and visualizing life weeks.

    This class serves as a thin bootstrapper that:
    - Loads handler plugins via PluginLoader
    - Registers handlers using HandlerRegistry
    - Manages application lifecycle (setup, start, stop)
    - Handles errors and scheduler integration

    :ivar _app: The telegram.ext.Application instance
    :type _app: Optional[Application]
    :ivar _scheduler: The weekly notification scheduler
    :type _scheduler: Optional[AsyncIOScheduler]
    :ivar services: Service container for dependency injection
    :type services: ServiceContainer
    :ivar registry: Handler registry for managing handlers
    :type registry: HandlerRegistry
    """

    def __init__(
        self,
        services: ServiceContainer | None = None,
        plugin_loader: PluginLoader | None = None,
    ) -> None:
        """Initialize the life weeks bot.

        :param services: Optional service container (creates new if not provided)
        :type services: ServiceContainer | None
        :param plugin_loader: Optional plugin loader (creates new if not provided)
        :type plugin_loader: PluginLoader | None
        """
        self._app: Optional[Application] = None
        # Scheduler process components
        self._scheduler_process: Optional[multiprocessing.Process] = None
        self._scheduler_client: Optional[SchedulerClient] = None
        self._scheduler_command_queue: Optional[multiprocessing.Queue] = None
        self._scheduler_response_queue: Optional[multiprocessing.Queue] = None

        self.services = services or ServiceContainer()
        self.registry = HandlerRegistry()
        self._plugin_loader = plugin_loader or PluginLoader()

        # Handler state for universal text handler routing
        self._handler_instances: dict[str, object] = {}
        self._text_input_handlers: dict[str, object] = {}
        self._waiting_states: dict[str, str] = {}  # Maps state value to command

        logger.info("Initializing LifeWeeksBot")

    def setup(self) -> None:
        """Set up the bot with command handlers.

        This method:
        - Creates the telegram.ext.Application instance
        - Discovers and registers handlers via plugin system
        - Registers global error handler
        - Sets up weekly notification scheduler

        :returns: None
        """
        if self._app is not None:
            return  # Already set up

        logger.info("Setting up bot application")
        builder = Application.builder().token(TOKEN)
        builder.post_init(self._post_init_scheduler_start)
        self._app = builder.build()

        # Register global error handler
        self._app.add_error_handler(self._error_handler)

        # Register event listeners
        register_event_listeners(self.services)

        # Discover and register handlers
        self._discover_and_register_handlers()

        # Register universal text handler
        self._app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self._universal_text_handler,
            )
        )
        logger.info("Registered universal text handler")

        # Register unknown handler as fallback
        self._register_unknown_handler_fallback()

        # Set up scheduler
        self._setup_scheduler()

    def _discover_and_register_handlers(self) -> None:
        """Discover handlers via plugin loader and register them.

        :returns: None
        """
        configs = self._plugin_loader.discover_handlers()

        for config in configs:
            self._register_handler_from_config(config)

    def _register_handler_from_config(self, config: HandlerConfig) -> None:
        """Register a single handler from its configuration.

        :param config: Handler configuration
        :type config: HandlerConfig
        :returns: None
        """
        try:
            handler_class = self._plugin_loader.load_handler_class(config)
            handler_instance = handler_class(self.services)

            # Store in handler dicts for routing
            self._handler_instances[config.command] = handler_instance

            # Register command handler
            self._app.add_handler(
                CommandHandler(config.command, handler_instance.handle)
            )
            logger.debug(f"Registered command handler: /{config.command}")

            # Register callbacks
            for callback in config.callbacks:
                callback_method = getattr(handler_instance, callback["method"])
                self._app.add_handler(
                    CallbackQueryHandler(
                        callback_method,
                        pattern=callback["pattern"],
                    )
                )
                logger.debug(f"Registered callback: {callback['method']}")

            # Register text input handler
            text_input_method = None
            if config.text_input:
                text_input_method = getattr(handler_instance, config.text_input)
                self._text_input_handlers[config.command] = text_input_method

            # Register waiting states
            waiting_states = config.waiting_states
            for state in waiting_states:
                self._waiting_states[state] = config.command

            # Register in HandlerRegistry
            self.registry.register(
                command=config.command,
                handler=handler_instance,
                text_input_method=text_input_method,
                waiting_states=waiting_states if waiting_states else None,
            )

        except Exception as error:
            logger.error(f"Failed to register handler '{config.command}': {error}")

    def _register_unknown_handler_fallback(self) -> None:
        """Register unknown handler as universal fallback.

        :returns: None
        """
        if COMMAND_UNKNOWN in self._handler_instances:
            unknown_handler = self._handler_instances[COMMAND_UNKNOWN]
            self._app.add_handler(MessageHandler(filters.ALL, unknown_handler.handle))
            logger.debug("Registered unknown handler as fallback")

    def start(self) -> None:
        """Start the bot in polling mode.

        :returns: None
        """
        if not self._app:
            self.setup()

        logger.info("Starting Life Weeks Bot")
        self._app.run_polling()

    def stop(self) -> None:
        """Stop the bot and cleanup resources.

        :returns: None
        """
        if self._scheduler_client:
            # Try to shutdown gracefully
            try:
                # We can't await here easily if valid async context not present,
                # but run_polling handles loop.
                # However, cleaner to just terminate process if needed.
                # Ideally we send SHUTDOWN command.
                pass
            except Exception:
                pass

        if self._scheduler_process and self._scheduler_process.is_alive():
            logger.info("Stopping scheduler worker process...")
            self._scheduler_process.terminate()
            self._scheduler_process.join(timeout=5)
            logger.info("Scheduler worker stopped")

        self._scheduler_process = None
        self._scheduler_client = None

        if hasattr(self, "services"):
            asyncio.run(self.services.cleanup())

        logger.info("Life Weeks Bot stopped")

    async def _universal_text_handler(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Route text messages to appropriate handlers.

        :param update: Telegram update object
        :type update: Update
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        waiting_for = context.user_data.get("waiting_for")
        # Convert string state to ConversationState enum for FSM routing
        current_state = ConversationState.from_string(value=waiting_for)

        if current_state != ConversationState.IDLE:
            await self._handle_waiting_state(update, context, current_state)
        else:
            await self._handle_no_waiting_state(update, context)

    async def _handle_waiting_state(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        current_state: ConversationState,
    ) -> None:
        """Handle message when user is in a waiting state.

        :param update: Telegram update object
        :type update: Update
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :param current_state: Current conversation state from FSM
        :type current_state: ConversationState
        :returns: None
        """
        # Use STATE_TO_COMMAND mapping for FSM-based routing
        target_command = STATE_TO_COMMAND.get(
            current_state, self._waiting_states.get(current_state.value, "")
        )
        error_occurred = await self._try_text_input_handler(
            update, context, target_command
        )

        if error_occurred:
            fallback_error = await self._try_unknown_handler_fallback(
                update, context, current_state.value
            )
            if fallback_error:
                await self._send_error_message(update, context)

    async def _handle_no_waiting_state(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle message when user is not in any waiting state.

        :param update: Telegram update object
        :type update: Update
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        try:
            if COMMAND_UNKNOWN in self._handler_instances:
                await self._handler_instances[COMMAND_UNKNOWN].handle(update, context)
        except Exception as error:
            logger.error(f"Error in unknown handler: {error}", exc_info=True)

    async def _try_text_input_handler(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        target_command: str,
    ) -> bool:
        """Try to execute text input handler for the target command.

        :param update: Telegram update object
        :type update: Update
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :param target_command: The command to handle
        :type target_command: str
        :returns: True if error occurred, False otherwise
        :rtype: bool
        """
        if target_command not in self._text_input_handlers:
            return True

        try:
            await self._text_input_handlers[target_command](update, context)
            return False
        except Exception as error:
            logger.error(
                f"Error in text input handler for '{target_command}': {error}",
                exc_info=True,
            )
            return True

    async def _try_unknown_handler_fallback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        waiting_for: str,
    ) -> bool:
        """Try to execute unknown handler as fallback.

        :param update: Telegram update object
        :type update: Update
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :param waiting_for: The waiting state identifier
        :type waiting_for: str
        :returns: True if error occurred, False otherwise
        :rtype: bool
        """
        try:
            if COMMAND_UNKNOWN in self._handler_instances:
                await self._handler_instances[COMMAND_UNKNOWN].handle(update, context)
            return False
        except Exception as error:
            logger.error(
                f"Error in unknown handler fallback for '{waiting_for}': {error}",
                exc_info=True,
            )
            return True

    async def _send_error_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Send user-friendly error message.

        :param update: Telegram update object
        :type update: Update
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Sorry, something went wrong. Please try again or use /help.",
            )
        except Exception as error:
            logger.error(f"Failed to send error message: {error}", exc_info=True)

    async def _error_handler(
        self,
        update: Optional[Update],
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Handle errors during bot operation.

        :param update: Telegram update object (may be None)
        :type update: Optional[Update]
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        error = context.error

        if isinstance(error, RetryAfter):
            logger.warning(f"Rate limit exceeded. Retry after {error.retry_after}s.")
            return

        if isinstance(error, TimedOut):
            logger.warning(f"Request timeout: {error}. Temporary network issue.")
            return

        if isinstance(error, NetworkError):
            logger.warning(f"Network error: {error}. Will retry automatically.")
            return

        logger.error(f"Unhandled exception: {error}", exc_info=error)

        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Sorry, an error occurred. Please try again or use /help.",
                )
            except Exception as send_error:
                logger.error(f"Failed to notify user: {send_error}", exc_info=True)

    def _setup_scheduler(self) -> None:
        """Set up the scheduler worker process.

        Creates IPC queues, initializes the worker and client,
        and starts the worker process.

        :returns: None
        """
        try:
            logger.info("Setting up scheduler worker process")

            # Create IPC queues
            self._scheduler_command_queue = multiprocessing.Queue()
            self._scheduler_response_queue = multiprocessing.Queue()

            # Initialize client
            self._scheduler_client = SchedulerClient(
                command_queue=self._scheduler_command_queue,
                response_queue=self._scheduler_response_queue,
            )

            # Register client with container
            self.services.set_scheduler_client(self._scheduler_client)

            # Initialize worker
            worker = SchedulerWorker(
                command_queue=self._scheduler_command_queue,
                response_queue=self._scheduler_response_queue,
            )

            # Create and start process
            self._scheduler_process = multiprocessing.Process(
                target=worker.run,
                name="SchedulerWorker",
                daemon=True,  # Daemonize to ensure it dies with parent
            )
            self._scheduler_process.start()

            # Start client listener loop
            # We need to run this in the event loop, which isn't running yet in setup()
            # It will be started in post_init or when needed.

            logger.info(
                f"Scheduler worker started (PID: {self._scheduler_process.pid})"
            )

        except Exception as error:
            logger.error(f"Failed to set up scheduler: {error}", exc_info=True)

    async def _post_init_scheduler_start(self, application: Application) -> None:
        """Post-initialization hook.

        :param application: The Application instance
        :type application: Application
        :returns: None
        """
        # Initialize services (database connections)
        await self.services.initialize()

        if self._scheduler_client:
            # Start client listening for responses
            await self._scheduler_client.start_listening()

            # Check worker health
            healthy = await self._scheduler_client.health_check()
            if healthy:
                logger.info("Scheduler worker is healthy and connected")
            else:
                logger.warning("Scheduler worker health check failed")
