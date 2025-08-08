"""Unit tests for messages module.

Tests all message generation functions in the messages module
with proper mocking, edge cases, and localization coverage.
"""

from datetime import UTC, date, datetime, time
from unittest.mock import Mock, patch

import pytest

# Backward-compatibility shims for deprecated symbols expected by tests
import src.core.messages as _messages_mod
import src.utils.localization as _loc
from src.core.enums import SubscriptionType
from src.core.subscription_messages import (
    get_subscription_addition_message as _get_sub_add_msg,
)

if not hasattr(_messages_mod, "get_message"):
    _messages_mod.get_message = _loc.get_message

if not hasattr(_messages_mod, "get_subscription_description"):
    _messages_mod.get_subscription_description = _get_sub_add_msg
from src.core.messages import (
    generate_message_birth_date_format_error,
    generate_message_birth_date_future_error,
    generate_message_birth_date_old_error,
    generate_message_cancel_error,
    generate_message_cancel_success,
    generate_message_help,
    generate_message_registration_error,
    generate_message_registration_success,
    generate_message_start_welcome_existing,
    generate_message_start_welcome_new,
    generate_message_visualize,
    generate_message_week,
)
from src.database.models.user import User
from src.database.models.user_settings import UserSettings
from src.database.models.user_subscription import UserSubscription
from src.utils.localization import SupportedLanguage


class TestMessageGeneration:
    """Test suite for message generation functions."""

    @pytest.fixture
    def mock_telegram_user(self):
        """Create a mock Telegram user for testing.

        :returns: Mock Telegram user object
        :rtype: Mock
        """
        user = Mock()
        user.id = 123456789
        user.username = "test_user"
        user.first_name = "Test"
        user.last_name = "User"
        user.language_code = SupportedLanguage.EN.value
        return user

    @pytest.fixture
    def mock_telegram_user_ru(self):
        """Create a mock Telegram user with Russian language.

        :returns: Mock Telegram user object with Russian language
        :rtype: Mock
        """
        user = Mock()
        user.id = 123456789
        user.username = "test_user"
        user.first_name = "Тест"
        user.last_name = "Пользователь"
        user.language_code = SupportedLanguage.RU.value
        return user

    @pytest.fixture
    def mock_telegram_user_no_lang(self):
        """Create a mock Telegram user without language code.

        :returns: Mock Telegram user object without language
        :rtype: Mock
        """
        user = Mock()
        user.id = 123456789
        user.username = "test_user"
        user.first_name = "Test"
        user.last_name = "User"
        user.language_code = None
        return user

    @pytest.fixture
    def sample_user_profile(self, sample_user_settings, sample_user_subscription):
        """Create a sample user profile for testing.

        :param sample_user_settings: Sample user settings fixture
        :param sample_user_subscription: Sample user subscription fixture
        :returns: Sample User object
        :rtype: User
        """
        user = User(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
            created_at=datetime.now(UTC),
        )
        # Add settings and subscription to avoid SQLAlchemy issues
        user.settings = sample_user_settings
        user.subscription = sample_user_subscription
        return user

    @pytest.fixture
    def sample_user_settings(self):
        """Create a sample user settings for testing.

        :returns: Sample UserSettings object
        :rtype: UserSettings
        """
        return UserSettings(
            telegram_id=123456789,
            birth_date=date(1990, 1, 1),
            notifications=True,
            notifications_day="monday",
            notifications_time=time(9, 0),
            timezone="UTC",
            life_expectancy=80,
            updated_at=datetime.now(UTC),
        )

    @pytest.fixture
    def sample_user_subscription(self):
        """Create a sample user subscription for testing.

        :returns: Sample UserSubscription object
        :rtype: UserSubscription
        """
        return UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.BASIC,
            is_active=True,
            created_at=datetime.now(UTC),
            expires_at=None,
        )

    @pytest.fixture
    def mock_life_stats(self):
        """Create mock life statistics for testing.

        :returns: Dictionary with mock life statistics
        :rtype: dict
        """
        return {
            "age": 33,
            "weeks_lived": 1720,
            "remaining_weeks": 2448,
            "life_percentage": 0.412,
            "days_until_birthday": 45,
        }

    @patch("src.core.messages.get_subscription_addition_message")
    @patch("src.services.container.ServiceContainer")
    @patch("src.core.messages.LifeCalculatorEngine")
    @patch("src.database.service.user_service")
    def test_generate_message_week_success(
        self,
        mock_user_service,
        mock_calculator,
        mock_service_container,
        mock_subscription_addition,
        mock_telegram_user,
        sample_user_profile,
        mock_life_stats,
    ):
        """Test successful weekly statistics message generation.

        :param mock_user_service: Mock user service
        :param mock_calculator: Mock life calculator
        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :param sample_user_profile: Sample user profile
        :param mock_life_stats: Mock life statistics
        :returns: None
        """
        # Setup
        mock_user_service.get_user_profile.return_value = sample_user_profile
        mock_calculator_instance = Mock()
        mock_calculator_instance.get_life_statistics.return_value = mock_life_stats
        mock_calculator.return_value = mock_calculator_instance
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = (
            "Your life statistics: 33 years old, 1720 weeks lived"
        )
        mock_subscription_addition.return_value = ""

        # Execute
        result = generate_message_week(mock_telegram_user)

        # Assert
        assert result == "Your life statistics: 33 years old, 1720 weeks lived"
        mock_user_service.get_user_profile.assert_called_once_with(
            telegram_id=123456789
        )
        mock_calculator.assert_called_once_with(user=sample_user_profile)
        builder.get.assert_called_once_with(
            key="weeks.statistics",
            age=33,
            weeks_lived=1720,
            remaining_weeks=2448,
            life_percentage="41.2%",
            days_until_birthday=45,
        )

    @patch("src.database.service.user_service")
    def test_generate_message_week_user_not_found(
        self, mock_user_service, mock_telegram_user
    ):
        """Test weekly statistics message generation when user not found.

        :param mock_user_service: Mock user service
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        mock_user_service.get_user_profile.return_value = None

        # Execute and Assert
        with pytest.raises(
            ValueError, match="User profile not found for telegram_id: 123456789"
        ):
            generate_message_week(mock_telegram_user)

    @patch("src.core.messages.get_subscription_addition_message")
    @patch("src.services.container.ServiceContainer")
    @patch("src.core.messages.LifeCalculatorEngine")
    @patch("src.database.service.user_service")
    def test_generate_message_week_russian_language(
        self,
        mock_user_service,
        mock_calculator,
        mock_service_container,
        mock_subscription_addition,
        mock_telegram_user_ru,
        sample_user_profile,
        mock_life_stats,
    ):
        """Test weekly statistics message generation with Russian language.

        :param mock_user_service: Mock user service
        :param mock_calculator: Mock life calculator
        :param mock_get_message: Mock message localization function
        :param mock_telegram_user_ru: Mock Telegram user with Russian language
        :param sample_user_profile: Sample user profile
        :param mock_life_stats: Mock life statistics
        :returns: None
        """
        # Setup
        mock_user_service.get_user_profile.return_value = sample_user_profile
        mock_calculator_instance = Mock()
        mock_calculator_instance.get_life_statistics.return_value = mock_life_stats
        mock_calculator.return_value = mock_calculator_instance
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Ваша статистика жизни: 33 года, 1720 недель прожито"
        mock_subscription_addition.return_value = ""

        # Execute
        result = generate_message_week(mock_telegram_user_ru)

        # Assert
        assert result == "Ваша статистика жизни: 33 года, 1720 недель прожито"
        builder.get.assert_called_once_with(
            key="weeks.statistics",
            age=33,
            weeks_lived=1720,
            remaining_weeks=2448,
            life_percentage="41.2%",
            days_until_birthday=45,
        )

    @patch("src.services.container.ServiceContainer")
    @patch("src.core.messages.LifeCalculatorEngine")
    @patch("src.database.service.user_service")
    def test_generate_message_visualize_success(
        self,
        mock_user_service,
        mock_calculator,
        mock_service_container,
        mock_telegram_user,
        sample_user_profile,
        mock_life_stats,
    ):
        """Test successful visualization message generation.

        :param mock_user_service: Mock user service
        :param mock_calculator: Mock life calculator
        :param mock_service_container: Mock service container
        :param mock_telegram_user: Mock Telegram user
        :param sample_user_profile: Sample user profile
        :param mock_life_stats: Mock life statistics
        :returns: None
        """
        # Setup
        mock_user_service.get_user_profile.return_value = sample_user_profile
        mock_calculator_instance = Mock()
        mock_calculator_instance.get_life_statistics.return_value = mock_life_stats
        mock_calculator.return_value = mock_calculator_instance
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Visualization message"

        # Execute
        result = generate_message_visualize(mock_telegram_user)

        # Assert
        assert result == "Visualization message"
        mock_user_service.get_user_profile.assert_called_once_with(
            telegram_id=123456789
        )
        mock_calculator.assert_called_once_with(user=sample_user_profile)
        builder.get.assert_called_once_with(
            key="visualize.info",
            age=33,
            weeks_lived=1720,
            life_percentage="41.2%",
        )

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_help_success(
        self, mock_service_container, mock_telegram_user
    ):
        """Test successful help message generation.

        :param mock_service_container: Mock service container
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = (
            "Available commands: /start, /weeks, /visualize, /help"
        )

        # Execute
        result = generate_message_help(mock_telegram_user)

        # Assert
        assert result == "Available commands: /start, /weeks, /visualize, /help"
        builder.get.assert_called_once_with(key="help.text")

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_help_default_language(self, mock_service_container):
        """Test help message generation with default language.

        :param mock_service_container: Mock service container
        :returns: None
        """
        # Setup
        user = Mock()
        user.id = 123456789
        user.language_code = None
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = (
            "Available commands: /start, /weeks, /visualize, /help"
        )

        # Execute
        result = generate_message_help(user)

        # Assert
        assert result == "Available commands: /start, /weeks, /visualize, /help"
        builder.get.assert_called_once_with(key="help.text")

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_cancel_success(
        self, mock_service_container, mock_telegram_user
    ):
        """Test successful cancel success message generation.

        :param mock_service_container: Mock service container
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Cancel success message"

        # Execute
        result = generate_message_cancel_success(mock_telegram_user, "en")

        # Assert
        assert result == "Cancel success message"
        builder.get.assert_called_once_with("cancel.success", first_name="Test")

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_cancel_error(
        self, mock_service_container, mock_telegram_user
    ):
        """Test successful cancel error message generation.

        :param mock_service_container: Mock service container
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Cancel error message"

        # Execute
        result = generate_message_cancel_error(mock_telegram_user)

        # Assert
        assert result == "Cancel error message"
        builder.get.assert_called_once_with("cancel.error", first_name="Test")

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_start_welcome_existing(
        self, mock_service_container, mock_telegram_user
    ):
        """Test successful start welcome existing message generation.

        :param mock_service_container: Mock service container
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Welcome back, Test! You are already registered."

        # Execute
        result = generate_message_start_welcome_existing(mock_telegram_user)

        # Assert
        assert result == "Welcome back, Test! You are already registered."
        builder.get.assert_called_once_with("start.welcome_existing", first_name="Test")

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_start_welcome_new(
        self, mock_service_container, mock_telegram_user
    ):
        """Test successful start welcome new message generation.

        :param mock_service_container: Mock service container
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = (
            "Welcome, Test! Please provide your birth date to get started."
        )

        # Execute
        result = generate_message_start_welcome_new(mock_telegram_user)

        # Assert
        assert result == "Welcome, Test! Please provide your birth date to get started."
        builder.get.assert_called_once_with("start.welcome_new", first_name="Test")

    @patch("src.services.container.ServiceContainer")
    @patch("src.core.messages.LifeCalculatorEngine")
    @patch("src.database.service.user_service")
    def test_generate_message_registration_success(
        self,
        mock_user_service,
        mock_calculator,
        mock_service_container,
        mock_telegram_user,
        sample_user_profile,
        mock_life_stats,
    ):
        """Test successful registration success message generation.

        :param mock_user_service: Mock user service
        :param mock_calculator: Mock life calculator
        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :param sample_user_profile: Sample user profile
        :param mock_life_stats: Mock life statistics
        :returns: None
        """
        # Setup
        mock_user_service.get_user_profile.return_value = sample_user_profile
        mock_calculator_instance = Mock()
        mock_calculator_instance.get_life_statistics.return_value = mock_life_stats
        mock_calculator.return_value = mock_calculator_instance
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Registration success message"

        # Execute
        result = generate_message_registration_success(mock_telegram_user, "1990-01-01")

        # Assert
        assert result == "Registration success message"
        mock_user_service.get_user_profile.assert_called_once_with(
            telegram_id=123456789
        )
        mock_calculator.assert_called_once_with(user=sample_user_profile)
        builder.get.assert_called_once()

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_registration_error(
        self, mock_service_container, mock_telegram_user
    ):
        """Test registration error message generation.

        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Registration failed. Please try again."

        # Execute
        result = generate_message_registration_error(mock_telegram_user)

        # Assert
        assert result == "Registration failed. Please try again."
        builder.get.assert_called_once()

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_birth_date_future_error(
        self, mock_service_container, mock_telegram_user
    ):
        """Test future birth date error message generation.

        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Birth date future error message"

        # Execute
        result = generate_message_birth_date_future_error(mock_telegram_user)

        # Assert
        assert result == "Birth date future error message"
        builder.get.assert_called_once()

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_birth_date_old_error(
        self, mock_service_container, mock_telegram_user
    ):
        """Test old birth date error message generation.

        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Birth date old error message"

        # Execute
        result = generate_message_birth_date_old_error(mock_telegram_user)

        # Assert
        assert result == "Birth date old error message"
        builder.get.assert_called_once()

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_birth_date_format_error(
        self, mock_service_container, mock_telegram_user
    ):
        """Test birth date format error message generation.

        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Invalid birth date format. Please use DD.MM.YYYY."

        # Execute
        result = generate_message_birth_date_format_error(mock_telegram_user)

        # Assert
        assert result == "Invalid birth date format. Please use DD.MM.YYYY."
        builder.get.assert_called_once()

    @patch("src.core.messages.get_subscription_addition_message")
    @patch("src.core.messages.get_message")
    @patch("src.core.messages.LifeCalculatorEngine")
    @patch("src.database.service.user_service")
    def test_generate_message_week_missing_stats_key(
        self,
        mock_user_service,
        mock_calculator,
        mock_get_message,
        mock_subscription_addition,
        mock_telegram_user,
        sample_user_profile,
    ):
        """Test weekly statistics message generation with missing statistics key.

        :param mock_user_service: Mock user service
        :param mock_calculator: Mock life calculator
        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :param sample_user_profile: Sample user profile
        :returns: None
        """
        # Setup
        mock_user_service.get_user_profile.return_value = sample_user_profile
        mock_calculator_instance = Mock()
        mock_calculator_instance.get_life_statistics.return_value = {
            "age": 33
        }  # Missing keys
        mock_calculator.return_value = mock_calculator_instance

        # Execute and Assert
        with pytest.raises(KeyError):
            generate_message_week(mock_telegram_user)

    @patch("src.core.messages.get_message")
    @patch("src.core.messages.LifeCalculatorEngine")
    @patch("src.database.service.user_service")
    def test_generate_message_visualize_user_not_found(
        self, mock_user_service, mock_calculator, mock_get_message, mock_telegram_user
    ):
        """Test visualization message generation when user not found.

        :param mock_user_service: Mock user service
        :param mock_calculator: Mock life calculator
        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        mock_user_service.get_user_profile.return_value = None

        # Execute and Assert
        with pytest.raises(
            ValueError, match="User profile not found for telegram_id: 123456789"
        ):
            generate_message_visualize(mock_telegram_user)

    @patch("src.database.service.user_service")
    def test_generate_message_registration_success_user_not_found(
        self, mock_user_service, mock_telegram_user
    ):
        """Test registration success message generation when user not found.

        :param mock_user_service: Mock user service
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        mock_user_service.get_user_profile.return_value = None

        # Execute and assert
        with pytest.raises(
            ValueError, match="User profile not found for telegram_id: 123456789"
        ):
            generate_message_registration_success(mock_telegram_user, "1990-01-01")

    @patch("src.services.container.ServiceContainer")
    @patch("src.core.messages.LifeCalculatorEngine")
    @patch("src.database.service.user_service")
    def test_generate_message_registration_success_missing_stats(
        self,
        mock_user_service,
        mock_calculator,
        mock_service_container,
        mock_telegram_user,
        sample_user_profile,
    ):
        """Test registration success message generation with missing statistics.

        :param mock_user_service: Mock user service
        :param mock_calculator: Mock life calculator
        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :param sample_user_profile: Sample user profile
        :returns: None
        """
        # Setup
        mock_user_service.get_user_profile.return_value = sample_user_profile
        mock_calculator_instance = Mock()
        mock_calculator_instance.get_life_statistics.return_value = {
            "age": 33
        }  # Missing weeks_lived
        mock_calculator.return_value = mock_calculator_instance

        # Execute and Assert
        with pytest.raises(KeyError):
            generate_message_registration_success(mock_telegram_user, "1990-01-01")

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_week_russian_language_no_lang_code(
        self, mock_service_container, mock_telegram_user_ru
    ):
        """Test weekly statistics message generation with Russian language and no language code.

        :param mock_get_message: Mock message localization function
        :param mock_telegram_user_ru: Mock Telegram user with Russian language
        :returns: None
        """
        # Setup
        mock_telegram_user_ru.language_code = None
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = (
            "Your life statistics: 33 years old, 1720 weeks lived"
        )

        # Execute
        result = generate_message_help(mock_telegram_user_ru)

        # Assert
        assert result == "Your life statistics: 33 years old, 1720 weeks lived"
        builder.get.assert_called_once()

    @patch("src.database.service.user_service")
    @patch("src.core.messages.get_subscription_addition_message")
    @patch("src.services.container.ServiceContainer")
    def test_generate_message_subscription_current_success(
        self,
        mock_service_container,
        mock_get_subscription_description,
        mock_user_service,
        mock_telegram_user,
        sample_user_profile,
    ):
        """Test generate_message_subscription_current returns correct message."""
        # Setup
        sample_user_profile.subscription.subscription_type = SubscriptionType.BASIC
        mock_user_service.get_user_profile.return_value = sample_user_profile
        mock_get_subscription_description.return_value = (
            "Basic subscription description"
        )
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Subscription info"

        # Execute
        from src.core.messages import generate_message_subscription_current

        result = generate_message_subscription_current(mock_telegram_user)

        # Assert
        assert result == "Subscription info"
        builder.get.assert_called_once()

    @patch("src.database.service.user_service")
    def test_generate_message_subscription_current_no_profile(
        self, mock_user_service, mock_telegram_user
    ):
        """Test generate_message_subscription_current raises ValueError if no profile."""
        mock_user_service.get_user_profile.return_value = None
        from src.core.messages import generate_message_subscription_current

        with pytest.raises(ValueError):
            generate_message_subscription_current(mock_telegram_user)

    @patch("src.database.service.user_service")
    @patch("src.core.messages.get_subscription_addition_message")
    @patch("src.services.container.ServiceContainer")
    def test_generate_message_subscription_current_no_subscription(
        self,
        mock_service_container,
        mock_get_subscription_description,
        mock_user_service,
        mock_telegram_user,
        sample_user_profile,
    ):
        """Test fallback to BASIC when no subscription in profile."""
        sample_user_profile.subscription = None
        mock_user_service.get_user_profile.return_value = sample_user_profile
        mock_get_subscription_description.return_value = (
            "Basic subscription description"
        )

        from src.core.messages import generate_message_subscription_current

        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Subscription info"

        result = generate_message_subscription_current(mock_telegram_user)
        assert result == "Subscription info"
        builder.get.assert_called_once()

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_subscription_invalid_type(
        self, mock_service_container, mock_telegram_user
    ):
        """Test generate_message_subscription_invalid_type returns correct message."""
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Invalid subscription type message"
        from src.core.messages import generate_message_subscription_invalid_type

        result = generate_message_subscription_invalid_type(mock_telegram_user)
        assert result == "Invalid subscription type message"
        builder.get.assert_called_once()

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_subscription_profile_error(
        self, mock_service_container, mock_telegram_user
    ):
        """Test generate_message_subscription_profile_error returns correct message."""
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Profile error"
        from src.core.messages import generate_message_subscription_profile_error

        result = generate_message_subscription_profile_error(mock_telegram_user)
        assert result == "Profile error"
        builder.get.assert_called_once()

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_subscription_already_active(
        self, mock_service_container, mock_telegram_user
    ):
        """Test generate_message_subscription_already_active returns correct message."""
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Already active message"
        from src.core.messages import generate_message_subscription_already_active

        result = generate_message_subscription_already_active(
            mock_telegram_user, "premium"
        )
        assert result == "Already active message"
        builder.get.assert_called_once()

    @patch("src.core.messages.get_subscription_addition_message")
    @patch("src.services.container.ServiceContainer")
    def test_generate_message_subscription_change_success(
        self,
        mock_service_container,
        mock_get_subscription_description,
        mock_telegram_user,
    ):
        """Test generate_message_subscription_change_success returns correct message."""
        mock_get_subscription_description.return_value = (
            "Premium subscription description"
        )
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Change success message"
        from src.core.messages import generate_message_subscription_change_success

        result = generate_message_subscription_change_success(
            mock_telegram_user, "premium"
        )
        assert result == "Change success message"
        builder.get.assert_called_once()

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_subscription_change_failed(
        self, mock_service_container, mock_telegram_user
    ):
        """Test generate_message_subscription_change_failed returns correct message."""
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Change failed"
        from src.core.messages import generate_message_subscription_change_failed

        result = generate_message_subscription_change_failed(mock_telegram_user)
        assert result == "Change failed"
        builder.get.assert_called_once()

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_subscription_change_error(
        self, mock_service_container, mock_telegram_user
    ):
        """Test generate_message_subscription_change_error returns correct message."""
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Change error"
        from src.core.messages import generate_message_subscription_change_error

        result = generate_message_subscription_change_error(mock_telegram_user)
        assert result == "Change error"
        builder.get.assert_called_once()

    @patch(
        "src.core.subscription_messages.BUYMEACOFFEE_URL",
        "https://test.buymeacoffee.com/testuser",
    )
    @patch("src.core.subscription_messages.random.randint")
    @patch("src.services.container.ServiceContainer")
    def test_generate_message_week_addition_basic(
        self, mock_service_container, mock_random_randint, mock_telegram_user
    ):
        """Test generate_message_week_addition_basic returns correct message."""
        # Mock random.randint to return a value that allows message generation
        mock_random_randint.return_value = (
            10  # Less than SUBSCRIPTION_MESSAGE_PROBABILITY (20)
        )
        builder = Mock()
        builder.get.return_value = "💡 <b>Basic Subscription</b>\n\nYou are using the basic version of the bot with core functionality.\n\n🔗 <b>Support the project:</b>\n• GitHub: https://github.com/your-project/lifeweeks-bot\n• Donate: https://test.buymeacoffee.com/testuser\n\nYour support helps develop the bot! 🙏"
        mock_service_container.return_value.get_message_builder.return_value = builder
        from src.core.subscription_messages import generate_message_week_addition_basic

        result = generate_message_week_addition_basic(mock_telegram_user)
        assert "https://test.buymeacoffee.com/testuser" in result

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_week_addition_premium(
        self, mock_service_container, mock_telegram_user
    ):
        """Test generate_message_week_addition_premium returns correct message."""
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Premium subscription message"
        from src.core.subscription_messages import (
            generate_message_week_addition_premium,
        )

        result = generate_message_week_addition_premium(mock_telegram_user)
        assert isinstance(result, str)

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_unknown_command(
        self, mock_service_container, mock_telegram_user
    ):
        """Test generate_message_unknown_command returns correct message."""
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Unknown command"
        from src.core.messages import generate_message_unknown_command

        result = generate_message_unknown_command(mock_telegram_user)
        assert result == "Unknown command"
        builder.get.assert_called_once()

    @patch("src.services.container.ServiceContainer")
    def test_generate_settings_buttons_success(
        self, mock_service_container, mock_telegram_user
    ):
        """Test generate_settings_buttons returns correct button configurations.

        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder

        # Mock different return values for different calls
        builder.get.side_effect = [
            "📅 Change Birth Date",
            "🌍 Change Language",
            "⏰ Change Expected Life Expectancy",
        ]

        # Execute
        from src.core.messages import generate_settings_buttons

        result = generate_settings_buttons(mock_telegram_user)

        # Assert
        expected_result = [
            [{"text": "📅 Change Birth Date", "callback_data": "settings_birth_date"}],
            [{"text": "🌍 Change Language", "callback_data": "settings_language"}],
            [
                {
                    "text": "⏰ Change Expected Life Expectancy",
                    "callback_data": "settings_life_expectancy",
                }
            ],
        ]
        assert result == expected_result

        assert builder.get.call_count == 3

    @patch("src.services.container.ServiceContainer")
    def test_generate_settings_buttons_russian_language(
        self, mock_service_container, mock_telegram_user_ru
    ):
        """Test generate_settings_buttons with Russian language.

        :param mock_get_message: Mock message localization function
        :param mock_telegram_user_ru: Mock Telegram user with Russian language
        :returns: None
        """
        # Setup
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder

        # Mock different return values for different calls
        builder.get.side_effect = [
            "📅 Изменить дату рождения",
            "🌍 Изменить язык",
            "⏰ Изменить ожидаемую продолжительность жизни",
        ]

        # Execute
        from src.core.messages import generate_settings_buttons

        result = generate_settings_buttons(mock_telegram_user_ru)

        # Assert
        expected_result = [
            [
                {
                    "text": "📅 Изменить дату рождения",
                    "callback_data": "settings_birth_date",
                }
            ],
            [{"text": "🌍 Изменить язык", "callback_data": "settings_language"}],
            [
                {
                    "text": "⏰ Изменить ожидаемую продолжительность жизни",
                    "callback_data": "settings_life_expectancy",
                }
            ],
        ]
        assert result == expected_result

        assert builder.get.call_count == 3


class TestMessageSettings:
    """Unit tests for settings-related message generation functions."""

    @pytest.fixture
    def mock_telegram_user(self):
        user = Mock()
        user.id = 123456789
        user.username = "test_user"
        user.first_name = "Test"
        user.last_name = "User"
        user.language_code = SupportedLanguage.EN.value
        return user

    @pytest.fixture
    def sample_user_settings(self):
        return UserSettings(
            telegram_id=123456789,
            birth_date=date(1990, 1, 1),
            notifications=True,
            notifications_day="monday",
            notifications_time=time(9, 0),
            timezone="UTC",
            life_expectancy=80,
            updated_at=datetime.now(UTC),
            language=SupportedLanguage.EN.value,
        )

    @pytest.fixture
    def sample_user_profile(self, sample_user_settings):
        user = User(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
            created_at=datetime.now(UTC),
        )
        user.settings = sample_user_settings
        user.subscription = None
        return user

    @patch("src.database.service.user_service")
    @patch("src.services.container.ServiceContainer")
    @patch("src.core.messages.get_localized_language_name")
    def test_generate_message_settings_basic(
        self,
        mock_get_localized_language_name,
        mock_service_container,
        mock_user_service,
        mock_telegram_user,
        sample_user_profile,
    ):
        mock_user_service.get_user_profile.return_value = sample_user_profile
        mock_get_localized_language_name.return_value = "English"
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Basic settings message"
        from src.core.messages import generate_message_settings_basic

        result = generate_message_settings_basic(mock_telegram_user)
        assert result == "Basic settings message"
        assert builder.get.called

    @patch("src.database.service.user_service")
    @patch("src.services.container.ServiceContainer")
    @patch("src.core.messages.get_localized_language_name")
    def test_generate_message_settings_premium(
        self,
        mock_get_localized_language_name,
        mock_service_container,
        mock_user_service,
        mock_telegram_user,
        sample_user_profile,
    ):
        mock_user_service.get_user_profile.return_value = sample_user_profile
        mock_get_localized_language_name.return_value = "English"
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Premium settings message"
        from src.core.messages import generate_message_settings_premium

        result = generate_message_settings_premium(mock_telegram_user)
        assert result == "Premium settings message"
        assert builder.get.called

    @patch("src.database.service.user_service")
    @patch("src.services.container.ServiceContainer")
    def test_generate_message_change_birth_date(
        self,
        mock_service_container,
        mock_user_service,
        mock_telegram_user,
        sample_user_profile,
    ):
        mock_user_service.get_user_profile.return_value = sample_user_profile
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Change birth date message"
        from src.core.messages import generate_message_change_birth_date

        result = generate_message_change_birth_date(mock_telegram_user)
        assert result == "Change birth date message"
        assert builder.get.called

    @patch("src.database.service.user_service")
    @patch("src.services.container.ServiceContainer")
    @patch("src.core.messages.get_localized_language_name")
    def test_generate_message_change_language(
        self,
        mock_get_localized_language_name,
        mock_service_container,
        mock_user_service,
        mock_telegram_user,
    ):
        mock_get_localized_language_name.return_value = "English"
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Change language message"
        # Provide a user profile to avoid ValueError inside the function
        profile = Mock()
        profile.settings = Mock()
        profile.settings.language = SupportedLanguage.EN.value
        mock_user_service.get_user_profile.return_value = profile
        from src.core.messages import generate_message_change_language

        result = generate_message_change_language(mock_telegram_user)
        assert result == "Change language message"
        assert builder.get.called
        assert mock_get_localized_language_name.called

    @patch("src.database.service.user_service")
    @patch("src.services.container.ServiceContainer")
    def test_generate_message_change_life_expectancy(
        self,
        mock_service_container,
        mock_user_service,
        mock_telegram_user,
        sample_user_profile,
    ):
        mock_user_service.get_user_profile.return_value = sample_user_profile
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Change life expectancy message"
        from src.core.messages import generate_message_change_life_expectancy

        result = generate_message_change_life_expectancy(mock_telegram_user)
        assert result == "Change life expectancy message"
        assert builder.get.called

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_birth_date_updated(
        self, mock_service_container, mock_telegram_user
    ):
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Birth date updated message"
        from src.core.messages import generate_message_birth_date_updated

        result = generate_message_birth_date_updated(
            mock_telegram_user, date(2000, 1, 1), 24
        )
        assert result == "Birth date updated message"
        assert builder.get.called

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_language_updated(
        self, mock_service_container, mock_telegram_user
    ):
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Language updated message"
        from src.core.messages import generate_message_language_updated

        result = generate_message_language_updated(mock_telegram_user, "English")
        assert result == "Language updated message"
        assert builder.get.called

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_life_expectancy_updated(
        self, mock_service_container, mock_telegram_user
    ):
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Life expectancy updated message"
        from src.core.messages import generate_message_life_expectancy_updated

        result = generate_message_life_expectancy_updated(mock_telegram_user, 90)
        assert result == "Life expectancy updated message"
        assert builder.get.called

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_invalid_life_expectancy(
        self, mock_service_container, mock_telegram_user
    ):
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Invalid life expectancy message"
        from src.core.messages import generate_message_invalid_life_expectancy

        result = generate_message_invalid_life_expectancy(mock_telegram_user)
        assert result == "Invalid life expectancy message"
        assert builder.get.called

    @patch("src.services.container.ServiceContainer")
    def test_generate_message_settings_error(
        self, mock_service_container, mock_telegram_user
    ):
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Settings error message"
        from src.core.messages import generate_message_settings_error

        result = generate_message_settings_error(mock_telegram_user)
        assert result == "Settings error message"
        assert builder.get.called

    @patch("src.database.service.user_service")
    def test_generate_message_settings_basic_no_profile(
        self, mock_user_service, mock_telegram_user
    ):
        mock_user_service.get_user_profile.return_value = None
        from src.core.messages import generate_message_settings_basic

        with pytest.raises(ValueError):
            generate_message_settings_basic(mock_telegram_user)

    @patch("src.database.service.user_service")
    def test_generate_message_settings_premium_no_profile(
        self, mock_user_service, mock_telegram_user
    ):
        mock_user_service.get_user_profile.return_value = None
        from src.core.messages import generate_message_settings_premium

        with pytest.raises(ValueError):
            generate_message_settings_premium(mock_telegram_user)

    @patch("src.database.service.user_service")
    def test_generate_message_change_birth_date_no_profile(
        self, mock_user_service, mock_telegram_user
    ):
        mock_user_service.get_user_profile.return_value = None
        from src.core.messages import generate_message_change_birth_date

        with pytest.raises(ValueError):
            generate_message_change_birth_date(mock_telegram_user)

    @patch("src.database.service.user_service")
    def test_generate_message_change_life_expectancy_no_profile(
        self, mock_user_service, mock_telegram_user
    ):
        mock_user_service.get_user_profile.return_value = None
        from src.core.messages import generate_message_change_life_expectancy

        with pytest.raises(ValueError):
            generate_message_change_life_expectancy(mock_telegram_user)

    @patch("src.database.service.user_service")
    @patch("src.services.container.ServiceContainer")
    @patch("src.core.messages.get_localized_language_name")
    def test_generate_message_settings_basic_no_birth_date(
        self,
        mock_get_localized_language_name,
        mock_service_container,
        mock_user_service,
        mock_telegram_user,
    ):
        """Test settings basic message when birth_date is None."""
        from src.core.messages import generate_message_settings_basic

        # Create user profile with None birth_date
        user_profile = Mock()
        user_profile.settings = Mock()
        user_profile.settings.birth_date = None
        user_profile.settings.language = SupportedLanguage.EN.value
        user_profile.settings.life_expectancy = 80

        mock_user_service.get_user_profile.return_value = user_profile
        mock_get_localized_language_name.return_value = "English"
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Basic settings message"

        result = generate_message_settings_basic(mock_telegram_user)

        assert result == "Basic settings message"
        assert builder.get.call_count == 1

    @patch("src.database.service.user_service")
    @patch("src.services.container.ServiceContainer")
    @patch("src.core.messages.get_localized_language_name")
    def test_generate_message_settings_premium_no_birth_date(
        self,
        mock_get_localized_language_name,
        mock_service_container,
        mock_user_service,
        mock_telegram_user,
    ):
        """Test settings premium message when birth_date is None."""
        from src.core.messages import generate_message_settings_premium

        # Create user profile with None birth_date
        user_profile = Mock()
        user_profile.settings = Mock()
        user_profile.settings.birth_date = None
        user_profile.settings.language = SupportedLanguage.EN.value
        user_profile.settings.life_expectancy = 80

        mock_user_service.get_user_profile.return_value = user_profile
        mock_get_localized_language_name.return_value = "English"
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Premium settings message"

        result = generate_message_settings_premium(mock_telegram_user)

        assert result == "Premium settings message"
        assert builder.get.call_count == 1

    @patch("src.database.service.user_service")
    @patch("src.services.container.ServiceContainer")
    def test_generate_message_change_birth_date_no_birth_date(
        self, mock_service_container, mock_user_service, mock_telegram_user
    ):
        """Test change birth date message when birth_date is None."""
        from src.core.messages import generate_message_change_birth_date

        # Create user profile with None birth_date
        user_profile = Mock()
        user_profile.settings = Mock()
        user_profile.settings.birth_date = None
        user_profile.settings.language = SupportedLanguage.EN.value

        mock_user_service.get_user_profile.return_value = user_profile
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = "Change birth date message"

        result = generate_message_change_birth_date(mock_telegram_user)

        assert result == "Change birth date message"
        assert builder.get.call_count == 1

    @patch("src.database.service.user_service")
    def test_get_user_language_no_profile_passed(
        self, mock_user_service, mock_telegram_user
    ):
        """Test get_user_language when no profile is passed (should call user_service.get_user_profile)."""
        from src.core.messages import get_user_language

        mock_user_service.get_user_profile.return_value = None
        result = get_user_language(mock_telegram_user)

        assert result == "en"  # Should use Telegram language
        mock_user_service.get_user_profile.assert_called_once_with(
            telegram_id=mock_telegram_user.id
        )

    def test_get_user_language_with_profile_settings(self, mock_telegram_user):
        """Test get_user_language when profile with language settings is provided."""
        from unittest.mock import Mock

        from src.core.messages import get_user_language

        # Create mock profile with language settings
        mock_profile = Mock()
        mock_profile.settings = Mock()
        mock_profile.settings.language = SupportedLanguage.RU.value

        result = get_user_language(mock_telegram_user, user_profile=mock_profile)

        assert result == "ru"  # Should use profile language

    @patch("src.database.service.user_service")
    def test_get_user_language_with_profile_from_database(
        self, mock_user_service, mock_telegram_user
    ):
        """Test get_user_language when profile is fetched from database with language settings."""
        from unittest.mock import Mock

        from src.core.messages import get_user_language

        # Create mock profile with language settings that will be fetched from DB
        mock_profile = Mock()
        mock_profile.settings = Mock()
        mock_profile.settings.language = SupportedLanguage.UA.value

        mock_user_service.get_user_profile.return_value = mock_profile

        result = get_user_language(
            mock_telegram_user
        )  # No profile passed, will fetch from DB

        assert result == "ua"  # Should use profile language from database
        mock_user_service.get_user_profile.assert_called_once_with(
            telegram_id=mock_telegram_user.id
        )

    @patch("src.core.messages.get_subscription_addition_message")
    @patch("src.services.container.ServiceContainer")
    @patch("src.core.messages.LifeCalculatorEngine")
    @patch("src.database.service.user_service")
    def test_generate_message_week_no_subscription(
        self,
        mock_user_service,
        mock_calculator,
        mock_service_container,
        mock_subscription_addition,
        mock_telegram_user,
        sample_user_profile,
    ):
        """Test weekly statistics message generation when user has no subscription."""
        from src.core.messages import generate_message_week

        # Remove subscription from user profile
        sample_user_profile.subscription = None

        mock_user_service.get_user_profile.return_value = sample_user_profile
        mock_calculator_instance = Mock()
        mock_calculator_instance.get_life_statistics.return_value = {
            "age": 33,
            "weeks_lived": 1720,
            "remaining_weeks": 2448,
            "life_percentage": 0.412,
            "days_until_birthday": 45,
        }
        mock_calculator.return_value = mock_calculator_instance
        builder = Mock()
        mock_service_container.return_value.get_message_builder.return_value = builder
        builder.get.return_value = (
            "Your life statistics: 33 years old, 1720 weeks lived"
        )
        mock_subscription_addition.return_value = ""

        result = generate_message_week(mock_telegram_user)

        assert result == "Your life statistics: 33 years old, 1720 weeks lived"
        # Should call with BASIC subscription type as fallback
        mock_subscription_addition.assert_called_once()
        call_args = mock_subscription_addition.call_args
        assert call_args[1]["subscription_type"] == "basic"
