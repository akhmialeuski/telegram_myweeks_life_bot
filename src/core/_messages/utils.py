from __future__ import annotations

from typing import Any

from telegram import User as TelegramUser

from ...utils.config import DEFAULT_LANGUAGE


def get_user_language(user_info: TelegramUser, user_profile: Any | None = None) -> str:
    """Get user's language preference from database or fallback to Telegram language.

    :param user_info: Telegram user object
    :type user_info: TelegramUser
    :param user_profile: Optional user profile from database (to avoid extra queries)
    :type user_profile: Any | None
    :returns: Language code (ru, en, ua, by)
    :rtype: str
    """
    if (
        user_profile
        and getattr(user_profile, "settings", None)
        and user_profile.settings.language
    ):
        return user_profile.settings.language

    if not user_profile:
        from ...database.service import user_service

        user_profile = user_service.get_user_profile(telegram_id=user_info.id)

    if (
        user_profile
        and getattr(user_profile, "settings", None)
        and user_profile.settings.language
    ):
        return user_profile.settings.language

    return user_info.language_code or DEFAULT_LANGUAGE
