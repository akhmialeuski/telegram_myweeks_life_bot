from __future__ import annotations

from datetime import date
from typing import Any

from telegram import User as TelegramUser

from ...constants import DEFAULT_LIFE_EXPECTANCY
from .base import BaseMessageGenerator


class SettingsMessages(BaseMessageGenerator):
    """Generate settings-related messages and buttons."""

    def basic(self, user_info: TelegramUser) -> str:
        """Generate basic subscription settings message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :returns: Localized basic settings message
        :rtype: str
        """
        profile: Any = self.ensure_profile()
        birth_date = getattr(profile.settings, "birth_date", None)
        return self.build(
            key="settings.basic",
            birth_date=self.birth_date_str(birth_date),
            language_name=self.language_name(),
            life_expectancy=profile.settings.life_expectancy,
        )

    def premium(self, user_info: TelegramUser) -> str:
        """Generate premium subscription settings message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :returns: Localized premium settings message
        :rtype: str
        """
        profile: Any = self.ensure_profile()
        birth_date = getattr(profile.settings, "birth_date", None)
        return self.build(
            key="settings.premium",
            birth_date=self.birth_date_str(birth_date),
            language_name=self.language_name(),
            life_expectancy=profile.settings.life_expectancy,
        )

    def change_birth_date(self, user_info: TelegramUser) -> str:
        """Generate birth date change prompt message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :returns: Localized birth date change message
        :rtype: str
        """
        profile: Any = self.ensure_profile()
        current_birth_date = getattr(profile.settings, "birth_date", None)
        current_birth_date_str: str = (
            current_birth_date.strftime("%d.%m.%Y")
            if current_birth_date
            else self.ctx.builder.not_set()
        )
        return self.build(
            "settings.change_birth_date",
            current_birth_date=current_birth_date_str,
        )

    def change_language(self, user_info: TelegramUser) -> str:
        """Generate language change prompt message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :returns: Localized language change message
        :rtype: str
        """
        profile: Any = self.ensure_profile()
        current_language: str = (
            getattr(profile.settings, "language", None) or self.ctx.language
        )
        current_language_name: str = self.language_name(current_language)
        text: str = self.build(
            "settings.change_language",
            current_language=current_language_name,
        )
        if text == "settings.change_language" or not isinstance(text, str):
            text = self.build(key="buttons.change_language")
        return text

    def change_life_expectancy(self, user_info: TelegramUser) -> str:
        """Generate life expectancy change prompt message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :returns: Localized life expectancy change message
        :rtype: str
        """
        profile: Any = self.ensure_profile()
        current_life_expectancy: int = (
            getattr(profile.settings, "life_expectancy", None)
            or DEFAULT_LIFE_EXPECTANCY
        )
        return self.build(
            "settings.change_life_expectancy",
            current_life_expectancy=current_life_expectancy,
        )

    def birth_date_updated(
        self, user_info: TelegramUser, new_birth_date: date, new_age: int
    ) -> str:
        """Generate birth date updated success message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :param new_birth_date: New birth date
        :type new_birth_date: date
        :param new_age: New age calculated from birth date
        :type new_age: int
        :returns: Localized birth date updated message
        :rtype: str
        """
        new_birth_date_str: str = new_birth_date.strftime("%d.%m.%Y")
        return self.build(
            "settings.birth_date_updated",
            new_birth_date=new_birth_date_str,
            new_age=new_age,
        )

    def language_updated(self, user_info: TelegramUser, new_language: str) -> str:
        """Generate language updated success message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :param new_language: New language code or display name (kept for compatibility)
        :type new_language: str
        :returns: Localized language updated message
        :rtype: str
        """
        display_name: str = self.language_name()
        return self.build("settings.language_updated", new_language=display_name)

    def life_expectancy_updated(
        self, user_info: TelegramUser, new_life_expectancy: int
    ) -> str:
        """Generate life expectancy updated success message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :param new_life_expectancy: New life expectancy value
        :type new_life_expectancy: int
        :returns: Localized life expectancy updated message
        :rtype: str
        """
        return self.build(
            "settings.life_expectancy_updated",
            new_life_expectancy=new_life_expectancy,
        )

    def invalid_life_expectancy(self, user_info: TelegramUser) -> str:
        """Generate invalid life expectancy error message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :returns: Localized invalid life expectancy message
        :rtype: str
        """
        return self.build("settings.invalid_life_expectancy")

    def settings_error(self, user_info: TelegramUser) -> str:
        """Generate settings error message.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :returns: Localized settings error message
        :rtype: str
        """
        return self.build("settings.error")

    def buttons(self, user_info: TelegramUser) -> list[list[dict[str, str]]]:
        """Generate localized settings buttons.

        :param user_info: Telegram user
        :type user_info: TelegramUser
        :returns: List of inline keyboard button configs
        :rtype: list[list[dict[str, str]]]
        """
        try:
            birth_date_text: str = self.build(key="buttons.change_birth_date")
            language_text: str = self.build(key="buttons.change_language")
            life_expectancy_text: str = self.build(key="buttons.change_life_expectancy")
            if not all(
                isinstance(x, str)
                for x in (birth_date_text, language_text, life_expectancy_text)
            ):
                raise TypeError("button texts must be strings")
        except Exception:
            birth_date_text = self.build(key="buttons.change_birth_date")
            language_text = self.build(key="buttons.change_language")
            life_expectancy_text = self.build(key="buttons.change_life_expectancy")

        return [
            [{"text": birth_date_text, "callback_data": "settings_birth_date"}],
            [{"text": language_text, "callback_data": "settings_language"}],
            [
                {
                    "text": life_expectancy_text,
                    "callback_data": "settings_life_expectancy",
                }
            ],
        ]

    def birth_date_future_error(self, user_info: TelegramUser) -> str:
        """Generate error for future birth date."""
        return self.build(key="birth_date.future_error")

    def birth_date_old_error(self, user_info: TelegramUser) -> str:
        """Generate error for too old birth date."""
        return self.build(key="birth_date.old_error")

    def birth_date_format_error(self, user_info: TelegramUser) -> str:
        """Generate error for invalid birth date format."""
        return self.build(key="birth_date.format_error")
