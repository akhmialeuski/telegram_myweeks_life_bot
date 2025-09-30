import gettext
from pathlib import Path
from typing import Any, Callable, Final

try:  # pragma: no cover - optional dependency at runtime
    from babel import Locale
    from babel.core import UnknownLocaleError
except ModuleNotFoundError:  # pragma: no cover - fallback when Babel missing
    Locale = None

    class UnknownLocaleError(Exception):
        """Fallback exception when Babel is not installed."""


"""Internationalization utilities for the Telegram bot.

This module provides functions for loading and managing translations
for the multi-language Telegram bot supporting Russian, English,
Ukrainian, and Belarusian languages.
"""

DOMAIN: Final[str] = "messages"
"""Gettext domain name for translation catalogs.

This constant defines the domain name used for gettext translation
catalogs. All translation files (.mo files) should use this domain.

:type: Final[str]
"""

LOCALE_DIR: Final[Path] = Path(__file__).resolve().parents[1] / "locales"
"""Directory containing translation files.

This constant specifies the path to the locales directory containing
translation catalogs (.mo files) for all supported languages.

:type: Final[Path]
"""


def get_translator(lang: str) -> gettext.NullTranslations:
    """Load translation for the specified language with English fallback.

    This function loads gettext translation catalog for the given language
    code. If the requested language catalog is not found, it falls back
    to the English translation catalog.

    :param lang: Language code (e.g., 'ru', 'en', 'ua', 'by')
    :type lang: str
    :returns: Translation object for the specified language
    :rtype: gettext.NullTranslations
    :raises OSError: If translation files cannot be loaded
    """
    try:
        return gettext.translation(DOMAIN, localedir=LOCALE_DIR, languages=[lang])
    except OSError:
        return gettext.translation(
            DOMAIN, localedir=LOCALE_DIR, languages=["en"], fallback=True
        )


def use_locale(
    lang: str,
) -> tuple[
    Callable[[str], str], Callable[[str, str, int], str], Callable[[str, str], str]
]:
    """Install and return translation functions for the specified language.

    This function installs the translation functions into Python builtins
    and returns them for direct use. The installed functions include:
    - `_` (gettext) for basic message translation
    - `ngettext` for pluralized message translation
    - `pgettext` for contextual message translation

    :param lang: Language code (e.g., 'ru', 'en', 'ua', 'by')
    :type lang: str
    :returns: Tuple of (gettext_func, ngettext_func, pgettext_func)
    :rtype: tuple[Callable[[str], str], Callable[[str, str, int], str], Callable[[str, str], str]]
    """
    translator = get_translator(lang)
    translator.install()  # installs `_`, `ngettext`, `pgettext` into builtins
    return translator.gettext, translator.ngettext, translator.pgettext


def normalize_babel_locale(lang: str) -> str:
    """Normalize project language codes to Babel/CLDR locale codes.

    This helper converts internal language codes like 'ua' and 'by' used
    in project and gettext catalogs to standard CLDR locale identifiers
    expected by Babel formatting functions.

    :param lang: Language code from DB or Telegram (e.g., 'ru', 'en', 'ua', 'by')
    :type lang: str
    :returns: Normalized locale code compatible with Babel (e.g., 'uk', 'be')
    :rtype: str
    """
    mapping = {
        "ua": "uk",  # Ukrainian
        "by": "be",  # Belarusian
        "ru": "ru",
        "en": "en",
    }
    code = (lang or "en").lower()
    return mapping.get(code, code)


def get_localized_language_name(
    language_code: str | None,
    display_locale: str | None,
) -> str:
    """Return a human-readable language name localized for the user.

    This function attempts to get the localized name of a language in the
    specified display locale. It uses multiple fallback strategies including
    direct Babel lookups, dictionary-based lookups, and display name fallbacks.

    :param language_code: The language code to get name for (e.g., 'en', 'ru')
    :type language_code: str | None
    :param display_locale: The locale to display the name in (e.g., 'ru', 'en')
    :type display_locale: str | None
    :returns: Localized language name with first letter capitalized
    :rtype: str
    """

    normalized_language = normalize_babel_locale(language_code or "") or "en"
    normalized_display = normalize_babel_locale(display_locale or "") or "en"

    if Locale is None:
        return language_code or normalized_language

    # Try to get language name with fallbacks
    name = _get_language_name_with_fallbacks(normalized_language, normalized_display)

    if isinstance(name, str) and name:
        return name[:1].upper() + name[1:]

    return language_code or normalized_language


def _get_language_name_with_fallbacks(
    language_code: str, display_locale: str
) -> str | None:
    """Get language name with multiple fallback strategies.

    :param language_code: The language code to get name for
    :type language_code: str
    :param display_locale: The locale to display the name in
    :type display_locale: str
    :returns: Localized language name or None if not found
    :rtype: str | None
    """
    locale_obj = _parse_locale_safely(display_locale)
    if not locale_obj:
        return None

    # Try direct language name lookup
    name = _get_language_name_direct(locale_obj, language_code)
    if name:
        return name

    # Try from locale languages dictionary
    name = _get_language_name_from_dict(locale_obj, language_code)
    if name:
        return name

    # Try display name lookup
    name = _get_display_name_fallback(locale_obj, language_code)
    if name:
        return name

    return None


def _parse_locale_safely(locale_str: str) -> Any | None:
    """Parse locale string with error handling.

    This function safely parses a locale string using Babel's Locale.parse()
    method. If parsing fails, it attempts to fall back to English locale.
    If that also fails, it returns None.

    :param locale_str: Locale string to parse (e.g., 'ru', 'en', 'uk')
    :type locale_str: str
    :returns: Parsed locale object or None if parsing fails
    :rtype: Any | None
    :raises ValueError: If locale string format is invalid
    :raises UnknownLocaleError: If locale is not recognized by Babel
    """
    try:
        return Locale.parse(locale_str)
    except (ValueError, UnknownLocaleError):
        try:
            return Locale.parse("en")
        except (ValueError, UnknownLocaleError):
            return None


def _get_language_name_direct(locale_obj: Any, language_code: str) -> str | None:
    """Get language name directly from locale object.

    This function attempts to get the language name using Babel's
    get_language_name() method, which provides the most direct lookup.

    :param locale_obj: Locale object to query for language names
    :type locale_obj: Any
    :param language_code: Language code to look up (e.g., 'en', 'ru')
    :type language_code: str
    :returns: Language name in the locale's language or None if not found
    :rtype: str | None
    :raises LookupError: If language code is not found in locale data
    :raises ValueError: If language code format is invalid
    :raises UnknownLocaleError: If locale object is in an invalid state
    """
    try:
        return locale_obj.get_language_name(language_code)
    except (LookupError, ValueError, UnknownLocaleError):
        return None


def _get_language_name_from_dict(locale_obj: Any, language_code: str) -> str | None:
    """Get language name from locale's languages dictionary.

    This function attempts to get the language name from the locale object's
    internal languages dictionary, which may contain additional language
    mappings not available through the standard get_language_name() method.

    :param locale_obj: Locale object to query for language names
    :type locale_obj: Any
    :param language_code: Language code to look up (e.g., 'en', 'ru')
    :type language_code: str
    :returns: Language name from dictionary or None if not found
    :rtype: str | None
    """
    languages = getattr(locale_obj, "languages", None)
    if isinstance(languages, dict):
        return languages.get(language_code)
    return None


def _get_display_name_fallback(locale_obj: Any, language_code: str) -> str | None:
    """Get display name as final fallback.

    This function attempts to get the display name of a language by parsing
    the language code as a locale and getting its display name in the target
    locale. This is the final fallback strategy when other methods fail.

    :param locale_obj: Locale object to query for display names
    :type locale_obj: Any
    :param language_code: Language code to look up (e.g., 'en', 'ru')
    :type language_code: str
    :returns: Display name of the language or None if not found
    :rtype: str | None
    :raises ValueError: If language code format is invalid for locale parsing
    :raises UnknownLocaleError: If language code is not recognized as a valid locale
    """
    try:
        language_locale = Locale.parse(language_code)
        return language_locale.get_display_name(locale_obj)
    except (ValueError, UnknownLocaleError):
        return None
