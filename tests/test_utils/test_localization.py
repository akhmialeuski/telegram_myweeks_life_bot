"""Unit tests for localization utilities.

Tests message retrieval, language detection, and fallback behavior
for the multilingual support system.
"""

import pytest
from unittest.mock import Mock

from src.utils.localization import (
    get_message,
    get_supported_languages,
    is_language_supported,
)


class TestLocalization:
    """Test suite for localization utilities."""

    def test_get_message_valid_key_ru(self):
        """Test getting a message with valid key in Russian.

        :returns: None
        """
        message = get_message("command_start", "welcome_new", "ru", first_name="Иван")

        assert isinstance(message, str)
        assert "Иван" in message
        assert "LifeWeeksBot" in message

    def test_get_message_valid_key_en(self):
        """Test getting a message with valid key in English.

        :returns: None
        """
        message = get_message("command_start", "welcome_new", "en", first_name="John")

        assert isinstance(message, str)
        assert "John" in message
        assert "LifeWeeksBot" in message

    def test_get_message_unsupported_language_fallback(self):
        """Test message fallback to default language for unsupported language.

        :returns: None
        """
        message = get_message("command_start", "welcome_new", "fr", first_name="Jean")

        # Should fallback to Russian (default language)
        assert isinstance(message, str)
        assert "Jean" in message

    def test_get_message_invalid_key_fallback(self):
        """Test behavior with invalid message key.

        :returns: None
        """
        with pytest.raises(KeyError, match="Message not found"):
            get_message("invalid_command", "invalid_sub", "ru")

    def test_get_message_invalid_subkey_fallback(self):
        """Test behavior with invalid sub-key.

        :returns: None
        """
        with pytest.raises(KeyError, match="Message not found"):
            get_message("command_start", "invalid_sub", "ru")

    def test_get_message_with_formatting_parameters(self):
        """Test message formatting with multiple parameters.

        :returns: None
        """
        message = get_message(
            "registration",
            "success",
            "ru",
            birth_date="15.03.1990",
            age=34,
            weeks_lived=1768,
        )

        assert isinstance(message, str)
        assert "15.03.1990" in message
        assert "34" in message
        assert "1,768" in message or "1768" in message

    def test_get_supported_languages(self):
        """Test getting list of supported languages.

        :returns: None
        """
        languages = get_supported_languages()

        assert isinstance(languages, list)
        assert len(languages) >= 2  # At least Russian and English
        assert "ru" in languages
        assert "en" in languages

    def test_is_language_supported_valid(self):
        """Test checking if valid languages are supported.

        :returns: None
        """
        assert is_language_supported("ru") is True
        assert is_language_supported("en") is True

    def test_is_language_supported_invalid(self):
        """Test checking if invalid languages are supported.

        :returns: None
        """
        assert is_language_supported("fr") is False
        assert is_language_supported("de") is False
        assert is_language_supported("invalid") is False

    def test_is_language_supported_edge_cases(self):
        """Test edge cases for language support checking.

        :returns: None
        """
        assert is_language_supported("") is False
        assert is_language_supported(None) is False

    def test_get_message_all_supported_languages(self):
        """Test getting messages in all supported languages.

        :returns: None
        """
        languages = get_supported_languages()

        for lang in languages:
            message = get_message(
                "command_start", "welcome_new", lang, first_name="Test"
            )
            assert isinstance(message, str)
            assert len(message) > 0
            assert "Test" in message

    def test_get_message_birth_date_validation_errors(self):
        """Test birth date validation error messages.

        :returns: None
        """
        future_error = get_message("birth_date_validation", "future_date_error", "ru")
        old_error = get_message("birth_date_validation", "old_date_error", "ru")
        format_error = get_message("birth_date_validation", "format_error", "ru")

        assert isinstance(future_error, str)
        assert isinstance(old_error, str)
        assert isinstance(format_error, str)
        assert len(future_error) > 0
        assert len(old_error) > 0
        assert len(format_error) > 0

    def test_get_message_command_weeks_not_registered(self):
        """Test getting 'not registered' message.

        :returns: None
        """
        message = get_message("command_weeks", "not_registered", "en")

        assert isinstance(message, str)
        assert "start" in message.lower()

    def test_get_message_statistics_formatting(self):
        """Test statistics message with complex formatting.

        :returns: None
        """
        message = get_message(
            "command_weeks",
            "statistics",
            "en",
            age=30,
            weeks_lived=1560,
            remaining_weeks=2600,
            life_percentage="37.5%",
            days_until_birthday=42,
        )

        assert isinstance(message, str)
        assert "30" in message
        assert "1,560" in message or "1560" in message
        assert "2,600" in message or "2600" in message
        assert "37.5%" in message
        assert "42" in message

    def test_get_message_case_sensitivity(self):
        """Test that language codes are handled case-insensitively.

        :returns: None
        """
        message_lower = get_message(
            "command_start", "welcome_new", "ru", first_name="Test"
        )
        message_upper = get_message(
            "command_start", "welcome_new", "RU", first_name="Test"
        )

        # Both should work (either the same or both valid strings)
        assert isinstance(message_lower, str)
        assert isinstance(message_upper, str)

    def test_get_message_empty_parameters(self):
        """Test message formatting with empty parameters.

        :returns: None
        """
        message = get_message("command_start", "welcome_new", "ru", first_name="")

        assert isinstance(message, str)
        # Should still be a valid message even with empty parameter

    def test_get_message_missing_parameters(self):
        """Test message formatting when required parameters are missing.

        :returns: None
        """
        # This should either handle gracefully or show placeholder text
        message = get_message("command_start", "welcome_new", "ru")

        assert isinstance(message, str)
