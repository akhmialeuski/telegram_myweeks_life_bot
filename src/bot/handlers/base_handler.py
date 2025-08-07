"""Base handler class for Telegram bot command handlers.

This module provides a base class that all command handlers should inherit from.
It includes common functionality such as user validation, error handling,
logging, and message generation that is shared across all handlers.

The base handler provides:
- Common initialization and setup
- User registration validation
- Error handling and logging
- Message generation utilities
- Context management
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, ClassVar, Optional, TypeVar

from telegram import CallbackQuery, InlineKeyboardMarkup, Update, User
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ...core.messages import get_user_language
from ...services.container import ServiceContainer
from ...utils.config import BOT_NAME
from ...utils.logger import get_logger
from ..constants import COMMAND_HELP, COMMAND_START

# Initialize logger for this module
logger = get_logger(BOT_NAME)

# Type definitions for better type checking
T = TypeVar("T")
HandlerMethod = Callable[[Update, ContextTypes.DEFAULT_TYPE], Any]
DecoratedHandler = Callable[[HandlerMethod], HandlerMethod]


@dataclass
class CommandContext:
    """Data class for command context data."""

    user: User
    user_id: int
    language: str
    user_profile: Optional[Any] = None
    command_name: Optional[str] = None


class BaseHandler(ABC):
    """Base class for all command handlers.

    This class provides common functionality that all command handlers
    need, including user validation, error handling, logging, and
    message generation utilities.

    Attributes:
        bot_name: Name of the bot for logging purposes
        command_name: Name of the command this handler processes (set by subclasses)
        NO_REGISTRATION_COMMANDS: Class variable listing commands that don't require registration
    """

    # Class constants
    NO_REGISTRATION_COMMANDS: ClassVar[list[str]] = [
        f"/{COMMAND_START}",
        f"/{COMMAND_HELP}",
    ]

    def __init__(self, services: ServiceContainer) -> None:
        """Initialize the base handler.

        Sets up common attributes that all handlers need.

        :param services: Service container with all dependencies
        :type services: ServiceContainer
        """
        self.bot_name = BOT_NAME
        self.command_name: Optional[str] = None
        self.services = services

    def _should_require_registration(self) -> bool:
        """Check if this handler should require registration.

        :returns: True if registration should be required, False otherwise
        :rtype: bool
        """
        if not self.command_name:
            return True
        return self.command_name not in self.NO_REGISTRATION_COMMANDS

    def _wrap_with_registration(self, handler_method: HandlerMethod) -> HandlerMethod:
        """Wrap handler method with registration check if needed.

        :param handler_method: The original handler method
        :type handler_method: HandlerMethod
        :returns: Wrapped method or original method
        :rtype: HandlerMethod
        """
        if self._should_require_registration():
            return self.require_registration()(handler_method)
        return handler_method

    def _extract_command_context(self, update: Update) -> CommandContext:
        """Extract common context information from an update.

        :param update: The update object containing the user's message
        :type update: Update
        :returns: CommandContext object with user, user_id, language, and user_profile
        :rtype: CommandContext
        """
        user = update.effective_user
        user_id = user.id

        # Get user profile from database
        user_profile = self.services.user_service.get_user_profile(user_id)

        return CommandContext(
            user=user,
            user_id=user_id,
            language=get_user_language(user),
            user_profile=user_profile,
            command_name=None,
        )

    def require_registration(self) -> DecoratedHandler:
        """Decorator to check user registration and handle errors.

        This decorator provides a centralized way to verify that users
        have completed the registration process before allowing access
        to protected commands. It handles common error scenarios and
        provides consistent error messaging.

        The decorator:
        - Extracts user information from the update
        - Validates user registration status using the database service
        - Sends appropriate error messages for unregistered users
        - Catches and logs any exceptions that occur during command execution
        - Provides graceful error handling with user-friendly messages

        :returns: Decorated function that includes registration validation
        :rtype: DecoratedHandler

        Example:
            >>> @self.require_registration()
            >>> async def protected_command(self, update, context):
            >>>     # This code only runs for registered users
            >>>     pass
        """

        def decorator(func: HandlerMethod) -> HandlerMethod:
            @wraps(func)
            async def wrapper(
                update: Update,
                context: ContextTypes.DEFAULT_TYPE,
            ) -> Any:
                # Extract user information from the update
                cmd_context = self._extract_command_context(update)
                user_id = cmd_context.user_id
                user_lang = cmd_context.language

                try:
                    # Validate that user has completed registration with birth date
                    if not self.services.user_service.is_valid_user_profile(user_id):
                        # Use MessageBuilder for generating the message
                        builder = self.services.get_message_builder(user_lang)
                        await update.message.reply_text(builder.not_registered())
                        return None

                    # Execute the original command handler
                    return await func(update, context)

                except Exception as error:  # pylint: disable=broad-exception-caught
                    # Handle error through the centralized error handler
                    await self.send_error_message(
                        update=update,
                        cmd_context=cmd_context,
                        error_message=str(error),
                    )
                    return None

            return wrapper

        return decorator

    async def send_message(
        self,
        update: Update,
        message_text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> None:
        """Send message to user.

        :param update: The update object containing the user's message
        :type update: Update
        :param message_text: The message text to send
        :type message_text: str
        :param reply_markup: The reply markup to send
        :type reply_markup: Optional[InlineKeyboardMarkup]
        :returns: None
        """
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )

    async def edit_message(
        self,
        query: CallbackQuery,
        message_text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> None:
        """Edit message in chat.

        :param query: The query object containing the message to edit
        :type query: CallbackQuery
        :param message_text: The message text to send
        :type message_text: str
        :param reply_markup: The reply markup to send
        :type reply_markup: Optional[InlineKeyboardMarkup]
        :returns: None
        """
        await query.edit_message_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )

    async def send_error_message(
        self,
        update: Update,
        cmd_context: CommandContext,
        error_message: str,
    ) -> None:
        """Handle errors in a consistent way across all handlers.

        This method provides centralized error handling that logs the error
        and sends an appropriate message to the user.

        :param update: The update object containing the user's message
        :type update: Update
        :param cmd_context: Command context with user information
        :type cmd_context: CommandContext
        :param error_message: The error message to display
        :type error_message: str
        :returns: None
        """
        logger.error(
            f"/{self.command_name}: [{cmd_context.user_id}]: Error occurred: {error_message}"
        )

        # Send user-friendly error message
        await update.message.reply_text(
            text=error_message,
            parse_mode=ParseMode.HTML,
        )

    @abstractmethod
    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle the command or callback.

        This is the main method that each handler must implement.
        It should contain the logic for processing the specific command
        or callback that this handler is responsible for.

        :param update: The update object containing the user's message
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: Conversation state (if applicable) or None
        :rtype: Optional[int]
        """
        pass
