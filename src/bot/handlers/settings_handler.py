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
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

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
    get_user_language,
)
from ...database.models import SubscriptionType
from ...database.service import (
    UserNotFoundError,
    UserSettingsUpdateError,
    user_service,
)
from ...utils.config import (
    MAX_LIFE_EXPECTANCY,
    MIN_BIRTH_YEAR,
    MIN_LIFE_EXPECTANCY,
)
from ...utils.localization import LANGUAGES, get_localized_language_name, get_message
from ..constants import COMMAND_SETTINGS
from ..scheduler import update_user_schedule
from .base_handler import BaseHandler


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
        return await self._wrap_with_registration(self._handle_settings)(
            update, context
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
        # Extract user information
        user = update.effective_user
        self.log_command(user.id, self.command_name)
        self.logger.info(f"Handling /settings command from user {user.id}")

        try:
            # Get user profile with current subscription
            user_profile = user_service.get_user_profile(user.id)

            # Get user's language preference
            language = get_user_language(user, user_profile)

            if not user_profile or not user_profile.subscription:
                await update.message.reply_text(
                    get_message(
                        message_key="common",
                        sub_key="error",
                        language=language,
                    )
                )
                return

            current_subscription = user_profile.subscription.subscription_type

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

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                text=message_text, reply_markup=reply_markup, parse_mode="HTML"
            )

        except Exception as error:
            await self.handle_error(update, context, error)

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
        user = update.effective_user
        self.log_callback(user.id, query.data)

        try:
            # Answer the callback query to remove loading state
            await query.answer()

            # Extract setting type from callback data
            callback_data = query.data
            if not callback_data.startswith("settings_"):
                return

            setting_type = callback_data.replace("settings_", "")

            if setting_type == "birth_date":
                # Show birth date change interface
                message_text = generate_message_change_birth_date(user_info=user)
                await query.edit_message_text(
                    text=message_text,
                    parse_mode="HTML",
                )
                # Store state in context for handling user input
                context.user_data["waiting_for"] = "birth_date"

            elif setting_type == "language":
                # Show language selection keyboard
                message_text = generate_message_change_language(user_info=user)
                keyboard = [
                    [InlineKeyboardButton("🇷🇺 Русский", callback_data="language_ru")],
                    [InlineKeyboardButton("🇺🇸 English", callback_data="language_en")],
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
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    text=message_text,
                    reply_markup=reply_markup,
                    parse_mode="HTML",
                )

            elif setting_type == "life_expectancy":
                # Show life expectancy change interface
                message_text = generate_message_change_life_expectancy(user_info=user)
                await query.edit_message_text(
                    text=message_text,
                    parse_mode="HTML",
                )
                # Store state in context for handling user input
                context.user_data["waiting_for"] = "life_expectancy"

        except Exception as error:
            await self.handle_error(update, context, error)
            await query.edit_message_text(
                text=generate_message_settings_error(user_info=user),
                parse_mode="HTML",
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
        user = update.effective_user
        self.log_callback(user.id, query.data)

        try:
            # Answer the callback query to remove loading state
            await query.answer()

            # Extract language from callback data
            callback_data = query.data
            if not callback_data.startswith("language_"):
                return

            language_code = callback_data.replace("language_", "")

            # Validate language code
            if language_code not in LANGUAGES:
                await query.edit_message_text(
                    text=generate_message_settings_error(user_info=user),
                    parse_mode="HTML",
                )
                return

            # Get language name for display
            language_name = get_localized_language_name(language_code, language_code)

            # Update user's language preference in database
            user_service.update_user_settings(
                telegram_id=user.id, language=language_code
            )

            # Update user's notification schedule
            scheduler_success = update_user_schedule(user.id)
            if scheduler_success:
                self.logger.info(f"Updated notification schedule for user {user.id}")
            else:
                self.logger.warning(
                    f"Failed to update notification schedule for user {user.id}"
                )

            # Show success message
            success_message = generate_message_language_updated(
                user_info=user, new_language=language_name
            )
            await query.edit_message_text(
                text=success_message,
                parse_mode="HTML",
            )

            self.logger.info(f"User {user.id} changed language to {language_code}")

        except (UserNotFoundError, UserSettingsUpdateError) as error:
            self.logger.error(f"Failed to update language for user {user.id}: {error}")
            await query.edit_message_text(
                text=generate_message_settings_error(user_info=user),
                parse_mode="HTML",
            )

        except Exception as error:
            await self.handle_error(update, context, error)
            await query.edit_message_text(
                text=generate_message_settings_error(user_info=user),
                parse_mode="HTML",
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
        user = update.effective_user
        message_text = update.message.text

        try:
            # Check what we're waiting for
            waiting_for = context.user_data.get("waiting_for")

            if waiting_for == "birth_date":
                await self.handle_birth_date_input(update, context, message_text)
            elif waiting_for == "life_expectancy":
                await self.handle_life_expectancy_input(update, context, message_text)
            else:
                # Not waiting for settings input, route to unknown handler
                from .unknown_handler import UnknownHandler

                unknown_handler = UnknownHandler()
                await unknown_handler.handle(update, context)

        except Exception as error:
            await self.handle_error(update, context, error)
            await update.message.reply_text(
                text=generate_message_settings_error(user_info=user),
                parse_mode="HTML",
            )

    async def handle_birth_date_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str
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
        user = update.effective_user

        try:
            # Parse birth date from user input (DD.MM.YYYY format)
            birth_date = datetime.strptime(message_text, "%d.%m.%Y").date()

            # Validate that birth date is not in the future
            if birth_date > date.today():
                await update.message.reply_text(
                    text=generate_message_birth_date_future_error(user_info=user),
                    parse_mode="HTML",
                )
                return

            # Validate that birth date is not unreasonably old
            if birth_date.year < MIN_BIRTH_YEAR:
                await update.message.reply_text(
                    text=generate_message_birth_date_old_error(user_info=user),
                    parse_mode="HTML",
                )
                return

            # Update birth date in database
            user_service.update_user_settings(
                telegram_id=user.id, birth_date=birth_date
            )

            # Update user's notification schedule
            scheduler_success = update_user_schedule(user.id)
            if scheduler_success:
                self.logger.info(f"Updated notification schedule for user {user.id}")
            else:
                self.logger.warning(
                    f"Failed to update notification schedule for user {user.id}"
                )

            # Calculate new age
            user_profile = user_service.get_user_profile(user.id)
            if user_profile:
                calculator = LifeCalculatorEngine(user=user_profile)
                new_age = calculator.calculate_age()
            else:
                new_age = 0

            # Send success message
            success_message = generate_message_birth_date_updated(
                user_info=user, new_birth_date=birth_date, new_age=new_age
            )
            await update.message.reply_text(
                text=success_message,
                parse_mode="HTML",
            )

            # Clear waiting state
            context.user_data.pop("waiting_for", None)

            self.logger.info(f"User {user.id} updated birth date to {birth_date}")

        except (UserNotFoundError, UserSettingsUpdateError) as error:
            self.logger.error(
                f"Failed to update birth date for user {user.id}: {error}"
            )
            await update.message.reply_text(
                text=generate_message_settings_error(user_info=user),
                parse_mode="HTML",
            )

        except ValueError:
            # Invalid date format
            await update.message.reply_text(
                text=generate_message_birth_date_format_error(user_info=user),
                parse_mode="HTML",
            )

    async def handle_life_expectancy_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str
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
        user = update.effective_user

        try:
            # Parse life expectancy from user input
            life_expectancy = int(message_text)

            # Validate life expectancy range
            if (
                life_expectancy < MIN_LIFE_EXPECTANCY
                or life_expectancy > MAX_LIFE_EXPECTANCY
            ):
                await update.message.reply_text(
                    text=generate_message_invalid_life_expectancy(user_info=user),
                    parse_mode="HTML",
                )
                return

            # Update life expectancy in database
            user_service.update_user_settings(
                telegram_id=user.id, life_expectancy=life_expectancy
            )

            # Update user's notification schedule
            scheduler_success = update_user_schedule(user.id)
            if scheduler_success:
                self.logger.info(f"Updated notification schedule for user {user.id}")
            else:
                self.logger.warning(
                    f"Failed to update notification schedule for user {user.id}"
                )

            # Send success message
            success_message = generate_message_life_expectancy_updated(
                user_info=user, new_life_expectancy=life_expectancy
            )
            await update.message.reply_text(
                text=success_message,
                parse_mode="HTML",
            )

            # Clear waiting state
            context.user_data.pop("waiting_for", None)

            self.logger.info(
                f"User {user.id} updated life expectancy to {life_expectancy}"
            )

        except (UserNotFoundError, UserSettingsUpdateError) as error:
            self.logger.error(
                f"Failed to update life expectancy for user {user.id}: {error}"
            )
            await update.message.reply_text(
                text=generate_message_settings_error(user_info=user),
                parse_mode="HTML",
            )

        except ValueError:
            # Invalid number format
            await update.message.reply_text(
                text=generate_message_invalid_life_expectancy(user_info=user),
                parse_mode="HTML",
            )
