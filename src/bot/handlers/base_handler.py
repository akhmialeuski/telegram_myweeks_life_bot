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
from typing import (
    Any,
    Callable,
    ClassVar,
    Optional,
    Protocol,
    TypeVar,
    runtime_checkable,
)

from telegram import CallbackQuery, InlineKeyboardMarkup, Update, User
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ...contracts import UserServiceProtocol
from ...core.dtos import UserProfileDTO
from ...core.exceptions import BotError
from ...i18n import use_locale
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


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandContext:
    """Data class for command context data.

    :ivar user: Telegram user object
    :type user: User
    :ivar user_id: Telegram user ID
    :type user_id: int
    :ivar language: User's preferred language code
    :type language: str
    :ivar user_profile: User's profile from database
    :type user_profile: Optional[UserProfileDTO]
    :ivar command_name: Name of the command being executed
    :type command_name: Optional[str]
    """

    user: User
    user_id: int
    language: str
    user_profile: Optional[UserProfileDTO] = None
    command_name: Optional[str] = None


@runtime_checkable
class ServiceContainerProtocol(Protocol):
    """Protocol for service container interface.

    This protocol defines the minimal interface that any service container
    must provide to be used with handlers. Allows using either the legacy
    ServiceContainer or new Protocol-based containers.
    """

    user_service: UserServiceProtocol


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

    def __init__(self, services: ServiceContainer | ServiceContainerProtocol) -> None:
        """Initialize the base handler.

        Sets up common attributes that all handlers need. Supports both
        the legacy ServiceContainer and new Protocol-based interfaces.

        :param services: Service container with all dependencies
        :type services: ServiceContainer | ServiceContainerProtocol
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

        # For commands not requiring registration (e.g., /help, /start), still
        # ensure MessageContext is available during execution.
        from ...core.message_context import use_message_context

        @wraps(handler_method)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
            cmd_context = await self._extract_command_context(update=update)
            async with use_message_context(
                user_info=cmd_context.user, fetch_profile=False
            ):
                return await handler_method(update, context)

        return wrapper

    async def _extract_command_context(self, update: Update) -> CommandContext:
        """Extract common context information from an update.

        :param update: The update object containing the user's message
        :type update: Update
        :returns: CommandContext object with user, user_id, language, and user_profile
        :rtype: CommandContext
        """
        user = update.effective_user
        user_id = user.id

        # Get user profile from database
        user_profile = await self.services.user_service.get_user_profile(
            telegram_id=user_id
        )

        # Get language from user profile or Telegram language code
        lang = (
            user_profile.settings.language
            if user_profile and user_profile.settings and user_profile.settings.language
            else (user.language_code or "en")
        )

        return CommandContext(
            user=user,
            user_id=user_id,
            language=lang,
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
                cmd_context = await self._extract_command_context(update=update)
                user_id = cmd_context.user_id
                user_lang = cmd_context.language

                try:
                    # Validate that user has completed registration with birth date
                    if not await self.services.user_service.is_valid_user_profile(
                        telegram_id=user_id
                    ):
                        # Use gettext for localization
                        _, _, pgettext = use_locale(user_lang)
                        await update.message.reply_text(
                            pgettext(
                                "common.not_registered",
                                "You are not registered. Use /start to register.",
                            )
                        )
                        return None

                    # Execute the original command handler under MessageContext
                    from ...core.message_context import use_message_context

                    async with use_message_context(
                        user_info=cmd_context.user, fetch_profile=True
                    ):
                        return await func(update, context)

                except BotError as error:
                    # Handle expected bot errors with localized messages
                    _, _, pgettext = use_locale(user_lang)
                    message = (
                        pgettext(error.user_message_key, error.message)
                        if error.user_message_key
                        else error.message
                    )
                    await self.send_error_message(
                        update=update,
                        cmd_context=cmd_context,
                        error_message=message,
                    )
                    return None

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
            f"{self.command_name}: [{cmd_context.user_id}]: Error occurred: {error_message}"
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
