"""Command handlers for the Telegram bot."""

from datetime import date, datetime
from functools import wraps
from typing import Any, Callable

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from ..core.life_calculator import LifeCalculatorEngine
from ..database.service import user_service
from ..utils.config import BOT_NAME, DEFAULT_LANGUAGE
from ..utils.localization import get_message
from ..utils.logger import get_logger
from ..visualization.grid import generate_visualization

logger = get_logger(BOT_NAME)

# Conversation states
WAITING_BIRTH_DATE = 1


def require_registration():
    """Decorator to check user registration and handle errors.

    This decorator:
    - Checks if user has a valid profile
    - Handles exceptions and logs errors
    - Sends appropriate error messages to user

    :returns: Decorated function
    :rtype: Callable
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
            user = update.effective_user
            user_id = user.id
            user_lang = user.language_code or DEFAULT_LANGUAGE

            try:
                # Check if user has valid profile
                if not user_service.is_valid_user_profile(user_id):
                    await update.message.reply_text(
                        get_message("common", "not_registered", user_lang)
                    )
                    return

                # Call the original function
                return await func(update, context)

            except Exception as error:  # pylint: disable=broad-exception-caught
                logger.error(f"Error in {func.__name__} command: {error}")
                await update.message.reply_text(
                    get_message("common", "error", user_lang)
                )

        return wrapper

    return decorator


async def command_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command - ask for birth date and register user.

    :param update: The update object containing the message.
    :param context: The context object for the command.
    :returns: Conversation state
    """
    user = update.effective_user
    user_lang = user.language_code

    logger.info(f"User {user.id} ({user.username}) started the bot")

    # Check if user already exists
    existing_user = user_service.get_user_profile(user.id)
    if existing_user:
        await update.message.reply_text(
            get_message(
                "command_start",
                "welcome_existing",
                user_lang,
                first_name=user.first_name,
            )
        )
        return ConversationHandler.END

    # Ask for birth date
    await update.message.reply_text(
        get_message(
            "command_start", "welcome_new", user_lang, first_name=user.first_name
        )
    )

    return WAITING_BIRTH_DATE


async def command_start_handle_birth_date(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle birth date input from user during /start command registration.

    :param update: The update object containing the message.
    :param context: The context object for the command.
    :returns: Conversation state
    """
    user = update.effective_user
    birth_date_text = update.message.text.strip()
    user_lang = user.language_code

    try:
        # Parse birth date
        birth_date = datetime.strptime(birth_date_text, "%d.%m.%Y").date()

        # Validate birth date (not in future, reasonable past)
        today = date.today()
        if birth_date > today:
            await update.message.reply_text(
                get_message("birth_date_validation", "future_date_error", user_lang)
            )
            return WAITING_BIRTH_DATE

        if birth_date.year < 1900:
            await update.message.reply_text(
                get_message("birth_date_validation", "old_date_error", user_lang)
            )
            return WAITING_BIRTH_DATE

        # Create user with settings using service
        success, error_message = user_service.create_user_with_settings(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            birth_date=birth_date,
        )

        if success:
            # Get user profile and create calculator instance
            user_profile = user_service.get_user_profile(user.id)
            calculator = LifeCalculatorEngine(user=user_profile)
            stats = calculator.get_life_statistics()
            weeks_lived = stats["weeks_lived"]
            age = stats["age"]

            await update.message.reply_text(
                get_message(
                    "registration",
                    "success",
                    user_lang,
                    birth_date=birth_date.strftime("%d.%m.%Y"),
                    age=age,
                    weeks_lived=weeks_lived,
                )
            )

            logger.info(f"User {user.id} registered with birth date {birth_date}")
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                get_message("registration", "database_error", user_lang)
            )
            logger.error(f"Failed to register user {user.id}: {error_message}")
            return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            get_message("birth_date_validation", "format_error", user_lang)
        )
        return WAITING_BIRTH_DATE


@require_registration()
async def command_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel command to cancel registration.

    This command cancels the registration process and removes all user data
    if the user was already registered.

    :param update: The update object containing the message.
    :param context: The context object for the command.
    :returns: Conversation state
    """
    user = update.effective_user
    user_id = user.id
    user_lang = user.language_code or DEFAULT_LANGUAGE

    success = user_service.delete_user_profile(user_id)
    if success:
        await update.message.reply_text(
            get_message("command_cancel", "user_deleted", user_lang)
        )
        logger.info(f"User {user_id} data deleted via /cancel command")
    else:
        await update.message.reply_text(
            get_message("command_cancel", "deletion_error", user_lang)
        )
        logger.error(f"Failed to delete user {user_id} data via /cancel command")

    return ConversationHandler.END


@require_registration()
async def command_weeks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /weeks command to display weeks and months lived.

    :param update: The update object containing the message.
    :type update: Update
    :param context: The context object for the command.
    :type context: ContextTypes.DEFAULT_TYPE
    :returns: None
    """
    user = update.effective_user
    user_id = user.id
    user_lang = user.language_code or DEFAULT_LANGUAGE

    logger.info(f"Handling /weeks command from user {user_id}")

    # Get user profile and create calculator instance
    user_profile = user_service.get_user_profile(user_id)
    calculator = LifeCalculatorEngine(user=user_profile)
    stats = calculator.get_life_statistics()

    age = stats["age"]
    weeks_lived = stats["weeks_lived"]
    remaining_weeks = stats["remaining_weeks"]
    life_percentage = f"{stats['life_percentage']:.1%}"
    days_until_birthday = stats["days_until_birthday"]

    await update.message.reply_text(
        get_message(
            "command_weeks",
            "statistics",
            user_lang,
            age=age,
            weeks_lived=weeks_lived,
            remaining_weeks=remaining_weeks,
            life_percentage=life_percentage,
            days_until_birthday=days_until_birthday,
        ),
        parse_mode="HTML",
    )


@require_registration()
async def command_visualize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /visualize command to show a visual representation of weeks lived.

    :param update: The update object containing the message.
    :type update: Update
    :param context: The context object for the command.
    :type context: ContextTypes.DEFAULT_TYPE
    :returns: None
    """
    user = update.effective_user
    user_id = user.id
    user_lang = user.language_code or DEFAULT_LANGUAGE
    logger.info(f"Handling /visualize command from user {user_id}")

    # Get user profile and create calculator instance
    user_profile = user_service.get_user_profile(user_id)
    calculator = LifeCalculatorEngine(user=user_profile)
    stats = calculator.get_life_statistics()

    age = stats["age"]
    weeks_lived = stats["weeks_lived"]
    life_percentage = f"{stats['life_percentage']:.1%}"

    # Generate visualization
    img_byte_arr = generate_visualization(user=user_profile, lang=user_lang)

    # Send image with caption
    caption = get_message(
        "command_visualize",
        "caption",
        user_lang,
        age=age,
        weeks_lived=weeks_lived,
        life_percentage=life_percentage,
    )

    await update.message.reply_photo(
        photo=img_byte_arr, caption=caption, parse_mode="HTML"
    )


async def command_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command - show help information.

    :param update: The update object containing the message.
    :param context: The context object for the command.
    :returns: None
    """
    user = update.effective_user
    user_lang = user.language_code or DEFAULT_LANGUAGE
    help_text = get_message("command_help", "help_text", user_lang)
    await update.message.reply_text(help_text)
