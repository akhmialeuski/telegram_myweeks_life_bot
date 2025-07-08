"""Test suite for SQLite user settings repository.

Tests all functionality of the SQLiteUserSettingsRepository class
including CRUD operations, error handling, and edge cases.
"""

import pytest
from datetime import UTC, date, datetime, time
from unittest.mock import patch
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.database.models import UserSettings
from src.database.repositories.sqlite.user_settings_repository import (
    SQLiteUserSettingsRepository,
)


class TestSQLiteUserSettingsRepository:
    """Test class for SQLiteUserSettingsRepository."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing.

        :returns: Path to temporary database file
        :rtype: str
        """
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp_file:
            yield tmp_file.name
        os.unlink(tmp_file.name)

    @pytest.fixture
    def repository(self, temp_db_path):
        """Create repository instance for testing.

        :param temp_db_path: Path to temporary database
        :returns: Repository instance
        :rtype: SQLiteUserSettingsRepository
        """
        repo = SQLiteUserSettingsRepository(temp_db_path)
        repo.initialize()
        yield repo
        repo.close()

    @pytest.fixture
    def sample_settings(self):
        """Create sample user settings for testing.

        :returns: Sample UserSettings object
        :rtype: UserSettings
        """
        return UserSettings(
            telegram_id=123456789,
            birth_date=date(1990, 1, 1),
            notifications_day="monday",
            life_expectancy=80,
            timezone="UTC",
            notifications=True,
            notifications_time=time(9, 0),
            updated_at=datetime.now(UTC),
        )

    def test_init_default_path(self):
        """Test repository initialization with default path.

        :returns: None
        """
        repo = SQLiteUserSettingsRepository()
        assert repo.db_path.name == "lifeweeks.db"

    def test_init_custom_path(self, temp_db_path):
        """Test repository initialization with custom path.

        :param temp_db_path: Path to temporary database
        :returns: None
        """
        repo = SQLiteUserSettingsRepository(temp_db_path)
        assert str(repo.db_path) == temp_db_path

    def test_initialize_success(self, repository):
        """Test successful repository initialization.

        :param repository: Repository instance
        :returns: None
        """
        assert repository.engine is not None
        assert repository.SessionLocal is not None

    def test_initialize_failure(self):
        """Test repository initialization failure.

        :returns: None
        """
        repo = SQLiteUserSettingsRepository("/invalid/path/db.db")
        with pytest.raises(SQLAlchemyError):
            repo.initialize()

    def test_close_success(self, repository):
        """Test successful repository closure.

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

        # Verify creation
        created_settings = repository.get_user_settings(sample_settings.telegram_id)
        assert created_settings is not None
        assert created_settings.telegram_id == sample_settings.telegram_id
        assert created_settings.birth_date == sample_settings.birth_date

    def test_create_user_settings_duplicate(self, repository, sample_settings):
        """Test user settings creation with duplicate ID.

        :param repository: Repository instance
        :param sample_settings: Sample settings object
        :returns: None
        """
        # Create settings first time
        result1 = repository.create_user_settings(sample_settings)
        assert result1 is True

        # Try to create duplicate
        duplicate_settings = UserSettings(
            telegram_id=sample_settings.telegram_id,
            birth_date=date(1995, 5, 5),
            notifications_day="tuesday",
            life_expectancy=85,
            timezone="EST",
            notifications=False,
            notifications_time=time(10, 30),
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
        with patch("sqlalchemy.orm.Session.add") as mock_add:
            mock_add.side_effect = SQLAlchemyError("Database error")
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
        result = repository.get_user_settings(sample_settings.telegram_id)
        assert result is not None
        assert result.telegram_id == sample_settings.telegram_id
        assert result.birth_date == sample_settings.birth_date

    def test_get_user_settings_not_found(self, repository):
        """Test user settings retrieval when settings don't exist.

        :param repository: Repository instance
        :returns: None
        """
        result = repository.get_user_settings(999999)
        assert result is None

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
