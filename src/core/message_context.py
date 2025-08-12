"""Message context utilities for localized message rendering.

This module provides a per-request/task ``MessageContext`` that encapsulates
resolved user profile, language, and a per-language ``MessageBuilder``.

All message generation functions should assume that a context is already set
via :pyfunc:`use_message_context` at the entry point (e.g., a Telegram handler).
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Any, Iterator, Optional

from telegram import User as TelegramUser

from ..core.enums import SubscriptionType
from ..database.models.user import User
from ..utils.config import DEFAULT_LANGUAGE
from ..utils.localization import MessageBuilder

_CURRENT_CTX: ContextVar[Optional["MessageContext"]] = ContextVar(
    "_CURRENT_CTX", default=None
)


@dataclass(slots=True)
class MessageContext:
    """Per-call message rendering context.

    Encapsulates user profile retrieval, language resolution, and access to
    the per-language :pyclass:`MessageBuilder`.

    :param user_info: Telegram user object
    :type user_info: TelegramUser
    :param user_id: Telegram user id
    :type user_id: int
    :param user_profile: Optional resolved user profile
    :type user_profile: Optional[User]
    :param language: Resolved UI language code
    :type language: str
    :param builder: Localized message builder
    :type builder: MessageBuilder
    """

    user_info: TelegramUser
    user_id: int
    user_profile: Optional[User]
    language: str
    builder: MessageBuilder

    @classmethod
    def from_user(
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
            container.get_user_service().get_user_profile(telegram_id=user_info.id)
            if fetch_profile
            else None
        )
        language: str = cls._resolve_language(user_info=user_info, user_profile=profile)
        builder: MessageBuilder = container.get_message_builder(lang_code=language)
        return cls(
            user_info=user_info,
            user_id=user_info.id,
            user_profile=profile,
            language=language,
            builder=builder,
        )

    @classmethod
    def require(cls) -> "MessageContext":
        """Get current context or raise if missing.

        :returns: Current :pyclass:`MessageContext`
        :rtype: MessageContext
        :raises RuntimeError: If context is not set
        """
        ctx: Optional["MessageContext"] = _CURRENT_CTX.get()
        if ctx is None:
            raise RuntimeError(
                "MessageContext is not set. Use use_message_context(...) at entry points."
            )
        return ctx

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

    def ensure_profile(self) -> User:
        """Ensure user profile is present, fetching it if needed.

        :returns: Resolved user profile
        :rtype: User
        :raises ValueError: When user profile does not exist
        """
        if self.user_profile is None:
            from ..services.container import ServiceContainer

            profile: Optional[User] = (
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

    def life_stats(self) -> dict[str, Any]:
        """Compute life statistics for the current user.

        :returns: Life statistics dict
        :rtype: dict[str, Any]
        :raises ValueError: When user profile is missing
        """
        from ..services.container import ServiceContainer

        profile: User = self.ensure_profile()
        calc_cls = ServiceContainer().get_life_calculator()
        engine = calc_cls(user=profile)
        return engine.get_life_statistics()

    def subscription_type_value(self) -> str:
        """Get current subscription type value with basic fallback.

        :returns: Subscription type value
        :rtype: str
        """
        profile: Optional[User] = self.user_profile
        if profile and profile.subscription:
            return profile.subscription.subscription_type.value
        return SubscriptionType.BASIC.value


@contextmanager
def use_message_context(
    user_info: TelegramUser, *, fetch_profile: bool
) -> Iterator[MessageContext]:
    """Context manager that sets per-task :pyclass:`MessageContext`.

    :param user_info: Telegram user object
    :type user_info: TelegramUser
    :param fetch_profile: Whether to fetch user profile
    :type fetch_profile: bool
    :returns: Iterator yielding the created context
    :rtype: Iterator[MessageContext]
    """
    ctx: MessageContext = MessageContext.from_user(
        user_info=user_info, fetch_profile=fetch_profile
    )
    token: Token = _CURRENT_CTX.set(ctx)
    try:
        yield ctx
    finally:
        _CURRENT_CTX.reset(token)
