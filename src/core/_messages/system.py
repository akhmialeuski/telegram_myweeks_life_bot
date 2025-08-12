from __future__ import annotations

from telegram import User as TelegramUser

from .base import BaseMessageGenerator


class SystemMessages(BaseMessageGenerator):
    """Generate system/help/start/unknown messages."""

    def help(self, user_info: TelegramUser) -> str:
        """Generate help message."""
        return self.build(key="help.text")

    def unknown(self, user_info: TelegramUser) -> str:
        """Generate unknown command/message error."""
        return self.build("unknown.command")

    def welcome_existing(self, user_info: TelegramUser) -> str:
        """Generate welcome message for existing users."""
        return self.build("start.welcome_existing", first_name=user_info.first_name)

    def welcome_new(self, user_info: TelegramUser) -> str:
        """Generate welcome message for new users."""
        return self.build("start.welcome_new", first_name=user_info.first_name)
