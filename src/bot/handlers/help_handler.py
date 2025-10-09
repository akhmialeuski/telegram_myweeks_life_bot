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

from src.i18n import use_locale

from ...services.container import ServiceContainer
from ...utils.config import BOT_NAME
from ...utils.logger import get_logger
from ..constants import COMMAND_HELP
from .base_handler import BaseHandler

# Initialize logger for this module
logger = get_logger(BOT_NAME)


class HelpHandler(BaseHandler):
    """Handler for /help command - show bot assistance.

    This handler provides users with comprehensive help information
    including available commands, features, and usage instructions.
    The help content is tailored based on the user's subscription level.

    Attributes:
        command_name: Name of the command this handler processes
    """

    def __init__(self, services: ServiceContainer) -> None:
        """Initialize the help handler.

        Sets up the command name and initializes the base handler.

        :param services: Service container with all dependencies
        :type services: ServiceContainer
        """
        super().__init__(services)
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
        cmd_context = self._extract_command_context(update=update)

        logger.info(f"{self.command_name}: [{cmd_context.user_id}]: Handling command")

        # Resolve language from DB profile or Telegram fallback
        profile = self.services.user_service.get_user_profile(
            telegram_id=cmd_context.user_id
        )
        lang = (
            profile.settings.language
            if profile and profile.settings and profile.settings.language
            else (cmd_context.user.language_code or "en")
        )
        _, _, pgettext = use_locale(lang=lang)

        await self.send_message(
            update=update,
            message_text=pgettext(
                "help.text",
                "🤖 LifeWeeksBot - Helps you track the weeks of your life\n\n"
                "📋 Available commands:\n"
                "• /start - Registration and settings\n"
                "• /weeks - Show life weeks\n"
                "• /visualize - Visualize life weeks\n"
                "• /settings - Settings\n"
                "• /subscription - Subscription\n"
                "• /help - This help\n\n"
                "💡 Fun facts:\n"
                "• There are 52 weeks in a year\n"
                "• Average life expectancy: 80 years\n"
                "• That's about 4,160 weeks\n\n"
                "🎯 The goal of the bot is to help you realize the value of time!",
            ),
        )
        return None
