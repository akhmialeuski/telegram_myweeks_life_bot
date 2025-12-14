"""Settings command handler for user profile management.

This module contains the SettingsHandler class which handles the /settings command
and related callbacks. Uses FSM-based ConversationState for state management.
"""

from datetime import date
from typing import Optional

from babel.dates import format_date
from babel.numbers import format_decimal
from telegram import Update
from telegram.ext import ContextTypes

from src.i18n import get_localized_language_name, normalize_babel_locale, use_locale
from src.services.validation_service import (
    ERROR_DATE_IN_FUTURE,
    ERROR_DATE_TOO_OLD,
    ERROR_INVALID_DATE_FORMAT,
    ERROR_INVALID_NUMBER,
    ERROR_OUT_OF_RANGE,
    ValidationService,
)

from ....core.enums import SubscriptionType, SupportedLanguage
from ....core.life_calculator import LifeCalculatorEngine
from ....database.service import UserNotFoundError, UserSettingsUpdateError
from ....services.container import ServiceContainer
from ....utils.config import BOT_NAME
from ....utils.logger import get_logger
from ...constants import COMMAND_SETTINGS
from ...conversations.persistence import TelegramContextPersistence
from ...conversations.states import ConversationState
from ...scheduler import update_user_schedule
from ..base_handler import BaseHandler
from .keyboards import get_language_keyboard, get_settings_keyboard

# Initialize logger for this module
logger = get_logger(BOT_NAME)


class SettingsHandler(BaseHandler):
    """Handler for /settings command and related callbacks.

    This handler manages user profile settings including birth date,
    language preference, and life expectancy. It provides different
    interfaces based on subscription type.

    Uses FSM-based ConversationState for state management.

    Attributes:
        command_name: Name of the command this handler processes
    """

    def __init__(self, services: ServiceContainer) -> None:
        """Initialize the settings handler.

        Sets up the command name and initializes the base handler.

        :param services: Service container with all dependencies
        :type services: ServiceContainer
        """
        super().__init__(services)
        self.command_name = f"/{COMMAND_SETTINGS}"
        self._persistence = TelegramContextPersistence()
        self._validation_service = ValidationService()

    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle /settings command - show user settings.

        This command allows users to view and manage their profile settings.
        It provides a list of available settings and allows users to change them.

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
        """Internal method to handle /settings command with registration check.

        :param update: The update object containing the settings command
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        # Extract user information using the new helper method
        cmd_context = await self._extract_command_context(update)
        user = cmd_context.user
        user_id = cmd_context.user_id

        logger.info(f"{self.command_name}: [{user_id}]: Handling settings command")

        # Resolve language and profile
        profile = await self.services.user_service.get_user_profile(telegram_id=user_id)
        lang = (
            profile.settings.language
            if profile and profile.settings and profile.settings.language
            else (user.language_code or "en")
        )
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

        except Exception:
            error_text = pgettext(
                "settings.error",
                "❌ An error occurred while updating settings.\n"
                "Please try again later or contact the administrator.",
            )
            await self.send_error_message(
                update=update, cmd_context=cmd_context, error_message=error_text
            )
            return None

    async def handle_settings_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle settings selection callback from inline keyboard.

        This function processes the user's settings selection and shows
        appropriate interface for changing the selected setting.

        :param update: The update object containing the callback
        :type update: Update
        :param context: The context object for the callback execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        query = update.callback_query
        cmd_context = await self._extract_command_context(update)
        user = cmd_context.user
        user_id = cmd_context.user_id

        callback_data = query.data
        logger.info(
            f"{self.command_name}: [{user_id}]: Executed callback: {callback_data}"
        )

        # Resolve language
        profile = await self.services.user_service.get_user_profile(telegram_id=user_id)
        lang = (
            profile.settings.language
            if profile and profile.settings and profile.settings.language
            else (user.language_code or "en")
        )
        _, _, pgettext = use_locale(lang=lang)

        try:
            # Answer the callback query to remove loading state
            await query.answer()

            # Use pattern matching for different setting types
            match callback_data:
                case ConversationState.AWAITING_SETTINGS_BIRTH_DATE.value:
                    # Show birth date change interface
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
                    # Store state using FSM
                    await self._persistence.set_state(
                        user_id=user_id,
                        state=ConversationState.AWAITING_SETTINGS_BIRTH_DATE,
                        context=context,
                    )

                case ConversationState.AWAITING_SETTINGS_LANGUAGE.value:
                    message_text = pgettext(
                        "settings.change_language",
                        "🌍 Select your preferred language",
                    )
                    await self.edit_message(
                        query=query,
                        message_text=message_text,
                        reply_markup=get_language_keyboard(),
                    )

                case ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY.value:
                    # Show life expectancy change interface
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
                    # Store state using FSM
                    await self._persistence.set_state(
                        user_id=user_id,
                        state=ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY,
                        context=context,
                    )

                case _:
                    # Unknown setting type
                    logger.warning(
                        f"{self.command_name}: [{user_id}]: Unknown setting type: {callback_data}"
                    )

        except Exception:
            message_text = pgettext(
                "settings.error",
                "❌ An error occurred while updating settings.\n"
                "Please try again later or contact the administrator.",
            )
            await self.edit_message(
                query=query,
                message_text=message_text,
            )

    async def handle_language_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle language selection callback from inline keyboard.

        This function processes the user's language selection and updates
        the user's language preference.

        :param update: The update object containing the callback
        :type update: Update
        :param context: The context object for the callback execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        query = update.callback_query
        cmd_context = await self._extract_command_context(update)
        user_id = cmd_context.user_id

        callback_data = query.data
        logger.info(
            f"{self.command_name}: [{user_id}]: Executed language callback: {callback_data}"
        )

        # Resolve current language for error messages
        profile = await self.services.user_service.get_user_profile(telegram_id=user_id)
        user = cmd_context.user
        lang = (
            profile.settings.language
            if profile and profile.settings and profile.settings.language
            else (user.language_code or "en")
        )
        _, _, pgettext = use_locale(lang=lang)

        try:
            # Answer the callback query to remove loading state
            await query.answer()

            # Extract language code from callback data
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

            # Update user's language preference in database
            await self.services.user_service.update_user_settings(
                telegram_id=user_id, language=language_code
            )

            # Update user's notification schedule
            scheduler = context.bot_data.get("scheduler")
            if scheduler:
                await update_user_schedule(scheduler, user_id)
            else:
                logger.warning(f"No scheduler available for user {user_id}")

            # Show success message in the new language
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
                f"{self.command_name}: [{user_id}]: Changed language to {language_code}"
            )

        except (UserNotFoundError, UserSettingsUpdateError) as error:
            logger.error(
                f"{self.command_name}: [{user_id}]: Failed to update language: {error}"
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

    async def handle_settings_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle text input for settings changes.

        This function processes text input when user is changing settings
        like birth date or life expectancy. Uses FSM for state validation.

        :param update: The update object containing the text input
        :type update: Update
        :param context: The context object for the input processing
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        cmd_context = await self._extract_command_context(update)
        message_text = update.message.text
        user_id = cmd_context.user_id

        try:
            # Check current state using FSM
            current_state = await self._persistence.get_state(
                user_id=user_id,
                context=context,
            )
            logger.info(
                f"{self.command_name}: [{user_id}]: Text input received: "
                f"'{message_text[:20]}', state: '{current_state.value}'"
            )

            # Use pattern matching for different waiting states with validation
            match current_state:
                case ConversationState.AWAITING_SETTINGS_BIRTH_DATE:
                    if await self._persistence.is_state_valid(
                        user_id=user_id,
                        expected_state=ConversationState.AWAITING_SETTINGS_BIRTH_DATE,
                        context=context,
                    ):
                        logger.info(
                            f"{self.command_name}: [{user_id}]: Processing birth date input"
                        )
                        await self.handle_birth_date_input(
                            update=update,
                            context=context,
                            message_text=message_text,
                        )
                    else:
                        logger.warning(
                            f"{self.command_name}: [{user_id}]: "
                            "Invalid or expired birth date waiting state, ignoring input"
                        )
                        await self._persistence.clear_state(
                            user_id=user_id,
                            context=context,
                        )

                case ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY:
                    if await self._persistence.is_state_valid(
                        user_id=user_id,
                        expected_state=ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY,
                        context=context,
                    ):
                        logger.info(
                            f"{self.command_name}: [{user_id}]: "
                            "Processing life expectancy input"
                        )
                        await self.handle_life_expectancy_input(
                            update=update,
                            context=context,
                            message_text=message_text,
                        )
                    else:
                        logger.warning(
                            f"{self.command_name}: [{user_id}]: "
                            "Invalid or expired life expectancy waiting state, ignoring"
                        )
                        await self._persistence.clear_state(
                            user_id=user_id,
                            context=context,
                        )

                case _:
                    # Not waiting for settings input, ignore this message
                    logger.info(
                        f"{self.command_name}: [{user_id}]: "
                        "Not waiting for settings input, ignoring message"
                    )

        except Exception as error:
            logger.error(
                f"{self.command_name}: [{user_id}]: "
                f"Error in handle_settings_input: {error}"
            )
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=str(error),
            )

    async def handle_birth_date_input(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message_text: str,
    ) -> None:
        """Handle birth date input for settings change.

        :param update: The update object
        :type update: Update
        :param context: The context object
        :type context: ContextTypes.DEFAULT_TYPE
        :param message_text: User's input text
        :type message_text: str
        :returns: None
        """
        cmd_context = await self._extract_command_context(update)
        user = cmd_context.user
        user_id = cmd_context.user_id

        logger.info(
            f"{self.command_name}: [{user_id}]: "
            f"handle_birth_date_input called with text: '{message_text}'"
        )

        # Resolve language
        profile = await self.services.user_service.get_user_profile(telegram_id=user_id)
        lang = (
            profile.settings.language
            if profile and profile.settings and profile.settings.language
            else (user.language_code or "en")
        )
        _, _, pgettext = use_locale(lang=lang)

        try:
            # Validate using ValidationService
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

            # Update birth date in database
            logger.info(
                f"{self.command_name}: [{user_id}]: Updating birth date to {birth_date_value}"
            )
            await self.services.user_service.update_user_settings(
                telegram_id=user_id, birth_date=birth_date_value
            )

            # Get updated user profile after birth date change
            updated_user_profile = await self.services.user_service.get_user_profile(
                telegram_id=user_id
            )

            # Calculate new age with updated profile
            calculator = LifeCalculatorEngine(user=updated_user_profile)

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
                    new_age=calculator.calculate_age(),
                ),
            )

            # Clear waiting state
            await self._persistence.clear_state(user_id=user_id, context=context)
            logger.info(
                f"{self.command_name}: [{user_id}]: Updated birth date to {birth_date_value}"
            )

        except (UserNotFoundError, UserSettingsUpdateError) as error:
            logger.error(
                f"{self.command_name}: [{user_id}]: Failed to update birth date: {error}"
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
                f"{self.command_name}: [{user_id}]: "
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

    async def handle_life_expectancy_input(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        message_text: str,
    ) -> None:
        """Handle life expectancy input for settings change.

        :param update: The update object
        :type update: Update
        :param context: The context object
        :type context: ContextTypes.DEFAULT_TYPE
        :param message_text: User's input text
        :type message_text: str
        :returns: None
        """
        cmd_context = await self._extract_command_context(update)
        user = cmd_context.user
        user_id = cmd_context.user_id
        logger.info(
            f"{self.command_name}: [{user_id}]: "
            f"Handling life expectancy input: {message_text}"
        )

        # Resolve language
        profile = await self.services.user_service.get_user_profile(telegram_id=user_id)
        lang = (
            profile.settings.language
            if profile and profile.settings and profile.settings.language
            else (user.language_code or "en")
        )
        _, _, pgettext = use_locale(lang=lang)

        try:
            # Validate using ValidationService
            validation_result = self._validation_service.validate_life_expectancy(
                input_str=message_text
            )

            if not validation_result.is_valid:
                await self._handle_life_expectancy_validation_error(
                    update=update,
                    error_key=validation_result.error_key,
                    lang=lang,
                )
                return

            life_expectancy: int = validation_result.value

            # Update life expectancy in database
            await self.services.user_service.update_user_settings(
                telegram_id=user_id, life_expectancy=life_expectancy
            )

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

            # Clear waiting state
            await self._persistence.clear_state(user_id=user_id, context=context)
            logger.info(
                f"{self.command_name}: [{user_id}]: "
                f"Updated life expectancy to {life_expectancy}"
            )

        except (UserNotFoundError, UserSettingsUpdateError) as error:
            logger.error(
                f"{self.command_name}: [{user_id}]: "
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
            # Invalid number format
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
                        "birth_date.format_error",
                        "❌ Invalid date format!\n"
                        "Please enter date in DD.MM.YYYY format\n"
                        "For example: 15.03.1990",
                    ),
                )

    async def _handle_life_expectancy_validation_error(
        self,
        update: Update,
        error_key: str | None,
        lang: str,
    ) -> None:
        """Handle life expectancy validation error.

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
            case _ if error_key in (ERROR_INVALID_NUMBER, ERROR_OUT_OF_RANGE):
                await self.send_message(
                    update=update,
                    message_text=pgettext(
                        "settings.invalid_life_expectancy",
                        "❌ Invalid life expectancy.\n"
                        "Please enter a value between 50 and 120 years.",
                    ),
                )
            case _:
                await self.send_message(
                    update=update,
                    message_text=pgettext(
                        "settings.invalid_life_expectancy",
                        "❌ Invalid life expectancy.\n"
                        "Please enter a value between 50 and 120 years.",
                    ),
                )
