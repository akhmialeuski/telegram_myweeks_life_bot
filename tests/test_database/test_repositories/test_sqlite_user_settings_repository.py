"""Unit tests for SQLiteUserSettingsRepository class.

Tests all methods of the SQLiteUserSettingsRepository class using pytest
with proper fixtures, mocking, and edge case coverage.
"""

import os
import tempfile
from datetime import UTC, date, datetime, time
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.database.constants import DEFAULT_DATABASE_PATH
from src.database.models import UserSettings
from src.database.repositories.sqlite.user_settings_repository import (
    SQLiteUserSettingsRepository,
)


class TestSQLiteUserSettingsRepository:
    """Test suite for SQLiteUserSettingsRepository class."""

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
        :returns: SQLiteUserSettingsRepository instance
        :rtype: SQLiteUserSettingsRepository
        """
        repo = SQLiteUserSettingsRepository(temp_db_path)
        repo.initialize()
        yield repo
        repo.close()

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
        repo = SQLiteUserSettingsRepository()
        assert repo.db_path == Path(DEFAULT_DATABASE_PATH)
        assert repo.engine is None
        assert repo.SessionLocal is None

    def test_init_custom_path(self, temp_db_path):
        """Test repository initialization with custom path.

        :param temp_db_path: Temporary database path
        :returns: None
        """
        repo = SQLiteUserSettingsRepository(temp_db_path)
        assert repo.db_path == Path(temp_db_path)
        assert repo.engine is None
        assert repo.SessionLocal is None

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
        repo = SQLiteUserSettingsRepository(invalid_path)

        with pytest.raises(SQLAlchemyError):
            repo.initialize()

    def test_close_success(self, repository):
        """Test successful database connection closure.

        :param repository: Repository instance
        :returns: None
        """
        repository.close()
        assert repository.engine is None

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
            birth_date=date(1991, 1, 1),
            notifications=False,
            notifications_day="tue",
            notifications_time=time(10, 0),
            timezone="GMT",
            life_expectancy=75,
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
        with patch.object(repository, "session") as mock_session:
            mock_session.side_effect = SQLAlchemyError("Database error")
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
        settings = repository.get_user_settings(sample_settings.telegram_id)
        assert settings is not None
        assert settings.telegram_id == sample_settings.telegram_id
        assert settings.birth_date == sample_settings.birth_date

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
        with patch("sqlalchemy.orm.Session.execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")
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
        sample_settings.notifications = False
        result = repository.update_user_settings(sample_settings)
        assert result is True

        # Verify update
        updated_settings = repository.get_user_settings(sample_settings.telegram_id)
        assert updated_settings.notifications is False

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
        with patch("sqlalchemy.orm.Session.execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")
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
        with patch("sqlalchemy.orm.Session.execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")
            result = repository.delete_user_settings(123)
            assert result is False

    def test_set_birth_date_success(self, repository, sample_settings):
        """Test successful birth date setting.

        :param repository: Repository instance
        :param sample_settings: Sample settings object
        :returns: None
        """
        # Create settings first
        repository.create_user_settings(sample_settings)

        # Set birth date
        new_birth_date = date(1991, 1, 1)
        result = repository.set_birth_date(sample_settings.telegram_id, new_birth_date)
        assert result is True

        # Verify update
        updated_settings = repository.get_user_settings(sample_settings.telegram_id)
        assert updated_settings.birth_date == new_birth_date

    def test_set_birth_date_new_settings(self, repository):
        """Test birth date setting for new settings.

        :param repository: Repository instance
        :returns: None
        """
        telegram_id = 123456789
        birth_date = date(1990, 1, 1)
        result = repository.set_birth_date(telegram_id, birth_date)
        assert result is True

        # Verify settings were created
        settings = repository.get_user_settings(telegram_id)
        assert settings is not None
        assert settings.birth_date == birth_date

    def test_set_birth_date_database_error(self, repository):
        """Test birth date setting with database error.

        :param repository: Repository instance
        :returns: None
        """
        with patch("sqlalchemy.orm.Session.execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")
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

    def test_set_notification_settings_success(self, repository, sample_settings):
        """Test successful notification settings update.

        :param repository: Repository instance
        :param sample_settings: Sample settings object
        :returns: None
        """
        # Create settings first
        repository.create_user_settings(sample_settings)

        # Update notification settings
        result = repository.set_notification_settings(
            sample_settings.telegram_id,
            notifications=False,
            notifications_day="tue",
            notifications_time=time(10, 0),
        )
        assert result is True

        # Verify update
        updated_settings = repository.get_user_settings(sample_settings.telegram_id)
        assert updated_settings.notifications is False
        assert updated_settings.notifications_day == "tue"
        assert updated_settings.notifications_time == time(10, 0)

    def test_set_notification_settings_new_settings(self, repository):
        """Test notification settings update for new settings.

        :param repository: Repository instance
        :returns: None
        """
        telegram_id = 123456789
        result = repository.set_notification_settings(
            telegram_id,
            notifications=True,
            notifications_day="mon",
            notifications_time=time(9, 0),
        )
        assert result is True

        # Verify settings were created
        settings = repository.get_user_settings(telegram_id)
        assert settings is not None
        assert settings.notifications is True
        assert settings.notifications_day == "mon"
        assert settings.notifications_time == time(9, 0)

    def test_set_notification_settings_database_error(self, repository):
        """Test notification settings update with database error.

        :param repository: Repository instance
        :returns: None
        """
        with patch("sqlalchemy.orm.Session.execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")
            result = repository.set_notification_settings(
                123,
                notifications=True,
                notifications_day="mon",
                notifications_time=time(9, 0),
            )
            assert result is False
