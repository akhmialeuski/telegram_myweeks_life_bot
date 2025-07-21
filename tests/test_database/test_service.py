"""Unit tests for UserService class.

Tests all methods of the UserService class using pytest
with proper fixtures, mocking, and edge case coverage.
"""

import os
import tempfile
from datetime import UTC, date, datetime
from unittest.mock import MagicMock, Mock

import pytest

from src.utils.localization import SupportedLanguage
from src.core.enums import SubscriptionType
from src.database.models.user import User
from src.database.models.user_settings import UserSettings
from src.database.models.user_subscription import UserSubscription
from src.database.repositories.sqlite.user_repository import SQLiteUserRepository
from src.database.repositories.sqlite.user_settings_repository import (
    SQLiteUserSettingsRepository,
)
from src.database.repositories.sqlite.user_subscription_repository import (
    SQLiteUserSubscriptionRepository,
)
from src.database.service import (
    UserAlreadyExistsError,
    UserDeletionError,
    UserNotFoundError,
    UserProfileError,
    UserRegistrationError,
    UserService,
    UserServiceError,
    UserSettingsUpdateError,
    UserSubscriptionUpdateError,
)


class TestUserServiceExceptions:
    """Test suite for UserService exception classes."""

    def test_user_service_error_inheritance(self):
        """Test UserServiceError inheritance.

        :returns: None
        """
        error = UserServiceError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_user_not_found_error_inheritance(self):
        """Test UserNotFoundError inheritance.

        :returns: None
        """
        error = UserNotFoundError("User not found")
        assert isinstance(error, UserServiceError)
        assert str(error) == "User not found"

    def test_user_deletion_error_inheritance(self):
        """Test UserDeletionError inheritance.

        :returns: None
        """
        error = UserDeletionError("Deletion failed")
        assert isinstance(error, UserServiceError)
        assert str(error) == "Deletion failed"

    def test_user_profile_error_inheritance(self):
        """Test UserProfileError inheritance.

        :returns: None
        """
        error = UserProfileError("Profile error")
        assert isinstance(error, UserServiceError)
        assert str(error) == "Profile error"

    def test_user_registration_error_inheritance(self):
        """Test UserRegistrationError inheritance.

        :returns: None
        """
        error = UserRegistrationError("Registration failed")
        assert isinstance(error, UserServiceError)
        assert str(error) == "Registration failed"

    def test_user_already_exists_error_inheritance(self):
        """Test UserAlreadyExistsError inheritance.

        :returns: None
        """
        error = UserAlreadyExistsError("User exists")
        assert isinstance(error, UserServiceError)
        assert str(error) == "User exists"


class TestUserService:
    """Test suite for UserService class."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path for testing.

        :returns: Path to temporary database file
        :rtype: str
        """
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def mock_user_repository(self):
        """Create mock user repository.

        :returns: Mock user repository
        :rtype: Mock
        """
        return Mock(spec=SQLiteUserRepository)

    @pytest.fixture
    def mock_settings_repository(self):
        """Create mock settings repository.

        :returns: Mock settings repository
        :rtype: Mock
        """
        return Mock(spec=SQLiteUserSettingsRepository)

    @pytest.fixture
    def mock_subscription_repository(self):
        """Create mock subscription repository.

        :returns: Mock subscription repository
        :rtype: Mock
        """
        return Mock(spec=SQLiteUserSubscriptionRepository)

    @pytest.fixture
    def user_service(
        self,
        mock_user_repository,
        mock_settings_repository,
        mock_subscription_repository,
    ):
        """Create UserService instance with mocked repositories.

        :param mock_user_repository: Mock user repository
        :param mock_settings_repository: Mock settings repository
        :param mock_subscription_repository: Mock subscription repository
        :returns: UserService instance
        :rtype: UserService
        """
        return UserService(
            user_repository=mock_user_repository,
            settings_repository=mock_settings_repository,
            subscription_repository=mock_subscription_repository,
        )

    @pytest.fixture
    def sample_user(self):
        """Create a sample User object for testing.

        :returns: Sample User object
        :rtype: User
        """
        return User(
            telegram_id=123456789,
            username="testuser",
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
            updated_at=datetime.now(UTC),
        )

    def test_init_with_default_repositories(self):
        """Test UserService initialization with default repositories.

        :returns: None
        """
        service = UserService()
        assert isinstance(service.user_repository, SQLiteUserRepository)
        assert isinstance(service.settings_repository, SQLiteUserSettingsRepository)
        assert isinstance(
            service.subscription_repository, SQLiteUserSubscriptionRepository
        )

    def test_init_with_custom_repositories(
        self,
        mock_user_repository,
        mock_settings_repository,
        mock_subscription_repository,
    ):
        """Test UserService initialization with custom repositories.

        :param mock_user_repository: Mock user repository
        :param mock_settings_repository: Mock settings repository
        :param mock_subscription_repository: Mock subscription repository
        :returns: None
        """
        service = UserService(
            user_repository=mock_user_repository,
            settings_repository=mock_settings_repository,
            subscription_repository=mock_subscription_repository,
        )
        assert service.user_repository == mock_user_repository
        assert service.settings_repository == mock_settings_repository
        assert service.subscription_repository == mock_subscription_repository

    def test_initialize(
        self,
        user_service,
        mock_user_repository,
        mock_settings_repository,
        mock_subscription_repository,
    ):
        """Test service initialization.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :param mock_settings_repository: Mock settings repository
        :param mock_subscription_repository: Mock subscription repository
        :returns: None
        """
        user_service.initialize()
        mock_user_repository.initialize.assert_called_once()
        mock_settings_repository.initialize.assert_called_once()
        mock_subscription_repository.initialize.assert_called_once()

    def test_close(
        self,
        user_service,
        mock_user_repository,
        mock_settings_repository,
        mock_subscription_repository,
    ):
        """Test service closure.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :param mock_settings_repository: Mock settings repository
        :param mock_subscription_repository: Mock subscription repository
        :returns: None
        """
        user_service.close()
        mock_user_repository.close.assert_called_once()
        mock_settings_repository.close.assert_called_once()
        mock_subscription_repository.close.assert_called_once()

    def test_create_user_profile_success(
        self,
        user_service,
        mock_user_repository,
        mock_settings_repository,
        mock_subscription_repository,
        sample_user,
        sample_settings,
    ):
        """Test successful user creation with settings.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :param mock_settings_repository: Mock settings repository
        :param mock_subscription_repository: Mock subscription repository
        :param sample_user: Sample user object
        :param sample_settings: Sample settings object
        :returns: None
        """
        # Mock get_user_profile to return None (user doesn't exist)
        user_service.get_user_profile = Mock(return_value=None)
        mock_user_repository.create_user.return_value = True
        mock_settings_repository.create_user_settings.return_value = True
        mock_subscription_repository.create_subscription.return_value = True

        # Mock get_user_profile to return user after creation
        created_user = User(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User",
            created_at=datetime.now(UTC),
        )
        created_user.settings = sample_settings
        user_service.get_user_profile = Mock(side_effect=[None, created_user])

        # Create mock user info object with id attribute
        mock_user_info = Mock()
        mock_user_info.id = 123456789
        mock_user_info.username = "testuser"
        mock_user_info.first_name = "Test"
        mock_user_info.last_name = "User"

        result = user_service.create_user_profile(
            user_info=mock_user_info,
            birth_date=date(1990, 1, 1),
            subscription_type=SubscriptionType.BASIC,
        )

        assert result is not None
        assert result.telegram_id == 123456789
        mock_user_repository.create_user.assert_called_once()
        mock_settings_repository.create_user_settings.assert_called_once()
        mock_subscription_repository.create_subscription.assert_called_once()

    def test_create_user_profile_user_exists(self, user_service, sample_user):
        """Test user creation when user already exists.

        :param user_service: UserService instance
        :param sample_user: Sample user object
        :returns: None
        """
        user_service.get_user_profile = Mock(return_value=sample_user)

        # Create mock user info object with id attribute
        mock_user_info = Mock()
        mock_user_info.id = 123456789
        mock_user_info.username = "testuser"
        mock_user_info.first_name = None
        mock_user_info.last_name = None

        result = user_service.create_user_profile(
            user_info=mock_user_info,
            birth_date=date(1990, 1, 1),
            subscription_type=SubscriptionType.BASIC,
        )

        assert result == sample_user

    def test_create_user_profile_user_creation_fails(
        self,
        user_service,
        mock_user_repository,
        mock_settings_repository,
        mock_subscription_repository,
    ):
        """Test user creation when user creation fails.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :param mock_settings_repository: Mock settings repository
        :param mock_subscription_repository: Mock subscription repository
        :returns: None
        """
        user_service.get_user_profile = Mock(return_value=None)
        mock_user_repository.create_user.return_value = False

        # Create mock user info object with id attribute
        mock_user_info = Mock()
        mock_user_info.id = 123456789
        mock_user_info.username = "testuser"
        mock_user_info.first_name = None
        mock_user_info.last_name = None

        result = user_service.create_user_profile(
            user_info=mock_user_info,
            birth_date=date(1990, 1, 1),
            subscription_type=SubscriptionType.BASIC,
        )

        assert result is None
        mock_user_repository.create_user.assert_called_once()
        mock_settings_repository.create_user_settings.assert_not_called()
        mock_subscription_repository.create_subscription.assert_not_called()

    def test_create_user_profile_settings_creation_fails(
        self,
        user_service,
        mock_user_repository,
        mock_settings_repository,
        mock_subscription_repository,
    ):
        """Test user creation when settings creation fails.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :param mock_settings_repository: Mock settings repository
        :param mock_subscription_repository: Mock subscription repository
        :returns: None
        """
        user_service.get_user_profile = Mock(return_value=None)
        mock_user_repository.create_user.return_value = True
        mock_settings_repository.create_user_settings.return_value = False
        mock_user_repository.delete_user.return_value = True

        # Create mock user info object with id attribute
        mock_user_info = Mock()
        mock_user_info.id = 123456789
        mock_user_info.username = "testuser"
        mock_user_info.first_name = None
        mock_user_info.last_name = None

        result = user_service.create_user_profile(
            user_info=mock_user_info,
            birth_date=date(1990, 1, 1),
            subscription_type=SubscriptionType.BASIC,
        )

        assert result is None
        mock_user_repository.create_user.assert_called_once()
        mock_settings_repository.create_user_settings.assert_called_once()
        mock_subscription_repository.create_subscription.assert_not_called()
        mock_user_repository.delete_user.assert_called_once_with(123456789)

    def test_create_user_profile_subscription_creation_fails(
        self,
        user_service,
        mock_user_repository,
        mock_settings_repository,
        mock_subscription_repository,
    ):
        """Test user creation when subscription creation fails.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :param mock_settings_repository: Mock settings repository
        :param mock_subscription_repository: Mock subscription repository
        :returns: None
        """
        user_service.get_user_profile = Mock(return_value=None)
        mock_user_repository.create_user.return_value = True
        mock_settings_repository.create_user_settings.return_value = True
        mock_subscription_repository.create_subscription.return_value = False
        mock_user_repository.delete_user.return_value = True
        mock_settings_repository.delete_user_settings.return_value = True

        # Create mock user info object with id attribute
        mock_user_info = Mock()
        mock_user_info.id = 123456789
        mock_user_info.username = "testuser"
        mock_user_info.first_name = None
        mock_user_info.last_name = None

        result = user_service.create_user_profile(
            user_info=mock_user_info,
            birth_date=date(1990, 1, 1),
            subscription_type=SubscriptionType.BASIC,
        )

        assert result is None
        mock_user_repository.create_user.assert_called_once()
        mock_settings_repository.create_user_settings.assert_called_once()
        mock_subscription_repository.create_subscription.assert_called_once()
        # Now both user and settings should be deleted on subscription failure
        mock_settings_repository.delete_user_settings.assert_called_once_with(123456789)
        mock_user_repository.delete_user.assert_called_once_with(123456789)

    def test_create_user_profile_exception(self, user_service):
        """Test user creation with exception.

        :param user_service: UserService instance
        :returns: None
        """
        user_service.get_user_profile = Mock(side_effect=Exception("Test error"))

        # Create mock user info object with id attribute
        mock_user_info = Mock()
        mock_user_info.id = 123456789
        mock_user_info.username = "testuser"
        mock_user_info.first_name = None
        mock_user_info.last_name = None

        result = user_service.create_user_profile(
            user_info=mock_user_info,
            birth_date=date(1990, 1, 1),
            subscription_type=SubscriptionType.BASIC,
        )

        assert result is None

    def test_get_user_profile_success(
        self,
        user_service,
        mock_user_repository,
        mock_settings_repository,
        mock_subscription_repository,
        sample_user,
        sample_settings,
    ):
        """Test successful user profile retrieval.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :param mock_settings_repository: Mock settings repository
        :param mock_subscription_repository: Mock subscription repository
        :param sample_user: Sample user object
        :param sample_settings: Sample settings object
        :returns: None
        """
        sample_subscription = UserSubscription(
            telegram_id=123456789,
            subscription_type=SubscriptionType.BASIC,
            is_active=True,
        )

        mock_user_repository.get_user.return_value = sample_user
        mock_settings_repository.get_user_settings.return_value = sample_settings
        mock_subscription_repository.get_subscription.return_value = sample_subscription

        result = user_service.get_user_profile(123456789)

        assert result is not None
        assert result.telegram_id == 123456789
        assert result.settings == sample_settings
        assert result.subscription == sample_subscription
        mock_user_repository.get_user.assert_called_once_with(123456789)
        mock_settings_repository.get_user_settings.assert_called_once_with(123456789)
        mock_subscription_repository.get_subscription.assert_called_once_with(123456789)

    def test_get_user_profile_user_not_found(self, user_service, mock_user_repository):
        """Test user profile retrieval when user not found.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :returns: None
        """
        mock_user_repository.get_user.return_value = None

        result = user_service.get_user_profile(123456789)

        assert result is None

    def test_get_user_profile_settings_not_found(
        self, user_service, mock_user_repository, mock_settings_repository, sample_user
    ):
        """Test user profile retrieval when settings not found.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :param mock_settings_repository: Mock settings repository
        :param sample_user: Sample user object
        :returns: None
        """
        mock_user_repository.get_user.return_value = sample_user
        mock_settings_repository.get_user_settings.return_value = None

        result = user_service.get_user_profile(123456789)

        assert result is None

    def test_get_user_profile_subscription_not_found(
        self,
        user_service,
        mock_user_repository,
        mock_settings_repository,
        mock_subscription_repository,
        sample_user,
        sample_settings,
    ):
        """Test user profile retrieval when subscription not found.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :param mock_settings_repository: Mock settings repository
        :param mock_subscription_repository: Mock subscription repository
        :param sample_user: Sample user object
        :param sample_settings: Sample settings object
        :returns: None
        """
        mock_user_repository.get_user.return_value = sample_user
        mock_settings_repository.get_user_settings.return_value = sample_settings
        mock_subscription_repository.get_subscription.return_value = None

        result = user_service.get_user_profile(123456789)

        assert result is None

    def test_get_user_profile_exception(self, user_service, mock_user_repository):
        """Test user profile retrieval with exception.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :returns: None
        """
        mock_user_repository.get_user.side_effect = Exception("Test error")

        result = user_service.get_user_profile(123456789)

        assert result is None

    def test_user_exists_true(self, user_service, sample_user):
        """Test user_exists returns True when user exists.

        :param user_service: UserService instance
        :param sample_user: Sample user object
        :returns: None
        """
        sample_user.settings = UserSettings(telegram_id=123456789)
        user_service.get_user_profile = Mock(return_value=sample_user)

        result = user_service.user_exists(123456789)

        assert result is True

    def test_user_exists_false_no_user(self, user_service):
        """Test user_exists returns False when user doesn't exist.

        :param user_service: UserService instance
        :returns: None
        """
        user_service.get_user_profile = Mock(return_value=None)

        result = user_service.user_exists(123456789)

        assert result is False

    def test_user_exists_false_no_settings(self, user_service, sample_user):
        """Test user_exists returns False when user has no settings.

        :param user_service: UserService instance
        :param sample_user: Sample user object
        :returns: None
        """
        sample_user.settings = None
        user_service.get_user_profile = Mock(return_value=sample_user)

        result = user_service.user_exists(123456789)

        assert result is False

    def test_user_exists_exception(self, user_service):
        """Test user_exists with exception.

        :param user_service: UserService instance
        :returns: None
        """
        user_service.get_user_profile = Mock(side_effect=Exception("Test error"))

        result = user_service.user_exists(123456789)

        assert result is False

    def test_is_valid_user_profile_true(
        self, user_service, mock_settings_repository, sample_settings
    ):
        """Test is_valid_user_profile returns True for valid profile.

        :param user_service: UserService instance
        :param mock_settings_repository: Mock settings repository
        :param sample_settings: Sample settings object
        :returns: None
        """
        mock_settings_repository.get_user_settings.return_value = sample_settings

        result = user_service.is_valid_user_profile(123456789)

        assert result is True

    def test_is_valid_user_profile_false_no_settings(
        self, user_service, mock_settings_repository
    ):
        """Test is_valid_user_profile returns False when no settings.

        :param user_service: UserService instance
        :param mock_settings_repository: Mock settings repository
        :returns: None
        """
        mock_settings_repository.get_user_settings.return_value = None

        result = user_service.is_valid_user_profile(123456789)

        assert result is False

    def test_is_valid_user_profile_false_no_birth_date(
        self, user_service, mock_settings_repository
    ):
        """Test is_valid_user_profile returns False when no birth date.

        :param user_service: UserService instance
        :param mock_settings_repository: Mock settings repository
        :returns: None
        """
        settings = UserSettings(telegram_id=123456789, birth_date=None)
        mock_settings_repository.get_user_settings.return_value = settings

        result = user_service.is_valid_user_profile(123456789)

        assert result is False

    def test_is_valid_user_profile_exception(
        self, user_service, mock_settings_repository
    ):
        """Test is_valid_user_profile with exception.

        :param user_service: UserService instance
        :param mock_settings_repository: Mock settings repository
        :returns: None
        """
        mock_settings_repository.get_user_settings.side_effect = Exception("Test error")

        result = user_service.is_valid_user_profile(123456789)

        assert result is False

    def test_delete_user_success(self, user_service, mock_user_repository):
        """Test successful user deletion.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :returns: None
        """
        mock_user_repository.delete_user.return_value = True

        result = user_service.delete_user(123456789)

        assert result is True
        mock_user_repository.delete_user.assert_called_once_with(123456789)

    def test_delete_user_failure(self, user_service, mock_user_repository):
        """Test failed user deletion.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :returns: None
        """
        mock_user_repository.delete_user.return_value = False

        result = user_service.delete_user(123456789)

        assert result is False

    def test_delete_user_exception(self, user_service, mock_user_repository):
        """Test user deletion with exception.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :returns: None
        """
        mock_user_repository.delete_user.side_effect = Exception("Test error")

        result = user_service.delete_user(123456789)

        assert result is False

    def test_delete_user_profile_success(
        self, user_service, mock_user_repository, mock_settings_repository
    ):
        """Test successful user profile deletion.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :param mock_settings_repository: Mock settings repository
        :returns: None
        """
        mock_settings_repository.delete_user_settings.return_value = True
        mock_user_repository.delete_user.return_value = True

        user_service.delete_user_profile(123456789)

        mock_settings_repository.delete_user_settings.assert_called_once_with(123456789)
        mock_user_repository.delete_user.assert_called_once_with(123456789)

    def test_delete_user_profile_no_settings(
        self, user_service, mock_user_repository, mock_settings_repository
    ):
        """Test user profile deletion when no settings exist.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :param mock_settings_repository: Mock settings repository
        :returns: None
        """
        mock_settings_repository.delete_user_settings.return_value = False
        mock_user_repository.delete_user.return_value = True

        user_service.delete_user_profile(123456789)

        mock_settings_repository.delete_user_settings.assert_called_once_with(123456789)
        mock_user_repository.delete_user.assert_called_once_with(123456789)

    def test_delete_user_profile_user_deletion_fails(
        self, user_service, mock_user_repository, mock_settings_repository
    ):
        """Test user profile deletion when user deletion fails.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :param mock_settings_repository: Mock settings repository
        :returns: None
        """
        mock_settings_repository.delete_user_settings.return_value = True
        mock_user_repository.delete_user.return_value = False

        with pytest.raises(
            UserDeletionError,
            match="Failed to delete user profile: User 123456789 not found",
        ):
            user_service.delete_user_profile(123456789)

    def test_delete_user_profile_user_deletion_error_reraise(
        self, user_service, mock_user_repository, mock_settings_repository
    ):
        """Test user profile deletion re-raises UserDeletionError.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :param mock_settings_repository: Mock settings repository
        :returns: None
        """
        mock_settings_repository.delete_user_settings.side_effect = UserDeletionError(
            "Test error"
        )

        with pytest.raises(UserDeletionError, match="Test error"):
            user_service.delete_user_profile(123456789)

    def test_delete_user_profile_general_exception(
        self, user_service, mock_user_repository, mock_settings_repository
    ):
        """Test user profile deletion with general exception.

        :param user_service: UserService instance
        :param mock_user_repository: Mock user repository
        :param mock_settings_repository: Mock settings repository
        :returns: None
        """
        mock_settings_repository.delete_user_settings.side_effect = Exception(
            "Test error"
        )

        with pytest.raises(
            UserDeletionError,
            match="Failed to delete user profile: Test error",
        ):
            user_service.delete_user_profile(123456789)


class TestUserServiceUpdateSubscription:
    """Test class for UserService update_user_subscription method.

    This class contains all tests for the update_user_subscription method,
    including success and error scenarios.
    """

    def test_update_user_subscription_success(self):
        """Test successful subscription type update.

        This test verifies that update_user_subscription correctly
        updates a user's subscription type.
        """
        user_service = UserService()
        subscription = MagicMock()
        subscription.subscription_type = SubscriptionType.BASIC

        user_service.subscription_repository = MagicMock()
        user_service.subscription_repository.get_subscription.return_value = (
            subscription
        )
        user_service.subscription_repository.update_subscription.return_value = True

        # Should not raise any exception
        user_service.update_user_subscription(123456789, SubscriptionType.PREMIUM)

        # Verify subscription type was updated
        assert subscription.subscription_type == SubscriptionType.PREMIUM
        user_service.subscription_repository.update_subscription.assert_called_once_with(
            subscription
        )

    def test_update_user_subscription_not_found(self):
        """Test update_user_subscription when subscription not found.

        This test verifies that UserNotFoundError is raised when
        trying to update a subscription that doesn't exist.
        """
        user_service = UserService()
        user_service.subscription_repository = MagicMock()
        user_service.subscription_repository.get_subscription.return_value = None

        with pytest.raises(
            UserNotFoundError, match="Subscription not found for user 123456789"
        ):
            user_service.update_user_subscription(123456789, SubscriptionType.PREMIUM)

    def test_update_user_subscription_update_fails(self):
        """Test update_user_subscription when repository update fails.

        This test verifies that UserSubscriptionUpdateError is raised when
        the repository update operation fails.
        """
        user_service = UserService()
        subscription = MagicMock()
        subscription.subscription_type = SubscriptionType.BASIC

        user_service.subscription_repository = MagicMock()
        user_service.subscription_repository.get_subscription.return_value = (
            subscription
        )
        user_service.subscription_repository.update_subscription.return_value = False

        with pytest.raises(
            UserSubscriptionUpdateError,
            match="Failed to update subscription for user 123456789",
        ):
            user_service.update_user_subscription(123456789, SubscriptionType.PREMIUM)

    def test_update_user_subscription_repository_exception(self):
        """Test update_user_subscription when repository raises exception.

        This test verifies that UserSubscriptionUpdateError is raised when
        the repository operation raises an unexpected exception.
        """
        user_service = UserService()
        subscription = MagicMock()

        user_service.subscription_repository = MagicMock()
        user_service.subscription_repository.get_subscription.return_value = (
            subscription
        )
        user_service.subscription_repository.update_subscription.side_effect = (
            Exception("Database error")
        )

        with pytest.raises(
            UserSubscriptionUpdateError,
            match="Error updating subscription for 123456789",
        ):
            user_service.update_user_subscription(123456789, SubscriptionType.PREMIUM)

    def test_update_user_subscription_get_subscription_exception(self):
        """Test update_user_subscription when get_subscription raises exception.

        This test verifies that UserSubscriptionUpdateError is raised when
        getting the subscription fails with an exception.
        """
        user_service = UserService()
        user_service.subscription_repository = MagicMock()
        user_service.subscription_repository.get_subscription.side_effect = Exception(
            "Database error"
        )

        with pytest.raises(
            UserSubscriptionUpdateError,
            match="Error updating subscription for 123456789: Database error",
        ):
            user_service.update_user_subscription(123456789, SubscriptionType.PREMIUM)


class TestUserServiceUpdateSettings:
    """Test class for UserService update_user_settings method.

    This class contains all tests for the update_user_settings method,
    including success and error scenarios.
    """

    def test_update_user_settings_success_all_fields(self):
        """Test successful settings update with all fields.

        This test verifies that update_user_settings correctly
        updates user settings with all provided fields.
        """
        user_service = UserService()
        settings = MagicMock()
        settings.birth_date = date(1990, 1, 1)
        settings.life_expectancy = 75
        settings.language = SupportedLanguage.EN.value

        user_service.settings_repository = MagicMock()
        user_service.settings_repository.get_user_settings.return_value = settings
        user_service.settings_repository.update_user_settings.return_value = True

        new_birth_date = date(1985, 5, 15)
        new_life_expectancy = 85
        new_language = SupportedLanguage.RU.value

        # Should not raise any exception
        user_service.update_user_settings(
            123456789,
            birth_date=new_birth_date,
            life_expectancy=new_life_expectancy,
            language=new_language,
        )

        # Verify all fields were updated
        assert settings.birth_date == new_birth_date
        assert settings.life_expectancy == new_life_expectancy
        assert settings.language == new_language
        user_service.settings_repository.update_user_settings.assert_called_once_with(
            settings
        )

    def test_update_user_settings_success_partial_fields(self):
        """Test successful settings update with partial fields.

        This test verifies that update_user_settings correctly
        updates only the provided fields, leaving others unchanged.
        """
        user_service = UserService()
        settings = MagicMock()
        settings.birth_date = date(1990, 1, 1)
        settings.life_expectancy = 75
        settings.language = SupportedLanguage.EN.value

        user_service.settings_repository = MagicMock()
        user_service.settings_repository.get_user_settings.return_value = settings
        user_service.settings_repository.update_user_settings.return_value = True

        new_language = SupportedLanguage.RU.value

        # Should not raise any exception
        user_service.update_user_settings(123456789, language=new_language)

        # Verify only language was updated
        assert settings.birth_date == date(1990, 1, 1)  # Unchanged
        assert settings.life_expectancy == 75  # Unchanged
        assert settings.language == new_language  # Updated
        user_service.settings_repository.update_user_settings.assert_called_once_with(
            settings
        )

    def test_update_user_settings_not_found(self):
        """Test update_user_settings when settings not found.

        This test verifies that UserNotFoundError is raised when
        trying to update settings that don't exist.
        """
        user_service = UserService()
        user_service.settings_repository = MagicMock()
        user_service.settings_repository.get_user_settings.return_value = None

        with pytest.raises(
            UserNotFoundError, match="Settings not found for user 123456789"
        ):
            user_service.update_user_settings(123456789, language=SupportedLanguage.RU.value)

    def test_update_user_settings_update_fails(self):
        """Test update_user_settings when repository update fails.

        This test verifies that UserSettingsUpdateError is raised when
        the repository update operation fails.
        """
        user_service = UserService()
        settings = MagicMock()

        user_service.settings_repository = MagicMock()
        user_service.settings_repository.get_user_settings.return_value = settings
        user_service.settings_repository.update_user_settings.return_value = False

        with pytest.raises(
            UserSettingsUpdateError,
            match="Failed to update settings for user 123456789",
        ):
            user_service.update_user_settings(123456789, language=SupportedLanguage.RU.value)

    def test_update_user_settings_repository_exception(self):
        """Test update_user_settings when repository raises exception.

        This test verifies that UserSettingsUpdateError is raised when
        the repository operation raises an unexpected exception.
        """
        user_service = UserService()
        settings = MagicMock()

        user_service.settings_repository = MagicMock()
        user_service.settings_repository.get_user_settings.return_value = settings
        user_service.settings_repository.update_user_settings.side_effect = Exception(
            "Database error"
        )

        with pytest.raises(
            UserSettingsUpdateError,
            match="Error updating settings for 123456789: Database error",
        ):
            user_service.update_user_settings(123456789, language=SupportedLanguage.RU.value)

    def test_update_user_settings_get_settings_exception(self):
        """Test update_user_settings when get_user_settings raises exception.

        This test verifies that UserSettingsUpdateError is raised when
        getting the settings fails with an exception.
        """
        user_service = UserService()
        user_service.settings_repository = MagicMock()
        user_service.settings_repository.get_user_settings.side_effect = Exception(
            "Database error"
        )

        with pytest.raises(
            UserSettingsUpdateError,
            match="Error updating settings for 123456789: Database error",
        ):
            user_service.update_user_settings(123456789, language=SupportedLanguage.RU.value)

    def test_update_user_settings_no_fields_provided(self):
        """Test update_user_settings when no fields are provided.

        This test verifies that the method works correctly when
        no fields are provided for update (all None).
        """
        user_service = UserService()
        settings = MagicMock()
        settings.birth_date = date(1990, 1, 1)
        settings.life_expectancy = 75
        settings.language = SupportedLanguage.EN.value

        user_service.settings_repository = MagicMock()
        user_service.settings_repository.get_user_settings.return_value = settings
        user_service.settings_repository.update_user_settings.return_value = True

        # Should not raise any exception
        user_service.update_user_settings(123456789)

        # Verify no fields were changed
        assert settings.birth_date == date(1990, 1, 1)
        assert settings.life_expectancy == 75
        assert settings.language == "en"
        user_service.settings_repository.update_user_settings.assert_called_once_with(
            settings
        )


class TestUserServiceDeleteUserProfile:
    """Test class for UserService delete_user_profile method.

    This class contains all tests for the delete_user_profile method,
    including success and error scenarios.
    """

    def test_delete_user_profile_success_all_components(self):
        """Test successful deletion of complete user profile.

        This test verifies that delete_user_profile correctly
        deletes settings, subscription, and user in order.
        """
        user_service = UserService()

        user_service.settings_repository = MagicMock()
        user_service.subscription_repository = MagicMock()
        user_service.user_repository = MagicMock()
        user_service.settings_repository.delete_user_settings.return_value = True
        user_service.subscription_repository.delete_subscription.return_value = True
        user_service.user_repository.delete_user.return_value = True

        # Should not raise any exception
        user_service.delete_user_profile(123456789)

        # Verify all deletions were called in correct order
        user_service.settings_repository.delete_user_settings.assert_called_once_with(
            123456789
        )
        user_service.subscription_repository.delete_subscription.assert_called_once_with(
            123456789
        )
        user_service.user_repository.delete_user.assert_called_once_with(123456789)

    def test_delete_user_profile_success_missing_settings(self):
        """Test successful deletion when settings don't exist.

        This test verifies that delete_user_profile works correctly
        when user settings are not found.
        """
        user_service = UserService()

        user_service.settings_repository = MagicMock()
        user_service.subscription_repository = MagicMock()
        user_service.user_repository = MagicMock()
        user_service.settings_repository.delete_user_settings.return_value = False
        user_service.subscription_repository.delete_subscription.return_value = True
        user_service.user_repository.delete_user.return_value = True

        # Should not raise any exception
        user_service.delete_user_profile(123456789)

        # Verify all deletions were attempted
        user_service.settings_repository.delete_user_settings.assert_called_once_with(
            123456789
        )
        user_service.subscription_repository.delete_subscription.assert_called_once_with(
            123456789
        )
        user_service.user_repository.delete_user.assert_called_once_with(123456789)

    def test_delete_user_profile_success_missing_subscription(self):
        """Test successful deletion when subscription doesn't exist.

        This test verifies that delete_user_profile works correctly
        when user subscription is not found.
        """
        user_service = UserService()

        user_service.settings_repository = MagicMock()
        user_service.subscription_repository = MagicMock()
        user_service.user_repository = MagicMock()
        user_service.settings_repository.delete_user_settings.return_value = True
        user_service.subscription_repository.delete_subscription.return_value = False
        user_service.user_repository.delete_user.return_value = True

        # Should not raise any exception
        user_service.delete_user_profile(123456789)

        # Verify all deletions were attempted
        user_service.settings_repository.delete_user_settings.assert_called_once_with(
            123456789
        )
        user_service.subscription_repository.delete_subscription.assert_called_once_with(
            123456789
        )
        user_service.user_repository.delete_user.assert_called_once_with(123456789)

    def test_delete_user_profile_user_not_found(self):
        """Test delete_user_profile when user doesn't exist.

        This test verifies that UserDeletionError is raised when
        the user to delete is not found.
        """
        user_service = UserService()

        user_service.settings_repository = MagicMock()
        user_service.subscription_repository = MagicMock()
        user_service.user_repository = MagicMock()
        user_service.settings_repository.delete_user_settings.return_value = True
        user_service.subscription_repository.delete_subscription.return_value = True
        user_service.user_repository.delete_user.return_value = False

        with pytest.raises(UserDeletionError, match="User 123456789 not found"):
            user_service.delete_user_profile(123456789)

    def test_delete_user_profile_general_exception(self):
        """Test delete_user_profile when an unexpected exception occurs.

        This test verifies that UserDeletionError is raised when
        any repository operation raises an unexpected exception.
        """
        user_service = UserService()

        user_service.settings_repository = MagicMock()
        user_service.settings_repository.delete_user_settings.side_effect = Exception(
            "Database error"
        )

        with pytest.raises(
            UserDeletionError, match="Failed to delete user profile: Database error"
        ):
            user_service.delete_user_profile(123456789)


class TestUserServiceGetAllUsers:
    """Test class for UserService get_all_users method edge cases.

    This class contains additional tests for the get_all_users method,
    focusing on edge cases and error scenarios.
    """

    def test_get_all_users_with_incomplete_profiles(self):
        """Test get_all_users when some users have incomplete profiles.

        This test verifies that get_all_users skips users with
        incomplete profiles and returns only valid ones.
        """
        user_service = UserService()

        # Create mock users
        user1 = MagicMock()
        user1.telegram_id = 111
        user1.username = "user1"
        user1.first_name = "User"
        user1.last_name = "One"
        user1.created_at = datetime.now(UTC)

        user2 = MagicMock()
        user2.telegram_id = 222
        user2.username = "user2"
        user2.first_name = "User"
        user2.last_name = "Two"
        user2.created_at = datetime.now(UTC)

        user_service.user_repository = MagicMock()
        user_service.settings_repository = MagicMock()
        user_service.subscription_repository = MagicMock()
        user_service.user_repository._get_all_entities.return_value = [user1, user2]

        # Mock settings and subscriptions - user2 will have missing settings
        settings1 = MagicMock()
        subscription1 = MagicMock()
        subscription2 = MagicMock()

        def mock_get_settings(telegram_id):
            if telegram_id == 111:
                return settings1
            return None  # User2 has no settings

        def mock_get_subscription(telegram_id):
            if telegram_id == 111:
                return subscription1
            return subscription2

        user_service.settings_repository.get_user_settings.side_effect = (
            mock_get_settings
        )
        user_service.subscription_repository.get_subscription.side_effect = (
            mock_get_subscription
        )

        result = user_service.get_all_users()

        # Should return both users (user2 with None settings is included)
        assert len(result) == 2
        assert result[0].telegram_id == 111
        assert result[1].telegram_id == 222
        assert result[0].settings is not None
        assert result[1].settings is None

    def test_get_all_users_repository_exception(self):
        """Test get_all_users when repository raises exception.

        This test verifies that get_all_users returns empty list when
        the repository operation raises an exception.
        """
        user_service = UserService()
        user_service.user_repository = MagicMock()
        user_service.user_repository._get_all_entities.side_effect = Exception(
            "Database error"
        )

        result = user_service.get_all_users()

        assert result == []

    def test_get_all_users_profile_building_exception(self):
        """Test get_all_users when profile building raises exception.

        This test verifies that get_all_users skips users where
        profile building fails due to exceptions.
        """
        user_service = UserService()

        # Create mock user
        user1 = MagicMock()
        user1.telegram_id = 111
        user1.username = "user1"
        user1.first_name = "User"
        user1.last_name = "One"
        user1.created_at = datetime.now(UTC)

        user_service.user_repository = MagicMock()
        user_service.settings_repository = MagicMock()
        user_service.user_repository._get_all_entities.return_value = [user1]

        # Mock settings retrieval to raise exception
        user_service.settings_repository.get_user_settings.side_effect = Exception(
            "Settings error"
        )

        result = user_service.get_all_users()

        # Should return empty list as user1 profile building failed
        assert result == []
