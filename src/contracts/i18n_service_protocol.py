"""I18n Service Protocol for localization operations.

This module defines the contract for internationalization services.
The I18nService implementation provides translation functionality
based on gettext with babel locale support.
"""

from typing import Callable, Protocol, runtime_checkable


@runtime_checkable
class I18nServiceProtocol(Protocol):
    """Service contract for internationalization operations.

    This protocol defines the interface for localization services,
    providing methods to get translated strings and locale utilities.

    Implementations:
        - I18nService: Production implementation using gettext/babel
        - FakeI18nService: In-memory implementation for testing
    """

    def get_translator(self, lang: str) -> object:
        """Load translation for the specified language.

        :param lang: Language code (e.g., 'en', 'ru')
        :type lang: str
        :returns: gettext NullTranslations object
        :rtype: object
        """
        ...

    def use_locale(
        self,
        lang: str,
    ) -> tuple[
        Callable[[str], str],
        Callable[[str, str, int], str],
        Callable[[str, str], str],
    ]:
        """Install and return translation functions for the specified language.

        :param lang: Language code (e.g., 'en', 'ru')
        :type lang: str
        :returns: Tuple of (gettext, ngettext, pgettext) translation functions
        :rtype: tuple[Callable, Callable, Callable]
        """
        ...

    def get_localized_language_name(
        self,
        lang_code: str,
        display_locale: str | None = None,
    ) -> str:
        """Get the localized name of a language.

        :param lang_code: Language code to get name for
        :type lang_code: str
        :param display_locale: Locale to display the name in (optional)
        :type display_locale: str | None
        :returns: Localized language name
        :rtype: str
        """
        ...

    def normalize_babel_locale(self, lang: str) -> str:
        """Normalize language code for babel compatibility.

        :param lang: Language code to normalize
        :type lang: str
        :returns: Normalized locale string
        :rtype: str
        """
        ...
