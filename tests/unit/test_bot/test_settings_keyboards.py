"""Unit tests for settings keyboards.

Tests the keyboard generation functions for the settings menu.
"""

from unittest.mock import MagicMock

from telegram import InlineKeyboardMarkup

from src.bot.handlers.settings.keyboards import (
    get_language_keyboard,
    get_settings_keyboard,
    get_timezone_keyboard,
)
from tests.constants import (
    CALLBACK_SETTINGS_TIMEZONE,
    CALLBACK_TIMEZONE_MINSK,
    CALLBACK_TIMEZONE_MOSCOW,
    CALLBACK_TIMEZONE_NEW_YORK,
    CALLBACK_TIMEZONE_OTHER,
    CALLBACK_TIMEZONE_UTC,
    CALLBACK_TIMEZONE_WARSAW,
)


class TestSettingsKeyboards:
    """Test suite for settings keyboards."""

    def test_get_language_keyboard(self) -> None:
        """Test getting language keyboard."""
        keyboard = get_language_keyboard()
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 4
        assert keyboard.inline_keyboard[0][0].callback_data == "language_ru"
        assert keyboard.inline_keyboard[1][0].callback_data == "language_en"

    def test_get_settings_keyboard_basic(self) -> None:
        """Test getting main settings keyboard for basic users."""
        mock_pgettext = MagicMock(side_effect=lambda ctx, text: text)
        keyboard = get_settings_keyboard(pgettext=mock_pgettext, is_premium=False)
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 3
        # Ensure premium buttons are not present
        callback_data = [
            btn.callback_data for row in keyboard.inline_keyboard for btn in row
        ]
        assert CALLBACK_SETTINGS_TIMEZONE not in callback_data
        assert "settings_notification_schedule" not in callback_data

    def test_get_settings_keyboard_premium(self) -> None:
        """Test getting main settings keyboard for premium users."""
        mock_pgettext = MagicMock(side_effect=lambda ctx, text: text)
        keyboard = get_settings_keyboard(pgettext=mock_pgettext, is_premium=True)
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 5
        # Ensure premium buttons are present
        callback_data = [
            btn.callback_data for row in keyboard.inline_keyboard for btn in row
        ]
        assert CALLBACK_SETTINGS_TIMEZONE in callback_data
        assert "settings_notification_schedule" in callback_data

    def test_get_timezone_keyboard(self) -> None:
        """Test getting timezone keyboard."""
        mock_pgettext = MagicMock(side_effect=lambda ctx, text: text)
        keyboard = get_timezone_keyboard(pgettext=mock_pgettext)
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 6

        callback_data = [
            btn.callback_data for row in keyboard.inline_keyboard for btn in row
        ]
        expected_callbacks = [
            CALLBACK_TIMEZONE_UTC,
            CALLBACK_TIMEZONE_MOSCOW,
            CALLBACK_TIMEZONE_WARSAW,
            CALLBACK_TIMEZONE_MINSK,
            CALLBACK_TIMEZONE_NEW_YORK,
            CALLBACK_TIMEZONE_OTHER,
        ]
        assert callback_data == expected_callbacks
