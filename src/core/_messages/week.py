from __future__ import annotations

from typing import Any

from telegram import User as TelegramUser

from ..subscription_messages import get_subscription_addition_message
from .base import BaseMessageGenerator


class WeeksMessages(BaseMessageGenerator):
    """Generate weekly statistics messages."""

    def generate(self, user_info: TelegramUser) -> str:
        """Generate weekly statistics message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :returns: Localized weekly stats message with subscription addition
        :rtype: str
        """
        stats: dict[str, Any] = self.life_stats()
        base: str = self.build(
            key="weeks.statistics",
            age=stats["age"],
            weeks_lived=stats["weeks_lived"],
            remaining_weeks=stats["remaining_weeks"],
            life_percentage=f"{float(stats['life_percentage']):.1%}",
            days_until_birthday=stats["days_until_birthday"],
        )
        subscription_type: str = self.subscription_type_value()
        addition: str = get_subscription_addition_message(
            user_info=user_info,
            subscription_type=subscription_type,
        )
        return base + addition
