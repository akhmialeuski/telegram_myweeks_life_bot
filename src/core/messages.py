"""Message generation module for LifeWeeksBot.

This module provides functions for generating localized messages
for different bot commands and user interactions. Each function
handles the retrieval of user data, calculation of life statistics,
and formatting of messages according to user's language preferences.
"""

from datetime import date

from telegram import User as TelegramUser

from ..constants import DEFAULT_LIFE_EXPECTANCY
from ..core.enums import SubscriptionType
from ..utils.config import DEFAULT_LANGUAGE
from ..utils.localization import get_localized_language_name
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
        from ..database.service import user_service

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
    from ..database.service import user_service

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

    # Use MessageBuilder for generating the base message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    # Generate the base message using MessageBuilder (which has built-in fallbacks)
    base_message = builder.get(
        key="weeks.statistics",
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
    from ..database.service import user_service

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

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get(
        key="visualize.info",
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

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    # Example: dynamic access via key if available
    return builder.get(key="help.text")


def generate_message_cancel_success(user_info: TelegramUser, language: str) -> str:
    """Generate cancel success message for the user.

    This function creates a localized success message when the user
    successfully cancels their account and deletes their data.

    :param user_info: Telegram user object containing user information
    :type user_info: TelegramUser
    :param language: Language code for message localization
    :type language: str
    :returns: Localized cancel success message
    :rtype: str
    """
    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(language)

    return builder.get("cancel.success", first_name=user_info.first_name)


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

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get("cancel.error", first_name=user_info.first_name)


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

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get("start.welcome_existing", first_name=user_info.first_name)


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

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get("start.welcome_new", first_name=user_info.first_name)


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
    from ..database.service import user_service

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

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get(
        key="registration.success",
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

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get(key="registration.error")


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

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get(key="birth_date.future_error")


def generate_message_birth_date_old_error(user_info: TelegramUser) -> str:
    """Generate birth date old error message for the user.

    This function creates a localized error message when the user
    enters a birth date that is too old.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized birth date old error message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get(key="birth_date.old_error")


def generate_message_birth_date_format_error(user_info: TelegramUser) -> str:
    """Generate birth date format error message for the user.

    This function creates a localized error message when the user
    enters a birth date in an incorrect format.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized birth date format error message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get(key="birth_date.format_error")


def generate_message_subscription_current(user_info: TelegramUser) -> str:
    """Generate current subscription message for the user.

    This function creates a localized message showing the user's current
    subscription type and options to change it.

    :param user_info: Telegram user object containing user ID and language
    :type user_info: TelegramUser
    :returns: Localized current subscription message
    :rtype: str
    :raises ValueError: If user profile is not found
    """
    # Extract user ID and get user profile from database
    user_id = user_info.id
    from ..database.service import user_service

    user_profile = user_service.get_user_profile(telegram_id=user_id)
    if not user_profile:
        raise ValueError(f"User profile not found for telegram_id: {user_id}")

    # Get user's language preference
    user_lang = get_user_language(user_info, user_profile)

    # Get subscription type and description
    subscription_type = "basic"  # Default
    if user_profile.subscription:
        subscription_type = user_profile.subscription.subscription_type.value

    subscription_description = get_subscription_addition_message(
        user_info=user_info,
        subscription_type=subscription_type,
    )

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get(
        "subscription.management",
        subscription_type=subscription_type,
        subscription_description=subscription_description,
    )


def generate_message_subscription_invalid_type(user_info: TelegramUser) -> str:
    """Generate invalid subscription type message for the user.

    This function creates a localized error message when the user
    selects an invalid subscription type.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized invalid subscription type message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get("subscription.invalid_type")


def generate_message_subscription_profile_error(user_info: TelegramUser) -> str:
    """Generate subscription profile error message for the user.

    This function creates a localized error message when there's an issue
    retrieving the user's profile for subscription management.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized subscription profile error message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get("subscription.change_error")


def generate_message_subscription_already_active(
    user_info: TelegramUser, subscription_type: str
) -> str:
    """Generate subscription already active message for the user.

    This function creates a localized message when the user tries to
    activate a subscription that is already active.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :param subscription_type: The subscription type that is already active
    :type subscription_type: str
    :returns: Localized subscription already active message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get(
        "subscription.already_active", subscription_type=subscription_type
    )


def generate_message_subscription_change_success(
    user_info: TelegramUser, subscription_type: str
) -> str:
    """Generate subscription change success message for the user.

    This function creates a localized success message when the user
    successfully changes their subscription type.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :param subscription_type: The new subscription type
    :type subscription_type: str
    :returns: Localized subscription change success message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Get subscription description
    subscription_description = get_subscription_addition_message(
        user_info=user_info,
        subscription_type=subscription_type,
    )

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get(
        key="subscription.change_success",
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

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get(key="subscription.change_failed")


def generate_message_subscription_change_error(user_info: TelegramUser) -> str:
    """Generate subscription change error message for the user.

    This function creates a localized error message when there's an error
    during subscription change process.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized subscription change error message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get(key="subscription.change_error")


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

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get("unknown.command")


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
    # Extract user ID and get user profile from database
    user_id = user_info.id
    from ..database.service import user_service

    user_profile = user_service.get_user_profile(telegram_id=user_id)
    if not user_profile or not user_profile.settings:
        raise ValueError(
            f"User profile or settings not found for telegram_id: {user_id}"
        )

    # Get language from database or use Telegram language as fallback
    db_language = (
        user_profile.settings.language or user_info.language_code or DEFAULT_LANGUAGE
    )

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(db_language)

    # Prefer dynamic key usage; compute values to avoid coupling to builder internals
    birth_date = user_profile.settings.birth_date
    birth_date_str = (
        birth_date.strftime("%d.%m.%Y") if birth_date else builder.not_set()
    )
    language_name = get_localized_language_name(db_language, db_language)
    life_expectancy = user_profile.settings.life_expectancy
    return builder.get(
        key="settings.basic",
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
    # Extract user ID and get user profile from database
    user_id = user_info.id
    from ..database.service import user_service

    user_profile = user_service.get_user_profile(telegram_id=user_id)
    if not user_profile or not user_profile.settings:
        raise ValueError(
            f"User profile or settings not found for telegram_id: {user_id}"
        )

    # Get language from database or use Telegram language as fallback
    db_language = (
        user_profile.settings.language or user_info.language_code or DEFAULT_LANGUAGE
    )

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(db_language)

    # Prepare the data for the message
    birth_date = user_profile.settings.birth_date
    birth_date_str = (
        birth_date.strftime("%d.%m.%Y") if birth_date else builder.not_set()
    )
    language_name = get_localized_language_name(db_language, db_language)
    life_expectancy = user_profile.settings.life_expectancy

    # Generate the message using MessageBuilder (which has built-in fallbacks)
    return builder.get(
        key="settings.premium",
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
    from ..database.service import user_service

    user_profile = user_service.get_user_profile(telegram_id=user_id)
    if not user_profile or not user_profile.settings:
        raise ValueError(
            f"User profile or settings not found for telegram_id: {user_id}"
        )

    # Get user's language preference
    user_lang = get_user_language(user_info, user_profile)

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    # Format current birth date
    current_birth_date = user_profile.settings.birth_date
    if current_birth_date:
        current_birth_date_str = current_birth_date.strftime("%d.%m.%Y")
    else:
        current_birth_date_str = builder.not_set()

    return builder.get(
        "settings.change_birth_date", current_birth_date=current_birth_date_str
    )


def generate_message_change_language(user_info: TelegramUser) -> str:
    """Generate language change message for the user.

    This function creates a localized message for changing language.

    :param user_info: Telegram user object containing user ID and language
    :type user_info: TelegramUser
    :returns: Localized language change message
    :rtype: str
    :raises ValueError: If user profile is not found
    """
    # Extract user ID and get user profile from database
    user_id = user_info.id
    from ..database.service import user_service

    user_profile = user_service.get_user_profile(telegram_id=user_id)
    if not user_profile or not user_profile.settings:
        raise ValueError(
            f"User profile or settings not found for telegram_id: {user_id}"
        )

    # Get user's language preference
    user_lang = get_user_language(user_info, user_profile)

    # Get current language name
    current_language = user_profile.settings.language or user_lang
    current_language_name = get_localized_language_name(
        current_language, current_language
    )

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    # Try primary localized key first
    text: str = builder.get(
        "settings.change_language", current_language=current_language_name
    )
    # Fallback: if key is missing and returned verbatim, reuse existing button label
    if text == "settings.change_language" or not isinstance(text, str):
        text = builder.get(key="buttons.change_language")
    return text


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
    from ..database.service import user_service

    user_profile = user_service.get_user_profile(telegram_id=user_id)
    if not user_profile or not user_profile.settings:
        raise ValueError(
            f"User profile or settings not found for telegram_id: {user_id}"
        )

    # Get user's language preference
    user_lang = get_user_language(user_info, user_profile)

    # Get current life expectancy
    current_life_expectancy = (
        user_profile.settings.life_expectancy or DEFAULT_LIFE_EXPECTANCY
    )

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get(
        "settings.change_life_expectancy",
        current_life_expectancy=current_life_expectancy,
    )


def generate_message_birth_date_updated(
    user_info: TelegramUser, new_birth_date: date, new_age: int
) -> str:
    """Generate birth date updated message for the user.

    This function creates a localized success message when the user
    successfully updates their birth date.

    :param user_info: Telegram user object containing user ID and language
    :type user_info: TelegramUser
    :param new_birth_date: New birth date
    :type new_birth_date: date
    :param new_age: New age calculated from birth date
    :type new_age: int
    :returns: Localized birth date updated message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Format new birth date
    new_birth_date_str = new_birth_date.strftime("%d.%m.%Y")

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get(
        "settings.birth_date_updated",
        new_birth_date=new_birth_date_str,
        new_age=new_age,
    )


def generate_message_language_updated(
    user_info: TelegramUser, new_language: str
) -> str:
    """Generate language updated message for the user.

    This function creates a localized success message when the user
    successfully changes their language preference.

    :param user_info: Telegram user object containing user ID and language
    :type user_info: TelegramUser
    :param new_language: New language (code or display name). Kept for compatibility,
                         actual language is read from updated user settings.
    :type new_language: str
    :returns: Localized language updated message
    :rtype: str
    """
    # Always render in the user's CURRENT language (already updated in DB)
    # and display the language name localized to itself
    current_lang: str = get_user_language(user_info)
    display_name: str = get_localized_language_name(current_lang, current_lang)

    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(current_lang)

    return builder.get("settings.language_updated", new_language=display_name)


def generate_message_life_expectancy_updated(
    user_info: TelegramUser, new_life_expectancy: int
) -> str:
    """Generate life expectancy updated message for the user.

    This function creates a localized success message when the user
    successfully updates their life expectancy.

    :param user_info: Telegram user object containing user ID and language
    :type user_info: TelegramUser
    :param new_life_expectancy: New life expectancy value
    :type new_life_expectancy: int
    :returns: Localized life expectancy updated message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get(
        "settings.life_expectancy_updated", new_life_expectancy=new_life_expectancy
    )


def generate_message_invalid_life_expectancy(user_info: TelegramUser) -> str:
    """Generate invalid life expectancy message for the user.

    This function creates a localized error message when the user
    enters an invalid life expectancy value.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized invalid life expectancy message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get("settings.invalid_life_expectancy")


def generate_message_settings_error(user_info: TelegramUser) -> str:
    """Generate settings error message for the user.

    This function creates a localized error message when there's an error
    updating user settings.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized settings error message
    :rtype: str
    """
    # Get user's language preference
    user_lang = get_user_language(user_info)

    # Use MessageBuilder for generating the message
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    return builder.get("settings.error")


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

    # Use MessageBuilder for generating button texts
    from ..services.container import ServiceContainer

    container = ServiceContainer()
    builder = container.get_message_builder(user_lang)

    # Generate localized button texts
    try:
        birth_date_text = builder.get(key="buttons.change_birth_date")
        language_text = builder.get(key="buttons.change_language")
        life_expectancy_text = builder.get(key="buttons.change_life_expectancy")
        # ensure they are strings
        if not all(
            isinstance(x, str)
            for x in (birth_date_text, language_text, life_expectancy_text)
        ):
            raise TypeError("button texts must be strings")
    except Exception:
        birth_date_text = builder.get(key="buttons.change_birth_date")
        language_text = builder.get(key="buttons.change_language")
        life_expectancy_text = builder.get(key="buttons.change_life_expectancy")

    # Return button configurations
    return [
        [{"text": birth_date_text, "callback_data": "settings_birth_date"}],
        [{"text": language_text, "callback_data": "settings_language"}],
        [{"text": life_expectancy_text, "callback_data": "settings_life_expectancy"}],
    ]
