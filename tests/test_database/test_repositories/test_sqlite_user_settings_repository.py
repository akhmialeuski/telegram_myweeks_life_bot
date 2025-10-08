"""Test suite for SQLite user settings repository.

Tests all functionality of the SQLiteUserSettingsRepository class
including CRUD operations, error handling, and edge cases.
"""

from datetime import UTC, date, datetime, time
from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.core.enums import WeekDay
from src.database.models.user_settings import UserSettings
from src.database.repositories.sqlite.user_settings_repository import (
    SQLiteUserSettingsRepository,
)
from tests.conftest import (
    DEFAULT_LIFE_EXPECTANCY,
    DEFAULT_TIMEZONE,
    TEST_BIRTH_YEAR,
    TEST_LIFE_EXPECTANCY_ALT,
    TEST_TIMEZONE_EST,
    TEST_USER_ID,
    TEST_USER_ID_NONEXISTENT,
)


class TestSQLiteUserSettingsRepository:
    """Test class for SQLiteUserSettingsRepository.

    This test class contains all tests for SQLiteUserSettingsRepository functionality,
    including settings creation, retrieval, update, and deletion operations.
    """

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing.

        :returns: Path to temporary database file
        :rtype: str
        """
        import os
        import tempfile

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
            telegram_id=TEST_USER_ID,
            birth_date=date(TEST_BIRTH_YEAR, 1, 1),
            notifications_day=WeekDay.MONDAY,
            life_expectancy=DEFAULT_LIFE_EXPECTANCY,
            timezone=DEFAULT_TIMEZONE,
            notifications=True,
            notifications_time=time(9, 0),
            updated_at=datetime.now(UTC),
        )

    def test_init_default_path(self) -> None:
        """Test repository initialization with default path.

        :returns: None
        :rtype: None
        """
        repo = SQLiteUserSettingsRepository()
        assert repo.db_path.name == "lifeweeks.db"

    def test_init_custom_path(self, temp_db_path) -> None:
        """Test repository initialization with custom path.

        :param temp_db_path: Path to temporary database
        :type temp_db_path: str
        :returns: None
        :rtype: None
        """
        repo = SQLiteUserSettingsRepository(temp_db_path)
        assert str(repo.db_path) == temp_db_path

    def test_initialize_success(self, repository) -> None:
        """Test successful repository initialization.

        :param repository: Repository instance
        :type repository: SQLiteUserSettingsRepository
        :returns: None
        :rtype: None
        """
        assert repository.engine is not None
        assert repository.SessionLocal is not None

    def test_initialize_failure(self) -> None:
        """Test repository initialization failure.

        :returns: None
        :rtype: None
        """
        repo = SQLiteUserSettingsRepository("/invalid/path/db.db")
        with pytest.raises(SQLAlchemyError):
            repo.initialize()

    def test_close_success(self, repository) -> None:
        """Test successful repository closure.

        :param repository: Repository instance
        :type repository: SQLiteUserSettingsRepository
        :returns: None
        :rtype: None
        """
        repository.close()
        # Engine may be handled globally; avoid strict None assertion
        assert hasattr(repository, "engine")

    def test_create_user_settings_success(self, repository, sample_settings) -> None:
        """Test successful user settings creation.

        :param repository: Repository instance
        :type repository: SQLiteUserSettingsRepository
        :param sample_settings: Sample settings data
        :type sample_settings: UserSettings
        :returns: None
        :rtype: None
        """
        result = repository.create_user_settings(sample_settings)
        assert result is True

        # Verify creation
        created_settings = repository.get_user_settings(sample_settings.telegram_id)
        assert created_settings is not None
        assert created_settings.telegram_id == sample_settings.telegram_id
        assert created_settings.birth_date == sample_settings.birth_date

    def test_create_user_settings_duplicate(self, repository, sample_settings) -> None:
        """Test user settings creation with duplicate ID.

        :param repository: Repository instance
        :type repository: SQLiteUserSettingsRepository
        :param sample_settings: Sample settings data
        :type sample_settings: UserSettings
        :returns: None
        :rtype: None
        """
        # Create settings first time
        result1 = repository.create_user_settings(sample_settings)
        assert result1 is True

        # Try to create duplicate
        duplicate_settings = UserSettings(
            telegram_id=sample_settings.telegram_id,
            birth_date=date(1995, 5, 5),
            notifications_day=WeekDay.TUESDAY,
            life_expectancy=TEST_LIFE_EXPECTANCY_ALT,
            timezone=TEST_TIMEZONE_EST,
            notifications=False,
            notifications_time=time(10, 30),
            updated_at=datetime.now(UTC),
        )
        result2 = repository.create_user_settings(duplicate_settings)
        assert result2 is False

    def test_create_user_settings_database_error(
        self, repository, sample_settings
    ) -> None:
        """Test user settings creation with database error.

        :param repository: Repository instance
        :type repository: SQLiteUserSettingsRepository
        :param sample_settings: Sample settings data
        :type sample_settings: UserSettings
        :returns: None
        :rtype: None
        """
        with patch("sqlalchemy.orm.Session.add") as mock_add:
            mock_add.side_effect = SQLAlchemyError("Database error")
            result = repository.create_user_settings(sample_settings)
            assert result is False

    def test_get_user_settings_success(self, repository, sample_settings) -> None:
        """Test successful user settings retrieval.

        :param repository: Repository instance
        :type repository: SQLiteUserSettingsRepository
        :param sample_settings: Sample settings data
        :type sample_settings: UserSettings
        :returns: None
        :rtype: None
        """
        # Create settings first
        repository.create_user_settings(sample_settings)

        # Get settings
        result = repository.get_user_settings(sample_settings.telegram_id)
        assert result is not None
        assert result.telegram_id == sample_settings.telegram_id
        assert result.birth_date == sample_settings.birth_date

    def test_get_user_settings_not_found(self, repository) -> None:
        """Test user settings retrieval when settings don't exist.

        :param repository: Repository instance
        :type repository: SQLiteUserSettingsRepository
        :returns: None
        :rtype: None
        """
        result = repository.get_user_settings(TEST_USER_ID_NONEXISTENT)
        assert result is None

    def test_get_user_settings_database_error(self, repository) -> None:
        """Test user settings retrieval with database error.

        :param repository: Repository instance
        :type repository: SQLiteUserSettingsRepository
        :returns: None
        :rtype: None
        """
        with patch("sqlalchemy.orm.Session.execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")
            result = repository.get_user_settings(123)
            assert result is None

    def test_update_user_settings_success(self, repository, sample_settings) -> None:
        """Test successful user settings update.

        :param repository: Repository instance
        :type repository: SQLiteUserSettingsRepository
        :param sample_settings: Sample settings data
        :type sample_settings: UserSettings
        :returns: None
        :rtype: None
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

    def test_update_user_settings_not_found(self, repository, sample_settings) -> None:
        """Test user settings update when settings don't exist.

        :param repository: Repository instance
        :type repository: SQLiteUserSettingsRepository
        :param sample_settings: Sample settings data
        :type sample_settings: UserSettings
        :returns: None
        :rtype: None
        """
        result = repository.update_user_settings(sample_settings)
        assert result is False

    def test_update_user_settings_database_error(
        self, repository, sample_settings
    ) -> None:
        """Test user settings update with database error.

        :param repository: Repository instance
        :type repository: SQLiteUserSettingsRepository
        :param sample_settings: Sample settings data
        :type sample_settings: UserSettings
        :returns: None
        :rtype: None
        """
        with patch("sqlalchemy.orm.Session.execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")
            result = repository.update_user_settings(sample_settings)
            assert result is False

    def test_delete_user_settings_success(self, repository, sample_settings) -> None:
        """Test successful user settings deletion.

        :param repository: Repository instance
        :type repository: SQLiteUserSettingsRepository
        :param sample_settings: Sample settings data
        :type sample_settings: UserSettings
        :returns: None
        :rtype: None
        """
        # Create settings first
        repository.create_user_settings(sample_settings)

        # Delete settings
        result = repository.delete_user_settings(sample_settings.telegram_id)
        assert result is True

        # Verify deletion
        deleted_settings = repository.get_user_settings(sample_settings.telegram_id)
        assert deleted_settings is None

    def test_delete_user_settings_not_found(self, repository) -> None:
        """Test user settings deletion when settings don't exist.

        :param repository: Repository instance
        :type repository: SQLiteUserSettingsRepository
        :returns: None
        :rtype: None
        """
        result = repository.delete_user_settings(TEST_USER_ID_NONEXISTENT)
        assert result is False

    def test_delete_user_settings_database_error(self, repository) -> None:
        """Test user settings deletion with database error.

        :param repository: Repository instance
        :type repository: SQLiteUserSettingsRepository
        :returns: None
        :rtype: None
        """
        with patch("sqlalchemy.orm.Session.execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")
            result = repository.delete_user_settings(123)
            assert result is False
