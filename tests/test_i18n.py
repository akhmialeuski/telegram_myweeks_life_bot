"""Tests for localization helpers.

This module contains tests for i18n utility functions, particularly
the get_localized_language_name helper function.
"""

from unittest.mock import MagicMock, patch

import src.i18n as i18n


class TestGetLocalizedLanguageName:
    """Test suite for get_localized_language_name function.

    This class contains tests verifying that language names are properly
    localized using Babel's Locale functionality with appropriate fallbacks.
    """

    def test_returns_localized_name_when_babel_available(self) -> None:
        """Test that localized language name is returned when Babel Locale works.

        This test verifies that the function correctly uses Babel's Locale
        to get the localized language name and capitalizes it properly.

        :returns: None
        :rtype: None
        """
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

    def test_returns_fallback_when_parsing_fails(self) -> None:
        """Test that fallback language code is returned when Locale parsing fails.

        This test verifies graceful error handling when Babel Locale
        cannot parse the display language code, returning the original
        language code as fallback.

        :returns: None
        :rtype: None
        """
        locale_mock = MagicMock()
        locale_mock.parse.side_effect = ValueError("bad locale")

        with patch.object(i18n, "Locale", locale_mock):
            assert i18n.get_localized_language_name("en", "xx") == "en"
