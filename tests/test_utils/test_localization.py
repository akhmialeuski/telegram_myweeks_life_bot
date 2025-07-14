"""Tests for localization functionality."""

import pytest
from unittest.mock import patch

from src.utils.localization import (
    get_message,
    get_supported_languages,
    is_language_supported,
    get_subscription_description,
)


class TestLocalization:
    """Test localization functions."""

    def test_get_message_valid_key_ru(self):
        """Test getting message with valid key in Russian."""
        result = get_message("common", "error", "ru")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_message_valid_key_en(self):
        """Test getting message with valid key in English."""
        result = get_message("common", "error", "en")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_message_unsupported_language_fallback(self):
        """Test getting message with unsupported language falls back to default."""
        result = get_message("common", "error", "fr")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_message_invalid_key_fallback(self):
        """Test getting message with invalid key raises KeyError."""
        with pytest.raises(KeyError):
            get_message("invalid_key", "error", "ru")

    def test_get_message_invalid_subkey_fallback(self):
        """Test getting message with invalid subkey raises KeyError."""
        with pytest.raises(KeyError):
            get_message("common", "invalid_subkey", "ru")

    def test_get_message_with_formatting_parameters(self):
        """Test getting message with formatting parameters."""
        result = get_message(
            "command_weeks",
            "statistics",
            "ru",
            age=25,
            weeks_lived=1300,
            remaining_weeks=2860,
            life_percentage="16.2%",
            days_until_birthday=45,
        )
        assert isinstance(result, str)
        assert len(result) > 0
        assert "25" in result
        # Check for formatted numbers (with commas for thousands)
        assert "1,300" in result or "1300" in result

    def test_get_supported_languages(self):
        """Test getting list of supported languages."""
        languages = get_supported_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "ru" in languages
        assert "en" in languages

    def test_is_language_supported_valid(self):
        """Test checking if valid language is supported."""
        assert is_language_supported("ru") is True
        assert is_language_supported("en") is True

    def test_is_language_supported_invalid(self):
        """Test checking if invalid language is supported."""
        assert is_language_supported("fr") is False
        assert is_language_supported("de") is False

    def test_is_language_supported_edge_cases(self):
        """Test language support with edge cases."""
        assert is_language_supported("") is False
        assert is_language_supported(None) is False

    def test_get_message_all_supported_languages(self):
        """Test getting messages in all supported languages."""
        languages = get_supported_languages()
        for lang in languages:
            result = get_message("common", "error", lang)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_get_message_birth_date_validation_errors(self):
        """Test getting birth date validation error messages."""
        errors = ["future_date_error", "old_date_error", "format_error"]
        for error in errors:
            result = get_message("birth_date_validation", error, "ru")
            assert isinstance(result, str)
            assert len(result) > 0

    def test_get_message_command_weeks_not_registered(self):
        """Test getting not registered message for weeks command."""
        result = get_message("command_weeks", "not_registered", "ru")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_message_statistics_formatting(self):
        """Test getting statistics message with proper formatting."""
        result = get_message(
            "command_weeks",
            "statistics",
            "en",
            age=30,
            weeks_lived=1560,
            remaining_weeks=2600,
            life_percentage="37.5%",
            days_until_birthday=120,
        )
        assert isinstance(result, str)
        assert "30" in result
        # Check for formatted numbers (with commas for thousands)
        assert "1,560" in result or "1560" in result
        assert "2,600" in result or "2600" in result
        assert "37.5%" in result
        assert "120" in result

    def test_get_message_case_sensitivity(self):
        """Test that message keys are case sensitive."""
        result1 = get_message("common", "error", "ru")
        # Should raise KeyError for incorrect case
        with pytest.raises(KeyError, match="Message not found: Common.Error"):
            get_message("Common", "Error", "ru")

    def test_get_message_empty_parameters(self):
        """Test getting message with empty parameters."""
        result = get_message("common", "error", "ru", empty_param="")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_message_missing_parameters(self):
        """Test getting message with missing parameters."""
        result = get_message("common", "error", "ru")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_subscription_description_basic_ru(self):
        """Test getting basic subscription description in Russian."""
        result = get_subscription_description("basic", "ru")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_subscription_description_premium_en(self):
        """Test getting premium subscription description in English."""
        result = get_subscription_description("premium", "en")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_subscription_description_trial_ru(self):
        """Test getting trial subscription description in Russian."""
        result = get_subscription_description("trial", "ru")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_subscription_description_unknown_type(self):
        """Test getting description for unknown subscription type."""
        result = get_subscription_description("unknown", "ru")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_subscription_description_unsupported_language(self):
        """Test getting subscription description with unsupported language."""
        result = get_subscription_description("basic", "fr")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_basic_addition_message_with_buymeacoffee_url_ru(self):
        """Test basic addition message with BuyMeACoffee URL in Russian."""
        result = get_message(
            "subscription_additions",
            "basic_addition",
            "ru",
            buymeacoffee_url="https://test.buymeacoffee.com/testuser",
        )
        assert isinstance(result, str)
        assert len(result) > 0
        assert "https://test.buymeacoffee.com/testuser" in result

    def test_basic_addition_message_with_buymeacoffee_url_en(self):
        """Test basic addition message with BuyMeACoffee URL in English."""
        result = get_message(
            "subscription_additions",
            "basic_addition",
            "en",
            buymeacoffee_url="https://test.buymeacoffee.com/testuser",
        )
        assert isinstance(result, str)
        assert len(result) > 0
        assert "https://test.buymeacoffee.com/testuser" in result

    def test_basic_addition_message_with_default_buymeacoffee_url(self):
        """Test basic addition message with default BuyMeACoffee URL."""
        result = get_message(
            "subscription_additions",
            "basic_addition",
            "ru",
            buymeacoffee_url="https://www.buymeacoffee.com/yourname",
        )
        assert isinstance(result, str)
        assert len(result) > 0
        assert "https://www.buymeacoffee.com/yourname" in result

    def test_basic_addition_message_with_custom_buymeacoffee_url(self):
        """Test basic addition message with custom BuyMeACoffee URL."""
        custom_url = "https://custom.buymeacoffee.com/customuser"
        result = get_message(
            "subscription_additions",
            "basic_addition",
            "en",
            buymeacoffee_url=custom_url,
        )
        assert isinstance(result, str)
        assert len(result) > 0
        assert custom_url in result

    def test_basic_addition_message_with_empty_buymeacoffee_url(self):
        """Test basic addition message with empty BuyMeACoffee URL."""
        result = get_message(
            "subscription_additions", "basic_addition", "ru", buymeacoffee_url=""
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_basic_addition_message_with_none_buymeacoffee_url(self):
        """Test basic addition message with None BuyMeACoffee URL."""
        result = get_message(
            "subscription_additions", "basic_addition", "en", buymeacoffee_url=None
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_basic_addition_message_missing_buymeacoffee_url(self):
        """Test basic addition message without BuyMeACoffee URL parameter."""
        result = get_message("subscription_additions", "basic_addition", "ru")
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain the placeholder {buymeacoffee_url} since no URL was provided
        assert "{buymeacoffee_url}" in result

    def test_premium_addition_message_no_buymeacoffee_url(self):
        """Test premium addition message doesn't require BuyMeACoffee URL."""
        result = get_message("subscription_additions", "premium_addition", "ru")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_basic_addition_message_formatting_with_url(self):
        """Test that basic addition message properly formats BuyMeACoffee URL."""
        test_url = "https://test.buymeacoffee.com/testuser"
        result = get_message(
            "subscription_additions", "basic_addition", "en", buymeacoffee_url=test_url
        )
        assert isinstance(result, str)
        assert test_url in result
        # Check that URL is properly integrated into the message
        assert "Donate:" in result or "Донат:" in result

    def test_basic_addition_message_multiple_languages_with_url(self):
        """Test basic addition message with URL in multiple languages."""
        test_url = "https://test.buymeacoffee.com/testuser"

        # Test Russian
        result_ru = get_message(
            "subscription_additions", "basic_addition", "ru", buymeacoffee_url=test_url
        )
        assert test_url in result_ru

        # Test English
        result_en = get_message(
            "subscription_additions", "basic_addition", "en", buymeacoffee_url=test_url
        )
        assert test_url in result_en

    def test_basic_addition_message_url_placement(self):
        """Test that BuyMeACoffee URL is placed correctly in the message."""
        test_url = "https://test.buymeacoffee.com/testuser"
        result = get_message(
            "subscription_additions", "basic_addition", "en", buymeacoffee_url=test_url
        )

        # URL should appear after "Donate:" or similar text
        assert test_url in result
        # Check that it's not at the very beginning
        assert not result.startswith(test_url)

    def test_localization_module_imports(self):
        """Test that all required functions are imported correctly."""
        from src.utils.localization import (
            get_message,
            get_supported_languages,
            is_language_supported,
            get_subscription_description,
        )

        assert callable(get_message)
        assert callable(get_supported_languages)
        assert callable(is_language_supported)
        assert callable(get_subscription_description)
