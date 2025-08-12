from __future__ import annotations

from datetime import date
from typing import Any

from ...utils.localization import get_localized_language_name
from ..enums import SubscriptionType
from ..message_context import MessageContext


class BaseMessageGenerator:
    """Common helpers for message generation.

    Provides access to MessageContext and helper formatting utilities.
    """

    @property
    def ctx(self) -> MessageContext:
        """Get required message context.

        :returns: Active message context
        :rtype: MessageContext
        :raises RuntimeError: If context is not initialized
        """
        return MessageContext.require()

    def ensure_profile(self) -> Any:
        """Ensure user profile is loaded.

        :returns: User profile object
        :rtype: Any
        """
        return self.ctx.ensure_profile()

    def life_stats(self) -> dict[str, Any]:
        """Get life statistics calculated for current user.

        :returns: Life statistics dictionary
        :rtype: dict[str, Any]
        """
        return self.ctx.life_stats()

    def format_life_percentage(self, value: float | None = None) -> str:
        """Format life percentage as human readable string.

        :param value: Optional precomputed value in range [0,1]
        :type value: float | None
        :returns: Percentage formatted string like '12.3%'
        :rtype: str
        """
        if value is None:
            value = float(self.life_stats()["life_percentage"])  # type: ignore[call-overload]
        return f"{value:.1%}"

    def language_name(self, language: str | None = None) -> str:
        """Get localized language display name.

        :param language: Language code to display, defaults to context language
        :type language: str | None
        :returns: Localized language name
        :rtype: str
        """
        lang: str = language or self.ctx.language
        return get_localized_language_name(lang, lang)

    def birth_date_str(self, d: date | None) -> str:
        """Format birth date or return 'not set' fallback.

        :param d: Date value or None
        :type d: date | None
        :returns: Formatted date DD.MM.YYYY or localization fallback
        :rtype: str
        """
        if d:
            return d.strftime("%d.%m.%Y")
        return self.ctx.builder.not_set()

    def subscription_type_value(self) -> str:
        """Return current subscription type value or BASIC.

        :returns: Subscription type as string
        :rtype: str
        """
        profile: Any | None = getattr(self.ctx, "user_profile", None)
        if profile and getattr(profile, "subscription", None):
            return profile.subscription.subscription_type.value
        return SubscriptionType.BASIC.value

    def build(self, key: str, **kwargs: Any) -> str:
        """Render localized string via message builder.

        :param key: Localization key
        :type key: str
        :returns: Localized string
        :rtype: str
        """
        return self.ctx.builder.get(key=key, **kwargs)
