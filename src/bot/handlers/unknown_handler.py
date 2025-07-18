"""Unknown message handler for unrecognized commands.

This module contains the UnknownHandler class which handles any messages
that are not recognized as valid commands. It provides helpful feedback
to users and suggests using the /help command.
"""

from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from ...core.messages import generate_message_unknown_command
from ..constants import COMMAND_UNKNOWN
from .base_handler import BaseHandler


class UnknownHandler(BaseHandler):
    """Handler for unknown messages and commands.

    This handler is called when user sends any message that is not a
    recognized command. It sends an error message and suggests using
    the /help command.

    Attributes:
        handler_name: Name of this handler for logging purposes
    """

    def __init__(self) -> None:
        """Initialize the unknown message handler.

        Sets up the handler name and initializes the base handler.
        """
        super().__init__()
        self.command_name = f"/{COMMAND_UNKNOWN}"
        self.handler_name = "unknown_message"

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
        user = update.effective_user
        message = update.message

        # Determine what type of message was sent
        if message.text and message.text.startswith("/"):
            # Unknown command
            self.logger.info(
                f"Handling unknown command '{message.text}' from user {user.id}"
            )
        elif message.text:
            # Unknown text message
            self.logger.info(
                f"Handling unknown text message '{message.text[:50]}...' from user {user.id}"
            )
        else:
            # Other message type (photo, document, etc.)
            message_type = type(message).__name__
            self.logger.info(
                f"Handling unknown message type '{message_type}' from user {user.id}"
            )

        await update.message.reply_text(generate_message_unknown_command(user))
