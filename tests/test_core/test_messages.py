"""Unit tests for messages module.

Tests all message generation functions in the messages module
with proper mocking, edge cases, and localization coverage.
"""

from datetime import UTC, date, datetime, time
from unittest.mock import Mock, patch

import pytest

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
from src.database.models import User, UserSettings


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
        user.language_code = "en"
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
        user.language_code = "ru"
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
        from src.database.models import SubscriptionType, UserSubscription

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

    @patch("src.core.messages.generate_message_week_addition_basic")
    @patch("src.core.messages.get_message")
    @patch("src.core.messages.LifeCalculatorEngine")
    @patch("src.core.messages.user_service")
    def test_generate_message_week_success(
        self,
        mock_user_service,
        mock_calculator,
        mock_get_message,
        mock_addition_basic,
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
        mock_get_message.return_value = (
            "Your life statistics: 33 years old, 1720 weeks lived"
        )
        mock_addition_basic.return_value = ""

        # Execute
        result = generate_message_week(mock_telegram_user)

        # Assert
        assert result == "Your life statistics: 33 years old, 1720 weeks lived"
        mock_user_service.get_user_profile.assert_called_once_with(123456789)
        mock_calculator.assert_called_once_with(user=sample_user_profile)
        mock_get_message.assert_called_once_with(
            "command_weeks",
            "statistics",
            "en",
            age=33,
            weeks_lived=1720,
            remaining_weeks=2448,
            life_percentage="41.2%",
            days_until_birthday=45,
        )

    @patch("src.core.messages.user_service")
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

    @patch("src.core.messages.generate_message_week_addition_basic")
    @patch("src.core.messages.get_message")
    @patch("src.core.messages.LifeCalculatorEngine")
    @patch("src.core.messages.user_service")
    def test_generate_message_week_russian_language(
        self,
        mock_user_service,
        mock_calculator,
        mock_get_message,
        mock_addition_basic,
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
        mock_get_message.return_value = (
            "Ваша статистика жизни: 33 года, 1720 недель прожито"
        )
        mock_addition_basic.return_value = ""

        # Execute
        result = generate_message_week(mock_telegram_user_ru)

        # Assert
        assert result == "Ваша статистика жизни: 33 года, 1720 недель прожито"
        mock_get_message.assert_called_once_with(
            "command_weeks",
            "statistics",
            "ru",
            age=33,
            weeks_lived=1720,
            remaining_weeks=2448,
            life_percentage="41.2%",
            days_until_birthday=45,
        )

    @patch("src.core.messages.get_message")
    @patch("src.core.messages.LifeCalculatorEngine")
    @patch("src.core.messages.user_service")
    def test_generate_message_visualize_success(
        self,
        mock_user_service,
        mock_calculator,
        mock_get_message,
        mock_telegram_user,
        sample_user_profile,
        mock_life_stats,
    ):
        """Test successful visualization caption message generation.

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
        mock_get_message.return_value = (
            "Visualization caption: 33 years, 1720 weeks, 41.2%"
        )

        # Execute
        result = generate_message_visualize(mock_telegram_user)

        # Assert
        assert result == "Visualization caption: 33 years, 1720 weeks, 41.2%"
        mock_get_message.assert_called_once_with(
            "command_visualize",
            "caption",
            "en",
            age=33,
            weeks_lived=1720,
            life_percentage="41.2%",
        )

    @patch("src.core.messages.get_message")
    def test_generate_message_help_success(self, mock_get_message, mock_telegram_user):
        """Test successful help message generation.

        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        mock_get_message.return_value = (
            "Available commands: /start, /weeks, /visualize, /help"
        )

        # Execute
        result = generate_message_help(mock_telegram_user)

        # Assert
        assert result == "Available commands: /start, /weeks, /visualize, /help"
        mock_get_message.assert_called_once_with("command_help", "help_text", "en")

    @patch("src.core.messages.get_message")
    def test_generate_message_help_default_language(self, mock_get_message):
        """Test help message generation with default language.

        :param mock_get_message: Mock message localization function
        :returns: None
        """
        # Setup
        user = Mock()
        user.id = 123456789
        user.username = "test_user"
        user.first_name = "Test"
        user.last_name = "User"
        user.language_code = None  # This should trigger DEFAULT_LANGUAGE

        mock_get_message.return_value = (
            "Available commands: /start, /weeks, /visualize, /help"
        )

        # Execute
        result = generate_message_help(user)

        # Assert
        assert result == "Available commands: /start, /weeks, /visualize, /help"
        mock_get_message.assert_called_once_with("command_help", "help_text", "ru")

    @patch("src.core.messages.get_message")
    def test_generate_message_cancel_success(
        self, mock_get_message, mock_telegram_user
    ):
        """Test successful cancel success message generation.

        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        mock_get_message.return_value = "Your data has been successfully deleted."

        # Execute
        result = generate_message_cancel_success(mock_telegram_user)

        # Assert
        assert result == "Your data has been successfully deleted."
        mock_get_message.assert_called_once_with("command_cancel", "user_deleted", "en")

    @patch("src.core.messages.get_message")
    def test_generate_message_cancel_error(self, mock_get_message, mock_telegram_user):
        """Test cancel error message generation.

        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        mock_get_message.return_value = "Failed to delete your data. Please try again."

        # Execute
        result = generate_message_cancel_error(mock_telegram_user)

        # Assert
        assert result == "Failed to delete your data. Please try again."
        mock_get_message.assert_called_once_with(
            "command_cancel", "deletion_error", "en"
        )

    @patch("src.core.messages.get_message")
    def test_generate_message_start_welcome_existing(
        self, mock_get_message, mock_telegram_user
    ):
        """Test welcome message generation for existing users.

        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        mock_get_message.return_value = (
            "Welcome back, Test! You are already registered."
        )

        # Execute
        result = generate_message_start_welcome_existing(mock_telegram_user)

        # Assert
        assert result == "Welcome back, Test! You are already registered."
        mock_get_message.assert_called_once_with(
            "command_start",
            "welcome_existing",
            "en",
            first_name="Test",
        )

    @patch("src.core.messages.get_message")
    def test_generate_message_start_welcome_new(
        self, mock_get_message, mock_telegram_user
    ):
        """Test welcome message generation for new users.

        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        mock_get_message.return_value = (
            "Welcome, Test! Please provide your birth date to get started."
        )

        # Execute
        result = generate_message_start_welcome_new(mock_telegram_user)

        # Assert
        assert result == "Welcome, Test! Please provide your birth date to get started."
        mock_get_message.assert_called_once_with(
            "command_start",
            "welcome_new",
            "en",
            first_name="Test",
        )

    @patch("src.core.messages.get_message")
    @patch("src.core.messages.LifeCalculatorEngine")
    @patch("src.core.messages.user_service")
    def test_generate_message_registration_success(
        self,
        mock_user_service,
        mock_calculator,
        mock_get_message,
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
        mock_get_message.return_value = (
            "Registration successful! Birth date: 1990-01-01, Age: 33, Weeks: 1720"
        )

        # Execute
        result = generate_message_registration_success(mock_telegram_user, "1990-01-01")

        # Assert
        assert (
            result
            == "Registration successful! Birth date: 1990-01-01, Age: 33, Weeks: 1720"
        )
        mock_get_message.assert_called_once_with(
            "registration",
            "success",
            "en",
            birth_date="1990-01-01",
            age=33,
            weeks_lived=1720,
        )

    @patch("src.core.messages.get_message")
    def test_generate_message_registration_error(
        self, mock_get_message, mock_telegram_user
    ):
        """Test registration error message generation.

        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        mock_get_message.return_value = "Registration failed. Please try again."

        # Execute
        result = generate_message_registration_error(mock_telegram_user)

        # Assert
        assert result == "Registration failed. Please try again."
        mock_get_message.assert_called_once_with("registration", "database_error", "en")

    @patch("src.core.messages.get_message")
    def test_generate_message_birth_date_future_error(
        self, mock_get_message, mock_telegram_user
    ):
        """Test future birth date error message generation.

        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        mock_get_message.return_value = "Birth date cannot be in the future."

        # Execute
        result = generate_message_birth_date_future_error(mock_telegram_user)

        # Assert
        assert result == "Birth date cannot be in the future."
        mock_get_message.assert_called_once_with(
            "birth_date_validation", "future_date_error", "en"
        )

    @patch("src.core.messages.get_message")
    def test_generate_message_birth_date_old_error(
        self, mock_get_message, mock_telegram_user
    ):
        """Test old birth date error message generation.

        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        mock_get_message.return_value = "Birth date cannot be before 1900."

        # Execute
        result = generate_message_birth_date_old_error(mock_telegram_user)

        # Assert
        assert result == "Birth date cannot be before 1900."
        mock_get_message.assert_called_once_with(
            "birth_date_validation", "old_date_error", "en"
        )

    @patch("src.core.messages.get_message")
    def test_generate_message_birth_date_format_error(
        self, mock_get_message, mock_telegram_user
    ):
        """Test birth date format error message generation.

        :param mock_get_message: Mock message localization function
        :param mock_telegram_user: Mock Telegram user
        :returns: None
        """
        # Setup
        mock_get_message.return_value = (
            "Invalid birth date format. Please use DD.MM.YYYY."
        )

        # Execute
        result = generate_message_birth_date_format_error(mock_telegram_user)

        # Assert
        assert result == "Invalid birth date format. Please use DD.MM.YYYY."
        mock_get_message.assert_called_once_with(
            "birth_date_validation", "format_error", "en"
        )

    @patch("src.core.messages.generate_message_week_addition_basic")
    @patch("src.core.messages.get_message")
    @patch("src.core.messages.LifeCalculatorEngine")
    @patch("src.core.messages.user_service")
    def test_generate_message_week_missing_stats_key(
        self,
        mock_user_service,
        mock_calculator,
        mock_get_message,
        mock_addition_basic,
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
    @patch("src.core.messages.user_service")
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

    @patch("src.core.messages.user_service")
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

        # Execute and Assert
        with pytest.raises(ValueError, match="User must have a valid birth date"):
            generate_message_registration_success(mock_telegram_user, "1990-01-01")

    @patch("src.core.messages.get_message")
    @patch("src.core.messages.LifeCalculatorEngine")
    @patch("src.core.messages.user_service")
    def test_generate_message_registration_success_missing_stats(
        self,
        mock_user_service,
        mock_calculator,
        mock_get_message,
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

    @patch("src.core.messages.get_message")
    def test_generate_message_week_russian_language_no_lang_code(
        self, mock_get_message, mock_telegram_user_ru
    ):
        """Test weekly statistics message generation with Russian language and no language code.

        :param mock_get_message: Mock message localization function
        :param mock_telegram_user_ru: Mock Telegram user with Russian language
        :returns: None
        """
        # Setup
        mock_telegram_user_ru.language_code = None
        mock_get_message.return_value = (
            "Your life statistics: 33 years old, 1720 weeks lived"
        )

        # Execute
        result = generate_message_help(mock_telegram_user_ru)

        # Assert
        assert result == "Your life statistics: 33 years old, 1720 weeks lived"
        mock_get_message.assert_called_once_with("command_help", "help_text", "ru")

    @patch("src.core.messages.user_service")
    @patch("src.core.messages.get_subscription_description")
    @patch("src.core.messages.get_message")
    def test_generate_message_subscription_current_success(
        self,
        mock_get_message,
        mock_get_subscription_description,
        mock_user_service,
        mock_telegram_user,
        sample_user_profile,
    ):
        """Test generate_message_subscription_current returns correct message."""
        # Setup
        from src.database.models import SubscriptionType

        sample_user_profile.subscription.subscription_type = SubscriptionType.BASIC
        mock_user_service.get_user_profile.return_value = sample_user_profile
        mock_get_subscription_description.return_value = (
            "Basic subscription description"
        )
        mock_get_message.return_value = "Subscription info"

        # Execute
        from src.core.messages import generate_message_subscription_current

        result = generate_message_subscription_current(mock_telegram_user)

        # Assert
        assert result == "Subscription info"
        mock_get_message.assert_called_once_with(
            "command_subscription",
            "current_subscription",
            "en",
            subscription_type="Basic",
            subscription_description="Basic subscription description",
        )

    @patch("src.core.messages.user_service")
    def test_generate_message_subscription_current_no_profile(
        self, mock_user_service, mock_telegram_user
    ):
        """Test generate_message_subscription_current raises ValueError if no profile."""
        mock_user_service.get_user_profile.return_value = None
        from src.core.messages import generate_message_subscription_current

        with pytest.raises(ValueError):
            generate_message_subscription_current(mock_telegram_user)

    @patch("src.core.messages.user_service")
    def test_generate_message_subscription_current_no_subscription(
        self, mock_user_service, mock_telegram_user, sample_user_profile
    ):
        """Test generate_message_subscription_current raises ValueError if no subscription."""
        sample_user_profile.subscription = None
        mock_user_service.get_user_profile.return_value = sample_user_profile
        from src.core.messages import generate_message_subscription_current

        with pytest.raises(ValueError):
            generate_message_subscription_current(mock_telegram_user)

    @patch("src.core.messages.get_message")
    def test_generate_message_subscription_invalid_type(
        self, mock_get_message, mock_telegram_user
    ):
        """Test generate_message_subscription_invalid_type returns correct message."""
        mock_get_message.return_value = "Invalid subscription type"
        from src.core.messages import generate_message_subscription_invalid_type

        result = generate_message_subscription_invalid_type(mock_telegram_user)
        assert result == "Invalid subscription type"
        mock_get_message.assert_called_once_with(
            "command_subscription", "invalid_subscription_type", "en"
        )

    @patch("src.core.messages.get_message")
    def test_generate_message_subscription_profile_error(
        self, mock_get_message, mock_telegram_user
    ):
        """Test generate_message_subscription_profile_error returns correct message."""
        mock_get_message.return_value = "Profile error"
        from src.core.messages import generate_message_subscription_profile_error

        result = generate_message_subscription_profile_error(mock_telegram_user)
        assert result == "Profile error"
        mock_get_message.assert_called_once_with(
            "command_subscription", "profile_error", "en"
        )

    @patch("src.core.messages.get_message")
    def test_generate_message_subscription_already_active(
        self, mock_get_message, mock_telegram_user
    ):
        """Test generate_message_subscription_already_active returns correct message."""
        mock_get_message.return_value = "Already active"
        from src.core.messages import generate_message_subscription_already_active

        result = generate_message_subscription_already_active(
            mock_telegram_user, "premium"
        )
        assert result == "Already active"
        mock_get_message.assert_called_once_with(
            "command_subscription", "already_active", "en", subscription_type="Premium"
        )

    @patch("src.core.messages.get_subscription_description")
    @patch("src.core.messages.get_message")
    def test_generate_message_subscription_change_success(
        self, mock_get_message, mock_get_subscription_description, mock_telegram_user
    ):
        """Test generate_message_subscription_change_success returns correct message."""
        mock_get_subscription_description.return_value = (
            "Premium subscription description"
        )
        mock_get_message.return_value = "Change success"
        from src.core.messages import generate_message_subscription_change_success

        result = generate_message_subscription_change_success(
            mock_telegram_user, "premium"
        )
        assert result == "Change success"
        mock_get_message.assert_called_once_with(
            "command_subscription",
            "change_success",
            "en",
            subscription_type="Premium",
            subscription_description="Premium subscription description",
        )

    @patch("src.core.messages.get_message")
    def test_generate_message_subscription_change_failed(
        self, mock_get_message, mock_telegram_user
    ):
        """Test generate_message_subscription_change_failed returns correct message."""
        mock_get_message.return_value = "Change failed"
        from src.core.messages import generate_message_subscription_change_failed

        result = generate_message_subscription_change_failed(mock_telegram_user)
        assert result == "Change failed"
        mock_get_message.assert_called_once_with(
            "command_subscription", "change_failed", "en"
        )

    @patch("src.core.messages.get_message")
    def test_generate_message_subscription_change_error(
        self, mock_get_message, mock_telegram_user
    ):
        """Test generate_message_subscription_change_error returns correct message."""
        mock_get_message.return_value = "Change error"
        from src.core.messages import generate_message_subscription_change_error

        result = generate_message_subscription_change_error(mock_telegram_user)
        assert result == "Change error"
        mock_get_message.assert_called_once_with(
            "command_subscription", "change_error", "en"
        )

    @patch("src.core.messages.get_message")
    def test_generate_message_week_addition_basic(
        self, mock_get_message, mock_telegram_user
    ):
        """Test generate_message_week_addition_basic returns correct message."""
        mock_get_message.return_value = "Basic addition"
        from src.core.messages import generate_message_week_addition_basic

        result = generate_message_week_addition_basic(mock_telegram_user)
        assert result == "Basic addition"
        mock_get_message.assert_called_once_with(
            "subscription_additions", "basic_addition", "en"
        )

    @patch("src.core.messages.get_message")
    def test_generate_message_week_addition_premium(
        self, mock_get_message, mock_telegram_user
    ):
        """Test generate_message_week_addition_premium returns correct message."""
        mock_get_message.return_value = "Premium addition"
        from src.core.messages import generate_message_week_addition_premium

        result = generate_message_week_addition_premium(mock_telegram_user)
        assert result == "Premium addition"
        mock_get_message.assert_called_once_with(
            "subscription_additions", "premium_addition", "en"
        )

    @patch("src.core.messages.get_message")
    def test_generate_message_unknown_command(
        self, mock_get_message, mock_telegram_user
    ):
        """Test generate_message_unknown_command returns correct message."""
        mock_get_message.return_value = "Unknown command"
        from src.core.messages import generate_message_unknown_command

        result = generate_message_unknown_command(mock_telegram_user)
        assert result == "Unknown command"
        mock_get_message.assert_called_once_with("common", "unknown_command", "en")
