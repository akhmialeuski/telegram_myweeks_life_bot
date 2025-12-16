"""Handler for birth date settings.

This module provides the BirthDateHandler class which handles the
viewing and modification of the user's birth date.
"""

from datetime import date
from typing import Optional

from babel.dates import format_date
from telegram import Update
from telegram.ext import ContextTypes

from src.bot.constants import COMMAND_SETTINGS
from src.bot.conversations.states import ConversationState
from src.core.life_calculator import calculate_life_statistics
from src.database.service import UserNotFoundError, UserSettingsUpdateError
from src.events.domain_events import UserSettingsChangedEvent
from src.i18n import normalize_babel_locale, use_locale
from src.services.container import ServiceContainer
from src.services.validation_service import (
    ERROR_DATE_IN_FUTURE,
    ERROR_DATE_TOO_OLD,
    ERROR_INVALID_DATE_FORMAT,
    ValidationService,
)
from src.utils.config import BOT_NAME
from src.utils.logger import get_logger

from .abstract_handler import AbstractSettingsHandler

logger = get_logger(BOT_NAME)


class BirthDateHandler(AbstractSettingsHandler):
    """Handler for birth date settings.

    Manages the user interface and logic for changing the birth date,
    including validation, state management, and event publishing.
    """

    def __init__(self, services: ServiceContainer) -> None:
        """Initialize the birth date handler.

        :param services: Service container with dependencies
        :type services: ServiceContainer
        """
        super().__init__(services)
        self.command_name = "settings_birth_date"
        self._validation_service = ValidationService()

    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle request to view/edit birth date.

        Typically triggered by a callback from the main settings menu.
        Since this is an inline action, we mainly handle it in handle_callback.
        For direct access, we would act similarly.

        :param update: The update object
        :type update: Update
        :param context: The context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        :rtype: Optional[int]
        """
        # For this specific refactor, this might be unused if we only use callbacks,
        # but we implement it to satisfy the contract and future extensibility.
        return None

    async def handle_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle birth date selection callback.

        Shows the interface for entering a new birth date.

        :param update: The update object
        :type update: Update
        :param context: The context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        query = update.callback_query
        cmd_context = await self._extract_command_context(update)
        user_id = cmd_context.user_id
        profile = cmd_context.user_profile
        lang = cmd_context.language
        _, _, pgettext = use_locale(lang=lang)

        await query.answer()

        message_text = pgettext(
            "settings.change_birth_date",
            "📅 <b>Change Birth Date</b>\n\n"
            "Current date: <b>{current_birth_date}</b>\n\n"
            "Enter new birth date in DD.MM.YYYY format\n"
            "For example: 15.03.1990\n\n"
            "Or press /cancel to cancel",
        ).format(
            current_birth_date=(
                format_date(
                    profile.birth_date,
                    format="dd.MM.yyyy",
                    locale=normalize_babel_locale(lang),
                )
                if getattr(profile, "birth_date", None)
                else pgettext("not.set", "Not set")
            )
        )

        await self.edit_message(
            query=query,
            message_text=message_text,
        )

        await self._set_waiting_state(
            user_id=user_id,
            state=ConversationState.AWAITING_SETTINGS_BIRTH_DATE,
            context=context,
        )

    async def handle_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle text input for birth date.

        Validates the input and updates the user's birth date if valid.

        :param update: The update object
        :type update: Update
        :param context: The context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        cmd_context = await self._extract_command_context(update)
        user_id = cmd_context.user_id
        message_text = update.message.text
        lang = cmd_context.language
        _, _, pgettext = use_locale(lang=lang)

        logger.info(
            f"{COMMAND_SETTINGS}: [{user_id}]: "
            f"Processing birth date input: '{message_text}'"
        )

        # Verify state validity
        if not await self._is_valid_waiting_state(
            user_id=user_id,
            expected_state=ConversationState.AWAITING_SETTINGS_BIRTH_DATE,
            context=context,
        ):
            logger.warning(
                f"{COMMAND_SETTINGS}: [{user_id}]: "
                "Invalid or expired birth date waiting state, ignoring input"
            )
            await self._clear_waiting_state(user_id=user_id, context=context)
            return

        try:
            # Validate input
            validation_result = self._validation_service.validate_birth_date(
                input_str=message_text
            )

            if not validation_result.is_valid:
                await self._handle_validation_error(
                    update=update,
                    error_key=validation_result.error_key,
                    lang=lang,
                )
                return

            birth_date_value: date = validation_result.value

            # Update database
            await self.services.user_service.update_user_settings(
                telegram_id=user_id, birth_date=birth_date_value
            )

            # Publish event
            await self.services.event_bus.publish(
                UserSettingsChangedEvent(
                    user_id=user_id,
                    setting_name="birth_date",
                    new_value=birth_date_value,
                    old_value=getattr(cmd_context.user_profile, "birth_date", None),
                )
            )

            # Get updated profile only if needed for calculation
            updated_profile = await self.services.user_service.get_user_profile(
                telegram_id=user_id
            )
            stats = calculate_life_statistics(
                birth_date=updated_profile.settings.birth_date,
                life_expectancy=updated_profile.settings.life_expectancy or 80,
            )

            # Send success message
            await self.send_message(
                update=update,
                message_text=pgettext(
                    "settings.birth_date_updated",
                    "✅ <b>Birth date successfully updated!</b>\n\n"
                    "New date: <b>{new_birth_date}</b>\n"
                    "New age: <b>{new_age} years</b>\n\n"
                    "Use /weeks to see updated statistics",
                ).format(
                    new_birth_date=format_date(
                        birth_date_value,
                        format="dd.MM.yyyy",
                        locale=normalize_babel_locale(lang),
                    ),
                    new_age=stats.age,
                ),
            )

            await self._clear_waiting_state(user_id=user_id, context=context)
            logger.info(
                f"{COMMAND_SETTINGS}: [{user_id}]: Updated birth date to {birth_date_value}"
            )

        except (UserNotFoundError, UserSettingsUpdateError) as error:
            logger.error(
                f"{COMMAND_SETTINGS}: [{user_id}]: Failed to update birth date: {error}"
            )
            error_message = pgettext(
                "settings.error",
                "❌ An error occurred while updating settings.\n"
                "Please try again later or contact the administrator.",
            )
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=error_message,
            )

        except Exception as error:
            logger.error(
                f"{COMMAND_SETTINGS}: [{user_id}]: "
                f"Exception in handle_birth_date_input: {error}"
            )
            error_message = pgettext(
                "birth_date.format_error",
                "❌ Invalid date format!\n"
                "Please enter date in DD.MM.YYYY format\n"
                "For example: 15.03.1990",
            )
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=error_message,
            )

    async def _handle_validation_error(
        self,
        update: Update,
        error_key: str | None,
        lang: str,
    ) -> None:
        """Handle validation error by sending appropriate error message.

        :param update: The update object
        :type update: Update
        :param error_key: Error key from validation service
        :type error_key: str | None
        :param lang: Language code for error messages
        :type lang: str
        :returns: None
        """
        _, _, pgettext = use_locale(lang=lang)

        match error_key:
            case _ if error_key == ERROR_DATE_IN_FUTURE:
                await self.send_message(
                    update=update,
                    message_text=pgettext(
                        "birth_date.future_error",
                        "❌ Birth date cannot be in the future!\n"
                        "Please enter a valid date in DD.MM.YYYY format",
                    ),
                )
            case _ if error_key == ERROR_DATE_TOO_OLD:
                await self.send_message(
                    update=update,
                    message_text=pgettext(
                        "birth_date.old_error",
                        "❌ Birth date is too old!\n"
                        "Please enter a valid date in DD.MM.YYYY format",
                    ),
                )
            case _ if error_key == ERROR_INVALID_DATE_FORMAT:
                await self.send_message(
                    update=update,
                    message_text=pgettext(
                        "birth_date.format_error",
                        "❌ Invalid date format!\n"
                        "Please enter date in DD.MM.YYYY format\n"
                        "For example: 15.03.1990",
                    ),
                )
            case _:
                await self.send_message(
                    update=update,
                    message_text=pgettext(
                        "birth_date.general_error",
                        "❌ Invalid birth date!\n"
                        "Please enter a valid date in DD.MM.YYYY format",
                    ),
                )
