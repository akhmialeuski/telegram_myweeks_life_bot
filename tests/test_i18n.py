"""Unit tests for i18n module.

Tests translation loading, locale normalization, and language name resolution.
"""

from unittest.mock import MagicMock, patch

import pytest
from babel import Locale

from src import i18n
from src.i18n import (
    get_localized_language_name,
    get_translator,
    normalize_babel_locale,
    use_locale,
)


class TestI18n:
    """Test suite for i18n module."""

    @patch("src.i18n.gettext.translation")
    def test_get_translator_success(self, mock_translation):
        """Test successful translator loading."""
        mock_trans = MagicMock()
        mock_translation.return_value = mock_trans

        result = get_translator("en")

        assert result == mock_trans
        mock_translation.assert_called_with(
            i18n.DOMAIN, localedir=i18n.LOCALE_DIR, languages=["en"]
        )

    @patch("src.i18n.gettext.translation")
    def test_get_translator_fallback(self, mock_translation):
        """Test fallback to english when translation fails."""
        mock_translation.side_effect = [OSError("fail"), MagicMock()]

        get_translator("xx")

        # Second call should be fallback
        assert mock_translation.call_count == 2
        mock_translation.assert_called_with(
            i18n.DOMAIN, localedir=i18n.LOCALE_DIR, languages=["en"], fallback=True
        )

    @patch("src.i18n.get_translator")
    def test_use_locale(self, mock_get_translator):
        """Test use_locale installs and returns functions."""
        mock_trans = MagicMock()
        mock_trans.gettext = "gettext"
        mock_trans.ngettext = "ngettext"
        mock_trans.pgettext = "pgettext"
        mock_get_translator.return_value = mock_trans

        funcs = use_locale("en")

        mock_trans.install.assert_called_once()
        assert funcs == ("gettext", "ngettext", "pgettext")

    @pytest.mark.parametrize(
        "input_lang,expected",
        [
            ("ua", "uk"),
            ("by", "be"),
            ("ru", "ru"),
            ("en", "en"),
            ("UK", "uk"),
            ("unknown", "unknown"),
            (None, "en"),
        ],
    )
    def test_normalize_babel_locale(self, input_lang, expected):
        """Test locale normalization."""
        assert normalize_babel_locale(input_lang) == expected

    @patch("src.i18n.Locale")
    def test_get_localized_language_name_direct(self, mock_locale_cls):
        """Test getting name using Babel directly."""
        mock_locale_instance = MagicMock()
        mock_locale_instance.get_language_name.return_value = "Russian"

        # Setup Locale.parse to return our mock
        mock_locale_cls.parse.return_value = mock_locale_instance

        # We need to mock _parse_locale_safely or let it use the mocked Locale.parse
        # Since _parse_locale_safely uses Locale.parse, patching Locale class is enough

        # 'ru' name in 'en' locale is 'Russian'
        name = get_localized_language_name("ru", "en")

        assert name == "Russian"
        mock_locale_cls.parse.assert_called_with("en")
        mock_locale_instance.get_language_name.assert_called_with("ru")

    def test_get_localized_language_name_dict_fallback(self):
        """Test getting name from locale dict methods."""

        mock_locale = MagicMock()
        mock_locale.languages = {"ex": "Example"}
        # Ensure get_language_name raises LookupError to trigger fallback
        mock_locale.get_language_name.side_effect = LookupError

        with patch("src.i18n._parse_locale_safely", return_value=mock_locale):
            name = i18n._get_language_name_with_fallbacks("ex", "en")
            assert name == "Example"

    def test_get_localized_language_name_invalid_locale_fallback(self):
        """Test fallback when display locale is invalid."""
        with patch("src.i18n._parse_locale_safely", return_value=None):
            name = get_localized_language_name("ru", "invalid")
            assert name == "ru"

    def test_parse_locale_safely_valid(self):
        """Test parsing valid locale."""
        loc = i18n._parse_locale_safely("en")
        assert str(loc) == "en"

    def test_parse_locale_safely_retry_en(self):
        """Test fallback to en when parsing fails."""
        # Mock Locale.parse to fail first time
        with patch.object(Locale, "parse", side_effect=[ValueError, Locale("en")]):
            loc = i18n._parse_locale_safely("invalid")
            assert str(loc) == "en"

    def test_parse_locale_safely_failure(self):
        """Test total failure in parsing."""
        with patch.object(Locale, "parse", side_effect=ValueError):
            loc = i18n._parse_locale_safely("invalid")
            assert loc is None

    def test_get_display_name_fallback_success(self):
        """Test get_display_name_fallback."""
        locale_obj = Locale("en")
        name = i18n._get_display_name_fallback(locale_obj, "ru")
        assert name == "Russian"

    def test_get_display_name_fallback_error(self):
        """Test get_display_name_fallback error."""
        locale_obj = Locale("en")
        name = i18n._get_display_name_fallback(locale_obj, "invalid_lang_code")
        assert name is None
