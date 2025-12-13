"""Visualize command handler for life weeks visualization.

This module contains the VisualizeHandler class which handles the /visualize command
and generates visual representations of life weeks. It creates charts and graphs
to help users visualize their life progress.

The visualization includes:
- Life weeks chart showing lived vs remaining weeks
- Age progression visualization
- Life expectancy comparison
- Customizable chart types based on subscription
"""

from typing import Optional

from babel.numbers import format_decimal, format_percent
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from src.i18n import normalize_babel_locale, use_locale

from ...services.container import ServiceContainer
from ...utils.config import BOT_NAME
from ...utils.logger import get_logger
from ...visualization.grid import generate_visualization
from ..constants import COMMAND_VISUALIZE
from .base_handler import BaseHandler

# Initialize logger for this module
logger = get_logger(BOT_NAME)


class VisualizeHandler(BaseHandler):
    """Handler for /visualize command - generate life weeks visualization.

    This handler provides users with visual representations of their life
    weeks including charts, graphs, and progress indicators. The type of
    visualization depends on the user's subscription level.

    Attributes:
        command_name: Name of the command this handler processes
    """

    def __init__(self, services: ServiceContainer) -> None:
        """Initialize the visualize handler.

        Sets up the command name and initializes the base handler.

        :param services: Service container with all dependencies
        :type services: ServiceContainer
        """
        super().__init__(services)
        self.command_name = f"/{COMMAND_VISUALIZE}"

    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle /visualize command - generate life weeks visualization.

        This command creates and sends a visual grid representation of the user's
        life, showing weeks lived as filled cells and remaining weeks as empty cells.
        It provides both the visual image and a caption with key statistics.

        The visualization process:
        1. Retrieves user profile from database
        2. Generates visual grid using LifeCalculatorEngine
        3. Creates image with weeks lived highlighted
        4. Generates caption with key statistics
        5. Sends both image and caption to user

        The visual grid shows:
        - Each cell represents one week
        - Each row represents one year (52 weeks)
        - Green cells = weeks lived
        - Empty cells = weeks not yet lived
        - Years labeled on vertical axis
        - Weeks labeled on horizontal axis

        :param update: The update object containing the visualize command
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None

        Example:
            User sends /visualize → Bot generates grid image → Shows visual life representation
        """
        return await self._wrap_with_registration(self._handle_visualize)(
            update=update,
            context=context,
        )

    async def _handle_visualize(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Internal method to handle /visualize command with registration check.

        :param update: The update object containing the visualize command
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        # Extract user information using the new helper method
        cmd_context = await self._extract_command_context(update=update)
        user = cmd_context.user
        user_id = cmd_context.user_id

        logger.info(f"{self.command_name}: [{user_id}]: Handling command")

        # Resolve language via DB profile or Telegram fallback
        profile = await self.services.user_service.get_user_profile(telegram_id=user_id)
        lang = (
            profile.settings.language
            if profile and profile.settings and profile.settings.language
            else (user.language_code or "en")
        )
        _, _, pgettext = use_locale(lang=lang)

        # Compute statistics for caption
        calc_engine = self.services.get_life_calculator()(user=profile)
        stats = calc_engine.get_life_statistics()

        caption = pgettext(
            "visualize.info",
            "📊 <b>Visualization of your life weeks</b>\n\n"
            "🎂 Age: %(age)s years\n"
            "📅 Weeks lived: %(weeks_lived)s\n"
            "📈 Life progress: %(life_percentage)s\n\n"
            "🟩 Green cells = weeks lived\n"
            "⬜ White cells = future weeks",
        ) % {
            "age": format_decimal(stats["age"], locale=normalize_babel_locale(lang)),
            "weeks_lived": format_decimal(
                stats["weeks_lived"],
                locale=normalize_babel_locale(lang),
                format="#,##0",
            ),
            "life_percentage": format_percent(
                stats["life_percentage"],
                locale=normalize_babel_locale(lang),
                format="#0.1%",
            ),
        }

        # Generate and send visual representation with caption
        try:
            image_data = await generate_visualization(user_info=user)
        except Exception as e:
            logger.error(f"Failed to generate visualization: {e}")
            return None

        await update.message.reply_photo(
            photo=image_data,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
        return None
