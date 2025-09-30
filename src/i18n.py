import gettext
from pathlib import Path
from typing import Any, Final

try:  # pragma: no cover - optional dependency at runtime
    from babel import Locale
    from babel.core import UnknownLocaleError
except ModuleNotFoundError:  # pragma: no cover - fallback when Babel missing
    Locale = None

    class UnknownLocaleError(Exception):
        """Fallback exception when Babel is not installed."""


DOMAIN: Final[str] = "messages"
LOCALE_DIR: Final[Path] = Path(__file__).resolve().parents[1] / "locales"


def get_translator(lang: str):
    """Загрузить перевод для языка lang с английским запасным вариантом."""
    try:
        return gettext.translation(DOMAIN, localedir=LOCALE_DIR, languages=[lang])
    except OSError:
        return gettext.translation(
            DOMAIN, localedir=LOCALE_DIR, languages=["en"], fallback=True
        )


def use_locale(lang: str):
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
    """Return a human-readable language name localized for the user."""

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

    :param locale_str: Locale string to parse
    :type locale_str: str
    :returns: Parsed locale object or None if parsing fails
    :rtype: Any | None
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

    :param locale_obj: Locale object to query
    :type locale_obj: Any
    :param language_code: Language code to look up
    :type language_code: str
    :returns: Language name or None if not found
    :rtype: str | None
    """
    try:
        return locale_obj.get_language_name(language_code)
    except (LookupError, ValueError, UnknownLocaleError):
        return None


def _get_language_name_from_dict(locale_obj: Any, language_code: str) -> str | None:
    """Get language name from locale's languages dictionary.

    :param locale_obj: Locale object to query
    :type locale_obj: Any
    :param language_code: Language code to look up
    :type language_code: str
    :returns: Language name or None if not found
    :rtype: str | None
    """
    languages = getattr(locale_obj, "languages", None)
    if isinstance(languages, dict):
        return languages.get(language_code)
    return None


def _get_display_name_fallback(locale_obj: Any, language_code: str) -> str | None:
    """Get display name as final fallback.

    :param locale_obj: Locale object to query
    :type locale_obj: Any
    :param language_code: Language code to look up
    :type language_code: str
    :returns: Display name or None if not found
    :rtype: str | None
    """
    try:
        language_locale = Locale.parse(language_code)
        return language_locale.get_display_name(locale_obj)
    except (ValueError, UnknownLocaleError):
        return None
