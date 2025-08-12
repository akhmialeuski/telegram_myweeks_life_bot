from __future__ import annotations

from typing import Any

from telegram import User as TelegramUser

from .base import BaseMessageGenerator


class VisualizeMessages(BaseMessageGenerator):
    """Generate visualization info messages."""

    def generate(self, user_info: TelegramUser) -> str:
        """Generate visualization message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :returns: Localized visualization message
        :rtype: str
        """
        stats: dict[str, Any] = self.life_stats()
        return self.build(
            key="visualize.info",
            age=stats["age"],
            weeks_lived=stats["weeks_lived"],
            life_percentage=f"{float(stats['life_percentage']):.1%}",
        )
