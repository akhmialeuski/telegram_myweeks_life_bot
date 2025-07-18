"""Help command handler for bot assistance.

This module contains the HelpHandler class which handles the /help command
and provides users with information about available commands and features.

The help system includes:
- List of available commands
- Command descriptions and usage
- Feature explanations
- Subscription information
"""

from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from ...core.messages import generate_message_help
from ..constants import COMMAND_HELP
from .base_handler import BaseHandler


class HelpHandler(BaseHandler):
    """Handler for /help command - show bot assistance.

    This handler provides users with comprehensive help information
    including available commands, features, and usage instructions.
    The help content is tailored based on the user's subscription level.

    Attributes:
        command_name: Name of the command this handler processes
    """

    def __init__(self) -> None:
        """Initialize the help handler.

        Sets up the command name and initializes the base handler.
        """
        super().__init__()
        self.command_name = f"/{COMMAND_HELP}"

    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle /help command - show bot usage information.

        This command provides users with information about available commands
        and how to use the bot. It's available to all users, including those
        who haven't completed registration.

        The help information includes:
        - List of available commands
        - Brief description of each command
        - Usage instructions
        - Contact information if needed

        :param update: The update object containing the help command
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None

        Example:
            User sends /help → Bot shows available commands and usage instructions
        """
        # Extract user information
        user = update.effective_user
        self.log_command(user.id, self.command_name)
        self.logger.info(f"Handling /help command from user {user.id}")

        # Generate and send help message
        await update.message.reply_text(
            text=generate_message_help(user_info=user),
            parse_mode="HTML",
        )
