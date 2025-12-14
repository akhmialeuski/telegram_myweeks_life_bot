"""Start command handler for user registration.

This module contains the StartHandler class which handles the /start command
and the user registration flow. It manages the registration process using
the FSM-based ConversationState for state management.

The registration flow includes:
- Welcome message for new users
- Birth date collection and validation
- User profile creation
- Integration with notification scheduler
"""

from datetime import date

from babel.dates import format_date
from babel.numbers import format_decimal, format_percent
from telegram import Update
from telegram.ext import ContextTypes

from src.i18n import normalize_babel_locale, use_locale
from src.services.validation_service import (
    ERROR_DATE_IN_FUTURE,
    ERROR_DATE_TOO_OLD,
    ERROR_INVALID_DATE_FORMAT,
    ValidationService,
)

from ...core.enums import SupportedLanguage
from ...database.service import UserRegistrationError, UserServiceError
from ...services.container import ServiceContainer
from ...utils.config import BOT_NAME
from ...utils.logger import get_logger
from ..constants import COMMAND_START
from ..conversations.persistence import TelegramContextPersistence
from ..conversations.states import ConversationState
from ..scheduler import SchedulerOperationError, add_user_to_scheduler
from .base_handler import BaseHandler

# Initialize logger for this module
logger = get_logger(BOT_NAME)


class StartHandler(BaseHandler):
    """Handler for /start command and user registration process.

    This handler manages the initial bot interaction and user registration
    flow using ConversationState enum for state management.

    Attributes:
        command_name: Name of the command this handler processes
    """

    def __init__(self, services: ServiceContainer) -> None:
        """Initialize the start handler.

        Sets up the command name and initializes the base handler.

        :param services: Service container with all dependencies
        :type services: ServiceContainer
        """
        super().__init__(services)
        self.command_name = f"/{COMMAND_START}"
        self._persistence = TelegramContextPersistence()
        self._validation_service = ValidationService()

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command - initiate user registration process.

        This command is the entry point for new users and handles the initial
        bot interaction. It checks if the user is already registered and either
        welcomes them back or initiates the registration process.

        The registration flow:
        1. Checks if user already has a valid profile with birth date
        2. If registered: sends welcome back message
        3. If not registered: sends welcome message and requests birth date
        4. Sets waiting state using ConversationState enum

        :param update: The update object containing the user's message
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None

        Example:
            User sends /start → Bot checks registration → Sends appropriate message
        """
        # Extract user information using the new helper method
        cmd_context = await self._extract_command_context(update=update)
        user = cmd_context.user
        user_id = cmd_context.user_id

        logger.info(f"{self.command_name}: [{user_id}]: User started the bot")

        # Check if user has already completed registration
        if await self.services.user_service.is_valid_user_profile(telegram_id=user_id):
            # Fetch profile to get preferred language
            profile = await self.services.user_service.get_user_profile(
                telegram_id=user_id
            )
            _, _, pgettext = use_locale(
                lang=profile.settings.language or user.language_code
            )

            # User is already registered - send welcome back message
            await self.send_message(
                update=update,
                message_text=pgettext(
                    "start.welcome_existing",
                    "👋 Hello, %(first_name)s! Welcome back to LifeWeeksBot!\n\n"
                    "You are already registered and ready to track your life weeks.\n\n"
                    "Use /weeks to view your life weeks.\n"
                    "Use /help for help.",
                )
                % {"first_name": profile.first_name},
            )
            return

        # For new users, use Telegram language
        lang = user.language_code or SupportedLanguage.EN.value
        _, _, pgettext = use_locale(lang=lang)

        # User needs to register - request birth date
        await self.send_message(
            update=update,
            message_text=pgettext(
                "start.welcome_new",
                "👋 Hello, %(first_name)s! Welcome to LifeWeeksBot!\n\n"
                "This bot will help you track the weeks of your life.\n\n"
                "📅 Please enter your birth date in DD.MM.YYYY format\n"
                "For example: 15.03.1990",
            )
            % {"first_name": user.first_name},
        )

        # Set waiting state using FSM persistence
        await self._persistence.set_state(
            user_id=user_id,
            state=ConversationState.AWAITING_START_BIRTH_DATE,
            context=context,
        )

    async def handle_birth_date_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle birth date input during registration process.

        This handler processes the birth date input from users during the
        registration flow. It uses ValidationService for input validation
        and provides feedback to the user.

        :param update: The update object containing the birth date input
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        # Extract user information using the new helper method
        cmd_context = await self._extract_command_context(update=update)
        user = cmd_context.user
        user_id = cmd_context.user_id
        birth_date_text = update.message.text.strip()

        # For validation errors, use Telegram language since user not registered yet
        lang = user.language_code or SupportedLanguage.EN.value

        try:
            # Validate birth date using ValidationService
            validation_result = self._validation_service.validate_birth_date(
                input_str=birth_date_text
            )

            if not validation_result.is_valid:
                await self._handle_validation_error(
                    update=update,
                    error_key=validation_result.error_key,
                    lang=lang,
                )
                return

            birth_date: date = validation_result.value

            # Create user profile
            await self.services.user_service.create_user_profile(
                user_info=user,
                birth_date=birth_date,
            )

            # Add user to notification scheduler
            await self._add_user_to_scheduler(context=context, user_id=user_id)

            # Send success message with calculated statistics
            await self._send_registration_success_message(
                update=update,
                context=context,
                user_id=user_id,
                birth_date=birth_date,
                lang=lang,
            )

            # Clear waiting state
            await self._persistence.clear_state(user_id=user_id, context=context)

        except (UserRegistrationError, UserServiceError) as error:
            # Handle all database errors with a single error message
            logger.error(
                f"{self.command_name}: [{user_id}]: Registration error: {error}"
            )
            _, _, pgettext = use_locale(lang=lang)
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=pgettext(
                    "registration.error",
                    "❌ An error occurred during registration.\n"
                    "Try again or contact the administrator.",
                ),
            )
            # Clear waiting state on error
            await self._persistence.clear_state(user_id=user_id, context=context)

        except Exception as error:
            logger.error(
                f"{self.command_name}: [{user_id}]: Error in handle_birth_date_input: {error}"
            )
            # Fallback error handling
            _, _, pgettext = use_locale(lang=lang)
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=pgettext(
                    "registration.error",
                    "❌ An error occurred during registration.\n"
                    "Try again or contact the administrator.",
                ),
            )
            await self._persistence.clear_state(user_id=user_id, context=context)

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
                await self._send_date_format_error(update=update, lang=lang)
            case _:
                await self._send_date_format_error(update=update, lang=lang)

    async def _add_user_to_scheduler(
        self, context: ContextTypes.DEFAULT_TYPE, user_id: int
    ) -> None:
        """Add user to notification scheduler.

        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :param user_id: Telegram user ID
        :type user_id: int
        """
        try:
            scheduler = context.bot_data.get("scheduler")
            if scheduler:
                await add_user_to_scheduler(scheduler, user_id)
                logger.info(
                    f"{self.command_name}: [{user_id}]: User added to notification scheduler"
                )
            else:
                logger.warning(
                    f"{self.command_name}: [{user_id}]: No scheduler available"
                )
        except SchedulerOperationError as scheduler_error:
            logger.warning(
                f"{self.command_name}: [{user_id}]: Failed to add user to notification scheduler: {scheduler_error}"
            )

    async def _send_registration_success_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int,
        birth_date: date,
        lang: str,
    ) -> None:
        """Send registration success message with calculated statistics.

        :param update: The update object containing the birth date input
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :param user_id: Telegram user ID
        :type user_id: int
        :param birth_date: User's birth date
        :type birth_date: date
        :param lang: Language code for messages
        :type lang: str
        """
        # Fetch profile and compute statistics for success message
        profile = await self.services.user_service.get_user_profile(telegram_id=user_id)
        if not profile:
            raise UserServiceError("Failed to fetch newly created profile")

        # Update language from profile if set
        final_lang = (
            profile.settings.language
            if profile and profile.settings and profile.settings.language
            else lang
        )
        _, _, pgettext = use_locale(lang=final_lang)

        calc_engine = self.services.get_life_calculator()(user=profile)
        stats = calc_engine.get_life_statistics()

        # Send success message with calculated statistics
        await self.send_message(
            update=update,
            message_text=pgettext(
                "registration.success",
                "✅ Great! You have successfully registered!\n\n"
                "📅 Birth date: %(birth_date)s\n"
                "🎂 Age: %(age)s years\n"
                "📊 Weeks lived: %(weeks_lived)s\n"
                "⏳ Remaining weeks: %(remaining_weeks)s\n"
                "📈 Life progress: %(life_percentage)s\n\n"
                "Now you can use commands:\n"
                "• /weeks - show life weeks\n"
                "• /visualize - visualize weeks\n"
                "• /help - help",
            )
            % {
                "birth_date": format_date(
                    birth_date,
                    format="dd.MM.yyyy",
                    locale=normalize_babel_locale(final_lang),
                ),
                "age": format_decimal(
                    stats["age"], locale=normalize_babel_locale(final_lang)
                ),
                "weeks_lived": format_decimal(
                    stats["weeks_lived"],
                    locale=normalize_babel_locale(final_lang),
                    format="#,##0",
                ),
                "remaining_weeks": format_decimal(
                    stats["remaining_weeks"],
                    locale=normalize_babel_locale(final_lang),
                    format="#,##0",
                ),
                "life_percentage": format_percent(
                    stats["life_percentage"],
                    locale=normalize_babel_locale(final_lang),
                    format="#0.1%",
                ),
            },
        )

    async def _send_date_format_error(self, update: Update, lang: str) -> None:
        """Send date format error message.

        :param update: The update object containing the birth date input
        :type update: Update
        :param lang: Language code for error messages
        :type lang: str
        """
        _, _, pgettext = use_locale(lang=lang)

        await self.send_message(
            update=update,
            message_text=pgettext(
                "birth_date.format_error",
                "❌ Invalid date format!\n"
                "Please enter date in DD.MM.YYYY format\n"
                "For example: 15.03.1990",
            ),
        )
