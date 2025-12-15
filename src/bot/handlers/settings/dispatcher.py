"""Dispatcher handler for settings command.

This module provides the SettingsDispatcher which handles the main /settings command
and displays the settings menu to the user.
"""

from typing import Optional

from babel.dates import format_date
from babel.numbers import format_decimal
from telegram import Update
from telegram.ext import ContextTypes

from src.bot.constants import COMMAND_SETTINGS
from src.bot.handlers.base_handler import BaseHandler
from src.enums import SubscriptionType
from src.i18n import get_localized_language_name, normalize_babel_locale, use_locale
from src.services.container import ServiceContainer
from src.utils.config import BOT_NAME
from src.utils.logger import get_logger

from .keyboards import get_settings_keyboard

logger = get_logger(BOT_NAME)


class SettingsDispatcher(BaseHandler):
    """Dispatcher for settings command.

    Handles displaying the main settings menu and routing to specific handlers.
    """

    def __init__(self, services: ServiceContainer) -> None:
        """Initialize the settings dispatcher.

        :param services: Service container with dependencies
        :type services: ServiceContainer
        """
        super().__init__(services)
        self.command_name = f"/{COMMAND_SETTINGS}"

    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle /settings command - show user settings.

        :param update: The update object containing the settings command
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        return await self._wrap_with_registration(handler_method=self._handle_settings)(
            update=update,
            context=context,
        )

    async def _handle_settings(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Internal method to handle /settings command.

        :param update: The update object
        :type update: Update
        :param context: The context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        cmd_context = await self._extract_command_context(update)
        user_id = cmd_context.user_id
        profile = cmd_context.user_profile
        lang = cmd_context.language

        logger.info(f"{self.command_name}: [{user_id}]: Handling settings command")

        _, _, pgettext = use_locale(lang=lang)

        try:
            # Determine subscription type
            is_premium = (
                profile
                and profile.subscription
                and profile.subscription.subscription_type
                in [SubscriptionType.PREMIUM, SubscriptionType.TRIAL]
            )

            birth_date_value = (
                format_date(
                    profile.birth_date,
                    format="dd.MM.yyyy",
                    locale=normalize_babel_locale(lang),
                )
                if getattr(profile, "birth_date", None)
                else pgettext("not.set", "Not set")
            )
            language_name = get_localized_language_name(
                getattr(getattr(profile, "settings", None), "language", None),
                lang,
            )
            life_expectancy_val = (
                getattr(getattr(profile, "settings", None), "life_expectancy", None)
                or 80
            )

            template = pgettext(
                "settings.premium" if is_premium else "settings.basic",
                (
                    "⚙️ <b>Profile Settings (Premium Subscription)</b>\n\n"
                    "📅 <b>Birth date:</b> {birth_date}\n"
                    "🌍 <b>Language:</b> {language_name}\n"
                    "⏰ <b>Expected life expectancy:</b> {life_expectancy} years\n\n"
                    "Select what you want to change:"
                    if is_premium
                    else "⚙️ <b>Profile Settings (Basic Subscription)</b>\n\n"
                    "📅 <b>Birth date:</b> {birth_date}\n"
                    "🌍 <b>Language:</b> {language_name}\n"
                    "⏰ <b>Expected life expectancy:</b> {life_expectancy} years\n\n"
                    "Select what you want to change:"
                ),
            ).format(
                birth_date=birth_date_value,
                language_name=language_name,
                life_expectancy=format_decimal(
                    life_expectancy_val, locale=normalize_babel_locale(lang)
                ),
            )

            await self.send_message(
                update=update,
                message_text=template,
                reply_markup=get_settings_keyboard(pgettext),
            )
            return None

        except Exception as error:
            logger.error(
                f"{self.command_name}: [{user_id}]: Error in settings: {error}"
            )
            error_text = pgettext(
                "settings.error",
                "❌ An error occurred while updating settings.\n"
                "Please try again later or contact the administrator.",
            )
            await self.send_error_message(
                update=update, cmd_context=cmd_context, error_message=error_text
            )
            return None
