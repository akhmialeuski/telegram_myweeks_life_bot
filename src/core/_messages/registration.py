from __future__ import annotations

from typing import Any

from telegram import User as TelegramUser

from .base import BaseMessageGenerator


class RegistrationMessages(BaseMessageGenerator):
    """Generate registration-related messages."""

    def success(self, user_info: TelegramUser, birth_date: str) -> str:
        """Generate registration success message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :param birth_date: User's birth date as formatted string
        :type birth_date: str
        :returns: Localized registration success message with statistics
        :rtype: str
        """
        # Ensure profile is present (value unused)
        self.ensure_profile()
        stats: dict[str, Any] = self.life_stats()
        return self.build(
            key="registration.success",
            birth_date=birth_date,
            age=stats["age"],
            weeks_lived=stats["weeks_lived"],
            remaining_weeks=stats["remaining_weeks"],
            life_percentage=f"{float(stats['life_percentage']):.1%}",
        )

    def error(self, user_info: TelegramUser) -> str:
        """Generate registration error message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :returns: Localized registration error message
        :rtype: str
        """
        return self.build(key="registration.error")
