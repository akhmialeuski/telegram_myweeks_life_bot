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

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from ..core.messages import (
    generate_message_birth_date_format_error,
    generate_message_birth_date_future_error,
    generate_message_birth_date_old_error,
    generate_message_birth_date_updated,
    generate_message_cancel_error,
    generate_message_cancel_success,
    generate_message_change_birth_date,
    generate_message_change_language,
    generate_message_change_life_expectancy,
    generate_message_help,
    generate_message_invalid_life_expectancy,
    generate_message_language_updated,
    generate_message_life_expectancy_updated,
    generate_message_registration_error,
    generate_message_settings_basic,
    generate_message_settings_error,
    generate_message_settings_premium,
    generate_message_start_welcome_existing,
    generate_message_start_welcome_new,
    generate_message_subscription_already_active,
    generate_message_subscription_change_error,
    generate_message_subscription_change_failed,
    generate_message_subscription_change_success,
    generate_message_subscription_current,
    generate_message_subscription_invalid_type,
    generate_message_subscription_profile_error,
    generate_message_unknown_command,
    generate_message_visualize,
    generate_message_week,
    generate_settings_buttons,
    get_user_language,
)
from ..database.models import SubscriptionType
from ..database.service import (
    UserDeletionError,
    UserNotFoundError,
    UserRegistrationError,
    UserServiceError,
    UserSettingsUpdateError,
    user_service,
)
from ..utils.config import (
    BOT_NAME,
    MAX_LIFE_EXPECTANCY,
    MIN_BIRTH_YEAR,
    MIN_LIFE_EXPECTANCY,
)
from ..utils.localization import LANGUAGES, get_localized_language_name, get_message
from ..utils.logger import get_logger
from ..visualization.grid import generate_visualization
from .scheduler import (
    add_user_to_scheduler,
    remove_user_from_scheduler,
    update_user_schedule,
)

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

            try:
                # Validate that user has completed registration with birth date
                if not user_service.is_valid_user_profile(user_id):
                    # Get user's language preference
                    user_lang = get_user_language(user)

                    await update.message.reply_text(
                        get_message(
                            message_key="common",
                            sub_key="not_registered",
                            language=user_lang,
                        )
                    )
                    return

                # Execute the original command handler
                return await func(update, context)

            except Exception as error:  # pylint: disable=broad-exception-caught
                # Log the error for debugging and monitoring
                logger.error(f"Error in {func.__name__} command: {error}")

                # Get user's language preference
                user_lang = get_user_language(user)

                # Send user-friendly error message
                await update.message.reply_text(
                    get_message(
                        message_key="common",
                        sub_key="error",
                        language=user_lang,
                    )
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
        if birth_date.year < MIN_BIRTH_YEAR:
            await update.message.reply_text(
                text=generate_message_birth_date_old_error(user_info=user),
                parse_mode="HTML",
            )
            return WAITING_USER_INPUT

        # Attempt to create user profile in the database
        user_service.create_user_profile(user_info=user, birth_date=birth_date)

        # Add user to notification scheduler
        scheduler_success = add_user_to_scheduler(user.id)
        if scheduler_success:
            logger.info(f"User {user.id} added to notification scheduler")
        else:
            logger.warning(f"Failed to add user {user.id} to notification scheduler")

        # Send success message with calculated statistics
        await update.message.reply_text(
            text=generate_message_start_welcome_existing(user_info=user),
            parse_mode="HTML",
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
    logger.info(f"Handling /cancel command from user {user_id}")

    try:
        # First remove user from notification scheduler
        scheduler_success = remove_user_from_scheduler(user_id)
        if scheduler_success:
            logger.info(f"User {user_id} removed from notification scheduler")
        else:
            logger.warning(
                f"Failed to remove user {user_id} from notification scheduler"
            )

        # Then attempt to delete user profile and all associated data
        user_lang = get_user_language(user)
        user_service.delete_user_profile(user_id)

        # Send success confirmation message
        await update.message.reply_text(
            text=generate_message_cancel_success(user_info=user, language=user_lang),
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


@require_registration()
async def command_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settings command - show user settings.

    This command allows users to view and manage their profile settings.
    It provides a list of available settings and allows users to change them.
    """
    # Extract user information
    user = update.effective_user
    logger.info(f"Handling /settings command from user {user.id}")

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
        if current_subscription in [SubscriptionType.PREMIUM, SubscriptionType.TRIAL]:
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
        logger.error(f"Error in settings command: {error}")
        await update.message.reply_text(
            get_message(
                message_key="common",
                sub_key="error",
                language=language,
            )
        )


@require_registration()
async def command_subscription(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /subscription command - show user subscription.

    This command allows users to view and manage their subscription.
    It provides a list of available subscriptions and allows users to change them.
    """
    user = update.effective_user
    language = None

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

        # Create subscription selection keyboard
        keyboard = []
        for subscription_type in SubscriptionType:
            # Add checkmark for current subscription
            text = (
                f"{'✅ ' if subscription_type == current_subscription else ''}"
                f"{subscription_type.value.title()}"
            )
            callback_data = f"subscription_{subscription_type.value}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Generate message using messages module
        message_text = generate_message_subscription_current(user_info=user)

        await update.message.reply_text(
            text=message_text, reply_markup=reply_markup, parse_mode="HTML"
        )

    except Exception as error:
        logger.error(f"Error in subscription command: {error}")
        # Use default language if language is not set
        fallback_language = language or get_user_language(user, None)
        await update.message.reply_text(
            get_message(
                message_key="common",
                sub_key="error",
                language=fallback_language,
            )
        )


async def command_subscription_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle subscription selection callback from inline keyboard.

    This function processes the user's subscription selection and updates
    the database accordingly. It provides feedback about the change.
    """
    query = update.callback_query
    user = update.effective_user

    try:
        # Answer the callback query to remove loading state
        await query.answer()

        # Extract subscription type from callback data
        callback_data = query.data
        if not callback_data.startswith("subscription_"):
            return

        subscription_value = callback_data.replace("subscription_", "")

        # Validate subscription type
        try:
            new_subscription_type = SubscriptionType(subscription_value)
        except ValueError:
            await query.edit_message_text(
                text=generate_message_subscription_invalid_type(user_info=user),
                parse_mode="HTML",
            )
            return

        # Get current user profile
        user_profile = user_service.get_user_profile(user.id)
        if not user_profile or not user_profile.subscription:
            await query.edit_message_text(
                text=generate_message_subscription_profile_error(user_info=user),
                parse_mode="HTML",
            )
            return

        current_subscription = user_profile.subscription.subscription_type

        # Check if subscription actually changed
        if current_subscription == new_subscription_type:
            await query.edit_message_text(
                text=generate_message_subscription_already_active(
                    user_info=user, subscription_type=new_subscription_type.value
                ),
                parse_mode="HTML",
            )
            return

        # Update subscription in database
        success = user_service.update_user_subscription(user.id, new_subscription_type)

        if success:
            success_message = generate_message_subscription_change_success(
                user_info=user, subscription_type=new_subscription_type.value
            )

            await query.edit_message_text(text=success_message, parse_mode="HTML")

            logger.info(
                f"User {user.id} changed subscription from {current_subscription} to {new_subscription_type}"
            )
        else:
            await query.edit_message_text(
                text=generate_message_subscription_change_failed(user_info=user),
                parse_mode="HTML",
            )

    except Exception as error:
        logger.error(f"Error in subscription callback handler: {error}")
        await query.edit_message_text(
            text=generate_message_subscription_change_error(user_info=user),
            parse_mode="HTML",
        )


async def command_settings_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle settings selection callback from inline keyboard.

    This function processes the user's settings selection and shows
    appropriate interface for changing the selected setting.
    """
    query = update.callback_query
    user = update.effective_user

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
                [InlineKeyboardButton("🇺🇦 Українська", callback_data="language_ua")],
                [InlineKeyboardButton("🇧🇾 Беларуская", callback_data="language_by")],
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
        logger.error(f"Error in settings callback handler: {error}")
        await query.edit_message_text(
            text=generate_message_settings_error(user_info=user),
            parse_mode="HTML",
        )


async def command_language_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle language selection callback from inline keyboard.

    This function processes the user's language selection and updates
    the user's language preference.
    """
    query = update.callback_query
    user = update.effective_user

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
        user_service.update_user_settings(telegram_id=user.id, language=language_code)

        # Update user's notification schedule
        scheduler_success = update_user_schedule(user.id)
        if scheduler_success:
            logger.info(f"Updated notification schedule for user {user.id}")
        else:
            logger.warning(f"Failed to update notification schedule for user {user.id}")

        # Show success message
        success_message = generate_message_language_updated(
            user_info=user, new_language=language_name
        )
        await query.edit_message_text(
            text=success_message,
            parse_mode="HTML",
        )

        logger.info(f"User {user.id} changed language to {language_code}")

    except (UserNotFoundError, UserSettingsUpdateError) as error:
        logger.error(f"Failed to update language for user {user.id}: {error}")
        await query.edit_message_text(
            text=generate_message_settings_error(user_info=user),
            parse_mode="HTML",
        )

    except Exception as error:
        logger.error(f"Error in language callback handler: {error}")
        await query.edit_message_text(
            text=generate_message_settings_error(user_info=user),
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


async def handle_settings_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle text input for settings changes.

    This function processes text input when user is changing settings
    like birth date or life expectancy.
    """
    user = update.effective_user
    message_text = update.message.text

    try:
        # Check what we're waiting for
        waiting_for = context.user_data.get("waiting_for")

        if waiting_for == "birth_date":
            await handle_birth_date_input(update, context, message_text)
        elif waiting_for == "life_expectancy":
            await handle_life_expectancy_input(update, context, message_text)
        else:
            # Not waiting for settings input, let unknown message handler deal with it
            await handle_unknown_message(update, context)

    except Exception as error:
        logger.error(f"Error in settings input handler: {error}")

        await update.message.reply_text(
            text=generate_message_settings_error(user_info=user),
            parse_mode="HTML",
        )


async def handle_birth_date_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str
) -> None:
    """Handle birth date input for settings change.

    :param update: The update object
    :param context: The context object
    :param message_text: User's input text
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
        user_service.update_user_settings(telegram_id=user.id, birth_date=birth_date)

        # Update user's notification schedule
        scheduler_success = update_user_schedule(user.id)
        if scheduler_success:
            logger.info(f"Updated notification schedule for user {user.id}")
        else:
            logger.warning(f"Failed to update notification schedule for user {user.id}")

        # Calculate new age
        from ..core.life_calculator import LifeCalculatorEngine

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

        logger.info(f"User {user.id} updated birth date to {birth_date}")

    except (UserNotFoundError, UserSettingsUpdateError) as error:
        logger.error(f"Failed to update birth date for user {user.id}: {error}")
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
    update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str
) -> None:
    """Handle life expectancy input for settings change.

    :param update: The update object
    :param context: The context object
    :param message_text: User's input text
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
            logger.info(f"Updated notification schedule for user {user.id}")
        else:
            logger.warning(f"Failed to update notification schedule for user {user.id}")

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

        logger.info(f"User {user.id} updated life expectancy to {life_expectancy}")

    except (UserNotFoundError, UserSettingsUpdateError) as error:
        logger.error(f"Failed to update life expectancy for user {user.id}: {error}")
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


async def handle_unknown_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle unknown messages and commands.

    This function is called when user sends any message that is not a recognized command.
    It sends an error message and suggests using /help command.

    :param update: The update object containing the message
    :type update: telegram.Update
    :param context: The context object
    :type context: telegram.ext.CallbackContext
    :returns: None
    """
    user = update.effective_user  # type: telegram.User
    await update.message.reply_text(generate_message_unknown_command(user))
