"""Unknown message handler for unrecognized commands.

This module contains the UnknownHandler class which handles any messages
that are not recognized as valid commands. It provides helpful feedback
to users and suggests using the /help command.
"""

from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from ...core.message_context import use_message_context
from ...core.messages import SystemMessages
from ...services.container import ServiceContainer
from ...utils.config import BOT_NAME
from ...utils.logger import get_logger
from ..constants import COMMAND_UNKNOWN
from .base_handler import BaseHandler

# Initialize logger for this module
logger = get_logger(BOT_NAME)


class UnknownHandler(BaseHandler):
    """Handler for unknown messages and commands.

    This handler is called when user sends any message that is not a
    recognized command. It sends an error message and suggests using
    the /help command.

    Attributes:
        command_name: Name of this handler for logging purposes
    """

    def __init__(self, services: ServiceContainer) -> None:
        """Initialize the unknown message handler.

        Sets up the handler name and initializes the base handler.

        :param services: Service container with all dependencies
        :type services: ServiceContainer
        """
        super().__init__(services)
        self.command_name = f"/{COMMAND_UNKNOWN}"

    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle unknown messages and commands.

        This function is called when user sends any message or command that is not
        recognized by other handlers. It sends an error message and suggests
        using the /help command.

        The handler processes:
        - Unknown commands (e.g., /invalid_command)
        - Unknown text messages
        - Other message types (photos, documents, etc.)

        :param update: The update object containing the message
        :type update: Update
        :param context: The context object for the message processing
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        # Extract user information using the new helper method
        cmd_context = self._extract_command_context(update=update)
        user = cmd_context.user
        user_id = cmd_context.user_id
        message = update.message

        logger.info(f"{self.command_name}: [{user_id}]: Handling command")

        # Determine what type of message was sent using match statement
        match (message.text, message.text.startswith("/") if message.text else False):
            case (text, True) if text:
                # Unknown command
                logger.info(
                    f"{self.command_name}: [{user_id}]: Handling unknown command '{text}'"
                )
            case (text, False) if text:
                # Unknown text message
                logger.info(
                    f"{self.command_name}: [{user_id}]: Handling unknown text message '{text[:50]}...'"
                )
            case _:
                # Other message type (photo, document, etc.)
                message_type = type(message).__name__
                logger.info(
                    f"{self.command_name}: [{user_id}]: Handling unknown message type '{message_type}'"
                )

        with use_message_context(user_info=user, fetch_profile=False):
            message_text = SystemMessages().unknown(user_info=user)

        await self.send_message(
            update=update,
            message_text=message_text,
        )
