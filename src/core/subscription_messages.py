"""Subscription message generation module for LifeWeeksBot.

This module provides functions for generating subscription-specific
additional content that is appended to main bot messages based on
user's subscription type.
"""

from telegram import User as TelegramUser

from ..utils.config import DEFAULT_LANGUAGE, BUYMEACOFFEE_URL
from ..utils.localization import get_message


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
    return get_message(
        "subscription_additions",
        "basic_addition",
        user_lang,
        buymeacoffee_url=BUYMEACOFFEE_URL,
    )


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


def get_subscription_addition_message(
    user_info: TelegramUser, subscription_type: str
) -> str:
    """Get appropriate subscription addition message based on subscription type.

    This function determines which additional message to generate based on
    the user's subscription type and returns the appropriate localized content.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :param subscription_type: User's subscription type
    :type subscription_type: str
    :returns: Localized subscription addition message
    :rtype: str
    """
    from ..database.models import SubscriptionType

    if subscription_type in [
        SubscriptionType.PREMIUM.value,
        SubscriptionType.TRIAL.value,
    ]:
        return generate_message_week_addition_premium(user_info)
    else:
        # Fallback to basic for unknown subscription types
        return generate_message_week_addition_basic(user_info)
