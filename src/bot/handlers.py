"""Command handlers for the Telegram bot.

This module contains all command handlers for the LifeWeeksBot Telegram bot.
Each handler is responsible for processing specific user commands and managing
the conversation flow. The module includes:

- Registration flow handlers (/start command)
- Life statistics handlers (/weeks command)
- Visualization handlers (/visualize command)
- Utility handlers (/help, /cancel commands)
- Decorators for common functionality

All handlers use exception-based error handling and localized message generation
for better user experience and maintainability.
"""

from datetime import date, datetime
from functools import wraps
from typing import Any, Callable

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from ..core.messages import (
    generate_message_birth_date_format_error,
    generate_message_birth_date_future_error,
    generate_message_birth_date_old_error,
    generate_message_cancel_error,
    generate_message_cancel_success,
    generate_message_help,
    generate_message_registration_error,
    generate_message_registration_success,
    generate_message_start_welcome_existing,
    generate_message_start_welcome_new,
    generate_message_visualize,
    generate_message_week,
)
from ..database.service import (
    UserAlreadyExistsError,
    UserDeletionError,
    UserRegistrationError,
    UserServiceError,
    user_service,
)
from ..utils.config import BOT_NAME, DEFAULT_LANGUAGE
from ..utils.localization import get_message
from ..utils.logger import get_logger
from ..visualization.grid import generate_visualization

logger = get_logger(BOT_NAME)

# Conversation states for managing user registration flow
WAITING_USER_INPUT = 1


def require_registration():
    """Decorator to check user registration and handle errors.

    This decorator provides a centralized way to verify that users
    have completed the registration process before allowing access
    to protected commands. It handles common error scenarios and
    provides consistent error messaging.

    The decorator:
    - Extracts user information from the update
    - Validates user registration status using the database service
    - Sends appropriate error messages for unregistered users
    - Catches and logs any exceptions that occur during command execution
    - Provides graceful error handling with user-friendly messages

    :returns: Decorated function that includes registration validation
    :rtype: Callable

    Example:
        >>> @require_registration()
        >>> async def protected_command(update, context):
        >>>     # This code only runs for registered users
        >>>     pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
            # Extract user information from the update
            user = update.effective_user
            user_id = user.id
            user_lang = user.language_code or DEFAULT_LANGUAGE

            try:
                # Validate that user has completed registration with birth date
                if not user_service.is_valid_user_profile(user_id):
                    await update.message.reply_text(
                        get_message("common", "not_registered", user_lang)
                    )
                    return

                # Execute the original command handler
                return await func(update, context)

            except Exception as error:  # pylint: disable=broad-exception-caught
                # Log the error for debugging and monitoring
                logger.error(f"Error in {func.__name__} command: {error}")
                # Send user-friendly error message
                await update.message.reply_text(
                    get_message("common", "error", user_lang)
                )

        return wrapper

    return decorator


async def command_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command - initiate user registration process.

    This command is the entry point for new users and handles the initial
    bot interaction. It checks if the user is already registered and either
    welcomes them back or initiates the registration process.

    The registration flow:
    1. Checks if user already has a valid profile with birth date
    2. If registered: sends welcome back message and ends conversation
    3. If not registered: sends welcome message and requests birth date
    4. Transitions to WAITING_USER_INPUT state for birth date collection

    :param update: The update object containing the user's message
    :type update: Update
    :param context: The context object for the command execution
    :type context: ContextTypes.DEFAULT_TYPE
    :returns: Conversation state (END if registered, WAITING_USER_INPUT if new)
    :rtype: int

    Example:
        User sends /start → Bot checks registration → Sends appropriate message
    """
    # Extract user information from the update
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot")

    # Check if user has already completed registration
    if user_service.is_valid_user_profile(user.id):
        # User is already registered - send welcome back message
        await update.message.reply_text(
            text=generate_message_start_welcome_existing(user_info=user),
            parse_mode="HTML",
        )
        return ConversationHandler.END

    # User needs to register - request birth date
    await update.message.reply_text(
        text=generate_message_start_welcome_new(user_info=user),
        parse_mode="HTML",
    )

    # Transition to waiting state for birth date input
    return WAITING_USER_INPUT


async def command_start_handle_birth_date(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle birth date input during user registration process.

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
    - Database errors: shows error message and ends conversation
    - User already exists: shows welcome message and ends conversation

    :param update: The update object containing the birth date input
    :type update: Update
    :param context: The context object for the command execution
    :type context: ContextTypes.DEFAULT_TYPE
    :returns: Conversation state (END if successful, WAITING_USER_INPUT if validation fails)
    :rtype: int

    Example:
        User sends "15.03.1990" → Bot validates → Creates profile → Shows success message
    """
    # Extract user information and birth date input
    user = update.effective_user
    birth_date_text = update.message.text.strip()

    try:
        # Parse birth date from user input (DD.MM.YYYY format)
        birth_date = datetime.strptime(birth_date_text, "%d.%m.%Y").date()

        # Validate that birth date is not in the future
        if birth_date > date.today():
            await update.message.reply_text(
                text=generate_message_birth_date_future_error(user_info=user),
                parse_mode="HTML",
            )
            return WAITING_USER_INPUT

        # Validate that birth date is not unreasonably old
        if birth_date.year < 1900:
            await update.message.reply_text(
                text=generate_message_birth_date_old_error(user_info=user),
                parse_mode="HTML",
            )
            return WAITING_USER_INPUT

        # Attempt to create user profile in the database
        try:
            user_service.create_user_with_settings(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                birth_date=birth_date,
            )

            # Send success message with calculated statistics
            await update.message.reply_text(
                text=generate_message_registration_success(
                    user_info=user,
                    birth_date=birth_date.strftime("%d.%m.%Y"),
                ),
                parse_mode="HTML",
            )

            logger.info(f"User {user.id} registered with birth date {birth_date}")
            return ConversationHandler.END

        except UserAlreadyExistsError as error:
            # Handle case where user somehow already exists
            await update.message.reply_text(
                text=generate_message_start_welcome_existing(user_info=user),
                parse_mode="HTML",
            )
            logger.info(
                f"User {user.id} already exists, showing welcome message: {error}"
            )
            return ConversationHandler.END

        except UserRegistrationError as error:
            # Handle database registration failures
            await update.message.reply_text(
                text=generate_message_registration_error(user_info=user),
                parse_mode="HTML",
            )
            logger.error(f"Failed to register user {user.id}: {error}")
            return ConversationHandler.END

        except UserServiceError as error:
            # Handle general service errors
            await update.message.reply_text(
                text=generate_message_registration_error(user_info=user),
                parse_mode="HTML",
            )
            logger.error(f"Service error during user {user.id} registration: {error}")
            return ConversationHandler.END

    except ValueError:
        # Handle invalid date format
        await update.message.reply_text(
            text=generate_message_birth_date_format_error(user_info=user),
            parse_mode="HTML",
        )
        return WAITING_USER_INPUT


@require_registration()
async def command_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel command - delete user profile and data.

    This command allows users to completely remove their profile and all
    associated data from the system. It's useful for users who want to
    start over or completely opt out of the service.

    The deletion process:
    1. Validates that user is registered (via decorator)
    2. Attempts to delete user profile and settings from database
    3. Provides feedback on success or failure
    4. Logs the operation for audit purposes

    Error handling:
    - UserDeletionError: Specific deletion failures
    - UserServiceError: General service errors
    - Both cases: Show error message to user

    :param update: The update object containing the cancel command
    :type update: Update
    :param context: The context object for the command execution
    :type context: ContextTypes.DEFAULT_TYPE
    :returns: Conversation state (always END)
    :rtype: int

    Example:
        User sends /cancel → Bot deletes profile → Shows confirmation message
    """
    # Extract user information
    user = update.effective_user
    user_id = user.id

    try:
        # Attempt to delete user profile and all associated data
        user_service.delete_user_profile(user_id)

        # Send success confirmation message
        await update.message.reply_text(
            text=generate_message_cancel_success(user_info=user),
            parse_mode="HTML",
        )
        logger.info(f"User {user_id} data deleted via /cancel command")

    except UserDeletionError as error:
        # Handle specific deletion failures
        await update.message.reply_text(
            text=generate_message_cancel_error(user_info=user),
            parse_mode="HTML",
        )
        logger.error(
            f"Failed to delete user {user_id} data via /cancel command: {error}"
        )

    except UserServiceError as error:
        # Handle general service errors
        await update.message.reply_text(
            text=generate_message_cancel_error(user_info=user),
            parse_mode="HTML",
        )
        logger.error(
            f"Service error during user {user_id} deletion via /cancel command: {error}"
        )

    # Always end conversation after cancel attempt
    return ConversationHandler.END


@require_registration()
async def command_weeks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /weeks command - display life statistics.

    This command provides users with detailed statistics about their life
    including age, weeks lived, remaining weeks, life percentage, and
    days until next birthday. It's the core functionality of the bot.

    The statistics calculation:
    1. Retrieves user profile from database
    2. Uses LifeCalculatorEngine to compute various metrics
    3. Formats statistics into a localized message
    4. Sends the formatted message to the user

    The statistics include:
    - Current age in years
    - Total weeks lived
    - Estimated remaining weeks (based on life expectancy)
    - Percentage of life lived
    - Days until next birthday

    :param update: The update object containing the weeks command
    :type update: Update
    :param context: The context object for the command execution
    :type context: ContextTypes.DEFAULT_TYPE
    :returns: None

    Example:
        User sends /weeks → Bot calculates statistics → Shows detailed life info
    """
    # Extract user information
    user = update.effective_user
    logger.info(f"Handling /weeks command from user {user.id}")

    # Generate and send life statistics message
    await update.message.reply_text(
        text=generate_message_week(user_info=user),
        parse_mode="HTML",
    )


@require_registration()
async def command_visualize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /visualize command - show visual life representation.

    This command creates and sends a visual grid representation of the user's
    life, showing weeks lived as filled cells and remaining weeks as empty cells.
    It provides both the visual image and a caption with key statistics.

    The visualization process:
    1. Retrieves user profile from database
    2. Generates visual grid using LifeCalculatorEngine
    3. Creates image with weeks lived highlighted
    4. Generates caption with key statistics
    5. Sends both image and caption to user

    The visual grid shows:
    - Each cell represents one week
    - Each row represents one year (52 weeks)
    - Green cells = weeks lived
    - Empty cells = weeks not yet lived
    - Years labeled on vertical axis
    - Weeks labeled on horizontal axis

    :param update: The update object containing the visualize command
    :type update: Update
    :param context: The context object for the command execution
    :type context: ContextTypes.DEFAULT_TYPE
    :returns: None

    Example:
        User sends /visualize → Bot generates grid image → Shows visual life representation
    """
    # Extract user information
    user = update.effective_user
    logger.info(f"Handling /visualize command from user {user.id}")

    # Generate and send visual representation with caption
    await update.message.reply_photo(
        photo=generate_visualization(user_info=user),
        caption=generate_message_visualize(user_info=user),
        parse_mode="HTML",
    )


async def command_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command - show bot usage information.

    This command provides users with information about available commands
    and how to use the bot. It's available to all users, including those
    who haven't completed registration.

    The help information includes:
    - List of available commands
    - Brief description of each command
    - Usage instructions
    - Contact information if needed

    :param update: The update object containing the help command
    :type update: Update
    :param context: The context object for the command execution
    :type context: ContextTypes.DEFAULT_TYPE
    :returns: None

    Example:
        User sends /help → Bot shows available commands and usage instructions
    """
    # Extract user information
    user = update.effective_user
    logger.info(f"Handling /help command from user {user.id}")

    # Generate and send help message
    await update.message.reply_text(
        text=generate_message_help(user_info=user),
        parse_mode="HTML",
    )
