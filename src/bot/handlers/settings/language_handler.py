"""Handler for language settings.

This module provides the LanguageHandler class which handles the
selection and updating of the user's interface language.
"""

from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from src.bot.constants import COMMAND_SETTINGS
from src.database.service import UserNotFoundError, UserSettingsUpdateError
from src.enums import SupportedLanguage
from src.events.domain_events import UserSettingsChangedEvent
from src.i18n import use_locale
from src.services.container import ServiceContainer
from src.utils.config import BOT_NAME
from src.utils.logger import get_logger

from .abstract_handler import AbstractSettingsHandler
from .keyboards import get_language_keyboard

logger = get_logger(BOT_NAME)


class LanguageHandler(AbstractSettingsHandler):
    """Handler for language settings.

    Manages the user interface and logic for changing the interface language.
    """

    def __init__(self, services: ServiceContainer) -> None:
        """Initialize the language handler.

        :param services: Service container with dependencies
        :type services: ServiceContainer
        """
        super().__init__(services)
        self.command_name = "settings_language"

    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle request to view/edit language.

        Typically triggered by a callback from the main settings menu.

        :param update: The update object
        :type update: Update
        :param context: The context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        :rtype: Optional[int]
        """
        return None

    async def handle_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle language selection menu display callback.

        Shows the available languages to the user.

        :param update: The update object
        :type update: Update
        :param context: The context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        query = update.callback_query
        cmd_context = await self._extract_command_context(update)
        lang = cmd_context.language
        _, _, pgettext = use_locale(lang=lang)

        await query.answer()

        message_text = pgettext(
            "settings.change_language",
            "🌍 Select your preferred language",
        )
        await self.edit_message(
            query=query,
            message_text=message_text,
            reply_markup=get_language_keyboard(),
        )

        # We don't necessarily need a waiting state for inline buttons,
        # but we can set one if we want to track context, or use IDLE.
        # Original code used AWAITING_SETTINGS_LANGUAGE but only for display.
        # The actual selection is a separate callback pattern.

    async def handle_selection_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle specific language option selection.

        Updates the user's language preference.

        :param update: The update object
        :type update: Update
        :param context: The context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        query = update.callback_query
        cmd_context = await self._extract_command_context(update)
        user_id = cmd_context.user_id
        lang = cmd_context.language
        _, _, pgettext = use_locale(lang=lang)

        callback_data = query.data
        logger.info(
            f"{COMMAND_SETTINGS}: [{user_id}]: "
            f"Executed language callback: {callback_data}"
        )

        try:
            await query.answer()

            # Extract language code
            language_code = callback_data.replace("language_", "")

            # Validate language code
            if language_code not in [e.value for e in SupportedLanguage]:
                error_text = pgettext(
                    "settings.error",
                    "❌ An error occurred while updating settings.\n"
                    "Please try again later or contact the administrator.",
                )
                await self.edit_message(
                    query=query,
                    message_text=error_text,
                )
                return

            # Update database
            await self.services.user_service.update_user_settings(
                telegram_id=user_id, language=language_code
            )

            # Publish event
            await self.services.event_bus.publish(
                UserSettingsChangedEvent(
                    user_id=user_id,
                    setting_name="language",
                    new_value=language_code,
                    old_value=lang,
                )
            )

            # Show success message in new language
            _, _, pgettext = use_locale(lang=language_code)

            success_message = pgettext(
                "settings.language_updated",
                "✅ <b>Language successfully changed!</b>\n\n"
                "New language: <b>{new_language}</b>\n\n"
                "All bot messages will now be in the selected language",
            ).format(new_language=language_code)

            await self.edit_message(
                query=query,
                message_text=success_message,
            )

            logger.info(
                f"{COMMAND_SETTINGS}: [{user_id}]: Changed language to {language_code}"
            )

        except (UserNotFoundError, UserSettingsUpdateError) as error:
            logger.error(
                f"{COMMAND_SETTINGS}: [{user_id}]: Failed to update language: {error}"
            )
            error_text = pgettext(
                "settings.error",
                "❌ An error occurred while updating settings.\n"
                "Please try again later or contact the administrator.",
            )
            await self.edit_message(
                query=query,
                message_text=error_text,
            )
