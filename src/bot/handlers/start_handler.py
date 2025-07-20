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

from telegram import Update
from telegram.ext import ContextTypes

from ...core.messages import (
    generate_message_birth_date_format_error,
    generate_message_birth_date_future_error,
    generate_message_birth_date_old_error,
    generate_message_registration_error,
    generate_message_start_welcome_existing,
    generate_message_start_welcome_new,
)
from ...database.service import (
    UserRegistrationError,
    UserServiceError,
    user_service,
)
from ...utils.config import BOT_NAME, MIN_BIRTH_YEAR
from ...utils.logger import get_logger
from ..constants import COMMAND_START
from ..scheduler import add_user_to_scheduler
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

    def __init__(self) -> None:
        """Initialize the start handler.

        Sets up the command name and initializes the base handler.
        """
        super().__init__()
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
        if user_service.is_valid_user_profile(user_id):
            # User is already registered - send welcome back message
            await self.send_message(
                update=update,
                message_text=generate_message_start_welcome_existing(user_info=user),
            )
            return

        # User needs to register - request birth date
        await self.send_message(
            update=update,
            message_text=generate_message_start_welcome_new(user_info=user),
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

        try:
            # Parse birth date from user input (DD.MM.YYYY format)
            birth_date = datetime.strptime(birth_date_text, "%d.%m.%Y").date()

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

            # Attempt to create user profile in the database
            user_service.create_user_profile(user_info=user, birth_date=birth_date)

            # Add user to notification scheduler
            scheduler_success = add_user_to_scheduler(user_id)
            if scheduler_success:
                logger.info(
                    f"{self.command_name}: [{user_id}]: User added to notification scheduler"
                )
            else:
                logger.warning(
                    f"{self.command_name}: [{user_id}]: Failed to add user to notification scheduler"
                )

            # Send success message with calculated statistics
            await self.send_message(
                update=update,
                message_text=generate_message_start_welcome_existing(user_info=user),
            )

            # Clear waiting state
            context.user_data.pop("waiting_for", None)

        except (UserRegistrationError, UserServiceError) as error:
            # Handle all database errors with a single error message
            logger.error(
                f"{self.command_name}: [{user_id}]: Registration error: {error}"
            )
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=generate_message_registration_error(user_info=user),
            )
            # Clear waiting state on error
            context.user_data.pop("waiting_for", None)

        except Exception as error:
            # Handle invalid date format
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=generate_message_birth_date_format_error(user_info=user),
            )
            logger.error(
                f"{self.command_name}: [{user_id}]: Error in handle_birth_date_input: {error}"
            )
