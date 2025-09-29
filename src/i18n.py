import gettext
from pathlib import Path
from typing import Final

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
