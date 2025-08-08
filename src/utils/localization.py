"""Localization module for LifeWeeksBot.

This module contains all user-facing messages in multiple languages.
Supports Russian (ru), English (en), Ukrainian (ua), and Belarusian (by).
"""

from __future__ import annotations

import gettext
import logging
from enum import StrEnum, auto
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

LOGGER = logging.getLogger(__name__)

# Define locale directory and domain name constants
LOCALE_DIR = Path(__file__).resolve().parent.parent.parent / "locales"
DOMAIN = "messages"


@lru_cache(maxsize=None)
def get_translator(lang_code: str) -> Callable[[str], str]:
    """Get gettext translator for the specified language.

    Translation objects are cached to avoid repeated disk access.

    :param lang_code: Language code (ru, en, ua, by)
    :type lang_code: str
    :returns: gettext translator function
    :rtype: Callable[[str], str]
    """
    return gettext.translation(
        DOMAIN, localedir=LOCALE_DIR, languages=[lang_code], fallback=True
    ).gettext


@lru_cache(maxsize=None)
def get_translation(lang_code: str) -> gettext.NullTranslations:
    """Get gettext translations object for the specified language.

    This returns the translations object itself (not just ``gettext`` function),
    which allows advanced lookups like ``pgettext`` for contextual messages.
    Translation objects are cached for efficiency.

    :param lang_code: Language code (ru, en, ua, by)
    :type lang_code: str
    :returns: Translations object with gettext/pgettext available
    :rtype: gettext.NullTranslations
    """
    return gettext.translation(
        DOMAIN, localedir=LOCALE_DIR, languages=[lang_code], fallback=True
    )


class SupportedLanguage(StrEnum):
    RU = auto()
    EN = auto()
    UA = auto()
    BY = auto()

    @classmethod
    def list(cls) -> list[str]:
        return [lang.value for lang in cls]


# Supported languages
LANGUAGES = SupportedLanguage.list()

# Default language
DEFAULT_LANGUAGE = SupportedLanguage.RU.value

# Localized language names
_LANGUAGE_NAMES = {
    SupportedLanguage.RU.value: {
        SupportedLanguage.RU.value: "Русский",
        SupportedLanguage.EN.value: "Английский",
        SupportedLanguage.UA.value: "Украинский",
        SupportedLanguage.BY.value: "Белорусский",
    },
    SupportedLanguage.EN.value: {
        SupportedLanguage.RU.value: "Russian",
        SupportedLanguage.EN.value: "English",
        SupportedLanguage.UA.value: "Ukrainian",
        SupportedLanguage.BY.value: "Belarusian",
    },
    SupportedLanguage.UA.value: {
        SupportedLanguage.RU.value: "Російська",
        SupportedLanguage.EN.value: "Англійська",
        SupportedLanguage.UA.value: "Українська",
        SupportedLanguage.BY.value: "Білоруська",
    },
    SupportedLanguage.BY.value: {
        SupportedLanguage.RU.value: "Рускай",
        SupportedLanguage.EN.value: "Англійская",
        SupportedLanguage.UA.value: "Украінская",
        SupportedLanguage.BY.value: "Беларуская",
    },
}


def get_localized_language_name(language: str, target_language: str) -> str:
    """
    Get the localized name of a language in the target language.

    :param language: Language code to localize (e.g., 'en')
    :param target_language: Target language code (e.g., 'ru')
    :return: Localized language name
    """
    return _LANGUAGE_NAMES.get(target_language, {}).get(language, language)


def get_supported_languages() -> list[str]:
    """Get list of supported languages.

    :returns: List of supported language codes
    :rtype: list[str]
    """
    return LANGUAGES.copy()


def is_language_supported(language: str | None) -> bool:
    """Check if language is supported.

    :param language: Language code to check
    :type language: str | None
    :returns: True if language is supported, False otherwise
    :rtype: bool
    """
    return language in LANGUAGES


def get_message(
    message_key: str,
    sub_key: str,
    language: str | None = None,
    **kwargs,
) -> str:
    """Backward-compatible message lookup used in some tests.

    This helper emulates the previous ``get_message`` API by delegating to
    ``MessageBuilder.get`` for the handful of keys used in tests.

    :param message_key: Message group key (e.g., "common", "weeks", "visualize")
    :type message_key: str
    :param sub_key: Specific message key within the group (e.g., "not_registered")
    :type sub_key: str
    :param language: Optional language code; defaults to ``DEFAULT_LANGUAGE``
    :type language: str | None
    :returns: Localized message text
    :rtype: str
    """
    lang_code: str = language or DEFAULT_LANGUAGE
    builder: MessageBuilder = MessageBuilder(lang_code)

    key: str = f"{message_key}.{sub_key}"
    return builder.get(key, **kwargs)


class MessageBuilder:
    """Message builder class for generating localized messages using gettext.

    This class provides a facade for generating localized messages using
    the gettext system. It maintains backward compatibility with existing
    message generation functions while providing a cleaner interface.
    """

    def __init__(self, lang: str, default_lang: str = DEFAULT_LANGUAGE):
        """Initialize MessageBuilder with language and default fallback language.

        :param lang: Language code (ru, en, ua, by)
        :type lang: str
        :param default_lang: Fallback language code to use when translation is missing
        :type default_lang: str
        """
        self.lang: str = lang
        self.default_lang: str = default_lang
        self._: Callable[[str], str] = get_translator(lang)
        self._trans: gettext.NullTranslations = get_translation(lang)
        # Default (fallback) translator objects, typically English
        self._default: Callable[[str], str] = get_translator(default_lang)
        self._default_trans: gettext.NullTranslations = get_translation(default_lang)

    def _safe_format(self, template: str, kwargs: dict[str, Any] | None) -> str:
        """Safely format a template string with kwargs, falling back to the template if formatting fails.

        This method attempts to format the template with the provided kwargs, but if the template
        contains format placeholders that are not present in kwargs, it returns the template as-is
        instead of raising a KeyError or ValueError.

        :param template: Template string to format
        :type template: str
        :param kwargs: Formatting parameters
        :type kwargs: dict[str, Any] | None
        :returns: Formatted string or original template if formatting fails
        :rtype: str
        """
        if not kwargs:
            return template

        try:
            return template.format(**kwargs)
        except (KeyError, ValueError):
            # If formatting fails due to missing placeholders, return the template as-is
            return template

    def get(self, key: str, **kwargs: Any) -> str:
        """Get localized message by logical key with automatic fallback.

        Lookup order:
        1) Current language: gettext(key)
        2) Current language: pgettext(key, "") (context-as-key with empty id)
        3) Current language: pgettext(key, key) (context and id are the key)
        4) Fallback language (default en): same three strategies
        5) If still not found, return the key itself as a last resort

        Always applies ``str.format(**kwargs)`` when kwargs provided.

        :param key: Dotted logical key, e.g. ``weeks.statistics``
        :type key: str
        :returns: Localized and formatted message text
        :rtype: str
        """
        # Attempt to resolve in the current language first
        resolved: str | None = self._lookup_in_translations(
            key=key,
            gettext_fn=self._,
            translations=self._trans,
            kwargs=kwargs,
        )
        if resolved is not None:
            return resolved

        # Attempt to resolve in the fallback language next
        resolved_fallback: str | None = self._lookup_in_translations(
            key=key,
            gettext_fn=self._default,
            translations=self._default_trans,
            kwargs=kwargs,
        )
        if resolved_fallback is not None:
            return resolved_fallback

        # Final fallback: return the key itself, safely formatted if kwargs provided
        LOGGER.warning(
            "Missing translation for key '%s' in '%s' with fallback '%s'",
            key,
            self.lang,
            self.default_lang,
        )
        return self._safe_format(key, kwargs)

    def ngettext(
        self,
        singular_key: str,
        plural_key: str,
        n: int,
        *,
        context: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Return a pluralized message.

        Attempts to resolve the pluralized form in the current language and
        falls back to ``default_lang``. Contextual plural forms are supported
        via ``npgettext``.

        :param singular_key: Message key for singular form
        :param plural_key: Message key for plural form
        :param n: Count used to determine the plural form
        :param context: Optional context used for lookup
        :param kwargs: Additional keyword arguments for formatting
        :return: Localized pluralized message
        """

        def _lookup(translations: gettext.NullTranslations) -> str:
            if context:
                try:
                    return translations.npgettext(
                        context, singular_key, plural_key, n
                    )  # type: ignore[attr-defined]
                except Exception:
                    return ""
            return translations.ngettext(singular_key, plural_key, n)

        text = _lookup(self._trans)
        if not text or text in {singular_key, plural_key}:
            text = _lookup(self._default_trans)

        if not text or text in {singular_key, plural_key}:
            LOGGER.warning(
                "Missing plural translation for keys '%s'/'%s'",
                singular_key,
                plural_key,
            )
            text = singular_key if n == 1 else plural_key

        return text.format(n=n, **kwargs)

    def nget(self, singular: str, plural: str, n: int, **kwargs: Any) -> str:
        """Get localized pluralized message with automatic fallback.

        :param singular: Singular message identifier
        :type singular: str
        :param plural: Plural message identifier
        :type plural: str
        :param n: Quantity used to determine singular or plural form
        :type n: int
        :returns: Localized singular or plural message
        :rtype: str
        """
        text: str = self._trans.ngettext(singular, plural, n)
        if text in {singular, plural}:
            text = self._default_trans.ngettext(singular, plural, n)
        return text.format(**kwargs) if kwargs else text

    def pget(self, context: str, message: str, **kwargs: Any) -> str:
        """Get contextualized message with automatic fallback.

        :param context: Context identifier for the message
        :type context: str
        :param message: Message identifier within the context
        :type message: str
        :returns: Localized message string
        :rtype: str
        """

        text: str = self._trans.pgettext(context, message)
        if text == message:
            text = self._default_trans.pgettext(context, message)
            if text == message:
                LOGGER.warning(
                    "Missing contextual translation for '%s' in '%s' with fallback '%s'",
                    f"{context}:{message}",
                    self.lang,
                    self.default_lang,
                )
        return text.format(**kwargs) if kwargs else text

    def npget(
        self,
        context: str,
        singular: str,
        plural: str,
        n: int,
        **kwargs: Any,
    ) -> str:
        """Get contextualized pluralized message with automatic fallback.

        :param context: Context identifier for the message
        :type context: str
        :param singular: Singular form message identifier
        :type singular: str
        :param plural: Plural form message identifier
        :type plural: str
        :param n: Quantity used to determine singular or plural form
        :type n: int
        :returns: Localized singular or plural message
        :rtype: str
        """

        text: str = self._trans.npgettext(context, singular, plural, n)
        if text in {singular, plural}:
            text = self._default_trans.npgettext(context, singular, plural, n)
            if text in {singular, plural}:
                LOGGER.warning(
                    "Missing contextual plural translation for '%s' in '%s' with fallback '%s'",
                    context,
                    self.lang,
                    self.default_lang,
                )
        return text.format(**kwargs) if kwargs else text

    def __getattr__(self, name: str) -> Callable[..., str]:
        """Dynamically resolve unknown message methods to keys.

        Example: ``builder.weeks_statistics(age=...)`` → key ``weeks.statistics``
        and delegates to :py:meth:`get`.
        """

        def _wrapper(**kwargs: Any) -> str:
            dotted_key: str = name.replace("_", ".")
            return self.get(dotted_key, **kwargs)

        return _wrapper

    def _lookup_in_translations(
        self,
        *,
        key: str,
        gettext_fn: Callable[[str], str],
        translations: gettext.NullTranslations,
        kwargs: dict[str, Any] | None = None,
    ) -> str | None:
        """Try to resolve a key using provided translations and patterns.

        This helper reduces branching in :py:meth:`get` by centralizing the
        lookup patterns and formatting behavior.

        :param key: Dotted logical key to resolve
        :type key: str
        :param gettext_fn: ``gettext`` function for direct id lookup
        :type gettext_fn: Callable[[str], str]
        :param translations: Translations object to use for contextual lookups
        :type translations: gettext.NullTranslations
        :param kwargs: Optional formatting kwargs applied if text is found
        :type kwargs: dict[str, Any] | None
        :returns: Formatted text if found, otherwise ``None``
        :rtype: str | None
        """
        # Strategy 1: gettext id-as-key
        template: str = gettext_fn(key)
        if template and template != key:
            return self._safe_format(template, kwargs)

        # Strategy 2: pgettext with context=key and empty id
        try:
            ctx_text_empty: str = translations.pgettext(key, "")  # type: ignore[attr-defined]
        except Exception:
            ctx_text_empty = ""
        if ctx_text_empty:
            return self._safe_format(ctx_text_empty, kwargs)

        # Strategy 3: pgettext with context=key and id=key
        try:
            ctx_text_same: str = translations.pgettext(key, key)  # type: ignore[attr-defined]
        except Exception:
            ctx_text_same = ""
        if ctx_text_same and ctx_text_same != key:
            return self._safe_format(ctx_text_same, kwargs)

        return None
