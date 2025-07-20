"""Unit tests for SQLiteUserRepository class.

Tests all methods of the SQLiteUserRepository class using pytest
with proper fixtures, mocking, and edge case coverage.
"""

import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.database.constants import DEFAULT_DATABASE_PATH
from src.database.models.user import User
from src.database.repositories.sqlite.user_repository import SQLiteUserRepository


class TestSQLiteUserRepository:
    """Test suite for SQLiteUserRepository class."""

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
        :returns: SQLiteUserRepository instance
        :rtype: SQLiteUserRepository
        """
        repo = SQLiteUserRepository(temp_db_path)
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

    def test_init_default_path(self):
        """Test repository initialization with default path.

        :returns: None
        """
        repo = SQLiteUserRepository()
        assert repo.db_path == Path(DEFAULT_DATABASE_PATH)
        assert repo.engine is None
        assert repo.SessionLocal is None

    def test_init_custom_path(self, temp_db_path):
        """Test repository initialization with custom path.

        :param temp_db_path: Temporary database path
        :returns: None
        """
        repo = SQLiteUserRepository(temp_db_path)
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
        repo = SQLiteUserRepository(invalid_path)

        with pytest.raises(SQLAlchemyError):
            repo.initialize()

    def test_close_success(self, repository):
        """Test successful database connection closure.

        :param repository: Repository instance
        :returns: None
        """
        repository.close()
        assert repository.engine is None

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
        with patch("sqlalchemy.orm.Session.add") as mock_add:
            mock_add.side_effect = SQLAlchemyError("Database error")
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
        user = repository.get_user(sample_user.telegram_id)
        assert user is not None
        assert user.telegram_id == sample_user.telegram_id
        assert user.username == sample_user.username

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
        with patch("sqlalchemy.orm.Session.execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")
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
        sample_user.username = "updated_user"
        result = repository.update_user(sample_user)
        assert result is True

        # Verify update
        updated_user = repository.get_user(sample_user.telegram_id)
        assert updated_user.username == "updated_user"

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
        with patch("sqlalchemy.orm.Session.execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")
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
        with patch("sqlalchemy.orm.Session.execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")
            result = repository.delete_user(123)
            assert result is False
