from __future__ import annotations

from telegram import User as TelegramUser

from .base import BaseMessageGenerator


class CancelMessages(BaseMessageGenerator):
    """Generate account cancellation messages."""

    def success(self, user_info: TelegramUser, language: str | None = None) -> str:
        """Generate cancel success message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :param language: Optional language code (kept for compatibility)
        :type language: str | None
        :returns: Localized cancel success message
        :rtype: str
        """
        return self.build("cancel.success", first_name=user_info.first_name)

    def error(self, user_info: TelegramUser) -> str:
        """Generate cancel error message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :returns: Localized cancel error message
        :rtype: str
        """
        return self.build("cancel.error", first_name=user_info.first_name)
