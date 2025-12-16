"""Adapter for I18nServiceProtocol using Babel-based i18n module.

This module provides an adapter that implements the I18nServiceProtocol
using the application's existing Babel-based internationalization system.
"""

from typing import Any

from src.core.messages import I18nServiceProtocol
from src.i18n import use_locale


class BabelI18nAdapter(I18nServiceProtocol):
    """Adapter for I18nServiceProtocol using Babel."""

    def __init__(self, lang: str) -> None:
        """Initialize the adapter with a language code.

        :param lang: Language code (e.g., 'en', 'ru')
        :type lang: str
        """
        _, _, self._pgettext = use_locale(lang)

    def translate(self, key: str, default: str, **kwargs: Any) -> str:
        """Translate a message key with arguments.

        :param key: Message key (context for pgettext)
        :type key: str
        :param default: Default message text (msgid for pgettext)
        :type default: str
        :param kwargs: Arguments for string formatting
        :type kwargs: Any
        :returns: Localized and formatted string
        :rtype: str
        """
        message = self._pgettext(key, default)
        if not kwargs:
            return message

        # Try % formatting first if legacy style is present
        if "%(" in message:
            return message % kwargs

        # Otherwise try .format() for modern style
        try:
            return message.format(**kwargs)
        except KeyError:
            # Fallback for mixed or problematic strings, try % as last resort
            # or return unformatted to avoid crashing
            try:
                return message % kwargs
            except (ValueError, TypeError):
                return message
