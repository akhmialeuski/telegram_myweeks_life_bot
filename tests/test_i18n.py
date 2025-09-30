"""Tests for localization helpers."""

from unittest.mock import MagicMock, patch

import src.i18n as i18n


class TestGetLocalizedLanguageName:
    """Tests for get_localized_language_name helper."""

    def test_returns_localized_name_when_babel_available(self):
        """Should return localized language name when Locale works."""

        fake_display_locale = MagicMock()
        fake_display_locale.languages = {"en": "английский"}
        fake_display_locale.get_language_name.return_value = "английский"

        fake_language_locale = MagicMock()
        fake_language_locale.get_display_name.return_value = "английский"

        locale_mock = MagicMock()
        locale_mock.parse.side_effect = [fake_display_locale, fake_language_locale]

        with patch.object(i18n, "Locale", locale_mock):
            result = i18n.get_localized_language_name("en", "ru")

        assert result == "Английский"
        locale_mock.parse.assert_called_with("ru")

    def test_returns_fallback_when_parsing_fails(self):
        """Should gracefully fallback when Locale parsing fails."""

        locale_mock = MagicMock()
        locale_mock.parse.side_effect = ValueError("bad locale")

        with patch.object(i18n, "Locale", locale_mock):
            assert i18n.get_localized_language_name("en", "xx") == "en"
