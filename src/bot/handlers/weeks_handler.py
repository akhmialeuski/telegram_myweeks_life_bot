"""Weeks command handler for life statistics.

This module contains the WeeksHandler class which handles the /weeks command
and displays detailed life statistics to users. It provides information about
age, weeks lived, remaining weeks, and life percentage.

The statistics include:
- Current age in years
- Total weeks lived
- Estimated remaining weeks (based on life expectancy)
- Percentage of life lived
- Days until next birthday
"""

from typing import Optional

from babel.numbers import format_decimal, format_percent
from telegram import Update
from telegram.ext import ContextTypes

from src.i18n import normalize_babel_locale, use_locale

from ...services.container import ServiceContainer
from ...utils.config import BOT_NAME
from ...utils.logger import get_logger
from ..constants import COMMAND_WEEKS
from .base_handler import BaseHandler

# Initialize logger for this module
logger = get_logger(BOT_NAME)


class WeeksHandler(BaseHandler):
    """Handler for /weeks command - display life statistics.

    This handler provides users with detailed statistics about their life
    including age, weeks lived, remaining weeks, life percentage, and
    days until next birthday. It's the core functionality of the bot.

    Attributes:
        command_name: Name of the command this handler processes
    """

    def __init__(self, services: ServiceContainer) -> None:
        """Initialize the weeks handler.

        Sets up the command name and initializes the base handler.

        :param services: Service container with all dependencies
        :type services: ServiceContainer
        """
        super().__init__(services)
        self.command_name = f"/{COMMAND_WEEKS}"

    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle /weeks command - display life statistics.

        This command provides users with detailed statistics about their life
        including age, weeks lived, remaining weeks, life percentage, and
        days until next birthday. It's the core functionality of the bot.

        The statistics calculation:
        1. Retrieves user profile from database
        2. Uses LifeCalculatorEngine to compute various metrics
        3. Formats statistics into a localized message
        4. Sends the formatted message to the user

        The statistics include:
        - Current age in years
        - Total weeks lived
        - Estimated remaining weeks (based on life expectancy)
        - Percentage of life lived
        - Days until next birthday

        :param update: The update object containing the weeks command
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        return await self._wrap_with_registration(handler_method=self._handle_weeks)(
            update=update,
            context=context,
        )

    async def _handle_weeks(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Internal method to handle /weeks command with registration check.

        :param update: The update object containing the weeks command
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        # Extract user information using the new helper method
        cmd_context = self._extract_command_context(update=update)
        user = cmd_context.user
        user_id = cmd_context.user_id

        logger.info(f"{self.command_name}: [{user_id}]: Handling command")

        # Resolve language via DB profile or Telegram fallback
        profile = self.services.user_service.get_user_profile(telegram_id=user_id)
        lang = (
            profile.settings.language
            if profile and profile.settings and profile.settings.language
            else (user.language_code or "en")
        )
        _, _, pgettext = use_locale(lang=lang)

        # Compute statistics
        calc_engine = self.services.get_life_calculator()(user=profile)
        stats = calc_engine.get_life_statistics()

        message_text = pgettext(
            "weeks.statistics",
            "📊 <b>Your life statistics:</b>\n\n"
            "🎂 <b>Age:</b> %(age)s years\n"
            "📅 <b>Weeks lived:</b> %(weeks_lived)s\n"
            "⏳ <b>Remaining weeks (until 80 years):</b> %(remaining_weeks)s\n"
            "📈 <b>Life progress:</b> %(life_percentage)s\n"
            "🎉 <b>Days until birthday:</b> %(days_until_birthday)s\n\n"
            "💡 Use /visualize to visualize your life weeks",
        ) % {
            "age": format_decimal(stats["age"], locale=normalize_babel_locale(lang)),
            "weeks_lived": format_decimal(
                stats["weeks_lived"],
                locale=normalize_babel_locale(lang),
                format="#,##0",
            ),
            "remaining_weeks": format_decimal(
                stats["remaining_weeks"],
                locale=normalize_babel_locale(lang),
                format="#,##0",
            ),
            "life_percentage": format_percent(
                stats["life_percentage"],
                locale=normalize_babel_locale(lang),
                format="#0.1%",
            ),
            "days_until_birthday": format_decimal(
                stats["days_until_birthday"], locale=normalize_babel_locale(lang)
            ),
        }

        # Generate and send life statistics message
        await self.send_message(
            update=update,
            message_text=message_text,
        )
        return None
