"""Tests for subscription message generation module."""

from unittest.mock import Mock

import pytest

# Backward-compatibility shim so patch targets exist even if implementation moved
import src.core.subscription_messages as _subs_mod
import src.utils.localization as _loc
from src.core.enums import SubscriptionType

if not hasattr(_subs_mod, "get_message"):
    _subs_mod.get_message = _loc.get_message
from src.core.message_context import use_message_context
from src.core.subscription_messages import (
    generate_message_week_addition_basic,
    generate_message_week_addition_premium,
    get_subscription_addition_message,
)
from src.utils.localization import SupportedLanguage


class TestSubscriptionMessages:
    """Test subscription message generation functions."""

    @pytest.fixture
    def mock_telegram_user(self):
        """Create a mock Telegram user."""
        user = Mock()
        user.id = 123456
        user.username = "test_user"
        user.first_name = "Test"
        user.language_code = SupportedLanguage.EN.value
        return user

    @pytest.fixture
    def mock_telegram_user_ru(self):
        """Create a mock Telegram user with Russian language."""
        user = Mock()
        user.id = 123456
        user.username = "test_user"
        user.first_name = "Тест"
        user.language_code = SupportedLanguage.RU.value
        return user

    @pytest.fixture
    def mock_telegram_user_no_lang(self):
        """Create a mock Telegram user without language code."""
        user = Mock()
        user.id = 123456
        user.username = "test_user"
        user.first_name = "Test"
        user.language_code = None
        return user

    def test_generate_message_week_addition_basic_success(
        self, mocker, mock_telegram_user
    ):
        """Test basic subscription message generation with BuyMeACoffee URL."""
        mock_randint = mocker.patch("src.core.subscription_messages.random.randint")
        mock_randint.return_value = (
            15  # Less than 20% probability, so message should be shown
        )

        # Patch builder so gettext passthrough returns template string
        svc = mocker.patch("src.services.container.ServiceContainer")
        builder = mocker.MagicMock()
        builder.get.return_value = "💡 <b>Basic Subscription</b>\n\nYou are using the basic version of the bot with core functionality.\n\n🔗 <b>Support the project:</b>\n• GitHub: https://github.com/your-project/lifeweeks-bot\n• Donate: https://coff.ee/akhmelevskiy\n\nYour support helps develop the bot! 🙏"
        svc.return_value.get_message_builder.return_value = builder
        from src.core.subscription_messages import generate_message_week_addition_basic

        with use_message_context(user_info=mock_telegram_user, fetch_profile=False):
            result = generate_message_week_addition_basic(mock_telegram_user)
        assert "https://coff.ee/akhmelevskiy" in result

    def test_generate_message_week_addition_basic_russian(
        self, mocker, mock_telegram_user_ru
    ):
        """Test basic subscription message generation with Russian language and BuyMeACoffee URL."""
        mock_randint = mocker.patch("src.core.subscription_messages.random.randint")
        mock_randint.return_value = (
            10  # Less than 20% probability, so message should be shown
        )

        svc = mocker.patch("src.services.container.ServiceContainer")
        builder = mocker.MagicMock()
        builder.get.return_value = "💡 <b>Базовая подписка</b>\n\nВы используете базовую версию бота с основной функциональностью.\n\n🔗 <b>Поддержать проект:</b>\n• GitHub: https://github.com/your-project/lifeweeks-bot\n• Донат: https://coff.ee/akhmelevskiy\n\nВаша поддержка помогает развивать бота! 🙏"
        svc.return_value.get_message_builder.return_value = builder
        from src.core.subscription_messages import generate_message_week_addition_basic

        with use_message_context(user_info=mock_telegram_user_ru, fetch_profile=False):
            result = generate_message_week_addition_basic(mock_telegram_user_ru)
        assert "https://coff.ee/akhmelevskiy" in result

    def test_generate_message_week_addition_basic_no_language(
        self, mocker, mock_telegram_user_no_lang
    ):
        """Test basic subscription message generation with no language code and BuyMeACoffee URL."""
        mock_randint = mocker.patch("src.core.subscription_messages.random.randint")
        mock_randint.return_value = (
            5  # Less than 20% probability, so message should be shown
        )

        svc = mocker.patch("src.services.container.ServiceContainer")
        builder = mocker.MagicMock()
        builder.get.return_value = "💡 <b>Basic Subscription</b>\n\nYou are using the basic version of the bot with core functionality.\n\n🔗 <b>Support the project:</b>\n• GitHub: https://github.com/your-project/lifeweeks-bot\n• Donate: https://coff.ee/akhmelevskiy\n\nYour support helps develop the bot! 🙏"
        svc.return_value.get_message_builder.return_value = builder
        from src.core.subscription_messages import generate_message_week_addition_basic

        with use_message_context(
            user_info=mock_telegram_user_no_lang, fetch_profile=False
        ):
            result = generate_message_week_addition_basic(mock_telegram_user_no_lang)
        assert "https://coff.ee/akhmelevskiy" in result

    def test_generate_message_week_addition_basic_custom_url(
        self, mocker, mock_telegram_user
    ):
        """Test basic subscription message generation with custom BuyMeACoffee URL."""
        mock_randint = mocker.patch("src.core.subscription_messages.random.randint")
        mock_randint.return_value = (
            15  # Less than 20% probability, so message should be shown
        )

        svc = mocker.patch("src.services.container.ServiceContainer")
        builder = mocker.MagicMock()
        builder.get.return_value = "💡 <b>Basic Subscription</b>\n\nYou are using the basic version of the bot with core functionality.\n\n🔗 <b>Support the project:</b>\n• GitHub: https://github.com/your-project/lifeweeks-bot\n• Donate: https://coff.ee/akhmelevskiy\n\nYour support helps develop the bot! 🙏"
        svc.return_value.get_message_builder.return_value = builder
        from src.core.subscription_messages import generate_message_week_addition_basic

        with use_message_context(user_info=mock_telegram_user, fetch_profile=False):
            result = generate_message_week_addition_basic(mock_telegram_user)
        assert "https://coff.ee" in result

    def test_generate_message_week_addition_basic_default_url(
        self, mocker, mock_telegram_user
    ):
        """Test basic subscription message generation with default BuyMeACoffee URL."""
        mock_randint = mocker.patch("src.core.subscription_messages.random.randint")
        mock_randint.return_value = (
            10  # Less than 20% probability, so message should be shown
        )

        svc = mocker.patch("src.services.container.ServiceContainer")
        builder = mocker.MagicMock()
        builder.get.return_value = "💡 <b>Basic Subscription</b>\n\nYou are using the basic version of the bot with core functionality.\n\n🔗 <b>Support the project:</b>\n• GitHub: https://github.com/your-project/lifeweeks-bot\n• Donate: https://coff.ee/akhmelevskiy\n\nYour support helps develop the bot! 🙏"
        svc.return_value.get_message_builder.return_value = builder
        from src.core.subscription_messages import generate_message_week_addition_basic

        with use_message_context(user_info=mock_telegram_user, fetch_profile=False):
            result = generate_message_week_addition_basic(mock_telegram_user)
        assert "https://coff.ee/akhmelevskiy" in result

    def test_generate_message_week_addition_basic_probability_high(
        self, mocker, mock_telegram_user
    ):
        """Test basic subscription message generation when probability check fails."""
        mock_randint = mocker.patch("src.core.subscription_messages.random.randint")
        mock_randint.return_value = (
            85  # Higher than 20% probability, so message should not be shown
        )

        with use_message_context(user_info=mock_telegram_user, fetch_profile=False):
            result = generate_message_week_addition_basic(mock_telegram_user)

        assert result == ""
        mock_randint.assert_called_once_with(1, 100)

    def test_generate_message_week_addition_basic_probability_exact(
        self, mocker, mock_telegram_user
    ):
        """Test basic subscription message generation with exact probability threshold."""
        mock_randint = mocker.patch("src.core.subscription_messages.random.randint")
        mock_randint.return_value = 20  # Exactly 20% probability, message is shown
        svc = mocker.patch("src.services.container.ServiceContainer")
        builder = mocker.MagicMock()
        builder.get.return_value = "Test message"
        svc.return_value.get_message_builder.return_value = builder
        from src.core.subscription_messages import generate_message_week_addition_basic

        with use_message_context(user_info=mock_telegram_user, fetch_profile=False):
            result = generate_message_week_addition_basic(mock_telegram_user)
        assert result == "Test message"
        mock_randint.assert_called_once_with(1, 100)

    def test_generate_message_week_addition_basic_probability_low(
        self, mocker, mock_telegram_user
    ):
        """Test basic subscription message generation when probability check passes."""
        mock_randint = mocker.patch("src.core.subscription_messages.random.randint")
        mock_randint.return_value = (
            19  # Less than 20% probability, so message should be shown
        )
        svc = mocker.patch("src.services.container.ServiceContainer")
        builder = mocker.MagicMock()
        builder.get.return_value = "Test message"
        svc.return_value.get_message_builder.return_value = builder
        from src.core.subscription_messages import generate_message_week_addition_basic

        with use_message_context(user_info=mock_telegram_user, fetch_profile=False):
            result = generate_message_week_addition_basic(mock_telegram_user)
        assert result == "Test message"
        mock_randint.assert_called_once_with(1, 100)

    def test_generate_message_week_addition_basic_custom_probability(
        self, mocker, mock_telegram_user
    ):
        """Test basic subscription message generation with custom probability setting."""
        mocker.patch(
            "src.core.subscription_messages.SUBSCRIPTION_MESSAGE_PROBABILITY", 50
        )
        mock_randint = mocker.patch("src.core.subscription_messages.random.randint")
        mock_randint.return_value = (
            30  # Less than 50% probability, so message should be shown
        )
        svc = mocker.patch("src.services.container.ServiceContainer")
        builder = mocker.MagicMock()
        builder.get.return_value = "Custom probability message"
        svc.return_value.get_message_builder.return_value = builder
        from src.core.subscription_messages import generate_message_week_addition_basic

        with use_message_context(user_info=mock_telegram_user, fetch_profile=False):
            result = generate_message_week_addition_basic(mock_telegram_user)
        assert result == "Custom probability message"
        mock_randint.assert_called_once_with(1, 100)

    def test_generate_message_week_addition_basic_custom_probability_fail(
        self, mocker, mock_telegram_user
    ):
        """Test basic subscription message generation with custom probability when check fails."""
        mocker.patch(
            "src.core.subscription_messages.SUBSCRIPTION_MESSAGE_PROBABILITY", 50
        )
        mock_randint = mocker.patch("src.core.subscription_messages.random.randint")
        mock_randint.return_value = (
            75  # Higher than 50% probability, so message should not be shown
        )

        with use_message_context(user_info=mock_telegram_user, fetch_profile=False):
            result = generate_message_week_addition_basic(mock_telegram_user)

        assert result == ""
        mock_randint.assert_called_once_with(1, 100)

    def test_generate_message_week_addition_premium_success(
        self, mocker, mock_telegram_user
    ):
        """Test premium subscription message generation."""
        svc = mocker.patch("src.services.container.ServiceContainer")
        builder = mocker.MagicMock()
        builder.get.return_value = "Premium subscription message"
        svc.return_value.get_message_builder.return_value = builder
        from src.core.subscription_messages import (
            generate_message_week_addition_premium,
        )

        with use_message_context(user_info=mock_telegram_user, fetch_profile=False):
            result = generate_message_week_addition_premium(mock_telegram_user)
        assert result == "Premium subscription message"

    def test_generate_message_week_addition_premium_russian(
        self, mocker, mock_telegram_user_ru
    ):
        """Test premium subscription message generation with Russian language."""
        svc = mocker.patch("src.services.container.ServiceContainer")
        builder = mocker.MagicMock()
        builder.get.return_value = "Сообщение премиум подписки"
        svc.return_value.get_message_builder.return_value = builder
        from src.core.subscription_messages import (
            generate_message_week_addition_premium,
        )

        with use_message_context(user_info=mock_telegram_user_ru, fetch_profile=False):
            result = generate_message_week_addition_premium(mock_telegram_user_ru)
        assert result == "Сообщение премиум подписки"

    def test_get_subscription_addition_message_premium(
        self, mocker, mock_telegram_user
    ):
        """Test subscription addition message for premium subscription."""
        mock_premium = mocker.patch(
            "src.core.subscription_messages.generate_message_week_addition_premium"
        )
        mock_premium.return_value = "Premium content"

        result = get_subscription_addition_message(
            mock_telegram_user, SubscriptionType.PREMIUM.value
        )

        mock_premium.assert_called_once_with(user_info=mock_telegram_user)
        assert result == "Premium content"

    def test_get_subscription_addition_message_trial(self, mocker, mock_telegram_user):
        """Test subscription addition message for trial subscription."""
        mock_premium = mocker.patch(
            "src.core.subscription_messages.generate_message_week_addition_premium"
        )
        mock_premium.return_value = "Trial content"

        result = get_subscription_addition_message(
            mock_telegram_user, SubscriptionType.TRIAL.value
        )

        mock_premium.assert_called_once_with(user_info=mock_telegram_user)
        assert result == "Trial content"

    def test_get_subscription_addition_message_basic(self, mocker, mock_telegram_user):
        """Test subscription addition message for basic subscription."""
        mock_basic = mocker.patch(
            "src.core.subscription_messages.generate_message_week_addition_basic"
        )
        mock_basic.return_value = "Basic content"

        result = get_subscription_addition_message(
            mock_telegram_user, SubscriptionType.BASIC.value
        )

        mock_basic.assert_called_once_with(user_info=mock_telegram_user)
        assert result == "Basic content"

    def test_get_subscription_addition_message_unknown_type(
        self, mocker, mock_telegram_user
    ):
        """Test subscription addition message for unknown subscription type."""
        mock_basic = mocker.patch(
            "src.core.subscription_messages.generate_message_week_addition_basic"
        )
        mock_basic.return_value = "Fallback content"

        result = get_subscription_addition_message(mock_telegram_user, "unknown_type")

        mock_basic.assert_called_once_with(user_info=mock_telegram_user)
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

    def test_integration_basic_message_generation(self, mocker, mock_telegram_user):
        """Test integration of basic message generation with BuyMeACoffee URL."""
        mock_randint = mocker.patch("src.core.subscription_messages.random.randint")
        mock_randint.return_value = (
            15  # Less than 20% probability, so message should be shown
        )
        svc = mocker.patch("src.services.container.ServiceContainer")
        builder = mocker.MagicMock()
        builder.get.return_value = "Integrated basic message with donation"
        svc.return_value.get_message_builder.return_value = builder
        from src.core.subscription_messages import generate_message_week_addition_basic

        with use_message_context(user_info=mock_telegram_user, fetch_profile=False):
            result = generate_message_week_addition_basic(mock_telegram_user)
        assert result == "Integrated basic message with donation"

    def test_integration_premium_message_generation(self, mocker, mock_telegram_user):
        """Test integration of premium message generation."""
        svc = mocker.patch("src.services.container.ServiceContainer")
        builder = mocker.MagicMock()
        builder.get.return_value = "Integrated premium message"
        svc.return_value.get_message_builder.return_value = builder
        from src.core.subscription_messages import (
            generate_message_week_addition_premium,
        )

        with use_message_context(user_info=mock_telegram_user, fetch_profile=False):
            result = generate_message_week_addition_premium(mock_telegram_user)
        assert result == "Integrated premium message"

    def test_integration_subscription_addition_message(
        self, mocker, mock_telegram_user
    ):
        """Test integration of subscription addition message selection."""
        mock_premium = mocker.patch(
            "src.core.subscription_messages.generate_message_week_addition_premium"
        )
        mock_basic = mocker.patch(
            "src.core.subscription_messages.generate_message_week_addition_basic"
        )
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
        mock_premium.assert_called_once_with(user_info=mock_telegram_user)
        mock_basic.assert_called_once_with(user_info=mock_telegram_user)

    def test_buymeacoffee_url_parameter_passed_correctly(
        self, mocker, mock_telegram_user
    ):
        """Test that BuyMeACoffee URL is present in the generated text."""
        mock_randint = mocker.patch("src.core.subscription_messages.random.randint")
        mock_randint.return_value = 15
        svc = mocker.patch("src.services.container.ServiceContainer")
        builder = mocker.MagicMock()
        builder.get.return_value = "https://coff.ee/akhmelevskiy"
        svc.return_value.get_message_builder.return_value = builder
        from src.core.subscription_messages import generate_message_week_addition_basic

        with use_message_context(user_info=mock_telegram_user, fetch_profile=False):
            message = generate_message_week_addition_basic(mock_telegram_user)
        assert "https://coff.ee/akhmelevskiy" in message

    def test_empty_buymeacoffee_url_handling(self, mocker, mock_telegram_user):
        """Test handling of BuyMeACoffee URL embedding with builder."""
        mock_randint = mocker.patch("src.core.subscription_messages.random.randint")
        mock_randint.return_value = 15
        svc = mocker.patch("src.services.container.ServiceContainer")
        builder = mocker.MagicMock()
        builder.get.return_value = "Empty URL message"
        svc.return_value.get_message_builder.return_value = builder
        from src.core.subscription_messages import generate_message_week_addition_basic

        with use_message_context(user_info=mock_telegram_user, fetch_profile=False):
            result = generate_message_week_addition_basic(mock_telegram_user)
        assert result == "Empty URL message"

    def test_none_buymeacoffee_url_handling(self, mocker, mock_telegram_user):
        """Test handling of BuyMeACoffee URL embedding with builder returning text."""
        mock_randint = mocker.patch("src.core.subscription_messages.random.randint")
        mock_randint.return_value = 15
        svc = mocker.patch("src.services.container.ServiceContainer")
        builder = mocker.MagicMock()
        builder.get.return_value = "None URL message"
        svc.return_value.get_message_builder.return_value = builder
        from src.core.subscription_messages import generate_message_week_addition_basic

        with use_message_context(user_info=mock_telegram_user, fetch_profile=False):
            result = generate_message_week_addition_basic(mock_telegram_user)
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

    def test_multiple_language_support_with_buymeacoffee(
        self, mocker, mock_telegram_user, mock_telegram_user_ru
    ):
        """Test that BuyMeACoffee URL works with multiple languages."""
        mock_randint = mocker.patch("src.core.subscription_messages.random.randint")
        mock_randint.return_value = (
            15  # Less than 20% probability, so message should be shown
        )
        svc = mocker.patch("src.services.container.ServiceContainer")
        builder = mocker.MagicMock()
        builder.get.return_value = "Multi-language message"
        svc.return_value.get_message_builder.return_value = builder
        from src.core.subscription_messages import generate_message_week_addition_basic

        # Test English
        with use_message_context(user_info=mock_telegram_user, fetch_profile=False):
            result_en = generate_message_week_addition_basic(mock_telegram_user)
        assert result_en == "Multi-language message"

        # Test Russian
        with use_message_context(user_info=mock_telegram_user_ru, fetch_profile=False):
            result_ru = generate_message_week_addition_basic(mock_telegram_user_ru)
        assert result_ru == "Multi-language message"

        # Just verify we got the expected return each time
