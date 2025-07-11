"""Message generation module for LifeWeeksBot.

This module provides functions for generating localized messages
for different bot commands and user interactions. Each function
handles the retrieval of user data, calculation of life statistics,
and formatting of messages according to user's language preferences.
"""

from telegram import User as TelegramUser

from ..database.models import SubscriptionType
from ..database.service import user_service
from ..utils.config import DEFAULT_LANGUAGE
from ..utils.localization import get_message, get_subscription_description
from .life_calculator import LifeCalculatorEngine


def generate_message_week(user_info: TelegramUser) -> str:
    """Generate weekly statistics message for the user.

    This function retrieves the user's profile from the database,
    calculates life statistics using the LifeCalculatorEngine,
    and formats a localized message showing the user's age,
    weeks lived, remaining weeks, life percentage, and days
    until next birthday. Additionally, it includes subscription-specific
    content based on the user's subscription type.

    :param user_info: Telegram user object containing user ID and language
    :type user_info: TelegramUser
    :returns: Localized message with life statistics and subscription content
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

    # Generate base localized message with statistics
    base_message = get_message(
        "command_weeks",
        "statistics",
        user_lang,
        age=age,
        weeks_lived=weeks_lived,
        remaining_weeks=remaining_weeks,
        life_percentage=life_percentage,
        days_until_birthday=days_until_birthday,
    )

    # Add subscription-specific content based on user's subscription type
    if user_profile.subscription:
        subscription_type = user_profile.subscription.subscription_type

        if (
            subscription_type.value == SubscriptionType.PREMIUM
            or subscription_type.value == SubscriptionType.TRIAL
        ):
            additional_content = generate_message_week_addition_premium(user_info)
        else:
            # Fallback to basic if unknown subscription type
            additional_content = generate_message_week_addition_basic(user_info)

        return base_message + additional_content
    else:
        # Fallback to basic content if no subscription found
        additional_content = generate_message_week_addition_basic(user_info)
        return base_message + additional_content


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


def generate_message_subscription_current(user_info: TelegramUser) -> str:
    """Generate current subscription message for the user.

    This function creates a localized message showing the user's current
    subscription type with description and options to change it.

    :param user_info: Telegram user object containing user ID and language
    :type user_info: TelegramUser
    :returns: Localized subscription management message
    :rtype: str
    :raises ValueError: If user profile is not found or has no subscription
    """
    # Extract user ID and language preference
    user_id = user_info.id
    user_lang = user_info.language_code or DEFAULT_LANGUAGE

    # Get user profile from database
    user_profile = user_service.get_user_profile(user_id)
    if not user_profile or not user_profile.subscription:
        raise ValueError(
            f"User profile or subscription not found for telegram_id: {user_id}"
        )

    current_subscription = user_profile.subscription.subscription_type
    subscription_type_title = current_subscription.value.title()

    # Get subscription description
    subscription_description = get_subscription_description(
        current_subscription.value, user_lang
    )

    # Generate localized message
    return get_message(
        "command_subscription",
        "current_subscription",
        user_lang,
        subscription_type=subscription_type_title,
        subscription_description=subscription_description,
    )


def generate_message_subscription_invalid_type(user_info: TelegramUser) -> str:
    """Generate invalid subscription type error message.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized invalid subscription type message
    :rtype: str
    """
    user_lang = user_info.language_code or DEFAULT_LANGUAGE
    return get_message("command_subscription", "invalid_subscription_type", user_lang)


def generate_message_subscription_profile_error(user_info: TelegramUser) -> str:
    """Generate subscription profile error message.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized profile error message
    :rtype: str
    """
    user_lang = user_info.language_code or DEFAULT_LANGUAGE
    return get_message("command_subscription", "profile_error", user_lang)


def generate_message_subscription_already_active(
    user_info: TelegramUser, subscription_type: str
) -> str:
    """Generate already active subscription message.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :param subscription_type: Current subscription type
    :type subscription_type: str
    :returns: Localized already active message
    :rtype: str
    """
    user_lang = user_info.language_code or DEFAULT_LANGUAGE
    return get_message(
        "command_subscription",
        "already_active",
        user_lang,
        subscription_type=subscription_type.title(),
    )


def generate_message_subscription_change_success(
    user_info: TelegramUser, subscription_type: str
) -> str:
    """Generate subscription change success message.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :param subscription_type: New subscription type
    :type subscription_type: str
    :returns: Localized success message
    :rtype: str
    """
    user_lang = user_info.language_code or DEFAULT_LANGUAGE

    # Get subscription description
    subscription_description = get_subscription_description(
        subscription_type, user_lang
    )

    return get_message(
        "command_subscription",
        "change_success",
        user_lang,
        subscription_type=subscription_type.title(),
        subscription_description=subscription_description,
    )


def generate_message_subscription_change_failed(user_info: TelegramUser) -> str:
    """Generate subscription change failed message.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized change failed message
    :rtype: str
    """
    user_lang = user_info.language_code or DEFAULT_LANGUAGE
    return get_message("command_subscription", "change_failed", user_lang)


def generate_message_subscription_change_error(user_info: TelegramUser) -> str:
    """Generate subscription change error message.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized change error message
    :rtype: str
    """
    user_lang = user_info.language_code or DEFAULT_LANGUAGE
    return get_message("command_subscription", "change_error", user_lang)


def generate_message_week_addition_basic(user_info: TelegramUser) -> str:
    """Generate additional basic subscription message for weekly statistics.

    This function creates a localized message with information about basic subscription,
    including links to support the project and donation options.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized basic subscription addition message
    :rtype: str
    """
    user_lang = user_info.language_code or DEFAULT_LANGUAGE
    return get_message("subscription_additions", "basic_addition", user_lang)


def generate_message_week_addition_premium(user_info: TelegramUser) -> str:
    """Generate additional premium subscription message for weekly statistics.

    This function creates a localized message with premium content including
    psychology of time, interesting facts, and daily tips for premium subscribers.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized premium subscription addition message
    :rtype: str
    """
    user_lang = user_info.language_code or DEFAULT_LANGUAGE
    return get_message("subscription_additions", "premium_addition", user_lang)
