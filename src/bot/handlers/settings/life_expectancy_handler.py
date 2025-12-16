"""Handler for life expectancy settings.

This module provides the LifeExpectancyHandler class which handles the
viewing and modification of the user's expected life expectancy.
"""

from typing import Any, Optional

from babel.numbers import format_decimal
from telegram import Update
from telegram.ext import ContextTypes

from src.bot.constants import COMMAND_SETTINGS
from src.bot.conversations.states import ConversationState
from src.core.exceptions import ValidationError as CoreValidationError
from src.database.service import UserNotFoundError, UserSettingsUpdateError
from src.events.domain_events import UserSettingsChangedEvent
from src.i18n import normalize_babel_locale, use_locale
from src.services.container import ServiceContainer
from src.services.validation_service import ValidationService
from src.utils.config import BOT_NAME
from src.utils.logger import get_logger

from ..base_handler import CommandContext
from .abstract_handler import AbstractSettingsHandler

logger = get_logger(BOT_NAME)


class LifeExpectancyHandler(AbstractSettingsHandler):
    """Handler for life expectancy settings.

    Manages the user interface and logic for changing the expected life expectancy.
    """

    def __init__(self, services: ServiceContainer) -> None:
        """Initialize the life expectancy handler.

        :param services: Service container with dependencies
        :type services: ServiceContainer
        """
        super().__init__(services)
        self.command_name = "settings_life_expectancy"
        self._validation_service = ValidationService()

    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle request to view/edit life expectancy.

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
        """Handle life expectancy selection callback.

        Shows the interface for entering a new life expectancy value.

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
            "settings.change_life_expectancy",
            "⏰ <b>Change Expected Life Expectancy</b>\n\n"
            "Current value: <b>{current_life_expectancy} years</b>\n\n"
            "Enter new value (from 50 to 120 years):",
        ).format(
            current_life_expectancy=format_decimal(
                getattr(
                    getattr(profile, "settings", None),
                    "life_expectancy",
                    80,
                ),
                locale=normalize_babel_locale(lang),
            )
        )

        await self.edit_message(
            query=query,
            message_text=message_text,
        )

        await self._set_waiting_state(
            user_id=user_id,
            state=ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY,
            context=context,
        )

    async def handle_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle text input for life expectancy.

        Validates the input and updates the user's life expectancy if valid.

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
            f"Handling life expectancy input: {message_text}"
        )

        # Verify state validity
        if not await self._is_valid_waiting_state(
            user_id=user_id,
            expected_state=ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY,
            context=context,
        ):
            logger.warning(
                f"{COMMAND_SETTINGS}: [{user_id}]: "
                "Invalid or expired life expectancy waiting state, ignoring"
            )
            await self._clear_waiting_state(user_id=user_id, context=context)
            return

        try:
            # Validate input
            life_expectancy = self._validation_service.validate_life_expectancy(
                input_str=message_text
            )

            await self._update_and_notify(
                cmd_context=cmd_context,
                life_expectancy=life_expectancy,
            )

            await self._send_update_success(
                update=update,
                life_expectancy=life_expectancy,
                lang=lang,
                pgettext=pgettext,
            )

            await self._clear_waiting_state(user_id=user_id, context=context)
            logger.info(
                f"{COMMAND_SETTINGS}: [{user_id}]: "
                f"Updated life expectancy to {life_expectancy}"
            )

        except CoreValidationError as error:
            await self._handle_validation_error(
                update=update,
                error_key=error.error_key,
                lang=lang,
            )
            return

            await self._clear_waiting_state(user_id=user_id, context=context)
            logger.info(
                f"{COMMAND_SETTINGS}: [{user_id}]: "
                f"Updated life expectancy to {life_expectancy}"
            )

        except (UserNotFoundError, UserSettingsUpdateError) as error:
            logger.error(
                f"{COMMAND_SETTINGS}: [{user_id}]: "
                f"Failed to update life expectancy: {error}"
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

        except Exception:
            # Invalid number format fallback
            error_message = pgettext(
                "settings.invalid_life_expectancy",
                "❌ Invalid life expectancy.\n"
                "Please enter a value between 50 and 120 years.",
            )
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=error_message,
            )

    async def _update_and_notify(
        self,
        cmd_context: CommandContext,
        life_expectancy: int,
    ) -> None:
        """Update life expectancy in database and publish event.

        :param cmd_context: Command context
        :type cmd_context: CommandContext
        :param life_expectancy: New life expectancy
        :type life_expectancy: int
        :returns: None
        """
        user_id = cmd_context.user_id

        # Update database
        await self.services.user_service.update_user_settings(
            telegram_id=user_id, life_expectancy=life_expectancy
        )

        # Publish event
        await self.services.event_bus.publish(
            UserSettingsChangedEvent(
                user_id=user_id,
                setting_name="life_expectancy",
                new_value=life_expectancy,
                old_value=getattr(
                    getattr(cmd_context.user_profile, "settings", None),
                    "life_expectancy",
                    None,
                ),
            )
        )

    async def _send_update_success(
        self,
        update: Update,
        life_expectancy: int,
        lang: str,
        pgettext: Any,
    ) -> None:
        """Send success message with updated statistics.

        :param update: Telegram update object
        :type update: Update
        :param life_expectancy: New life expectancy
        :type life_expectancy: int
        :param lang: Language code
        :type lang: str
        :param pgettext: Localization function
        :type pgettext: Any
        :returns: None
        """
        message_text_out = pgettext(
            "settings.life_expectancy_updated",
            "✅ <b>Expected life expectancy updated!</b>\n\n"
            "New value: <b>{new_life_expectancy} years</b>\n\n"
            "Use /weeks to see updated statistics",
        ).format(
            new_life_expectancy=format_decimal(
                life_expectancy, locale=normalize_babel_locale(lang)
            )
        )
        await self.send_message(
            update=update,
            message_text=message_text_out,
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
        # For now, we only have one generic error for range or format failing validation
        # But if we had specific keys like ERROR_OUT_OF_RANGE, we could handle them.
        # The validation service returns specific keys, let's use a generic message for now
        # or custom mapping if needed.
        # Assuming validation service returns a key we can default to:

        error_message = pgettext(
            "settings.invalid_life_expectancy",
            "❌ Invalid life expectancy.\n"
            "Please enter a value between 50 and 120 years.",
        )
        await self.send_message(
            update=update,
            message_text=error_message,
        )
