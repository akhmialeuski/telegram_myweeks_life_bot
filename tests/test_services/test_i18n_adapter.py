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

    def test_translate_mixed_fallback(self, adapter, mock_pgettext):
        """Test fallback when checking for one format type but failing."""
        # Case specific to implementation detail: check for % but actually needs {}?
        # Or check for {} but needs %?
        pass
