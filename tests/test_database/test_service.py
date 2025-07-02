"""Unit tests for UserService class.

Tests all methods of the UserService class using pytest
with proper fixtures, mocking, and edge case coverage.
"""

from datetime import UTC, date, datetime, time
from unittest.mock import Mock, patch

import pytest

from src.database.models import User, UserSettings
from src.database.service import (
    UserDeletionError,
    UserRegistrationError,
    UserService,
    UserServiceError,
    user_service,
)
from src.database.sqlite_repository import SQLAlchemyUserRepository


class TestUserService:
    """Test suite for UserService class."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing.

        :returns: Mock repository instance
        :rtype: Mock
        """
        return Mock(spec=SQLAlchemyUserRepository)

    @pytest.fixture
    def service(self, mock_repository):
        """Create service instance with mock repository.

        :param mock_repository: Mock repository instance
        :returns: UserService instance
        :rtype: UserService
        """
        return UserService(mock_repository)

    @pytest.fixture
    def sample_user(self):
        """Create a sample User object for testing.

        :returns: Sample User object
        :rtype: User
        """
        return User(
            telegram_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User",
            created_at=datetime.now(UTC),
        )

    @pytest.fixture
    def sample_settings(self):
        """Create a sample UserSettings object for testing.

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

    def test_init_with_repository(self, mock_repository):
        """Test service initialization with provided repository.

        :param mock_repository: Mock repository instance
        :returns: None
        """
        service = UserService(mock_repository)
        assert service.repository is mock_repository

    def test_init_without_repository(self):
        """Test service initialization without repository.

        :returns: None
        """
        service = UserService()
        assert isinstance(service.repository, SQLAlchemyUserRepository)

    @patch("src.database.service.datetime")
    def test_create_user_with_settings_success(
        self, mock_datetime, service, mock_repository
    ):
        """Test successful user creation with settings.

        :param mock_datetime: Mock datetime module
        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        from unittest.mock import Mock

        from telegram import User as TelegramUser

        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 123456789
        mock_user.username = "test_user"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"

        mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.strptime.return_value = datetime(2023, 1, 1, 9, 0, 0)
        mock_repository.get_user_profile.return_value = None  # User doesn't exist
        mock_repository.create_user_profile.return_value = True

        # Execute
        service.create_user_with_settings(
            user_info=mock_user,
            birth_date=date(1990, 1, 1),
            notifications_enabled=True,
            timezone="UTC",
            notifications_day="monday",
            notifications_time="09:00:00",
        )

        # Assert
        mock_repository.create_user_profile.assert_called_once()

    def test_create_user_with_settings_invalid_time_format(
        self, service, mock_repository
    ):
        """Test user creation with invalid time format.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        from unittest.mock import Mock

        from telegram import User as TelegramUser

        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 123456789
        mock_user.username = "test_user"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"

        mock_repository.get_user_profile.return_value = None  # User doesn't exist

        # Execute and Assert
        with pytest.raises(UserServiceError) as exc_info:
            service.create_user_with_settings(
                user_info=mock_user,
                birth_date=date(1990, 1, 1),
                notifications_time="invalid_time",
            )

        assert "Error creating user profile" in str(exc_info.value)
        mock_repository.create_user_profile.assert_not_called()

    def test_create_user_with_settings_repository_failure(
        self, service, mock_repository
    ):
        """Test user creation when repository fails.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        from unittest.mock import Mock

        from telegram import User as TelegramUser

        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 123456789
        mock_user.username = "test_user"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"

        mock_repository.get_user_profile.return_value = None  # User doesn't exist
        mock_repository.create_user_profile.return_value = False

        # Execute and Assert
        with pytest.raises(UserRegistrationError) as exc_info:
            service.create_user_with_settings(
                user_info=mock_user,
                birth_date=date(1990, 1, 1),
            )

        assert "Failed to create user profile in database" in str(exc_info.value)

    def test_create_user_with_settings_exception(self, service, mock_repository):
        """Test user creation when exception occurs.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        from unittest.mock import Mock

        from telegram import User as TelegramUser

        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 123456789
        mock_user.username = "test_user"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"

        mock_repository.get_user_profile.return_value = None  # User doesn't exist
        mock_repository.create_user_profile.side_effect = Exception("Database error")

        # Execute and Assert
        with pytest.raises(UserServiceError) as exc_info:
            service.create_user_with_settings(
                user_info=mock_user,
                birth_date=date(1990, 1, 1),
            )

        assert "Error creating user profile" in str(exc_info.value)

    def test_get_user_profile_success(self, service, mock_repository, sample_user):
        """Test successful user profile retrieval.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        # Setup
        mock_repository.get_user_profile.return_value = sample_user

        # Execute
        result = service.get_user_profile(123456789)

        # Assert
        assert result == sample_user
        mock_repository.get_user_profile.assert_called_once_with(123456789)

    def test_get_user_profile_not_found(self, service, mock_repository):
        """Test user profile retrieval when user not found.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.get_user_profile.return_value = None

        # Execute
        result = service.get_user_profile(123456789)

        # Assert
        assert result is None

    def test_get_user_profile_exception(self, service, mock_repository):
        """Test user profile retrieval when exception occurs.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.get_user_profile.side_effect = Exception("Database error")

        # Execute
        result = service.get_user_profile(123456789)

        # Assert
        assert result is None

    def test_is_valid_user_profile_valid(
        self, service, mock_repository, sample_user, sample_settings
    ):
        """Test valid user profile check with complete profile.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :param sample_user: Sample user object
        :param sample_settings: Sample settings object
        :returns: None
        """
        # Setup
        sample_user.settings = sample_settings
        mock_repository.get_user_profile.return_value = sample_user

        # Execute
        result = service.is_valid_user_profile(123456789)

        # Assert
        assert result is True

    def test_is_valid_user_profile_no_user(self, service, mock_repository):
        """Test valid user profile check when user not found.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.get_user_profile.return_value = None

        # Execute
        result = service.is_valid_user_profile(123456789)

        # Assert
        assert result is False

    def test_is_valid_user_profile_no_settings(
        self, service, mock_repository, sample_user
    ):
        """Test valid user profile check when user has no settings.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        # Setup
        sample_user.settings = None
        mock_repository.get_user_profile.return_value = sample_user

        # Execute
        result = service.is_valid_user_profile(123456789)

        # Assert
        assert result is False

    def test_is_valid_user_profile_no_birth_date(
        self, service, mock_repository, sample_user, sample_settings
    ):
        """Test valid user profile check when user has no birth date.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :param sample_user: Sample user object
        :param sample_settings: Sample settings object
        :returns: None
        """
        # Setup
        sample_settings.birth_date = None
        sample_user.settings = sample_settings
        mock_repository.get_user_profile.return_value = sample_user

        # Execute
        result = service.is_valid_user_profile(123456789)

        # Assert
        assert result is False

    def test_is_valid_user_profile_exception(self, service, mock_repository):
        """Test valid user profile check when exception occurs.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.get_user_profile.side_effect = Exception("Database error")

        # Execute
        result = service.is_valid_user_profile(123456789)

        # Assert
        assert result is False

    def test_update_user_birth_date_success(self, service, mock_repository):
        """Test successful birth date update.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.set_birth_date.return_value = True

        # Execute
        result = service.update_user_birth_date(123456789, date(1990, 1, 1))

        # Assert
        assert result is True
        mock_repository.set_birth_date.assert_called_once_with(
            123456789, date(1990, 1, 1)
        )

    def test_update_user_birth_date_failure(self, service, mock_repository):
        """Test birth date update failure.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.set_birth_date.return_value = False

        # Execute
        result = service.update_user_birth_date(123456789, date(1990, 1, 1))

        # Assert
        assert result is False

    def test_update_user_birth_date_exception(self, service, mock_repository):
        """Test birth date update when exception occurs.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.set_birth_date.side_effect = Exception("Database error")

        # Execute
        result = service.update_user_birth_date(123456789, date(1990, 1, 1))

        # Assert
        assert result is False

    @patch("src.database.service.datetime")
    def test_update_notification_settings_success(
        self, mock_datetime, service, mock_repository
    ):
        """Test successful notification settings update.

        :param mock_datetime: Mock datetime module
        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_datetime.strptime.return_value = datetime(2023, 1, 1, 9, 0, 0)
        mock_repository.set_notification_settings.return_value = True

        # Execute
        result = service.update_notification_settings(
            telegram_id=123456789,
            notifications_enabled=True,
            notifications_day="monday",
            notifications_time="09:00:00",
        )

        # Assert
        assert result is True
        mock_repository.set_notification_settings.assert_called_once()

    def test_update_notification_settings_no_time(self, service, mock_repository):
        """Test notification settings update without time.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.set_notification_settings.return_value = True

        # Execute
        result = service.update_notification_settings(
            telegram_id=123456789,
            notifications_enabled=True,
            notifications_day="monday",
        )

        # Assert
        assert result is True
        mock_repository.set_notification_settings.assert_called_once_with(
            123456789, True, "monday", None
        )

    def test_update_notification_settings_invalid_time(self, service, mock_repository):
        """Test notification settings update with invalid time format.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Execute
        result = service.update_notification_settings(
            telegram_id=123456789,
            notifications_enabled=True,
            notifications_time="invalid_time",
        )

        # Assert
        assert result is False
        mock_repository.set_notification_settings.assert_not_called()

    def test_update_notification_settings_failure(self, service, mock_repository):
        """Test notification settings update failure.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.set_notification_settings.return_value = False

        # Execute
        result = service.update_notification_settings(
            telegram_id=123456789, notifications_enabled=True
        )

        # Assert
        assert result is False

    def test_update_notification_settings_exception(self, service, mock_repository):
        """Test notification settings update when exception occurs.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.set_notification_settings.side_effect = Exception(
            "Database error"
        )

        # Execute
        result = service.update_notification_settings(
            telegram_id=123456789, notifications_enabled=True
        )

        # Assert
        assert result is False

    def test_get_users_with_notifications_success(
        self, service, mock_repository, sample_user
    ):
        """Test successful retrieval of users with notifications.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        # Setup
        mock_repository.get_users_with_notifications.return_value = [sample_user]

        # Execute
        result = service.get_users_with_notifications()

        # Assert
        assert result == [sample_user]
        mock_repository.get_users_with_notifications.assert_called_once()

    def test_get_users_with_notifications_exception(self, service, mock_repository):
        """Test retrieval of users with notifications when exception occurs.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.get_users_with_notifications.side_effect = Exception(
            "Database error"
        )

        # Execute
        result = service.get_users_with_notifications()

        # Assert
        assert result == []

    def test_delete_user_success(self, service, mock_repository):
        """Test successful user deletion.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.delete_user.return_value = True

        # Execute
        result = service.delete_user(123456789)

        # Assert
        assert result is True
        mock_repository.delete_user.assert_called_once_with(123456789)

    def test_delete_user_failure(self, service, mock_repository):
        """Test user deletion failure.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.delete_user.return_value = False

        # Execute
        result = service.delete_user(123456789)

        # Assert
        assert result is False

    def test_delete_user_exception(self, service, mock_repository):
        """Test user deletion when exception occurs.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.delete_user.side_effect = Exception("Database error")

        # Execute
        result = service.delete_user(123456789)

        # Assert
        assert result is False

    def test_delete_user_profile_success_both_deleted(self, service, mock_repository):
        """Test successful user profile deletion with both settings and user deleted.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.delete_user_settings.return_value = True
        mock_repository.delete_user.return_value = True

        # Execute
        service.delete_user_profile(123456789)

        # Assert
        mock_repository.delete_user_settings.assert_called_once_with(123456789)
        mock_repository.delete_user.assert_called_once_with(123456789)

    def test_delete_user_profile_success_user_only(self, service, mock_repository):
        """Test successful user profile deletion when only user exists.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.delete_user_settings.return_value = False
        mock_repository.delete_user.return_value = True

        # Execute
        service.delete_user_profile(123456789)

        # Assert - should complete without raising exception

    def test_delete_user_profile_failure(self, service, mock_repository):
        """Test user profile deletion failure.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.delete_user_settings.return_value = True
        mock_repository.delete_user.return_value = False

        # Execute and Assert
        with pytest.raises(UserDeletionError) as exc_info:
            service.delete_user_profile(123456789)

        assert "Failed to delete user record" in str(exc_info.value)

    def test_delete_user_profile_exception(self, service, mock_repository):
        """Test user profile deletion when exception occurs.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Setup
        mock_repository.delete_user_settings.side_effect = Exception("Database error")

        # Execute and Assert
        with pytest.raises(UserServiceError) as exc_info:
            service.delete_user_profile(123456789)

        assert "Error during complete profile deletion" in str(exc_info.value)

    def test_close_with_repository(self, service, mock_repository):
        """Test service closure with repository.

        :param service: Service instance
        :param mock_repository: Mock repository instance
        :returns: None
        """
        # Execute
        service.close()

        # Assert
        mock_repository.close.assert_called_once()

    def test_close_without_repository(self):
        """Test service closure without repository.

        :returns: None
        """
        # Setup
        service = UserService(None)

        # Execute - should not raise exception
        service.close()

    def test_close_with_none_repository(self):
        """Test service closure when repository is None.

        :returns: None
        """
        # Setup
        service = UserService()
        service.repository = None

        # Execute - should not raise exception
        service.close()


class TestGlobalUserService:
    """Test suite for global user_service instance."""

    def test_global_service_instance(self):
        """Test that global service instance is created correctly.

        :returns: None
        """
        assert isinstance(user_service, UserService)
        assert isinstance(user_service.repository, SQLAlchemyUserRepository)
