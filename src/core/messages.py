"""Message generation module for LifeWeeksBot.

This module provides functions for generating localized messages
for different bot commands and user interactions. Each function
handles the retrieval of user data, calculation of life statistics,
and formatting of messages according to user's language preferences.
"""

from telegram import User as TelegramUser

from ..database.service import user_service
from ..utils.config import DEFAULT_LANGUAGE
from ..utils.localization import get_message
from .life_calculator import LifeCalculatorEngine


def generate_message_week(user_info: TelegramUser) -> str:
    """Generate weekly statistics message for the user.

    This function retrieves the user's profile from the database,
    calculates life statistics using the LifeCalculatorEngine,
    and formats a localized message showing the user's age,
    weeks lived, remaining weeks, life percentage, and days
    until next birthday.

    :param user_info: Telegram user object containing user ID and language
    :type user_info: TelegramUser
    :returns: Localized message with life statistics
    :rtype: str
    :raises ValueError: If user profile is not found or has no birth date
    :raises KeyError: If required statistics are missing from calculator output
    """
    # Extract user ID and language preference
    user_id = user_info.id
    user_lang = user_info.language_code or DEFAULT_LANGUAGE

    # Get user profile from database and create calculator instance
    user_profile = user_service.get_user_profile(user_id)
    if not user_profile:
        raise ValueError(f"User profile not found for telegram_id: {user_id}")

    calculator = LifeCalculatorEngine(user=user_profile)
    stats = calculator.get_life_statistics()

    # Extract relevant statistics for the message
    age = stats["age"]
    weeks_lived = stats["weeks_lived"]
    remaining_weeks = stats["remaining_weeks"]
    life_percentage = f"{stats['life_percentage']:.1%}"
    days_until_birthday = stats["days_until_birthday"]

    # Generate localized message with statistics
    return get_message(
        "command_weeks",
        "statistics",
        user_lang,
        age=age,
        weeks_lived=weeks_lived,
        remaining_weeks=remaining_weeks,
        life_percentage=life_percentage,
        days_until_birthday=days_until_birthday,
    )


def generate_message_visualize(user_info: TelegramUser) -> str:
    """Generate visualization caption message for the user.

    This function creates a caption for the life visualization image,
    showing key statistics like age, weeks lived, and life percentage.
    The message is formatted according to the user's language preference.

    :param user_info: Telegram user object containing user ID and language
    :type user_info: TelegramUser
    :returns: Localized caption message for visualization
    :rtype: str
    :raises ValueError: If user profile is not found or has no birth date
    :raises KeyError: If required statistics are missing from calculator output
    """
    # Extract user ID and language preference
    user_id = user_info.id
    user_lang = user_info.language_code or DEFAULT_LANGUAGE

    # Get user profile from database and create calculator instance
    user_profile = user_service.get_user_profile(user_id)
    if not user_profile:
        raise ValueError(f"User profile not found for telegram_id: {user_id}")

    calculator = LifeCalculatorEngine(user=user_profile)
    stats = calculator.get_life_statistics()

    # Extract relevant statistics for the caption
    age = stats["age"]
    weeks_lived = stats["weeks_lived"]
    life_percentage = f"{stats['life_percentage']:.1%}"

    # Generate localized caption message
    return get_message(
        "command_visualize",
        "caption",
        user_lang,
        age=age,
        weeks_lived=weeks_lived,
        life_percentage=life_percentage,
    )


def generate_message_help(user_info: TelegramUser) -> str:
    """Generate help message for the user.

    This function creates a localized help message that explains
    available bot commands and their usage. The message is formatted
    according to the user's language preference.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized help message
    :rtype: str
    """
    # Get user's language preference or use default
    user_lang = user_info.language_code or DEFAULT_LANGUAGE

    # Generate localized help message
    return get_message("command_help", "help_text", user_lang)


def generate_message_cancel_success(user_info: TelegramUser) -> str:
    """Generate success message for user cancellation.

    This function creates a localized message confirming that
    the user's data has been successfully deleted.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized success message
    :rtype: str
    """
    # Get user's language preference or use default
    user_lang = user_info.language_code or DEFAULT_LANGUAGE

    # Generate localized success message
    return get_message("command_cancel", "user_deleted", user_lang)


def generate_message_cancel_error(user_info: TelegramUser) -> str:
    """Generate error message for user cancellation failure.

    This function creates a localized message indicating that
    the user's data deletion failed.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized error message
    :rtype: str
    """
    # Get user's language preference or use default
    user_lang = user_info.language_code or DEFAULT_LANGUAGE

    # Generate localized error message
    return get_message("command_cancel", "deletion_error", user_lang)


def generate_message_start_welcome_existing(user_info: TelegramUser) -> str:
    """Generate welcome message for existing users.

    This function creates a localized welcome message for users
    who are already registered in the system.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized welcome message for existing users
    :rtype: str
    """
    # Get user's language preference or use default
    user_lang = user_info.language_code or DEFAULT_LANGUAGE

    # Generate localized welcome message
    return get_message(
        "command_start",
        "welcome_existing",
        user_lang,
        first_name=user_info.first_name,
    )


def generate_message_start_welcome_new(user_info: TelegramUser) -> str:
    """Generate welcome message for new users.

    This function creates a localized welcome message for new users
    who need to register with their birth date.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized welcome message for new users
    :rtype: str
    """
    # Get user's language preference or use default
    user_lang = user_info.language_code or DEFAULT_LANGUAGE

    # Generate localized welcome message
    return get_message(
        "command_start",
        "welcome_new",
        user_lang,
        first_name=user_info.first_name,
    )


def generate_message_registration_success(
    user_info: TelegramUser, birth_date: str
) -> str:
    """Generate success message for user registration.

    This function creates a localized success message confirming
    that the user has been successfully registered with their
    birth date and showing initial statistics.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :param birth_date: User's birth date as formatted string
    :type birth_date: str
    :returns: Localized registration success message
    :rtype: str
    :raises ValueError: If user profile is invalid or has no birth date
    :raises KeyError: If required statistics are missing from calculator output
    """
    # Get user's language preference or use default
    user_lang = user_info.language_code or DEFAULT_LANGUAGE

    # Create calculator instance and get statistics
    user_profile = user_service.get_user_profile(user_info.id)
    calculator = LifeCalculatorEngine(user=user_profile)
    stats = calculator.get_life_statistics()
    weeks_lived = stats["weeks_lived"]
    age = stats["age"]

    # Generate localized success message
    return get_message(
        "registration",
        "success",
        user_lang,
        birth_date=birth_date,
        age=age,
        weeks_lived=weeks_lived,
    )


def generate_message_registration_error(user_info: TelegramUser) -> str:
    """Generate error message for registration failure.

    This function creates a localized error message indicating
    that user registration failed.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized registration error message
    :rtype: str
    """
    # Get user's language preference or use default
    user_lang = user_info.language_code or DEFAULT_LANGUAGE

    # Generate localized error message
    return get_message("registration", "database_error", user_lang)


def generate_message_birth_date_future_error(user_info: TelegramUser) -> str:
    """Generate error message for future birth date.

    This function creates a localized error message indicating
    that the provided birth date is in the future.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized future date error message
    :rtype: str
    """
    # Get user's language preference or use default
    user_lang = user_info.language_code or DEFAULT_LANGUAGE

    # Generate localized error message
    return get_message("birth_date_validation", "future_date_error", user_lang)


def generate_message_birth_date_old_error(user_info: TelegramUser) -> str:
    """Generate error message for very old birth date.

    This function creates a localized error message indicating
    that the provided birth date is too old (before 1900).

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized old date error message
    :rtype: str
    """
    # Get user's language preference or use default
    user_lang = user_info.language_code or DEFAULT_LANGUAGE

    # Generate localized error message
    return get_message("birth_date_validation", "old_date_error", user_lang)


def generate_message_birth_date_format_error(user_info: TelegramUser) -> str:
    """Generate error message for invalid birth date format.

    This function creates a localized error message indicating
    that the provided birth date format is invalid.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized format error message
    :rtype: str
    """
    # Get user's language preference or use default
    user_lang = user_info.language_code or DEFAULT_LANGUAGE

    # Generate localized error message
    return get_message("birth_date_validation", "format_error", user_lang)
