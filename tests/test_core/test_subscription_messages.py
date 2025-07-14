"""Tests for subscription message generation module."""

from unittest.mock import patch

import pytest

from src.core.subscription_messages import (
    generate_message_week_addition_basic,
    generate_message_week_addition_premium,
    get_subscription_addition_message,
)
from src.database.models import SubscriptionType


class TestSubscriptionMessages:
    """Test subscription message generation functions."""

    @pytest.fixture
    def mock_telegram_user(self):
        """Create a mock Telegram user."""
        from unittest.mock import Mock

        user = Mock()
        user.id = 123456
        user.username = "test_user"
        user.first_name = "Test"
        user.language_code = "en"
        return user

    @pytest.fixture
    def mock_telegram_user_ru(self):
        """Create a mock Telegram user with Russian language."""
        from unittest.mock import Mock

        user = Mock()
        user.id = 123456
        user.username = "test_user"
        user.first_name = "Тест"
        user.language_code = "ru"
        return user

    @pytest.fixture
    def mock_telegram_user_no_lang(self):
        """Create a mock Telegram user without language code."""
        from unittest.mock import Mock

        user = Mock()
        user.id = 123456
        user.username = "test_user"
        user.first_name = "Test"
        user.language_code = None
        return user

    @patch(
        "src.core.subscription_messages.BUYMEACOFFEE_URL",
        "https://test.buymeacoffee.com/testuser",
    )
    @patch("src.core.subscription_messages.get_message")
    def test_generate_message_week_addition_basic_success(
        self, mock_get_message, mock_telegram_user
    ):
        """Test basic subscription message generation with BuyMeACoffee URL."""
        mock_get_message.return_value = "Basic subscription message with donation link"

        result = generate_message_week_addition_basic(mock_telegram_user)

        mock_get_message.assert_called_once_with(
            "subscription_additions",
            "basic_addition",
            "en",
            buymeacoffee_url="https://test.buymeacoffee.com/testuser",
        )
        assert result == "Basic subscription message with donation link"

    @patch(
        "src.core.subscription_messages.BUYMEACOFFEE_URL",
        "https://test.buymeacoffee.com/testuser",
    )
    @patch("src.core.subscription_messages.get_message")
    def test_generate_message_week_addition_basic_russian(
        self, mock_get_message, mock_telegram_user_ru
    ):
        """Test basic subscription message generation with Russian language and BuyMeACoffee URL."""
        mock_get_message.return_value = "Сообщение базовой подписки с ссылкой на донат"

        result = generate_message_week_addition_basic(mock_telegram_user_ru)

        mock_get_message.assert_called_once_with(
            "subscription_additions",
            "basic_addition",
            "ru",
            buymeacoffee_url="https://test.buymeacoffee.com/testuser",
        )
        assert result == "Сообщение базовой подписки с ссылкой на донат"

    @patch(
        "src.core.subscription_messages.BUYMEACOFFEE_URL",
        "https://test.buymeacoffee.com/testuser",
    )
    @patch("src.core.subscription_messages.get_message")
    def test_generate_message_week_addition_basic_no_language(
        self, mock_get_message, mock_telegram_user_no_lang
    ):
        """Test basic subscription message generation with no language code and BuyMeACoffee URL."""
        mock_get_message.return_value = "Default language message with donation link"

        result = generate_message_week_addition_basic(mock_telegram_user_no_lang)

        mock_get_message.assert_called_once_with(
            "subscription_additions",
            "basic_addition",
            "ru",
            buymeacoffee_url="https://test.buymeacoffee.com/testuser",
        )
        assert result == "Default language message with donation link"

    @patch(
        "src.core.subscription_messages.BUYMEACOFFEE_URL",
        "https://custom.buymeacoffee.com/customuser",
    )
    @patch("src.core.subscription_messages.get_message")
    def test_generate_message_week_addition_basic_custom_url(
        self, mock_get_message, mock_telegram_user
    ):
        """Test basic subscription message generation with custom BuyMeACoffee URL."""
        mock_get_message.return_value = "Custom URL message"

        result = generate_message_week_addition_basic(mock_telegram_user)

        mock_get_message.assert_called_once_with(
            "subscription_additions",
            "basic_addition",
            "en",
            buymeacoffee_url="https://custom.buymeacoffee.com/customuser",
        )
        assert result == "Custom URL message"

    @patch(
        "src.core.subscription_messages.BUYMEACOFFEE_URL",
        "https://www.buymeacoffee.com/yourname",
    )
    @patch("src.core.subscription_messages.get_message")
    def test_generate_message_week_addition_basic_default_url(
        self, mock_get_message, mock_telegram_user
    ):
        """Test basic subscription message generation with default BuyMeACoffee URL."""
        mock_get_message.return_value = "Default URL message"

        result = generate_message_week_addition_basic(mock_telegram_user)

        mock_get_message.assert_called_once_with(
            "subscription_additions",
            "basic_addition",
            "en",
            buymeacoffee_url="https://www.buymeacoffee.com/yourname",
        )
        assert result == "Default URL message"

    @patch("src.core.subscription_messages.get_message")
    def test_generate_message_week_addition_premium_success(
        self, mock_get_message, mock_telegram_user
    ):
        """Test premium subscription message generation."""
        mock_get_message.return_value = "Premium subscription message"

        result = generate_message_week_addition_premium(mock_telegram_user)

        mock_get_message.assert_called_once_with(
            "subscription_additions", "premium_addition", "en"
        )
        assert result == "Premium subscription message"

    @patch("src.core.subscription_messages.get_message")
    def test_generate_message_week_addition_premium_russian(
        self, mock_get_message, mock_telegram_user_ru
    ):
        """Test premium subscription message generation with Russian language."""
        mock_get_message.return_value = "Сообщение премиум подписки"

        result = generate_message_week_addition_premium(mock_telegram_user_ru)

        mock_get_message.assert_called_once_with(
            "subscription_additions", "premium_addition", "ru"
        )
        assert result == "Сообщение премиум подписки"

    @patch("src.core.subscription_messages.generate_message_week_addition_premium")
    def test_get_subscription_addition_message_premium(
        self, mock_premium, mock_telegram_user
    ):
        """Test subscription addition message for premium subscription."""
        mock_premium.return_value = "Premium content"

        result = get_subscription_addition_message(
            mock_telegram_user, SubscriptionType.PREMIUM.value
        )

        mock_premium.assert_called_once_with(mock_telegram_user)
        assert result == "Premium content"

    @patch("src.core.subscription_messages.generate_message_week_addition_premium")
    def test_get_subscription_addition_message_trial(
        self, mock_premium, mock_telegram_user
    ):
        """Test subscription addition message for trial subscription."""
        mock_premium.return_value = "Trial content"

        result = get_subscription_addition_message(
            mock_telegram_user, SubscriptionType.TRIAL.value
        )

        mock_premium.assert_called_once_with(mock_telegram_user)
        assert result == "Trial content"

    @patch("src.core.subscription_messages.generate_message_week_addition_basic")
    def test_get_subscription_addition_message_basic(
        self, mock_basic, mock_telegram_user
    ):
        """Test subscription addition message for basic subscription."""
        mock_basic.return_value = "Basic content"

        result = get_subscription_addition_message(
            mock_telegram_user, SubscriptionType.BASIC.value
        )

        mock_basic.assert_called_once_with(mock_telegram_user)
        assert result == "Basic content"

    @patch("src.core.subscription_messages.generate_message_week_addition_basic")
    def test_get_subscription_addition_message_unknown_type(
        self, mock_basic, mock_telegram_user
    ):
        """Test subscription addition message for unknown subscription type."""
        mock_basic.return_value = "Fallback content"

        result = get_subscription_addition_message(mock_telegram_user, "unknown_type")

        mock_basic.assert_called_once_with(mock_telegram_user)
        assert result == "Fallback content"

    def test_generate_message_week_addition_basic_function_signature(self):
        """Test function signature for basic subscription message."""
        import inspect

        sig = inspect.signature(generate_message_week_addition_basic)
        params = list(sig.parameters.keys())

        assert len(params) == 1
        assert params[0] == "user_info"

    def test_generate_message_week_addition_premium_function_signature(self):
        """Test function signature for premium subscription message."""
        import inspect

        sig = inspect.signature(generate_message_week_addition_premium)
        params = list(sig.parameters.keys())

        assert len(params) == 1
        assert params[0] == "user_info"

    def test_get_subscription_addition_message_function_signature(self):
        """Test function signature for subscription addition message."""
        import inspect

        sig = inspect.signature(get_subscription_addition_message)
        params = list(sig.parameters.keys())

        assert len(params) == 2
        assert params[0] == "user_info"
        assert params[1] == "subscription_type"

    @patch(
        "src.core.subscription_messages.BUYMEACOFFEE_URL",
        "https://test.buymeacoffee.com/testuser",
    )
    @patch("src.core.subscription_messages.get_message")
    def test_integration_basic_message_generation(
        self, mock_get_message, mock_telegram_user
    ):
        """Test integration of basic message generation with BuyMeACoffee URL."""
        mock_get_message.return_value = "Integrated basic message with donation"

        result = generate_message_week_addition_basic(mock_telegram_user)

        assert result == "Integrated basic message with donation"
        mock_get_message.assert_called_once_with(
            "subscription_additions",
            "basic_addition",
            "en",
            buymeacoffee_url="https://test.buymeacoffee.com/testuser",
        )

    @patch("src.core.subscription_messages.get_message")
    def test_integration_premium_message_generation(
        self, mock_get_message, mock_telegram_user
    ):
        """Test integration of premium message generation."""
        mock_get_message.return_value = "Integrated premium message"

        result = generate_message_week_addition_premium(mock_telegram_user)

        assert result == "Integrated premium message"
        mock_get_message.assert_called_once()

    @patch("src.core.subscription_messages.generate_message_week_addition_premium")
    @patch("src.core.subscription_messages.generate_message_week_addition_basic")
    def test_integration_subscription_addition_message(
        self, mock_basic, mock_premium, mock_telegram_user
    ):
        """Test integration of subscription addition message selection."""
        mock_premium.return_value = "Premium integration"
        mock_basic.return_value = "Basic integration"

        # Test premium
        result_premium = get_subscription_addition_message(
            mock_telegram_user, SubscriptionType.PREMIUM.value
        )
        assert result_premium == "Premium integration"

        # Test basic
        result_basic = get_subscription_addition_message(
            mock_telegram_user, SubscriptionType.BASIC.value
        )
        assert result_basic == "Basic integration"

        # Verify calls
        mock_premium.assert_called_once_with(mock_telegram_user)
        mock_basic.assert_called_once_with(mock_telegram_user)

    @patch(
        "src.core.subscription_messages.BUYMEACOFFEE_URL",
        "https://test.buymeacoffee.com/testuser",
    )
    @patch("src.core.subscription_messages.get_message")
    def test_buymeacoffee_url_parameter_passed_correctly(
        self, mock_get_message, mock_telegram_user
    ):
        """Test that BuyMeACoffee URL is passed correctly to get_message."""
        mock_get_message.return_value = "Test message"

        generate_message_week_addition_basic(mock_telegram_user)

        # Verify that buymeacoffee_url parameter is passed
        call_args = mock_get_message.call_args
        assert (
            call_args[1]["buymeacoffee_url"] == "https://test.buymeacoffee.com/testuser"
        )

    @patch("src.core.subscription_messages.BUYMEACOFFEE_URL", "")
    @patch("src.core.subscription_messages.get_message")
    def test_empty_buymeacoffee_url_handling(
        self, mock_get_message, mock_telegram_user
    ):
        """Test handling of empty BuyMeACoffee URL."""
        mock_get_message.return_value = "Empty URL message"

        result = generate_message_week_addition_basic(mock_telegram_user)

        mock_get_message.assert_called_once_with(
            "subscription_additions", "basic_addition", "en", buymeacoffee_url=""
        )
        assert result == "Empty URL message"

    @patch("src.core.subscription_messages.BUYMEACOFFEE_URL", None)
    @patch("src.core.subscription_messages.get_message")
    def test_none_buymeacoffee_url_handling(self, mock_get_message, mock_telegram_user):
        """Test handling of None BuyMeACoffee URL."""
        mock_get_message.return_value = "None URL message"

        result = generate_message_week_addition_basic(mock_telegram_user)

        mock_get_message.assert_called_once_with(
            "subscription_additions", "basic_addition", "en", buymeacoffee_url=None
        )
        assert result == "None URL message"

    def test_module_imports_correctly(self):
        """Test that all required functions are imported correctly."""
        from src.core.subscription_messages import (
            generate_message_week_addition_basic,
            generate_message_week_addition_premium,
            get_subscription_addition_message,
        )

        assert callable(generate_message_week_addition_basic)
        assert callable(generate_message_week_addition_premium)
        assert callable(get_subscription_addition_message)

    def test_buymeacoffee_url_config_import(self):
        """Test that BUYMEACOFFEE_URL is imported from config."""
        from src.core.subscription_messages import BUYMEACOFFEE_URL

        assert isinstance(BUYMEACOFFEE_URL, str)
        assert len(BUYMEACOFFEE_URL) > 0
        # Check that it's a valid URL (either buymeacoffee.com or coff.ee)
        assert "buymeacoffee.com" in BUYMEACOFFEE_URL or "coff.ee" in BUYMEACOFFEE_URL

    @patch(
        "src.core.subscription_messages.BUYMEACOFFEE_URL",
        "https://test.buymeacoffee.com/testuser",
    )
    @patch("src.core.subscription_messages.get_message")
    def test_multiple_language_support_with_buymeacoffee(
        self, mock_get_message, mock_telegram_user, mock_telegram_user_ru
    ):
        """Test that BuyMeACoffee URL works with multiple languages."""
        mock_get_message.return_value = "Multi-language message"

        # Test English
        result_en = generate_message_week_addition_basic(mock_telegram_user)
        assert result_en == "Multi-language message"

        # Test Russian
        result_ru = generate_message_week_addition_basic(mock_telegram_user_ru)
        assert result_ru == "Multi-language message"

        # Verify both calls included the URL
        assert mock_get_message.call_count == 2
        for call in mock_get_message.call_args_list:
            assert (
                call[1]["buymeacoffee_url"] == "https://test.buymeacoffee.com/testuser"
            )
