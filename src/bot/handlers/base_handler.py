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
from functools import wraps
from typing import Any, Callable, Optional

from telegram import Update
from telegram.ext import ContextTypes

from ...core.messages import get_user_language
from ...database.service import user_service
from ...utils.config import BOT_NAME
from ...utils.localization import get_message
from ...utils.logger import get_logger


class BaseHandler(ABC):
    """Base class for all command handlers.

    This class provides common functionality that all command handlers
    need, including user validation, error handling, logging, and
    message generation utilities.

    Attributes:
        logger: Logger instance for this handler
        bot_name: Name of the bot for logging purposes
    """

    def __init__(self) -> None:
        """Initialize the base handler.

        Sets up logging and common attributes that all handlers need.
        """
        self.logger = get_logger(BOT_NAME)
        self.bot_name = BOT_NAME
        self.command_name = None

    def _should_require_registration(self) -> bool:
        """Check if this handler should require registration.

        :returns: True if registration should be required, False otherwise
        :rtype: bool
        """
        # Commands that don't require registration
        no_registration_commands = ["/start", "/help"]
        return self.command_name not in no_registration_commands

    def _wrap_with_registration(self, handler_method):
        """Wrap handler method with registration check if needed.

        :param handler_method: The original handler method
        :type handler_method: Callable
        :returns: Wrapped method or original method
        :rtype: Callable
        """
        if self._should_require_registration():
            return self.require_registration()(handler_method)
        return handler_method

    def require_registration(self) -> Callable:
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
        :rtype: Callable

        Example:
            >>> @self.require_registration()
            >>> async def protected_command(self, update, context):
            >>>     # This code only runs for registered users
            >>>     pass
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(
                update: Update,
                context: ContextTypes.DEFAULT_TYPE,
            ) -> Any:
                # Extract user information from the update
                user = update.effective_user
                user_id = user.id

                try:
                    # Validate that user has completed registration with birth date
                    if not user_service.is_valid_user_profile(user_id):
                        # Get user's language preference
                        user_lang = get_user_language(user)

                        await update.message.reply_text(
                            get_message(
                                message_key="common",
                                sub_key="not_registered",
                                language=user_lang,
                            )
                        )
                        return

                    # Execute the original command handler
                    return await func(update, context)

                except Exception as error:  # pylint: disable=broad-exception-caught
                    # Log the error for debugging and monitoring
                    self.logger.error(f"Error in {func.__name__} command: {error}")

                    # Get user's language preference
                    user_lang = get_user_language(user)

                    # Send user-friendly error message
                    await update.message.reply_text(
                        get_message(
                            message_key="common",
                            sub_key="error",
                            language=user_lang,
                        )
                    )

            return wrapper

        return decorator

    async def handle_error(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        error: Exception,
        error_message_key: str = "error",
    ) -> None:
        """Handle errors in a consistent way across all handlers.

        This method provides centralized error handling that logs the error
        and sends an appropriate message to the user.

        :param update: The update object containing the user's message
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :param error: The exception that occurred
        :type error: Exception
        :param error_message_key: Key for the error message to display
        :type error_message_key: str
        :returns: None
        """
        user = update.effective_user
        user_lang = get_user_language(user)

        # Log the error
        self.logger.error(f"Error in {self.__class__.__name__}: {error}")

        # Send user-friendly error message
        await update.message.reply_text(
            get_message(
                message_key="common",
                sub_key=error_message_key,
                language=user_lang,
            )
        )

    def get_user_language(self, user) -> str:
        """Get user's language preference.

        This is a convenience method that delegates to the core messages module.

        :param user: Telegram user object
        :type user: telegram.User
        :returns: User's language preference
        :rtype: str
        """
        return get_user_language(user)

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

    def log_command(self, user_id: int, command_name: str) -> None:
        """Log command execution for monitoring and debugging.

        :param user_id: ID of the user executing the command
        :type user_id: int
        :param command_name: Name of the command being executed
        :type command_name: str
        :returns: None
        """
        self.logger.info(f"User {user_id} executed {command_name} command")

    def log_callback(self, user_id: int, callback_data: str) -> None:
        """Log callback execution for monitoring and debugging.

        :param user_id: ID of the user executing the callback
        :type user_id: int
        :param callback_data: Data from the callback
        :type callback_data: str
        :returns: None
        """
        self.logger.info(f"User {user_id} executed callback: {callback_data}")
