"""Unit tests for SQLAlchemyUserRepository class.

Tests all methods of the SQLAlchemyUserRepository class using pytest
with proper fixtures, mocking, and edge case coverage.
"""

import os
import tempfile
from datetime import UTC, date, datetime, time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.database.constants import DEFAULT_DATABASE_PATH
from src.database.models import User, UserSettings
from src.database.sqlite_repository import SQLAlchemyUserRepository


class TestSQLAlchemyUserRepository:
    """Test suite for SQLAlchemyUserRepository class."""

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
    def repository(self, temp_db_path):
        """Create repository instance with temporary database.

        :param temp_db_path: Temporary database path
        :returns: SQLAlchemyUserRepository instance
        :rtype: SQLAlchemyUserRepository
        """
        repo = SQLAlchemyUserRepository(temp_db_path)
        repo.initialize()
        yield repo
        repo.close()

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
            notifications_day="mon",
            notifications_time=time(9, 0),
            timezone="UTC",
            life_expectancy=80,
            updated_at=datetime.now(UTC),
        )

    def test_init_default_path(self):
        """Test repository initialization with default path.

        :returns: None
        """
        repo = SQLAlchemyUserRepository()
        assert repo.db_path == Path(DEFAULT_DATABASE_PATH)
        assert repo.engine is None
        assert repo.SessionLocal is None
        assert repo._session is None

    def test_init_custom_path(self, temp_db_path):
        """Test repository initialization with custom path.

        :param temp_db_path: Temporary database path
        :returns: None
        """
        repo = SQLAlchemyUserRepository(temp_db_path)
        assert repo.db_path == Path(temp_db_path)
        assert repo.engine is None
        assert repo.SessionLocal is None
        assert repo._session is None

    def test_initialize_success(self, repository):
        """Test successful database initialization.

        :param repository: Repository instance
        :returns: None
        """
        assert repository.engine is not None
        assert repository.SessionLocal is not None
        assert repository.db_path.exists()

    def test_initialize_failure(self):
        """Test database initialization failure.

        :returns: None
        """
        # Test with invalid path
        invalid_path = "/invalid/path/database.db"
        repo = SQLAlchemyUserRepository(invalid_path)

        with pytest.raises(SQLAlchemyError):
            repo.initialize()

    def test_close_success(self, repository):
        """Test successful database connection closure.

        :param repository: Repository instance
        :returns: None
        """
        repository.close()
        assert repository._session is None
        assert repository.engine is None

    def test_get_session_new(self, repository):
        """Test getting new database session.

        :param repository: Repository instance
        :returns: None
        """
        session = repository._get_session()
        assert session is not None
        assert repository._session is session

    def test_get_session_existing(self, repository):
        """Test getting existing database session.

        :param repository: Repository instance
        :returns: None
        """
        session1 = repository._get_session()
        session2 = repository._get_session()
        assert session1 is session2

    def test_create_user_success(self, repository, sample_user):
        """Test successful user creation.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        result = repository.create_user(sample_user)
        assert result is True

        # Verify user was created
        created_user = repository.get_user(sample_user.telegram_id)
        assert created_user is not None
        assert created_user.telegram_id == sample_user.telegram_id
        assert created_user.username == sample_user.username

    def test_create_user_duplicate(self, repository, sample_user):
        """Test user creation with duplicate telegram_id.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        # Create user first time
        result1 = repository.create_user(sample_user)
        assert result1 is True
        # Clear session to avoid identity conflict warning
        repository._session.expunge_all()
        # Try to create duplicate with same telegram_id
        duplicate_user = User(
            telegram_id=sample_user.telegram_id,
            username="duplicate_user",
            first_name="Duplicate",
            last_name="User",
            created_at=datetime.now(UTC),
        )
        result2 = repository.create_user(duplicate_user)
        assert result2 is False

    def test_create_user_database_error(self, repository, sample_user):
        """Test user creation with database error.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        with patch.object(repository, "_get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.add.side_effect = SQLAlchemyError("Database error")
            mock_get_session.return_value = mock_session

            result = repository.create_user(sample_user)
            assert result is False

    def test_get_user_success(self, repository, sample_user):
        """Test successful user retrieval.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        # Create user first
        repository.create_user(sample_user)

        # Get user
        retrieved_user = repository.get_user(sample_user.telegram_id)
        assert retrieved_user is not None
        assert retrieved_user.telegram_id == sample_user.telegram_id
        assert retrieved_user.username == sample_user.username

    def test_get_user_not_found(self, repository):
        """Test user retrieval when user doesn't exist.

        :param repository: Repository instance
        :returns: None
        """
        user = repository.get_user(999999)
        assert user is None

    def test_get_user_database_error(self, repository):
        """Test user retrieval with database error.

        :param repository: Repository instance
        :returns: None
        """
        with patch.object(repository, "_get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.execute.side_effect = SQLAlchemyError("Database error")
            mock_get_session.return_value = mock_session

            result = repository.get_user(123)
            assert result is None

    def test_update_user_success(self, repository, sample_user):
        """Test successful user update.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        # Create user first
        repository.create_user(sample_user)

        # Update user
        sample_user.username = "updated_username"
        result = repository.update_user(sample_user)
        assert result is True

        # Verify update
        updated_user = repository.get_user(sample_user.telegram_id)
        assert updated_user.username == "updated_username"

    def test_update_user_not_found(self, repository, sample_user):
        """Test user update when user doesn't exist.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        result = repository.update_user(sample_user)
        assert result is False

    def test_update_user_database_error(self, repository, sample_user):
        """Test user update with database error.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        with patch.object(repository, "_get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.execute.side_effect = SQLAlchemyError("Database error")
            mock_get_session.return_value = mock_session

            result = repository.update_user(sample_user)
            assert result is False

    def test_delete_user_success(self, repository, sample_user):
        """Test successful user deletion.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        # Create user first
        repository.create_user(sample_user)

        # Delete user
        result = repository.delete_user(sample_user.telegram_id)
        assert result is True

        # Verify deletion
        deleted_user = repository.get_user(sample_user.telegram_id)
        assert deleted_user is None

    def test_delete_user_not_found(self, repository):
        """Test user deletion when user doesn't exist.

        :param repository: Repository instance
        :returns: None
        """
        result = repository.delete_user(999999)
        assert result is False

    def test_delete_user_database_error(self, repository):
        """Test user deletion with database error.

        :param repository: Repository instance
        :returns: None
        """
        with patch.object(repository, "_get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.execute.side_effect = SQLAlchemyError("Database error")
            mock_get_session.return_value = mock_session

            result = repository.delete_user(123)
            assert result is False

    def test_get_all_users_success(self, repository, sample_user):
        """Test successful retrieval of all users.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        # Create multiple users
        user1 = User(telegram_id=1, username="user1", created_at=datetime.now(UTC))
        user2 = User(telegram_id=2, username="user2", created_at=datetime.now(UTC))

        repository.create_user(user1)
        repository.create_user(user2)

        # Get all users
        users = repository.get_all_users()
        assert len(users) == 2
        assert any(u.telegram_id == 1 for u in users)
        assert any(u.telegram_id == 2 for u in users)

    def test_get_all_users_empty(self, repository):
        """Test retrieval of all users when database is empty.

        :param repository: Repository instance
        :returns: None
        """
        users = repository.get_all_users()
        assert users == []

    def test_get_all_users_database_error(self, repository):
        """Test retrieval of all users with database error.

        :param repository: Repository instance
        :returns: None
        """
        with patch.object(repository, "_get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.execute.side_effect = SQLAlchemyError("Database error")
            mock_get_session.return_value = mock_session

            result = repository.get_all_users()
            assert result == []

    def test_create_user_settings_success(self, repository, sample_settings):
        """Test successful user settings creation.

        :param repository: Repository instance
        :param sample_settings: Sample settings object
        :returns: None
        """
        result = repository.create_user_settings(sample_settings)
        assert result is True

        # Verify settings were created
        created_settings = repository.get_user_settings(sample_settings.telegram_id)
        assert created_settings is not None
        assert created_settings.telegram_id == sample_settings.telegram_id
        assert created_settings.birth_date == sample_settings.birth_date

    def test_create_user_settings_duplicate(self, repository, sample_settings):
        """Test user settings creation with duplicate telegram_id.

        :param repository: Repository instance
        :param sample_settings: Sample settings object
        :returns: None
        """
        # Create settings first time
        result1 = repository.create_user_settings(sample_settings)
        assert result1 is True

        # Try to create duplicate with same telegram_id
        duplicate_settings = UserSettings(
            telegram_id=sample_settings.telegram_id,
            birth_date=date(1995, 5, 15),
            notifications=False,
            notifications_day="tue",
            notifications_time=time(10, 30),
            timezone="UTC",
            life_expectancy=85,
            updated_at=datetime.now(UTC),
        )
        result2 = repository.create_user_settings(duplicate_settings)
        assert result2 is False

    def test_create_user_settings_database_error(self, repository, sample_settings):
        """Test user settings creation with database error.

        :param repository: Repository instance
        :param sample_settings: Sample settings object
        :returns: None
        """
        with patch.object(repository, "_get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.add.side_effect = SQLAlchemyError("Database error")
            mock_get_session.return_value = mock_session

            result = repository.create_user_settings(sample_settings)
            assert result is False

    def test_get_user_settings_success(self, repository, sample_settings):
        """Test successful user settings retrieval.

        :param repository: Repository instance
        :param sample_settings: Sample settings object
        :returns: None
        """
        # Create settings first
        repository.create_user_settings(sample_settings)

        # Get settings
        retrieved_settings = repository.get_user_settings(sample_settings.telegram_id)
        assert retrieved_settings is not None
        assert retrieved_settings.telegram_id == sample_settings.telegram_id
        assert retrieved_settings.birth_date == sample_settings.birth_date

    def test_get_user_settings_not_found(self, repository):
        """Test user settings retrieval when settings don't exist.

        :param repository: Repository instance
        :returns: None
        """
        settings = repository.get_user_settings(999999)
        assert settings is None

    def test_get_user_settings_database_error(self, repository):
        """Test user settings retrieval with database error.

        :param repository: Repository instance
        :returns: None
        """
        with patch.object(repository, "_get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.execute.side_effect = SQLAlchemyError("Database error")
            mock_get_session.return_value = mock_session

            result = repository.get_user_settings(123)
            assert result is None

    def test_update_user_settings_success(self, repository, sample_settings):
        """Test successful user settings update.

        :param repository: Repository instance
        :param sample_settings: Sample settings object
        :returns: None
        """
        # Create settings first
        repository.create_user_settings(sample_settings)

        # Update settings
        sample_settings.birth_date = date(1995, 5, 15)
        result = repository.update_user_settings(sample_settings)
        assert result is True

        # Verify update
        updated_settings = repository.get_user_settings(sample_settings.telegram_id)
        assert updated_settings.birth_date == date(1995, 5, 15)

    def test_update_user_settings_not_found(self, repository, sample_settings):
        """Test user settings update when settings don't exist.

        :param repository: Repository instance
        :param sample_settings: Sample settings object
        :returns: None
        """
        result = repository.update_user_settings(sample_settings)
        assert result is False

    def test_update_user_settings_database_error(self, repository, sample_settings):
        """Test user settings update with database error.

        :param repository: Repository instance
        :param sample_settings: Sample settings object
        :returns: None
        """
        with patch.object(repository, "_get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.execute.side_effect = SQLAlchemyError("Database error")
            mock_get_session.return_value = mock_session

            result = repository.update_user_settings(sample_settings)
            assert result is False

    def test_delete_user_settings_success(self, repository, sample_settings):
        """Test successful user settings deletion.

        :param repository: Repository instance
        :param sample_settings: Sample settings object
        :returns: None
        """
        # Create settings first
        repository.create_user_settings(sample_settings)

        # Delete settings
        result = repository.delete_user_settings(sample_settings.telegram_id)
        assert result is True

        # Verify deletion
        deleted_settings = repository.get_user_settings(sample_settings.telegram_id)
        assert deleted_settings is None

    def test_delete_user_settings_not_found(self, repository):
        """Test user settings deletion when settings don't exist.

        :param repository: Repository instance
        :returns: None
        """
        result = repository.delete_user_settings(999999)
        assert result is False

    def test_delete_user_settings_database_error(self, repository):
        """Test user settings deletion with database error.

        :param repository: Repository instance
        :returns: None
        """
        with patch.object(repository, "_get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.execute.side_effect = SQLAlchemyError("Database error")
            mock_get_session.return_value = mock_session

            result = repository.delete_user_settings(123)
            assert result is False

    def test_get_user_profile_success(self, repository, sample_user, sample_settings):
        """Test successful user profile retrieval.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :param sample_settings: Sample settings object
        :returns: None
        """
        # Create user profile
        repository.create_user_profile(sample_user, sample_settings)

        # Get user profile
        profile = repository.get_user_profile(sample_user.telegram_id)
        assert profile is not None
        assert profile.telegram_id == sample_user.telegram_id
        assert profile.settings is not None
        assert profile.settings.birth_date == sample_settings.birth_date

    def test_get_user_profile_not_found(self, repository):
        """Test user profile retrieval when user doesn't exist.

        :param repository: Repository instance
        :returns: None
        """
        profile = repository.get_user_profile(999999)
        assert profile is None

    def test_get_user_profile_database_error(self, repository):
        """Test user profile retrieval with database error.

        :param repository: Repository instance
        :returns: None
        """
        with patch.object(repository, "_get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.refresh.side_effect = SQLAlchemyError("Database error")
            mock_get_session.return_value = mock_session

            result = repository.get_user_profile(123)
            assert result is None

    def test_get_user_profile_database_error_with_existing_user(
        self, repository, sample_user
    ):
        """Test user profile retrieval with database error when user exists.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        # Create user first
        repository.create_user(sample_user)

        # Mock get_user to return the user, but refresh to fail
        with patch.object(repository, "get_user", return_value=sample_user):
            with patch.object(repository, "_get_session") as mock_get_session:
                mock_session = Mock()
                mock_session.refresh.side_effect = SQLAlchemyError("Database error")
                mock_get_session.return_value = mock_session

                result = repository.get_user_profile(sample_user.telegram_id)
                assert result is None

    def test_create_user_profile_success(
        self, repository, sample_user, sample_settings
    ):
        """Test successful user profile creation.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :param sample_settings: Sample settings object
        :returns: None
        """
        result = repository.create_user_profile(sample_user, sample_settings)
        assert result is True

        # Verify profile was created
        profile = repository.get_user_profile(sample_user.telegram_id)
        assert profile is not None
        assert profile.telegram_id == sample_user.telegram_id
        assert profile.settings is not None
        assert profile.settings.birth_date == sample_settings.birth_date

    def test_create_user_profile_database_error(
        self, repository, sample_user, sample_settings
    ):
        """Test user profile creation with database error.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :param sample_settings: Sample settings object
        :returns: None
        """
        with patch.object(repository, "_get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.add.side_effect = SQLAlchemyError("Database error")
            mock_get_session.return_value = mock_session

            result = repository.create_user_profile(sample_user, sample_settings)
            assert result is False

    def test_update_user_profile_success(
        self, repository, sample_user, sample_settings
    ):
        """Test successful user profile update.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :param sample_settings: Sample settings object
        :returns: None
        """
        # Create profile first
        repository.create_user_profile(sample_user, sample_settings)

        # Update profile
        sample_user.username = "updated_username"
        sample_settings.birth_date = date(1995, 5, 15)

        result = repository.update_user_profile(sample_user, sample_settings)
        assert result is True

        # Verify updates
        profile = repository.get_user_profile(sample_user.telegram_id)
        assert profile.username == "updated_username"
        assert profile.settings.birth_date == date(1995, 5, 15)

    def test_update_user_profile_user_not_found(
        self, repository, sample_user, sample_settings
    ):
        """Test user profile update when user doesn't exist.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :param sample_settings: Sample settings object
        :returns: None
        """
        result = repository.update_user_profile(sample_user, sample_settings)
        assert result is False

    def test_update_user_profile_exception(
        self, repository, sample_user, sample_settings
    ):
        """Test user profile update when exception occurs.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :param sample_settings: Sample settings object
        :returns: None
        """
        # Mock update_user to raise exception
        with patch.object(
            repository, "update_user", side_effect=Exception("Update error")
        ):
            result = repository.update_user_profile(sample_user, sample_settings)
            assert result is False

    def test_set_birth_date_existing_settings(self, repository, sample_settings):
        """Test setting birth date for existing settings.

        :param repository: Repository instance
        :param sample_settings: Sample settings object
        :returns: None
        """
        # Create settings first
        repository.create_user_settings(sample_settings)

        # Set new birth date
        new_birth_date = date(1995, 5, 15)
        result = repository.set_birth_date(sample_settings.telegram_id, new_birth_date)
        assert result is True

        # Verify birth date was set
        settings = repository.get_user_settings(sample_settings.telegram_id)
        assert settings.birth_date == new_birth_date

    def test_set_birth_date_new_settings(self, repository):
        """Test setting birth date for new settings.

        :param repository: Repository instance
        :returns: None
        """
        birth_date = date(1990, 1, 1)
        result = repository.set_birth_date(123456, birth_date)
        assert result is True

        # Verify settings were created with birth date
        settings = repository.get_user_settings(123456)
        assert settings is not None
        assert settings.birth_date == birth_date

    def test_set_birth_date_database_error(self, repository):
        """Test setting birth date with database error.

        :param repository: Repository instance
        :returns: None
        """
        with patch.object(repository, "_get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.commit.side_effect = SQLAlchemyError("Database error")
            mock_get_session.return_value = mock_session

            result = repository.set_birth_date(123, date(1990, 1, 1))
            assert result is False

    def test_get_birth_date_success(self, repository, sample_settings):
        """Test successful birth date retrieval.

        :param repository: Repository instance
        :param sample_settings: Sample settings object
        :returns: None
        """
        # Create settings first
        repository.create_user_settings(sample_settings)

        # Get birth date
        birth_date = repository.get_birth_date(sample_settings.telegram_id)
        assert birth_date == sample_settings.birth_date

    def test_get_birth_date_not_found(self, repository):
        """Test birth date retrieval when settings don't exist.

        :param repository: Repository instance
        :returns: None
        """
        birth_date = repository.get_birth_date(999999)
        assert birth_date is None

    def test_set_notification_settings_existing(self, repository, sample_settings):
        """Test setting notification settings for existing settings.

        :param repository: Repository instance
        :param sample_settings: Sample settings object
        :returns: None
        """
        # Create settings first
        repository.create_user_settings(sample_settings)

        # Set notification settings
        result = repository.set_notification_settings(
            sample_settings.telegram_id,
            notifications=False,
            notifications_day="tue",
            notifications_time=time(10, 30),
        )
        assert result is True

        # Verify settings were updated
        settings = repository.get_user_settings(sample_settings.telegram_id)
        assert settings.notifications is False
        assert settings.notifications_day == "tue"
        assert settings.notifications_time == time(10, 30)

    def test_set_notification_settings_new(self, repository):
        """Test setting notification settings for new settings.

        :param repository: Repository instance
        :returns: None
        """
        result = repository.set_notification_settings(
            123456,
            notifications=True,
            notifications_day="wed",
            notifications_time=time(8, 0),
        )
        assert result is True

        # Verify settings were created
        settings = repository.get_user_settings(123456)
        assert settings is not None
        assert settings.notifications is True
        assert settings.notifications_day == "wed"
        assert settings.notifications_time == time(8, 0)

    def test_set_notification_settings_database_error(self, repository):
        """Test setting notification settings with database error.

        :param repository: Repository instance
        :returns: None
        """
        with patch.object(repository, "_get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.commit.side_effect = SQLAlchemyError("Database error")
            mock_get_session.return_value = mock_session

            result = repository.set_notification_settings(123, True)
            assert result is False

    def test_get_users_with_notifications_success(self, repository):
        """Test successful retrieval of users with notifications.

        :param repository: Repository instance
        :returns: None
        """
        # Create users with different notification settings
        user1 = User(telegram_id=1, username="user1", created_at=datetime.now(UTC))
        user2 = User(telegram_id=2, username="user2", created_at=datetime.now(UTC))
        user3 = User(telegram_id=3, username="user3", created_at=datetime.now(UTC))

        settings1 = UserSettings(
            telegram_id=1, notifications=True, updated_at=datetime.now(UTC)
        )
        settings2 = UserSettings(
            telegram_id=2, notifications=False, updated_at=datetime.now(UTC)
        )
        settings3 = UserSettings(
            telegram_id=3, notifications=True, updated_at=datetime.now(UTC)
        )

        repository.create_user_profile(user1, settings1)
        repository.create_user_profile(user2, settings2)
        repository.create_user_profile(user3, settings3)

        # Get users with notifications
        users_with_notifications = repository.get_users_with_notifications()
        assert len(users_with_notifications) == 2
        assert any(u.telegram_id == 1 for u in users_with_notifications)
        assert any(u.telegram_id == 3 for u in users_with_notifications)
        assert not any(u.telegram_id == 2 for u in users_with_notifications)

    def test_get_users_with_notifications_empty(self, repository):
        """Test retrieval of users with notifications when none exist.

        :param repository: Repository instance
        :returns: None
        """
        users = repository.get_users_with_notifications()
        assert users == []

    def test_get_users_with_notifications_database_error(self, repository):
        """Test retrieval of users with notifications with database error.

        :param repository: Repository instance
        :returns: None
        """
        with patch.object(repository, "_get_session") as mock_get_session:
            mock_session = Mock()
            mock_session.execute.side_effect = SQLAlchemyError("Database error")
            mock_get_session.return_value = mock_session

            result = repository.get_users_with_notifications()
            assert result == []

    def test_integration_full_user_lifecycle(self, repository):
        """Test complete user lifecycle: create, update, delete.

        :param repository: Repository instance
        :returns: None
        """
        # Create user and settings
        user = User(telegram_id=123, username="test", created_at=datetime.now(UTC))
        settings = UserSettings(
            telegram_id=123,
            birth_date=date(1990, 1, 1),
            notifications=True,
            updated_at=datetime.now(UTC),
        )

        # Test creation
        assert repository.create_user_profile(user, settings) is True

        # Test retrieval
        profile = repository.get_user_profile(123)
        assert profile is not None
        assert profile.telegram_id == 123
        assert profile.settings.birth_date == date(1990, 1, 1)

        # Test update
        user.username = "updated_test"
        settings.birth_date = date(1995, 5, 15)
        assert repository.update_user_profile(user, settings) is True

        # Verify update
        updated_profile = repository.get_user_profile(123)
        assert updated_profile.username == "updated_test"
        assert updated_profile.settings.birth_date == date(1995, 5, 15)

        # Test deletion
        assert repository.delete_user(123) is True

        # Verify deletion
        deleted_profile = repository.get_user_profile(123)
        assert deleted_profile is None
