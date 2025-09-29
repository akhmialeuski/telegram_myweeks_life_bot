"""Start command handler for user registration.

This module contains the StartHandler class which handles the /start command
and the user registration flow. It manages the registration process using
context.user_data for state management instead of ConversationHandler.

The registration flow includes:
- Welcome message for new users
- Birth date collection and validation
- User profile creation
- Integration with notification scheduler
"""

from datetime import date, datetime

from babel.dates import format_date
from babel.numbers import format_decimal, format_percent
from telegram import Update
from telegram.ext import ContextTypes

from src.i18n import normalize_babel_locale, use_locale

from ...core.enums import SupportedLanguage
from ...database.service import UserRegistrationError, UserServiceError
from ...services.container import ServiceContainer
from ...utils.config import BOT_NAME, MIN_BIRTH_YEAR
from ...utils.logger import get_logger
from ..constants import COMMAND_START
from ..scheduler import SchedulerOperationError, add_user_to_scheduler
from .base_handler import BaseHandler

# Initialize logger for this module
logger = get_logger(BOT_NAME)


class StartHandler(BaseHandler):
    """Handler for /start command and user registration process.

    This handler manages the initial bot interaction and user registration
    flow using context.user_data for state management instead of ConversationHandler.

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

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command - initiate user registration process.

        This command is the entry point for new users and handles the initial
        bot interaction. It checks if the user is already registered and either
        welcomes them back or initiates the registration process.

        The registration flow:
        1. Checks if user already has a valid profile with birth date
        2. If registered: sends welcome back message
        3. If not registered: sends welcome message and requests birth date
        4. Sets waiting state in context.user_data for birth date collection

        :param update: The update object containing the user's message
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None

        Example:
            User sends /start → Bot checks registration → Sends appropriate message
        """
        # Extract user information using the new helper method
        cmd_context = self._extract_command_context(update)
        user = cmd_context.user
        user_id = cmd_context.user_id

        logger.info(f"{self.command_name}: [{user_id}]: User started the bot")

        # Check if user has already completed registration
        if self.services.user_service.is_valid_user_profile(telegram_id=user_id):
            # Fetch profile to get preferred language
            profile = self.services.user_service.get_user_profile(telegram_id=user_id)
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

        # Set waiting state for birth date input
        context.user_data["waiting_for"] = "start_birth_date"

    async def handle_birth_date_input(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle birth date input during registration process.

        This handler processes the birth date input from users during the
        registration flow. It validates the input format and date range,
        creates the user profile, and provides feedback to the user.

        The validation process:
        1. Parses the birth date string (expected format: DD.MM.YYYY)
        2. Validates that the date is not in the future
        3. Validates that the date is not too old (before 1900)
        4. Attempts to create user profile in the database
        5. Handles various error scenarios with appropriate messages

        Error handling:
        - Invalid date format: requests re-entry
        - Future date: explains the error and requests re-entry
        - Too old date: explains the error and requests re-entry
        - Database errors: shows error message and clears waiting state
        - User already exists: shows welcome message and clears waiting state

        :param update: The update object containing the birth date input
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None

        Example:
            User sends "15.03.1990" → Bot validates → Creates profile → Shows success message
        """
        # Extract user information using the new helper method
        cmd_context = self._extract_command_context(update)
        user = cmd_context.user
        user_id = cmd_context.user_id
        birth_date_text = update.message.text.strip()

        # For validation errors, use Telegram language since user not registered yet
        lang = user.language_code or SupportedLanguage.EN.value
        _, _, pgettext = use_locale(lang=lang)

        try:
            # Parse birth date from user input (DD.MM.YYYY format)
            birth_date = datetime.strptime(birth_date_text, "%d.%m.%Y").date()

            # Validate that birth date is not in the future
            if birth_date > date.today():
                await self.send_message(
                    update=update,
                    message_text=pgettext(
                        "birth_date.future_error",
                        "❌ Birth date cannot be in the future!\n"
                        "Please enter a valid date in DD.MM.YYYY format",
                    ),
                )
                return

            # Validate that birth date is not unreasonably old
            if birth_date.year < MIN_BIRTH_YEAR:
                await self.send_message(
                    update=update,
                    message_text=pgettext(
                        "birth_date.old_error",
                        "❌ Birth date is too old!\n"
                        "Please enter a valid date in DD.MM.YYYY format",
                    ),
                )
                return

            # Attempt to create user profile in the database
            self.services.user_service.create_user_profile(
                user_info=user, birth_date=birth_date
            )

            # Add user to notification scheduler
            try:
                scheduler = context.bot_data.get("scheduler")
                if scheduler:
                    add_user_to_scheduler(scheduler, user_id)
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

            # Fetch profile and compute statistics for success message
            profile = self.services.user_service.get_user_profile(telegram_id=user_id)
            if not profile:
                raise UserServiceError("Failed to fetch newly created profile")

            # Update language from profile if set
            lang = (
                profile.settings.language
                if profile and profile.settings and profile.settings.language
                else lang
            )
            _, _, pgettext = use_locale(lang=lang)

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
                        locale=normalize_babel_locale(lang),
                    ),
                    "age": format_decimal(
                        stats["age"], locale=normalize_babel_locale(lang)
                    ),
                    "weeks_lived": format_decimal(
                        stats["weeks_lived"],
                        locale=normalize_babel_locale(lang),
                        format="#,##0",
                    ),
                    "remaining_weeks": format_decimal(
                        stats["remaining_weeks"],
                        locale=normalize_babel_locale(lang),
                        format="#,##0",
                    ),
                    "life_percentage": format_percent(
                        stats["life_percentage"],
                        locale=normalize_babel_locale(lang),
                        format="#0.1%",
                    ),
                },
            )

            # Clear waiting state
            context.user_data.pop("waiting_for", None)

        except ValueError:
            # Handle invalid date format
            await self.send_message(
                update=update,
                message_text=pgettext(
                    "birth_date.format_error",
                    "❌ Invalid date format!\n"
                    "Please enter date in DD.MM.YYYY format\n"
                    "For example: 15.03.1990",
                ),
            )

        except (UserRegistrationError, UserServiceError) as error:
            # Handle all database errors with a single error message
            logger.error(
                f"{self.command_name}: [{user_id}]: Registration error: {error}"
            )
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
            context.user_data.pop("waiting_for", None)

        except Exception as error:
            logger.error(
                f"{self.command_name}: [{user_id}]: Error in handle_birth_date_input: {error}"
            )
            # Fallback error handling
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=pgettext(
                    "registration.error",
                    "❌ An error occurred during registration.\n"
                    "Try again or contact the administrator.",
                ),
            )
            context.user_data.pop("waiting_for", None)
