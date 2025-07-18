"""Message generation module for LifeWeeksBot.

This module provides functions for generating localized messages
for different bot commands and user interactions. Each function
handles the retrieval of user data, calculation of life statistics,
and formatting of messages according to user's language preferences.
"""

from datetime import date

from telegram import User as TelegramUser

from ..database.constants import DEFAULT_LIFE_EXPECTANCY
from ..database.models import SubscriptionType
from ..database.service import user_service
from ..utils.config import DEFAULT_LANGUAGE
from ..utils.localization import (
    get_localized_language_name,
    get_message,
    get_subscription_description,
)
from .life_calculator import LifeCalculatorEngine
from .subscription_messages import get_subscription_addition_message


def get_user_language(user_info: TelegramUser, user_profile=None) -> str:
    """Get user's language preference from database or fallback to Telegram language.

    This function retrieves the user's language preference from the database
    if available, otherwise falls back to the Telegram user's language code.

    :param user_info: Telegram user object
    :type user_info: TelegramUser
    :param user_profile: Optional user profile from database (to avoid extra queries)
    :type user_profile: Optional[User]
    :returns: Language code (ru, en, ua, by)
    :rtype: str
    """
    # If user_profile is provided, use it directly
    if user_profile and user_profile.settings and user_profile.settings.language:
        return user_profile.settings.language

    # Otherwise, get user profile from database
    if not user_profile:
        user_profile = user_service.get_user_profile(telegram_id=user_info.id)

    # Get language from database or use Telegram language as fallback
    if user_profile and user_profile.settings and user_profile.settings.language:
        return user_profile.settings.language

    # Fallback to Telegram language or default
    return user_info.language_code or DEFAULT_LANGUAGE


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
    # Extract user ID and get user profile from database
    user_id = user_info.id
    user_profile = user_service.get_user_profile(telegram_id=user_id)

    # Get user's language preference
    user_lang = get_user_language(user_info, user_profile)

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
        message_key="command_weeks",
        sub_key="statistics",
        language=user_lang,
        age=age,
        weeks_lived=weeks_lived,
        remaining_weeks=remaining_weeks,
        life_percentage=life_percentage,
        days_until_birthday=days_until_birthday,
    )

    # Add subscription-specific content based on user's subscription type
    if user_profile.subscription:
        subscription_type = user_profile.subscription.subscription_type.value
        additional_content = get_subscription_addition_message(
            user_info=user_info,
            subscription_type=subscription_type,
        )
    else:
        # Fallback to basic content if no subscription found
        additional_content = get_subscription_addition_message(
            user_info=user_info,
            subscription_type=SubscriptionType.BASIC.value,
        )

    return base_message + additional_content


def generate_message_visualize(user_info: TelegramUser) -> str:
    """Generate visualization message for the user.

    This function creates a localized message that accompanies the visual
    grid representation of the user's life weeks. The message provides
    context and explanation for the visualization.

    :param user_info: Telegram user object containing user ID and language
    :type user_info: TelegramUser
    :returns: Localized visualization message
    :rtype: str
    :raises ValueError: If user profile is not found or has no birth date
    """
    # Extract user ID and get user profile from database
    user_id = user_info.id
    user_profile = user_service.get_user_profile(telegram_id=user_id)

    # Get user's language preference
    user_lang = get_user_language(user_info, user_profile)

    if not user_profile:
        raise ValueError(f"User profile not found for telegram_id: {user_id}")

    calculator = LifeCalculatorEngine(user=user_profile)
    stats = calculator.get_life_statistics()

    # Extract relevant statistics for the message
    age = stats["age"]
    weeks_lived = stats["weeks_lived"]
    life_percentage = f"{stats['life_percentage']:.1%}"

    # Generate localized visualization message
    return get_message(
        message_key="command_visualize",
        sub_key="visualization_info",
        language=user_lang,
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
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized help message
    return get_message(
        message_key="command_help",
        sub_key="help_text",
        language=user_lang,
    )


def generate_message_cancel_success(user_info: TelegramUser, language: str) -> str:
    """Generate cancel success message for the user.

    This function creates a localized success message when the user
    successfully cancels their account and deletes their data.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized cancel success message
    :rtype: str
    """
    return get_message(
        message_key="command_cancel",
        sub_key="success",
        language=language,
        first_name=user_info.first_name,
    )


def generate_message_cancel_error(user_info: TelegramUser) -> str:
    """Generate cancel error message for the user.

    This function creates a localized error message when the user
    fails to cancel their account and delete their data.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized cancel error message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized cancel error message
    return get_message(
        message_key="command_cancel",
        sub_key="error",
        language=user_lang,
        first_name=user_info.first_name,
    )


def generate_message_start_welcome_existing(user_info: TelegramUser) -> str:
    """Generate welcome message for existing users.

    This function creates a localized welcome message for users
    who are already registered in the system.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized welcome message for existing users
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized welcome message
    return get_message(
        message_key="command_start",
        sub_key="welcome_existing",
        language=user_lang,
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
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized welcome message
    return get_message(
        message_key="command_start",
        sub_key="welcome_new",
        language=user_lang,
        first_name=user_info.first_name,
    )


def generate_message_registration_success(
    user_info: TelegramUser, birth_date: str
) -> str:
    """Generate registration success message for the user.

    This function creates a localized success message when the user
    successfully registers with their birth date. It includes calculated
    life statistics to show the user what they can expect.

    :param user_info: Telegram user object containing user ID and language
    :type user_info: TelegramUser
    :param birth_date: User's birth date as formatted string
    :type birth_date: str
    :returns: Localized registration success message with statistics
    :rtype: str
    :raises ValueError: If user profile is not found
    :raises KeyError: If required statistics are missing from calculator output
    """
    # Extract user ID and get user profile from database
    user_id = user_info.id
    user_profile = user_service.get_user_profile(telegram_id=user_id)

    # Get user's language preference
    user_lang = get_user_language(user_info, user_profile)

    if not user_profile:
        raise ValueError(f"User profile not found for telegram_id: {user_id}")

    calculator = LifeCalculatorEngine(user=user_profile)
    stats = calculator.get_life_statistics()

    # Extract relevant statistics for the message
    age = stats["age"]
    weeks_lived = stats["weeks_lived"]
    remaining_weeks = stats["remaining_weeks"]
    life_percentage = f"{stats['life_percentage']:.1%}"

    # Generate localized registration success message
    return get_message(
        message_key="command_start",
        sub_key="registration_success",
        language=user_lang,
        first_name=user_info.first_name,
        birth_date=birth_date,
        age=age,
        weeks_lived=weeks_lived,
        remaining_weeks=remaining_weeks,
        life_percentage=life_percentage,
    )


def generate_message_registration_error(user_info: TelegramUser) -> str:
    """Generate registration error message for the user.

    This function creates a localized error message when the user
    fails to register with their birth date.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized registration error message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized registration error message
    return get_message(
        message_key="command_start",
        sub_key="registration_error",
        language=user_lang,
        first_name=user_info.first_name,
    )


def generate_message_birth_date_future_error(user_info: TelegramUser) -> str:
    """Generate birth date future error message for the user.

    This function creates a localized error message when the user
    enters a birth date that is in the future.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized birth date future error message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized birth date future error message
    return get_message(
        message_key="command_start",
        sub_key="birth_date_future_error",
        language=user_lang,
        first_name=user_info.first_name,
    )


def generate_message_birth_date_old_error(user_info: TelegramUser) -> str:
    """Generate birth date old error message for the user.

    This function creates a localized error message when the user
    enters a birth date that is too old (before 1900).

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized birth date old error message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized birth date old error message
    return get_message(
        message_key="command_start",
        sub_key="birth_date_old_error",
        language=user_lang,
        first_name=user_info.first_name,
    )


def generate_message_birth_date_format_error(user_info: TelegramUser) -> str:
    """Generate birth date format error message for the user.

    This function creates a localized error message when the user
    enters a birth date in an invalid format.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized birth date format error message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized birth date format error message
    return get_message(
        message_key="command_start",
        sub_key="birth_date_format_error",
        language=user_lang,
        first_name=user_info.first_name,
    )


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
    # Extract user ID and get user profile from database
    user_id = user_info.id
    user_profile = user_service.get_user_profile(telegram_id=user_id)

    # Get user's language preference
    user_lang = get_user_language(user_info, user_profile)

    if not user_profile or not user_profile.subscription:
        raise ValueError(
            f"User profile or subscription not found for telegram_id: {user_id}"
        )

    current_subscription = user_profile.subscription.subscription_type
    subscription_type_title = current_subscription.value.title()

    # Get subscription description
    subscription_description = get_subscription_description(
        subscription_type=current_subscription.value,
        language=user_lang,
    )

    # Generate localized message
    return get_message(
        message_key="command_subscription",
        sub_key="current_subscription",
        language=user_lang,
        subscription_type=subscription_type_title,
        subscription_description=subscription_description,
    )


def generate_message_subscription_invalid_type(user_info: TelegramUser) -> str:
    """Generate invalid subscription type error message for the user.

    This function creates a localized error message when the user
    selects an invalid subscription type.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized invalid subscription type error message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized invalid subscription type error message
    return get_message(
        message_key="command_subscription",
        sub_key="invalid_type",
        language=user_lang,
    )


def generate_message_subscription_profile_error(user_info: TelegramUser) -> str:
    """Generate subscription profile error message for the user.

    This function creates a localized error message when the user's
    profile or subscription is not found.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized subscription profile error message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized subscription profile error message
    return get_message(
        message_key="command_subscription",
        sub_key="profile_error",
        language=user_lang,
    )


def generate_message_subscription_already_active(
    user_info: TelegramUser, subscription_type: str
) -> str:
    """Generate subscription already active message for the user.

    This function creates a localized message when the user tries
    to activate a subscription that is already active.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :param subscription_type: Current subscription type
    :type subscription_type: str
    :returns: Localized subscription already active message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized subscription already active message
    return get_message(
        message_key="command_subscription",
        sub_key="already_active",
        language=user_lang,
        subscription_type=subscription_type,
    )


def generate_message_subscription_change_success(
    user_info: TelegramUser, subscription_type: str
) -> str:
    """Generate subscription change success message for the user.

    This function creates a localized success message when the user
    successfully changes their subscription type.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :param subscription_type: New subscription type
    :type subscription_type: str
    :returns: Localized subscription change success message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Get subscription description
    subscription_description = get_subscription_description(
        subscription_type=subscription_type,
        language=user_lang,
    )

    # Generate localized subscription change success message
    return get_message(
        message_key="command_subscription",
        sub_key="change_success",
        language=user_lang,
        subscription_type=subscription_type,
        subscription_description=subscription_description,
    )


def generate_message_subscription_change_failed(user_info: TelegramUser) -> str:
    """Generate subscription change failed message for the user.

    This function creates a localized error message when the user
    fails to change their subscription type.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized subscription change failed message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized subscription change failed message
    return get_message(
        message_key="command_subscription",
        sub_key="change_failed",
        language=user_lang,
    )


def generate_message_subscription_change_error(user_info: TelegramUser) -> str:
    """Generate subscription change error message for the user.

    This function creates a localized error message when an error
    occurs during subscription change.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized subscription change error message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized subscription change error message
    return get_message(
        message_key="command_subscription",
        sub_key="change_error",
        language=user_lang,
    )


def generate_message_unknown_command(user_info: TelegramUser) -> str:
    """Generate message for unknown command or message.

    This function creates a localized error message when the user sends an unknown command or message.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized error message for unknown command
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    return get_message(
        message_key="common",
        sub_key="unknown_command",
        language=user_lang,
    )


def generate_message_settings_basic(user_info: TelegramUser) -> str:
    """Generate basic subscription settings message for the user.

    This function creates a localized message showing the user's current
    settings for basic subscription with options to change them.

    :param user_info: Telegram user object containing user ID and language
    :type user_info: TelegramUser
    :returns: Localized basic settings message
    :rtype: str
    :raises ValueError: If user profile is not found
    """
    # Extract user ID and language preference
    user_id = user_info.id
    user_lang = user_info.language_code or DEFAULT_LANGUAGE

    # Get user profile from database
    user_profile = user_service.get_user_profile(telegram_id=user_id)
    if not user_profile or not user_profile.settings:
        raise ValueError(
            f"User profile or settings not found for telegram_id: {user_id}"
        )

    # Get language from database or use Telegram language as fallback
    db_language = user_profile.settings.language or user_lang

    # Format birth date (localized 'not set')
    birth_date = user_profile.settings.birth_date
    if birth_date:
        birth_date_str = birth_date.strftime("%d.%m.%Y")
    else:
        birth_date_str = get_message(
            message_key="common",
            sub_key="not_set",
            language=db_language,
        )

    # Локализованное название языка
    language_name = get_localized_language_name(db_language, db_language)

    # Get life expectancy
    life_expectancy = user_profile.settings.life_expectancy or DEFAULT_LIFE_EXPECTANCY

    # Generate localized message
    return get_message(
        message_key="command_settings",
        sub_key="basic_settings",
        language=db_language,
        birth_date=birth_date_str,
        language_name=language_name,
        life_expectancy=life_expectancy,
    )


def generate_message_settings_premium(user_info: TelegramUser) -> str:
    """Generate premium subscription settings message for the user.

    This function creates a localized message showing the user's current
    settings for premium subscription with options to change them.

    :param user_info: Telegram user object containing user ID and language
    :type user_info: TelegramUser
    :returns: Localized premium settings message
    :rtype: str
    :raises ValueError: If user profile is not found
    """
    # Extract user ID and language preference
    user_id = user_info.id
    user_lang = user_info.language_code or DEFAULT_LANGUAGE

    # Get user profile from database
    user_profile = user_service.get_user_profile(telegram_id=user_id)
    if not user_profile or not user_profile.settings:
        raise ValueError(
            f"User profile or settings not found for telegram_id: {user_id}"
        )

    # Get language from database or use Telegram language as fallback
    db_language = user_profile.settings.language or user_lang

    # Format birth date (localized 'not set')
    birth_date = user_profile.settings.birth_date
    if birth_date:
        birth_date_str = birth_date.strftime("%d.%m.%Y")
    else:
        birth_date_str = get_message(
            message_key="common",
            sub_key="not_set",
            language=db_language,
        )

    # Локализованное название языка
    language_name = get_localized_language_name(db_language, db_language)

    # Get life expectancy
    life_expectancy = user_profile.settings.life_expectancy or DEFAULT_LIFE_EXPECTANCY

    # Generate localized message
    return get_message(
        message_key="command_settings",
        sub_key="premium_settings",
        language=db_language,
        birth_date=birth_date_str,
        language_name=language_name,
        life_expectancy=life_expectancy,
    )


def generate_message_change_birth_date(user_info: TelegramUser) -> str:
    """Generate birth date change message for the user.

    This function creates a localized message for changing birth date.

    :param user_info: Telegram user object containing user ID and language
    :type user_info: TelegramUser
    :returns: Localized birth date change message
    :rtype: str
    :raises ValueError: If user profile is not found
    """
    # Extract user ID and get user profile from database
    user_id = user_info.id
    user_profile = user_service.get_user_profile(telegram_id=user_id)

    # Get user's language preference
    user_lang = get_user_language(user_info, user_profile)

    if not user_profile or not user_profile.settings:
        raise ValueError(
            f"User profile or settings not found for telegram_id: {user_id}"
        )

    # Format current birth date (localized 'not set')
    birth_date = user_profile.settings.birth_date
    if birth_date:
        current_birth_date = birth_date.strftime("%d.%m.%Y")
    else:
        current_birth_date = get_message(
            message_key="common",
            sub_key="not_set",
            language=user_lang,
        )

    # Generate localized message
    return get_message(
        message_key="command_settings",
        sub_key="change_birth_date",
        language=user_lang,
        current_birth_date=current_birth_date,
    )


def generate_message_change_language(user_info: TelegramUser) -> str:
    """Generate language change message for the user.

    This function creates a localized message for changing language.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized language change message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Локализованное название языка
    current_language = get_localized_language_name(user_lang, user_lang)

    # Generate localized message
    return get_message(
        message_key="command_settings",
        sub_key="change_language",
        language=user_lang,
        current_language=current_language,
    )


def generate_message_change_life_expectancy(user_info: TelegramUser) -> str:
    """Generate life expectancy change message for the user.

    This function creates a localized message for changing life expectancy.

    :param user_info: Telegram user object containing user ID and language
    :type user_info: TelegramUser
    :returns: Localized life expectancy change message
    :rtype: str
    :raises ValueError: If user profile is not found
    """
    # Extract user ID and get user profile from database
    user_id = user_info.id
    user_profile = user_service.get_user_profile(telegram_id=user_id)

    # Get user's language preference
    user_lang = get_user_language(user_info, user_profile)

    if not user_profile or not user_profile.settings:
        raise ValueError(
            f"User profile or settings not found for telegram_id: {user_id}"
        )

    # Get current life expectancy
    current_life_expectancy = (
        user_profile.settings.life_expectancy or DEFAULT_LIFE_EXPECTANCY
    )

    # Generate localized message
    return get_message(
        message_key="command_settings",
        sub_key="change_life_expectancy",
        language=user_lang,
        current_life_expectancy=current_life_expectancy,
    )


def generate_message_birth_date_updated(
    user_info: TelegramUser, new_birth_date: date, new_age: int
) -> str:
    """Generate birth date update success message for the user.

    This function creates a localized success message when birth date is updated.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :param new_birth_date: New birth date
    :type new_birth_date: date
    :param new_age: New calculated age
    :type new_age: int
    :returns: Localized birth date update success message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Format new birth date
    new_birth_date_str = new_birth_date.strftime("%d.%m.%Y")

    # Generate localized message
    return get_message(
        message_key="command_settings",
        sub_key="birth_date_updated",
        language=user_lang,
        new_birth_date=new_birth_date_str,
        new_age=new_age,
    )


def generate_message_language_updated(
    user_info: TelegramUser, new_language: str
) -> str:
    """Generate language update success message for the user.

    This function creates a localized success message when language is updated.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :param new_language: New language name
    :type new_language: str
    :returns: Localized language update success message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized message
    return get_message(
        message_key="command_settings",
        sub_key="language_updated",
        language=user_lang,
        new_language=new_language,
    )


def generate_message_life_expectancy_updated(
    user_info: TelegramUser, new_life_expectancy: int
) -> str:
    """Generate life expectancy update success message for the user.

    This function creates a localized success message when life expectancy is updated.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :param new_life_expectancy: New life expectancy value
    :type new_life_expectancy: int
    :returns: Localized life expectancy update success message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized message
    return get_message(
        message_key="command_settings",
        sub_key="life_expectancy_updated",
        language=user_lang,
        new_life_expectancy=new_life_expectancy,
    )


def generate_message_invalid_life_expectancy(user_info: TelegramUser) -> str:
    """Generate invalid life expectancy error message for the user.

    This function creates a localized error message for invalid life expectancy input.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized invalid life expectancy error message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized message
    return get_message(
        message_key="command_settings",
        sub_key="invalid_life_expectancy",
        language=user_lang,
    )


def generate_message_settings_error(user_info: TelegramUser) -> str:
    """Generate settings error message for the user.

    This function creates a localized error message for settings operations.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized settings error message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized message
    return get_message(
        message_key="command_settings",
        sub_key="settings_error",
        language=user_lang,
    )


def generate_settings_buttons(user_info: TelegramUser) -> list[list[dict[str, str]]]:
    """Generate localized settings buttons for the user.

    This function creates a list of localized button texts for settings
    based on the user's language preference.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: List of button configurations with localized text and callback data
    :rtype: list[list[dict[str, str]]]
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Generate localized button texts
    birth_date_text = get_message(
        message_key="command_settings",
        sub_key="button_change_birth_date",
        language=user_lang,
    )

    language_text = get_message(
        message_key="command_settings",
        sub_key="button_change_language",
        language=user_lang,
    )

    life_expectancy_text = get_message(
        message_key="command_settings",
        sub_key="button_change_life_expectancy",
        language=user_lang,
    )

    # Return button configurations
    return [
        [{"text": birth_date_text, "callback_data": "settings_birth_date"}],
        [{"text": language_text, "callback_data": "settings_language"}],
        [{"text": life_expectancy_text, "callback_data": "settings_life_expectancy"}],
    ]
