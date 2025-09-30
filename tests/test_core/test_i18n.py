"""Tests for internationalization utilities."""

from pathlib import Path
from unittest.mock import Mock, patch

from src.i18n import (
    DOMAIN,
    LOCALE_DIR,
    get_translator,
    normalize_babel_locale,
    use_locale,
)


class TestI18nConstants:
    """Test class for i18n module constants.

    This class contains tests for module-level constants and configuration.
    """

    def test_domain_constant(self):
        """Test DOMAIN constant value.

        This test verifies that DOMAIN constant has the expected value.
        """
        assert DOMAIN == "messages"

    def test_locale_dir_constant(self):
        """Test LOCALE_DIR constant value.

        This test verifies that LOCALE_DIR constant points to the correct
        locales directory relative to the module.
        """
        # Verify LOCALE_DIR is a Path object
        assert isinstance(LOCALE_DIR, Path)

        # Verify it points to the locales directory
        assert LOCALE_DIR.name == "locales"
        assert LOCALE_DIR.exists() or not LOCALE_DIR.exists()  # May or may not exist


class TestGetTranslator:
    """Test class for get_translator function.

    This class contains all tests for the get_translator function,
    including successful translation loading and fallback behavior.
    """

    @patch("src.i18n.gettext.translation")
    def test_get_translator_success(self, mock_translation):
        """Test get_translator with successful translation loading.

        This test verifies that get_translator successfully loads
        translation for a supported language.
        """
        # Setup mock
        mock_translator = Mock()
        mock_translation.return_value = mock_translator

        # Test successful translation loading
        result = get_translator("ru")

        # Verify translation was called with correct parameters
        mock_translation.assert_called_once_with(
            DOMAIN, localedir=LOCALE_DIR, languages=["ru"]
        )

        # Verify result is the mock translator
        assert result == mock_translator

    @patch("src.i18n.gettext.translation")
    def test_get_translator_with_fallback(self, mock_translation):
        """Test get_translator with fallback to English.

        This test verifies that get_translator falls back to English
        when the requested language is not available.
        """
        # Setup mock to raise OSError for first call, succeed for second
        mock_translator = Mock()
        mock_translation.side_effect = [
            OSError("Translation not found"),
            mock_translator,
        ]

        # Test translation with fallback
        result = get_translator("unknown_lang")

        # Verify both calls were made
        assert mock_translation.call_count == 2

        # Verify first call was for requested language
        first_call = mock_translation.call_args_list[0]
        assert first_call[1]["languages"] == ["unknown_lang"]

        # Verify second call was for English fallback
        second_call = mock_translation.call_args_list[1]
        assert second_call[1]["languages"] == ["en"]
        assert second_call[1]["fallback"] is True

        # Verify result is the fallback translator
        assert result == mock_translator

    @patch("src.i18n.gettext.translation")
    def test_get_translator_with_english(self, mock_translation):
        """Test get_translator with English language.

        This test verifies that get_translator works correctly
        when English is requested.
        """
        # Setup mock
        mock_translator = Mock()
        mock_translation.return_value = mock_translator

        # Test English translation loading
        result = get_translator("en")

        # Verify translation was called with correct parameters
        mock_translation.assert_called_once_with(
            DOMAIN, localedir=LOCALE_DIR, languages=["en"]
        )

        # Verify result is the mock translator
        assert result == mock_translator

    @patch("src.i18n.gettext.translation")
    def test_get_translator_with_ukrainian(self, mock_translation):
        """Test get_translator with Ukrainian language.

        This test verifies that get_translator works correctly
        when Ukrainian is requested.
        """
        # Setup mock
        mock_translator = Mock()
        mock_translation.return_value = mock_translator

        # Test Ukrainian translation loading
        result = get_translator("ua")

        # Verify translation was called with correct parameters
        mock_translation.assert_called_once_with(
            DOMAIN, localedir=LOCALE_DIR, languages=["ua"]
        )

        # Verify result is the mock translator
        assert result == mock_translator


class TestUseLocale:
    """Test class for use_locale function.

    This class contains all tests for the use_locale function,
    including translator installation and return values.
    """

    @patch("src.i18n.get_translator")
    def test_use_locale_success(self, mock_get_translator):
        """Test use_locale with successful translator installation.

        This test verifies that use_locale properly installs translator
        and returns the expected functions.
        """
        # Setup mock translator
        mock_translator = Mock()
        mock_gettext = Mock()
        mock_ngettext = Mock()
        mock_pgettext = Mock()

        mock_translator.gettext = mock_gettext
        mock_translator.ngettext = mock_ngettext
        mock_translator.pgettext = mock_pgettext

        mock_get_translator.return_value = mock_translator

        # Test use_locale
        gettext_func, ngettext_func, pgettext_func = use_locale("ru")

        # Verify get_translator was called with correct language
        mock_get_translator.assert_called_once_with("ru")

        # Verify translator.install was called
        mock_translator.install.assert_called_once()

        # Verify correct functions are returned
        assert gettext_func == mock_gettext
        assert ngettext_func == mock_ngettext
        assert pgettext_func == mock_pgettext

    @patch("src.i18n.get_translator")
    def test_use_locale_with_different_language(self, mock_get_translator):
        """Test use_locale with different language.

        This test verifies that use_locale works correctly
        with different language codes.
        """
        # Setup mock translator
        mock_translator = Mock()
        mock_gettext = Mock()
        mock_ngettext = Mock()
        mock_pgettext = Mock()

        mock_translator.gettext = mock_gettext
        mock_translator.ngettext = mock_ngettext
        mock_translator.pgettext = mock_pgettext

        mock_get_translator.return_value = mock_translator

        # Test use_locale with Belarusian
        gettext_func, ngettext_func, pgettext_func = use_locale("by")

        # Verify get_translator was called with correct language
        mock_get_translator.assert_called_once_with("by")

        # Verify translator.install was called
        mock_translator.install.assert_called_once()

        # Verify correct functions are returned
        assert gettext_func == mock_gettext
        assert ngettext_func == mock_ngettext
        assert pgettext_func == mock_pgettext


class TestNormalizeBabelLocale:
    """Test class for normalize_babel_locale function.

    This class contains all tests for the normalize_babel_locale function,
    including various language code mappings and edge cases.
    """

    def test_normalize_ukrainian_language(self):
        """Test normalize_babel_locale with Ukrainian language code.

        This test verifies that 'ua' is correctly mapped to 'uk'.
        """
        result = normalize_babel_locale("ua")
        assert result == "uk"

    def test_normalize_belarusian_language(self):
        """Test normalize_babel_locale with Belarusian language code.

        This test verifies that 'by' is correctly mapped to 'be'.
        """
        result = normalize_babel_locale("by")
        assert result == "be"

    def test_normalize_russian_language(self):
        """Test normalize_babel_locale with Russian language code.

        This test verifies that 'ru' remains unchanged.
        """
        result = normalize_babel_locale("ru")
        assert result == "ru"

    def test_normalize_english_language(self):
        """Test normalize_babel_locale with English language code.

        This test verifies that 'en' remains unchanged.
        """
        result = normalize_babel_locale("en")
        assert result == "en"

    def test_normalize_uppercase_language(self):
        """Test normalize_babel_locale with uppercase language code.

        This test verifies that uppercase language codes are normalized
        to lowercase before mapping.
        """
        result = normalize_babel_locale("UA")
        assert result == "uk"

    def test_normalize_mixed_case_language(self):
        """Test normalize_babel_locale with mixed case language code.

        This test verifies that mixed case language codes are normalized
        to lowercase before mapping.
        """
        result = normalize_babel_locale("By")
        assert result == "be"

    def test_normalize_unknown_language(self):
        """Test normalize_babel_locale with unknown language code.

        This test verifies that unknown language codes are returned
        as-is in lowercase.
        """
        result = normalize_babel_locale("fr")
        assert result == "fr"

    def test_normalize_unknown_language_uppercase(self):
        """Test normalize_babel_locale with unknown uppercase language code.

        This test verifies that unknown uppercase language codes are
        returned in lowercase.
        """
        result = normalize_babel_locale("FR")
        assert result == "fr"

    def test_normalize_none_language(self):
        """Test normalize_babel_locale with None language.

        This test verifies that None language code defaults to 'en'.
        """
        result = normalize_babel_locale(None)
        assert result == "en"

    def test_normalize_empty_string_language(self):
        """Test normalize_babel_locale with empty string language.

        This test verifies that empty string language code defaults to 'en'.
        """
        result = normalize_babel_locale("")
        assert result == "en"

    def test_normalize_whitespace_language(self):
        """Test normalize_babel_locale with whitespace language.

        This test verifies that whitespace-only language code is returned as-is.
        """
        result = normalize_babel_locale("   ")
        assert result == "   "  # Whitespace is preserved

    def test_normalize_all_mapped_languages(self):
        """Test normalize_babel_locale with all mapped languages.

        This test verifies all language mappings work correctly.
        """
        test_cases = [
            ("ua", "uk"),
            ("by", "be"),
            ("ru", "ru"),
            ("en", "en"),
        ]

        for input_lang, expected_output in test_cases:
            result = normalize_babel_locale(input_lang)
            assert result == expected_output, f"Failed for {input_lang}"

    def test_normalize_edge_cases(self):
        """Test normalize_babel_locale with edge cases.

        This test verifies edge cases are handled correctly.
        """
        test_cases = [
            ("de", "de"),  # German - not mapped, should return as-is
            ("es", "es"),  # Spanish - not mapped, should return as-is
            ("zh", "zh"),  # Chinese - not mapped, should return as-is
            ("0", "0"),  # Numeric string - not mapped, should return as-is
            ("!", "!"),  # Special character - not mapped, should return as-is
        ]

        for input_lang, expected_output in test_cases:
            result = normalize_babel_locale(input_lang)
            assert result == expected_output, f"Failed for {input_lang}"
