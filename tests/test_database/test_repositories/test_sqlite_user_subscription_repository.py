"""Unit tests for SQLiteUserSubscriptionRepository class.

Tests all methods of the SQLiteUserSubscriptionRepository class using pytest
with proper fixtures, mocking, and edge case coverage.
"""

import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.database.constants import DEFAULT_DATABASE_PATH
from src.database.models import UserSubscription
from src.database.repositories.sqlite.user_subscription_repository import (
    SQLiteUserSubscriptionRepository,
)


class TestSQLiteUserSubscriptionRepository:
    """Test suite for SQLiteUserSubscriptionRepository class."""

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
        :returns: SQLiteUserSubscriptionRepository instance
        :rtype: SQLiteUserSubscriptionRepository
        """
        repo = SQLiteUserSubscriptionRepository(temp_db_path)
        repo.initialize()
        yield repo
        repo.close()

    @pytest.fixture
    def sample_subscription(self):
        """Create a sample UserSubscription object for testing.

        :returns: Sample UserSubscription object
        :rtype: UserSubscription
        """
        return UserSubscription(
            telegram_id=123456789,
            subscription_type="premium",
            is_active=True,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )

    def test_init_default_path(self):
        """Test repository initialization with default path.

        :returns: None
        """
        repo = SQLiteUserSubscriptionRepository()
        assert repo.db_path == Path(DEFAULT_DATABASE_PATH)
        assert repo.engine is None
        assert repo.SessionLocal is None

    def test_init_custom_path(self, temp_db_path):
        """Test repository initialization with custom path.

        :param temp_db_path: Temporary database path
        :returns: None
        """
        repo = SQLiteUserSubscriptionRepository(temp_db_path)
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
        repo = SQLiteUserSubscriptionRepository(invalid_path)

        with pytest.raises(SQLAlchemyError):
            repo.initialize()

    def test_close_success(self, repository):
        """Test successful database connection closure.

        :param repository: Repository instance
        :returns: None
        """
        repository.close()
        assert repository.engine is None

    def test_create_subscription_success(self, repository, sample_subscription):
        """Test successful subscription creation.

        :param repository: Repository instance
        :param sample_subscription: Sample subscription object
        :returns: None
        """
        result = repository.create_subscription(sample_subscription)
        assert result is True

        # Verify subscription was created
        created_subscription = repository.get_subscription(
            sample_subscription.telegram_id
        )
        assert created_subscription is not None
        assert created_subscription.telegram_id == sample_subscription.telegram_id
        assert (
            created_subscription.subscription_type
            == sample_subscription.subscription_type
        )

    def test_create_subscription_duplicate(self, repository, sample_subscription):
        """Test subscription creation with duplicate telegram_id.

        :param repository: Repository instance
        :param sample_subscription: Sample subscription object
        :returns: None
        """
        # Create subscription first time
        result1 = repository.create_subscription(sample_subscription)
        assert result1 is True

        # Try to create duplicate with same telegram_id
        duplicate_subscription = UserSubscription(
            telegram_id=sample_subscription.telegram_id,
            subscription_type="basic",
            is_active=True,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        result2 = repository.create_subscription(duplicate_subscription)
        assert result2 is False

    def test_create_subscription_database_error(self, repository, sample_subscription):
        """Test subscription creation with database error.

        :param repository: Repository instance
        :param sample_subscription: Sample subscription object
        :returns: None
        """
        with patch("sqlalchemy.orm.Session.add") as mock_add:
            mock_add.side_effect = SQLAlchemyError("Database error")
            result = repository.create_subscription(sample_subscription)
            assert result is False

    def test_get_subscription_success(self, repository, sample_subscription):
        """Test successful subscription retrieval.

        :param repository: Repository instance
        :param sample_subscription: Sample subscription object
        :returns: None
        """
        # Create subscription first
        repository.create_subscription(sample_subscription)

        # Get subscription
        subscription = repository.get_subscription(sample_subscription.telegram_id)
        assert subscription is not None
        assert subscription.telegram_id == sample_subscription.telegram_id
        assert subscription.subscription_type == sample_subscription.subscription_type

    def test_get_subscription_not_found(self, repository):
        """Test subscription retrieval when subscription doesn't exist.

        :param repository: Repository instance
        :returns: None
        """
        subscription = repository.get_subscription(999999)
        assert subscription is None

    def test_get_subscription_database_error(self, repository):
        """Test subscription retrieval with database error.

        :param repository: Repository instance
        :returns: None
        """
        with patch("sqlalchemy.orm.Session.execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")
            result = repository.get_subscription(123)
            assert result is None

    def test_update_subscription_success(self, repository, sample_subscription):
        """Test successful subscription update.

        :param repository: Repository instance
        :param sample_subscription: Sample subscription object
        :returns: None
        """
        # Create subscription first
        repository.create_subscription(sample_subscription)

        # Update subscription
        sample_subscription.subscription_type = "basic"
        result = repository.update_subscription(sample_subscription)
        assert result is True

        # Verify update
        updated_subscription = repository.get_subscription(
            sample_subscription.telegram_id
        )
        assert updated_subscription.subscription_type == "basic"

    def test_update_subscription_not_found(self, repository, sample_subscription):
        """Test subscription update when subscription doesn't exist.

        :param repository: Repository instance
        :param sample_subscription: Sample subscription object
        :returns: None
        """
        result = repository.update_subscription(sample_subscription)
        assert result is False

    def test_update_subscription_database_error(self, repository, sample_subscription):
        """Test subscription update with database error.

        :param repository: Repository instance
        :param sample_subscription: Sample subscription object
        :returns: None
        """
        with patch("sqlalchemy.orm.Session.execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")
            result = repository.update_subscription(sample_subscription)
            assert result is False

    def test_delete_subscription_success(self, repository, sample_subscription):
        """Test successful subscription deletion.

        :param repository: Repository instance
        :param sample_subscription: Sample subscription object
        :returns: None
        """
        # Create subscription first
        repository.create_subscription(sample_subscription)

        # Delete subscription
        result = repository.delete_subscription(sample_subscription.telegram_id)
        assert result is True

        # Verify deletion
        deleted_subscription = repository.get_subscription(
            sample_subscription.telegram_id
        )
        assert deleted_subscription is None

    def test_delete_subscription_not_found(self, repository):
        """Test subscription deletion when subscription doesn't exist.

        :param repository: Repository instance
        :returns: None
        """
        result = repository.delete_subscription(999999)
        assert result is False

    def test_delete_subscription_database_error(self, repository):
        """Test subscription deletion with database error.

        :param repository: Repository instance
        :returns: None
        """
        with patch("sqlalchemy.orm.Session.execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")
            result = repository.delete_subscription(123)
            assert result is False
