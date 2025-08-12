"""Subscription message generation module for LifeWeeksBot.

This module provides functions for generating subscription-specific
additional content that is appended to main bot messages based on
user's subscription type.
"""

import random

from telegram import User as TelegramUser

from ..utils.config import BUYMEACOFFEE_URL, SUBSCRIPTION_MESSAGE_PROBABILITY
from .enums import SubscriptionType
from .message_context import MessageContext


def generate_message_week_addition_basic(user_info: TelegramUser) -> str:
    """Generate additional basic subscription message for weekly statistics.

    This function creates a localized message with information about basic subscription,
    including links to support the project and donation options. The message is returned
    only with a configurable probability (default 20%).

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized basic subscription addition message or empty string based on probability
    :rtype: str
    """
    # Check probability - return empty string if random check fails
    if random.randint(1, 100) > SUBSCRIPTION_MESSAGE_PROBABILITY:
        return ""

    ctx: MessageContext = MessageContext.require()
    return ctx.builder.get("subscription.basic_info", buymeacoffee_url=BUYMEACOFFEE_URL)


def generate_message_week_addition_premium(user_info: TelegramUser) -> str:
    """Generate additional premium subscription message for weekly statistics.

    This function creates a localized message with premium content including
    psychology of time, interesting facts, and daily tips for premium subscribers.

    :param user_info: Telegram user object containing language preference
    :type user_info: TelegramUser
    :returns: Localized premium subscription addition message
    :rtype: str
    """
    ctx: MessageContext = MessageContext.require()
    return ctx.builder.get("subscription.premium_content")


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
    if subscription_type in [
        SubscriptionType.PREMIUM.value,
        SubscriptionType.TRIAL.value,
    ]:
        return generate_message_week_addition_premium(user_info=user_info)
    else:
        # Fallback to basic for unknown subscription types
        return generate_message_week_addition_basic(user_info=user_info)
