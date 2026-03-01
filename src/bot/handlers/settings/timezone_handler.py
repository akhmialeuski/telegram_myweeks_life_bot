"""Handler for timezone settings.

This module provides the TimezoneHandler class which handles the
selection and updating of the user's notification timezone.
"""

import zoneinfo
from typing import Optional

from telegram import CallbackQuery, Message, Update
from telegram.ext import ContextTypes

from src.bot.constants import COMMAND_SETTINGS
from src.bot.conversations.states import ConversationState
from src.database.service import UserNotFoundError, UserSettingsUpdateError
from src.events.domain_events import UserSettingsChangedEvent
from src.i18n import use_locale
from src.services.container import ServiceContainer
from src.utils.config import BOT_NAME
from src.utils.logger import get_logger

from .abstract_handler import AbstractSettingsHandler
from .keyboards import get_timezone_keyboard

logger = get_logger(BOT_NAME)


class TimezoneHandler(AbstractSettingsHandler):
    """Handler for timezone settings.

    Manages the user interface and logic for changing the notification timezone.
    """

    def __init__(self, services: ServiceContainer) -> None:
        """Initialize the timezone handler.

        :param services: Service container with dependencies
        :type services: ServiceContainer
        """
        super().__init__(services)
        self.command_name = "settings_timezone"

    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle request to view/edit timezone.

        Typically triggered by a callback from the main settings menu.

        :param update: The update object
        :type update: Update
        :param context: The context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: New conversation state
        :rtype: Optional[int]
        """
        return None

    async def handle_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle timezone selection menu display callback.

        Shows the available popular timezones to the user.

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
            "settings.change_timezone",
            "🌍 Select your timezone from the list below, or choose 'Other' to enter manually:",
        )
        await self.edit_message(
            query=query,
            message_text=message_text,
            reply_markup=get_timezone_keyboard(pgettext),
        )

    async def handle_selection_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[str]:
        """Handle specific timezone option selection.

        Updates the user's timezone or prompts for manual input.

        :param update: The update object
        :type update: Update
        :param context: The context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: Next conversation state if applicable, else None
        :rtype: Optional[str]
        """
        query = update.callback_query
        cmd_context = await self._extract_command_context(update)
        user_id = cmd_context.user_id
        lang = cmd_context.language
        _, _, pgettext = use_locale(lang=lang)

        callback_data = query.data
        logger.info(
            f"{COMMAND_SETTINGS}: [{user_id}]: "
            f"Executed timezone callback: {callback_data}"
        )

        try:
            await query.answer()

            timezone_value = callback_data.replace("timezone_", "")

            if timezone_value == "other":
                message_text = pgettext(
                    "settings.enter_timezone_manual",
                    "✍️ Please enter your timezone in IANA format (e.g., Europe/London, America/New_York):",
                )
                await self.edit_message(
                    query=query,
                    message_text=message_text,
                )
                return ConversationState.AWAITING_SETTINGS_TIMEZONE.value

            return await self._update_timezone(
                timezone_value=timezone_value,
                user_id=user_id,
                lang=lang,
                query=query,
            )

        except Exception as error:
            logger.error(
                f"{COMMAND_SETTINGS}: [{user_id}]: Failed to handle timezone selection: {error}"
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
            return None

    async def handle_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle manual timezone input.

        :param update: The update object
        :type update: Update
        :param context: The context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: New conversation state
        :rtype: Optional[int]
        """
        cmd_context = await self._extract_command_context(update)
        user_id = cmd_context.user_id
        lang = cmd_context.language
        _, _, pgettext = use_locale(lang=lang)

        timezone_input = update.message.text.strip()

        logger.info(
            f"{COMMAND_SETTINGS}: [{user_id}]: Manual timezone input: '{timezone_input}'"
        )

        try:
            # Validate timezone
            zoneinfo.ZoneInfo(key=timezone_input)

            await self._update_timezone(
                timezone_value=timezone_input,
                user_id=user_id,
                lang=lang,
                query=None,
                message=update.message,
            )
            return ConversationState.IDLE.value

        except zoneinfo.ZoneInfoNotFoundError:
            logger.warning(
                f"{COMMAND_SETTINGS}: [{user_id}]: Invalid timezone input: '{timezone_input}'"
            )
            error_text = pgettext(
                "settings.invalid_timezone",
                "⚠️ Invalid timezone format. Please enter a valid IANA timezone identifier (e.g., Europe/London).",
            )
            await update.message.reply_text(error_text)
            return ConversationState.AWAITING_SETTINGS_TIMEZONE.value
        except Exception as error:
            logger.error(
                f"{COMMAND_SETTINGS}: [{user_id}]: Error in manual timezone input: {error}"
            )
            error_msg = pgettext(
                "settings.error",
                "❌ An error occurred while updating settings.\n"
                "Please try again later or contact the administrator.",
            )
            await update.message.reply_text(error_msg)
            return ConversationState.IDLE.value

    async def _update_timezone(
        self,
        timezone_value: str,
        user_id: int,
        lang: str,
        query: Optional[CallbackQuery] = None,
        message: Optional[Message] = None,
    ) -> Optional[str]:
        """Update the timezone in the database and notify the user.

        :param timezone_value: The new timezone value
        :type timezone_value: str
        :param user_id: User's Telegram ID
        :type user_id: int
        :param lang: User's language code
        :type lang: str
        :param query: Optional callback query for editing message
        :type query: Any
        :param message: Optional message for replying
        :type message: Any
        :returns: Next conversation state if applicable, else None
        :rtype: Optional[str]
        """
        _, _, pgettext = use_locale(lang=lang)

        try:
            # Get old timezone for event
            profile = await self.services.user_service.get_user_profile(
                telegram_id=user_id
            )
            old_timezone = getattr(profile.settings, "timezone", None)

            # Update database
            await self.services.user_service.update_user_settings(
                telegram_id=user_id, timezone=timezone_value
            )

            # Publish event
            await self.services.event_bus.publish(
                UserSettingsChangedEvent(
                    user_id=user_id,
                    setting_name="timezone",
                    new_value=timezone_value,
                    old_value=old_timezone,
                )
            )

            success_message = pgettext(
                "settings.timezone_updated",
                "✅ <b>Timezone successfully changed!</b>\n\n"
                "New timezone: <b>{new_timezone}</b>\n\n"
                "Your notifications will now be sent according to this timezone.",
            ).format(new_timezone=timezone_value)

            if query:
                await self.edit_message(
                    query=query,
                    message_text=success_message,
                )
            elif message:
                await message.reply_text(success_message, parse_mode="HTML")

            logger.info(
                f"{COMMAND_SETTINGS}: [{user_id}]: Changed timezone to {timezone_value}"
            )
            return None

        except (UserNotFoundError, UserSettingsUpdateError) as error:
            logger.error(
                f"{COMMAND_SETTINGS}: [{user_id}]: Failed to update timezone: {error}"
            )
            error_text = pgettext(
                "settings.error",
                "❌ An error occurred while updating settings.\n"
                "Please try again later or contact the administrator.",
            )

            if query:
                await self.edit_message(
                    query=query,
                    message_text=error_text,
                )
            elif message:
                await message.reply_text(error_text)

            return None
