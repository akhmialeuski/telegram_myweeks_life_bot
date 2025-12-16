"""Tests for BabelI18nAdapter."""

from unittest.mock import MagicMock

import pytest

from src.services.i18n_adapter import BabelI18nAdapter


class TestBabelI18nAdapter:
    """Test suite for BabelI18nAdapter."""

    @pytest.fixture
    def mock_pgettext(self):
        """Mock pgettext function."""
        return MagicMock()

    @pytest.fixture
    def adapter(self, mocker, mock_pgettext):
        """Create adapter with mocked locale."""
        mocker.patch(
            "src.services.i18n_adapter.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return BabelI18nAdapter("en")

    def test_translate_no_formatting(self, adapter, mock_pgettext):
        """Test translation without formatting."""
        mock_pgettext.return_value = "Hello"
        result = adapter.translate("key", "default")
        assert result == "Hello"

    def test_translate_percent_formatting(self, adapter, mock_pgettext):
        """Test translation with % formatting."""
        mock_pgettext.return_value = "Hello %(name)s"
        result = adapter.translate("key", "default", name="World")
        assert result == "Hello World"

    def test_translate_brace_formatting(self, adapter, mock_pgettext):
        """Test translation with {} formatting."""
        mock_pgettext.return_value = "Hello {name}"
        result = adapter.translate("key", "default", name="World")
        assert result == "Hello World"

    def test_translate_mixed_fallback(self, adapter, mock_pgettext) -> None:
        """Test fallback when .format() fails and % fallback works.

        This test verifies that when .format() raises KeyError,
        the translate method falls back to % formatting.
        """
        # Message without %( marker but needs % formatting
        mock_pgettext.return_value = "Hello %(name)s - extra"
        result = adapter.translate("key", "default", name="World")
        assert result == "Hello World - extra"

    def test_translate_format_keyerror_fallback_to_percent(
        self, adapter, mock_pgettext
    ) -> None:
        """Test fallback to % formatting when .format() raises KeyError.

        This test verifies that when the message uses .format() style
        but the key is missing, it falls back to % formatting.
        """
        # Message that looks like it needs .format() but will fail
        mock_pgettext.return_value = "{missing_key} text"
        result = adapter.translate("key", "default", name="World")
        # Should try % formatting, which will also fail, return unformatted
        assert result == "{missing_key} text"

    def test_translate_all_formatting_fails(self, adapter, mock_pgettext) -> None:
        """Test returning unformatted message when all formatting fails.

        This test verifies that when both .format() and % formatting fail,
        the original message is returned unformatted.
        """
        # Message that can't be formatted with any method
        mock_pgettext.return_value = "Some text %d invalid"
        result = adapter.translate("key", "default", name="World")
        # Should return unformatted since both formats fail
        assert result == "Some text %d invalid"

    def test_translate_valueerror_in_percent_formatting(
        self, adapter, mock_pgettext
    ) -> None:
        """Test ValueError during % formatting fallback.

        This test specifically covers line 52-53 where ValueError is caught
        during % formatting fallback.
        """
        # Message without %( that will fail .format() with KeyError
        # and then fail % formatting with ValueError
        # Using %d without parentheses - causes ValueError when dict is passed
        mock_pgettext.return_value = "{missing_key} with %d specifier"
        result = adapter.translate("key", "default", name="value")
        # .format() fails with KeyError (missing_key not in kwargs)
        # % formatting fails with ValueError (%d expects number, gets dict)
        assert result == "{missing_key} with %d specifier"

    def test_translate_typeerror_in_percent_formatting(
        self, adapter, mock_pgettext
    ) -> None:
        """Test TypeError during % formatting fallback.

        This test specifically covers line 52-53 where TypeError is caught
        during % formatting fallback.
        """
        # Message without %( that will fail .format() with KeyError
        # and then fail % formatting with TypeError
        mock_pgettext.return_value = "{unknown} text %s %s end"
        result = adapter.translate("key", "default", other_key="value")
        # .format() fails with KeyError (unknown not in kwargs)
        # % formatting fails with TypeError (not enough arguments)
        assert result == "{unknown} text %s %s end"
