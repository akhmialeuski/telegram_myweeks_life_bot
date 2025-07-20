"""Settings command handler for user profile management.

This module contains the SettingsHandler class which handles the /settings command
and related callbacks. It allows users to view and modify their profile settings
including birth date, language preference, and life expectancy.

The settings management includes:
- Display current settings based on subscription type
- Change birth date with validation
- Change language preference
- Change life expectancy with validation
- Integration with notification scheduler
"""

from datetime import date, datetime
from typing import Literal, Optional, TypedDict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from ...core.enums import SubscriptionType
from ...core.life_calculator import LifeCalculatorEngine
from ...core.messages import (
    generate_message_birth_date_format_error,
    generate_message_birth_date_future_error,
    generate_message_birth_date_old_error,
    generate_message_birth_date_updated,
    generate_message_change_birth_date,
    generate_message_change_language,
    generate_message_change_life_expectancy,
    generate_message_invalid_life_expectancy,
    generate_message_language_updated,
    generate_message_life_expectancy_updated,
    generate_message_settings_basic,
    generate_message_settings_error,
    generate_message_settings_premium,
    generate_settings_buttons,
)
from ...database.service import (
    UserNotFoundError,
    UserSettingsUpdateError,
    user_service,
)
from ...utils.config import (
    BOT_NAME,
    MAX_LIFE_EXPECTANCY,
    MIN_BIRTH_YEAR,
    MIN_LIFE_EXPECTANCY,
)
from ...utils.localization import LANGUAGES, get_localized_language_name
from ...utils.logger import get_logger
from ..constants import COMMAND_SETTINGS
from ..scheduler import update_user_schedule
from .base_handler import BaseHandler

# Initialize logger for this module
logger = get_logger(BOT_NAME)


class SettingsWaitingState(TypedDict, total=False):
    """Type definition for settings waiting state."""

    waiting_for: Optional[Literal["birth_date", "life_expectancy"]]


class SettingsHandler(BaseHandler):
    """Handler for /settings command and related callbacks.

    This handler manages user profile settings including birth date,
    language preference, and life expectancy. It provides different
    interfaces based on subscription type.

    Attributes:
        command_name: Name of the command this handler processes
    """

    def __init__(self) -> None:
        """Initialize the settings handler.

        Sets up the command name and initializes the base handler.
        """
        super().__init__()
        self.command_name = f"/{COMMAND_SETTINGS}"

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
        cmd_context = self._extract_command_context(update)
        user = cmd_context.user
        user_id = cmd_context.user_id
        user_profile = cmd_context.user_profile
        current_subscription = user_profile.subscription.subscription_type

        logger.info(f"{self.command_name}: [{user_id}]: Handling settings command")

        try:
            # Generate appropriate settings message based on subscription type
            if current_subscription in [
                SubscriptionType.PREMIUM,
                SubscriptionType.TRIAL,
            ]:
                message_text = generate_message_settings_premium(user_info=user)
            else:
                message_text = generate_message_settings_basic(user_info=user)

            # Create settings selection keyboard with localized buttons
            button_configs = generate_settings_buttons(user_info=user)
            keyboard = []
            for button_config in button_configs:
                for button in button_config:
                    keyboard.append(
                        [
                            InlineKeyboardButton(
                                button["text"], callback_data=button["callback_data"]
                            )
                        ]
                    )

            await self.send_message(
                update=update,
                message_text=message_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return None

        except Exception as error:
            await self.send_error_message(
                update=update, cmd_context=cmd_context, error_message=str(error)
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
        cmd_context = self._extract_command_context(update)
        user = cmd_context.user
        user_id = cmd_context.user_id

        callback_data = query.data
        logger.info(
            f"{self.command_name}: [{user_id}]: Executed callback: {callback_data}"
        )

        try:
            # Answer the callback query to remove loading state
            await query.answer()

            # Use pattern matching for different setting types (Python 3.10+)
            match callback_data:
                case "settings_birth_date":
                    # Show birth date change interface
                    await self.edit_message(
                        query=query,
                        message_text=generate_message_change_birth_date(user_info=user),
                    )
                    # Store state in context for handling user input
                    context.user_data["waiting_for"] = "settings_birth_date"

                case "settings_language":
                    # Show language selection keyboard
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                "🇷🇺 Русский", callback_data="language_ru"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "🇺🇸 English", callback_data="language_en"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "🇺🇦 Українська", callback_data="language_ua"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "🇧🇾 Беларуская", callback_data="language_by"
                            )
                        ],
                    ]
                    await self.edit_message(
                        query=query,
                        message_text=generate_message_change_language(user_info=user),
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )

                case "settings_life_expectancy":
                    # Show life expectancy change interface
                    await self.edit_message(
                        query=query,
                        message_text=generate_message_change_life_expectancy(
                            user_info=user
                        ),
                    )
                    # Store state in context for handling user input
                    context.user_data["waiting_for"] = "settings_life_expectancy"

                case _:
                    # Unknown setting type
                    logger.warning(
                        f"{self.command_name}: [{user_id}]: Unknown setting type: {callback_data}"
                    )

        except Exception:
            await self.edit_message(
                query=query,
                message_text=generate_message_settings_error(user_info=user),
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
        cmd_context = self._extract_command_context(update)
        user = cmd_context.user
        user_id = cmd_context.user_id

        callback_data = query.data
        logger.info(
            f"{self.command_name}: [{user_id}]: Executed language callback: {callback_data}"
        )

        try:
            # Answer the callback query to remove loading state
            await query.answer()

            # Extract language code from callback data
            language_code = callback_data.replace("language_", "")

            # Validate language code
            if language_code not in LANGUAGES:
                await self.edit_message(
                    query=query,
                    message_text=generate_message_settings_error(user_info=user),
                )
                return

            # Get language name for display
            language_name = get_localized_language_name(language_code, language_code)

            # Update user's language preference in database
            user_service.update_user_settings(
                telegram_id=user_id, language=language_code
            )

            # Update user's notification schedule
            update_user_schedule(user_id=user_id)

            # Show success message
            success_message = generate_message_language_updated(
                user_info=user, new_language=language_name
            )
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
            await self.edit_message(
                query=query,
                message_text=generate_message_settings_error(user_info=user),
            )

    async def handle_settings_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle text input for settings changes.

        This function processes text input when user is changing settings
        like birth date or life expectancy.

        :param update: The update object containing the text input
        :type update: Update
        :param context: The context object for the input processing
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        cmd_context = self._extract_command_context(update)
        message_text = update.message.text
        user_id = cmd_context.user_id

        try:
            # Check what we're waiting for
            waiting_for = context.user_data.get("waiting_for")
            logger.info(
                f"{self.command_name}: [{user_id}]: Text input received: '{message_text[:20]}', waiting_for: '{waiting_for}'"
            )

            # Use pattern matching for different waiting states
            match waiting_for:
                case "settings_birth_date":
                    logger.info(
                        f"{self.command_name}: [{user_id}]: Processing birth date input"
                    )
                    await self.handle_birth_date_input(
                        update=update,
                        context=context,
                        message_text=message_text,
                    )
                case "settings_life_expectancy":
                    logger.info(
                        f"{self.command_name}: [{user_id}]: Processing life expectancy input"
                    )
                    await self.handle_life_expectancy_input(
                        update=update,
                        context=context,
                        message_text=message_text,
                    )
                case _:
                    # Not waiting for settings input, ignore this message
                    logger.info(
                        f"{self.command_name}: [{user_id}]: Not waiting for settings input, ignoring message"
                    )

        except Exception as error:
            logger.error(
                f"{self.command_name}: [{user_id}]: Error in handle_settings_input: {error}"
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
        cmd_context = self._extract_command_context(update)
        user = cmd_context.user
        user_id = cmd_context.user_id

        logger.info(
            f"{self.command_name}: [{user_id}]: handle_birth_date_input called with text: '{message_text}'"
        )

        try:
            # Parse birth date from user input (DD.MM.YYYY format)
            birth_date = datetime.strptime(message_text, "%d.%m.%Y").date()

            # Validate that birth date is not in the future
            if birth_date > date.today():
                await self.send_message(
                    update=update,
                    message_text=generate_message_birth_date_future_error(
                        user_info=user
                    ),
                )
                return

            # Validate that birth date is not unreasonably old
            if birth_date.year < MIN_BIRTH_YEAR:
                await self.send_message(
                    update=update,
                    message_text=generate_message_birth_date_old_error(user_info=user),
                )
                return

            # Update birth date in database
            logger.info(
                f"{self.command_name}: [{user_id}]: Updating birth date to {birth_date}"
            )
            user_service.update_user_settings(
                telegram_id=user_id, birth_date=birth_date
            )

            # Get updated user profile after birth date change
            updated_user_profile = user_service.get_user_profile(user_id)

            # Calculate new age with updated profile
            calculator = LifeCalculatorEngine(user=updated_user_profile)

            # Send success message
            await self.send_message(
                update=update,
                message_text=generate_message_birth_date_updated(
                    user_info=user,
                    new_birth_date=birth_date,
                    new_age=calculator.calculate_age(),
                ),
            )

            # Clear waiting state
            context.user_data.pop("waiting_for", None)
            logger.info(
                f"{self.command_name}: [{user_id}]: Updated birth date to {birth_date}"
            )

        except (UserNotFoundError, UserSettingsUpdateError) as error:
            logger.error(
                f"{self.command_name}: [{user_id}]: Failed to update birth date: {error}"
            )
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=generate_message_settings_error(user_info=user),
            )

        except Exception as error:
            # Invalid date format
            logger.error(
                f"{self.command_name}: [{user_id}]: Exception in handle_birth_date_input: {error}"
            )
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=generate_message_birth_date_format_error(user_info=user),
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
        cmd_context = self._extract_command_context(update)
        user = cmd_context.user
        user_id = cmd_context.user_id
        logger.info(
            f"{self.command_name}: [{user_id}]: Handling life expectancy input: {message_text}"
        )

        try:
            # Parse life expectancy from user input
            life_expectancy = int(message_text)

            # Validate life expectancy range
            if (
                life_expectancy < MIN_LIFE_EXPECTANCY
                or life_expectancy > MAX_LIFE_EXPECTANCY
            ):
                await self.send_message(
                    update=update,
                    message_text=generate_message_invalid_life_expectancy(
                        user_info=user
                    ),
                )
                return

            # Update life expectancy in database
            user_service.update_user_settings(
                telegram_id=user_id, life_expectancy=life_expectancy
            )

            await self.send_message(
                update=update,
                message_text=generate_message_life_expectancy_updated(
                    user_info=user, new_life_expectancy=life_expectancy
                ),
            )

            # Clear waiting state
            context.user_data.pop("waiting_for", None)
            logger.info(
                f"{self.command_name}: [{user_id}]: Updated life expectancy to {life_expectancy}"
            )

        except (UserNotFoundError, UserSettingsUpdateError) as error:
            logger.error(
                f"{self.command_name}: [{user_id}]: Failed to update life expectancy: {error}"
            )
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=generate_message_settings_error(user_info=user),
            )

        except Exception:
            # Invalid number format
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=generate_message_invalid_life_expectancy(user_info=user),
            )
