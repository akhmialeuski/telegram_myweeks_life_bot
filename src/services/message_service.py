"""Message service for caching and retrieving MessageBuilder instances.

This module provides a lightweight service that manages per-language
``MessageBuilder`` instances with simple in-memory caching. It avoids
re-creating builders for the same language across calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from ..utils.config import DEFAULT_LANGUAGE
from ..utils.localization import MessageBuilder, get_supported_languages


@dataclass(slots=True)
class MessageService:
    """Service responsible for creating and caching ``MessageBuilder`` instances.

    The service keeps a cache of builders by language and validates that
    requested languages are supported, falling back to ``DEFAULT_LANGUAGE``
    if needed.
    """

    _cache: Dict[str, MessageBuilder] = field(default_factory=dict)

    def get_builder(self, lang_code: str = DEFAULT_LANGUAGE) -> MessageBuilder:
        """Get cached ``MessageBuilder`` for a language, creating if missing.

        :param lang_code: IETF language tag, use values from ``SupportedLanguage``
        :type lang_code: str
        :returns: Builder configured for the language
        :rtype: MessageBuilder
        """
        normalized_lang: str
        try:
            if hasattr(lang_code, "value"):
                normalized_lang = str(getattr(lang_code, "value"))
            elif isinstance(lang_code, str):
                normalized_lang = lang_code
            else:
                normalized_lang = DEFAULT_LANGUAGE
        except Exception:
            normalized_lang = DEFAULT_LANGUAGE

        try:
            supported_languages = get_supported_languages()
            if normalized_lang not in supported_languages:
                normalized_lang = DEFAULT_LANGUAGE
        except Exception:
            normalized_lang = DEFAULT_LANGUAGE

        cached = self._cache.get(normalized_lang)
        if cached is not None:
            return cached

        builder = MessageBuilder(normalized_lang)
        self._cache[normalized_lang] = builder
        return builder
