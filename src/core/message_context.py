"""Message context utilities for localized message rendering.

This module provides a per-request/task ``MessageContext`` that encapsulates
resolved user profile and language.

All message generation functions should assume that a context is already set
via :pyfunc:`use_message_context` at the entry point (e.g., a Telegram handler).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import AsyncIterator, Optional

from telegram import User as TelegramUser

from ..database.models.user import User
from ..utils.config import DEFAULT_LANGUAGE

_CURRENT_CTX: ContextVar[Optional["MessageContext"]] = ContextVar(
    "_CURRENT_CTX", default=None
)


@dataclass(slots=True)
class MessageContext:
    """Per-call message rendering context.

    Encapsulates user profile retrieval and language resolution.

    :param user_info: Telegram user object
    :type user_info: TelegramUser
    :param user_id: Telegram user id
    :type user_id: int
    :param user_profile: Optional resolved user profile
    :type user_profile: Optional[User]
    :param language: Resolved UI language code
    :type language: str
    """

    user_info: TelegramUser
    user_id: int
    user_profile: Optional[User]
    language: str

    @classmethod
    async def from_user(
        cls, user_info: TelegramUser, *, fetch_profile: bool
    ) -> "MessageContext":
        """Build context for a user.

        :param user_info: Telegram user object
        :type user_info: TelegramUser
        :param fetch_profile: Whether to fetch user profile
        :type fetch_profile: bool
        :returns: Initialized message context
        :rtype: MessageContext
        """
        from ..services.container import ServiceContainer

        container: ServiceContainer = ServiceContainer()
        profile: Optional[User] = (
            await container.get_user_service().get_user_profile(
                telegram_id=user_info.id
            )
            if fetch_profile
            else None
        )
        language: str = cls._resolve_language(user_info=user_info, user_profile=profile)
        return cls(
            user_info=user_info,
            user_id=user_info.id,
            user_profile=profile,
            language=language,
        )

    @staticmethod
    def _resolve_language(user_info: TelegramUser, user_profile: Optional[User]) -> str:
        """Resolve UI language from profile or Telegram fallback.

        :param user_info: Telegram user object
        :type user_info: TelegramUser
        :param user_profile: Optional user profile
        :type user_profile: Optional[User]
        :returns: Language code
        :rtype: str
        """
        if user_profile and user_profile.settings and user_profile.settings.language:
            return user_profile.settings.language
        return user_info.language_code or DEFAULT_LANGUAGE

    async def ensure_profile(self) -> User:
        """Ensure user profile is present, fetching it if needed.

        :returns: Resolved user profile
        :rtype: User
        :raises ValueError: When user profile does not exist
        """
        if self.user_profile is None:
            from ..services.container import ServiceContainer

            profile: Optional[User] = await (
                ServiceContainer()
                .get_user_service()
                .get_user_profile(telegram_id=self.user_info.id)
            )
            if profile is None:
                raise ValueError(
                    f"User profile not found for telegram_id: {self.user_info.id}"
                )
            self.user_profile = profile
        return self.user_profile


@asynccontextmanager
async def use_message_context(
    user_info: TelegramUser, *, fetch_profile: bool
) -> AsyncIterator[MessageContext]:
    """Async context manager that sets per-task :pyclass:`MessageContext`.

    :param user_info: Telegram user object
    :type user_info: TelegramUser
    :param fetch_profile: Whether to fetch user profile
    :type fetch_profile: bool
    :returns: AsyncIterator yielding the created context
    :rtype: AsyncIterator[MessageContext]
    """
    ctx: MessageContext = await MessageContext.from_user(
        user_info=user_info, fetch_profile=fetch_profile
    )
    token: Token = _CURRENT_CTX.set(ctx)
    try:
        yield ctx
    finally:
        _CURRENT_CTX.reset(token)
