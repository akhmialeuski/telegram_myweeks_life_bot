from __future__ import annotations

from typing import Any

from telegram import User as TelegramUser

from ..subscription_messages import get_subscription_addition_message
from .base import BaseMessageGenerator


class SubscriptionMessages(BaseMessageGenerator):
    """Generate subscription management messages."""

    def current(self, user_info: TelegramUser) -> str:
        """Generate current subscription message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :returns: Localized current subscription message
        :rtype: str
        """
        profile: Any = self.ensure_profile()
        subscription_type: str = (
            profile.subscription.subscription_type.value
            if getattr(profile, "subscription", None)
            else self.subscription_type_value()
        )
        description: str = get_subscription_addition_message(
            user_info=user_info,
            subscription_type=subscription_type,
        )
        return self.build(
            "subscription.management",
            subscription_type=subscription_type,
            subscription_description=description,
        )

    def invalid_type(self) -> str:
        """Generate invalid subscription type message.

        :returns: Localized invalid subscription type message
        :rtype: str
        """
        return self.build("subscription.invalid_type")

    def profile_error(self) -> str:
        """Generate subscription profile error message.

        :returns: Localized subscription profile error message
        :rtype: str
        """
        return self.build("subscription.change_error")

    def already_active(self, subscription_type: str) -> str:
        """Generate subscription already active message.

        :param subscription_type: Already active subscription type
        :type subscription_type: str
        :returns: Localized already active message
        :rtype: str
        """
        return self.build(
            "subscription.already_active",
            subscription_type=subscription_type,
        )

    def change_success(self, user_info: TelegramUser, subscription_type: str) -> str:
        """Generate subscription change success message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :param subscription_type: New subscription type
        :type subscription_type: str
        :returns: Localized subscription change success message
        :rtype: str
        """
        description: str = get_subscription_addition_message(
            user_info=user_info,
            subscription_type=subscription_type,
        )
        return self.build(
            key="subscription.change_success",
            subscription_type=subscription_type,
            subscription_description=description,
        )

    def change_failed(self) -> str:
        """Generate subscription change failed message.

        :returns: Localized subscription change failed message
        :rtype: str
        """
        return self.build("subscription.change_failed")

    def change_error(self) -> str:
        """Generate subscription change error message.

        :returns: Localized subscription change error message
        :rtype: str
        """
        return self.build("subscription.change_error")
