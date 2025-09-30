import gettext
from pathlib import Path
from typing import Final

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
    translator.install()  # устанавливает `_`, `ngettext`, `pgettext` в builtins
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

    try:
        locale_obj = Locale.parse(normalized_display)
    except (ValueError, UnknownLocaleError):
        try:
            locale_obj = Locale.parse("en")
        except (ValueError, UnknownLocaleError):
            return language_code or normalized_language

    name = None

    try:
        name = locale_obj.get_language_name(normalized_language)
    except (LookupError, ValueError, UnknownLocaleError):
        name = None

    if not name:
        languages = getattr(locale_obj, "languages", None)
        if isinstance(languages, dict):
            name = languages.get(normalized_language)

    if not name:
        try:
            language_locale = Locale.parse(normalized_language)
            name = language_locale.get_display_name(locale_obj)
        except (ValueError, UnknownLocaleError):
            name = None

    if isinstance(name, str) and name:
        return name[:1].upper() + name[1:]

    return language_code or normalized_language
