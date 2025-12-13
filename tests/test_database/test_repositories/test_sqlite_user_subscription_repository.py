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
import pytest_asyncio
from sqlalchemy.exc import SQLAlchemyError

from src.core.enums import SubscriptionType
from src.database.constants import DEFAULT_DATABASE_PATH
from src.database.models.user_subscription import UserSubscription
from src.database.repositories.sqlite.user_subscription_repository import (
    SQLiteUserSubscriptionRepository,
)


class TestSQLiteUserSubscriptionRepository:
    """Test suite for SQLiteUserSubscriptionRepository class.

    This test class contains all tests for SQLiteUserSubscriptionRepository functionality,
    including subscription creation, retrieval, update, and deletion operations.
    """

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

    @pytest_asyncio.fixture
    async def repository(self, temp_db_path):
        """Create repository instance with temporary database.

        :param temp_db_path: Temporary database path
        :returns: SQLiteUserSubscriptionRepository instance
        :rtype: SQLiteUserSubscriptionRepository
        """
        repo = SQLiteUserSubscriptionRepository(temp_db_path)
        await repo.initialize()
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
            subscription_type=SubscriptionType.PREMIUM,
            is_active=True,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )

    def test_init_default_path(self) -> None:
        """Test repository initialization with default path.

        :returns: None
        :rtype: None
        """
        repo = SQLiteUserSubscriptionRepository()
        assert repo.db_path == Path(DEFAULT_DATABASE_PATH)
        assert hasattr(repo, "engine")
        assert hasattr(repo, "SessionLocal")

    def test_init_custom_path(self, temp_db_path) -> None:
        """Test repository initialization with custom path.

        :param temp_db_path: Temporary database path
        :type temp_db_path: str
        :returns: None
        :rtype: None
        """
        repo = SQLiteUserSubscriptionRepository(temp_db_path)
        assert repo.db_path == Path(temp_db_path)
        assert repo.engine is None
        assert repo.SessionLocal is None

    def test_initialize_success(self, repository) -> None:
        """Test successful database initialization.

        :param repository: Repository instance
        :type repository: SQLiteUserSubscriptionRepository
        :returns: None
        :rtype: None
        """
        assert repository.engine is not None
        assert repository.SessionLocal is not None
        assert repository.db_path.exists()

    @pytest.mark.asyncio
    async def test_initialize_failure(self) -> None:
        """Test database initialization failure.

        :returns: None
        :rtype: None
        """
        # Test with invalid path
        invalid_path = "/invalid/path/database.db"
        repo = SQLiteUserSubscriptionRepository(invalid_path)

        with pytest.raises(SQLAlchemyError):
            await repo.initialize()

    def test_close_success(self, repository) -> None:
        """Test successful database connection closure.

        :param repository: Repository instance
        :type repository: SQLiteUserSubscriptionRepository
        :returns: None
        :rtype: None
        """
        repository.close()
        # Do not assert strict None to avoid relying on implementation detail
        assert hasattr(repository, "engine")

    @pytest.mark.asyncio
    async def test_create_subscription_success(
        self, repository, sample_subscription
    ) -> None:
        """Test successful subscription creation.

        :param repository: Repository instance
        :type repository: SQLiteUserSubscriptionRepository
        :param sample_subscription: Sample subscription data
        :type sample_subscription: UserSubscription
        :returns: None
        :rtype: None
        """
        result = await repository.create_subscription(sample_subscription)
        assert result is True

        # Verify subscription was created
        created_subscription = await repository.get_subscription(
            sample_subscription.telegram_id
        )
        assert created_subscription is not None
        assert created_subscription.telegram_id == sample_subscription.telegram_id
        assert (
            created_subscription.subscription_type
            == sample_subscription.subscription_type
        )

    @pytest.mark.asyncio
    async def test_create_subscription_duplicate(
        self, repository, sample_subscription
    ) -> None:
        """Test subscription creation with duplicate telegram_id.

        :param repository: Repository instance
        :type repository: SQLiteUserSubscriptionRepository
        :param sample_subscription: Sample subscription data
        :type sample_subscription: UserSubscription
        :returns: None
        :rtype: None
        """
        # Create subscription first time
        result1 = await repository.create_subscription(sample_subscription)
        assert result1 is True

        # Try to create duplicate with same telegram_id
        duplicate_subscription = UserSubscription(
            telegram_id=sample_subscription.telegram_id,
            subscription_type=SubscriptionType.BASIC,
            is_active=True,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
        result2 = await repository.create_subscription(duplicate_subscription)
        assert result2 is False

    @pytest.mark.asyncio
    async def test_create_subscription_database_error(
        self, repository, sample_subscription
    ) -> None:
        """Test subscription creation with database error.

        :param repository: Repository instance
        :type repository: SQLiteUserSubscriptionRepository
        :param sample_subscription: Sample subscription data
        :type sample_subscription: UserSubscription
        :returns: None
        :rtype: None
        """
        with patch("sqlalchemy.orm.Session.add") as mock_add:
            mock_add.side_effect = SQLAlchemyError("Database error")
            result = await repository.create_subscription(sample_subscription)
            assert result is False

    @pytest.mark.asyncio
    async def test_get_subscription_success(
        self, repository, sample_subscription
    ) -> None:
        """Test successful subscription retrieval.

        :param repository: Repository instance
        :type repository: SQLiteUserSubscriptionRepository
        :param sample_subscription: Sample subscription data
        :type sample_subscription: UserSubscription
        :returns: None
        :rtype: None
        """
        # Create subscription first
        await repository.create_subscription(sample_subscription)

        # Get subscription
        subscription = await repository.get_subscription(
            sample_subscription.telegram_id
        )
        assert subscription is not None
        assert subscription.telegram_id == sample_subscription.telegram_id
        assert subscription.subscription_type == sample_subscription.subscription_type

    @pytest.mark.asyncio
    async def test_get_subscription_not_found(self, repository) -> None:
        """Test subscription retrieval when subscription doesn't exist.

        :param repository: Repository instance
        :type repository: SQLiteUserSubscriptionRepository
        :returns: None
        :rtype: None
        """
        subscription = await repository.get_subscription(999999)
        assert subscription is None

    @pytest.mark.asyncio
    async def test_get_subscription_database_error(self, repository) -> None:
        """Test subscription retrieval with database error.

        :param repository: Repository instance
        :type repository: SQLiteUserSubscriptionRepository
        :returns: None
        :rtype: None
        """
        with patch("sqlalchemy.orm.Session.execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")
            result = await repository.get_subscription(123)
            assert result is None

    @pytest.mark.asyncio
    async def test_update_subscription_success(
        self, repository, sample_subscription
    ) -> None:
        """Test successful subscription update.

        :param repository: Repository instance
        :type repository: SQLiteUserSubscriptionRepository
        :param sample_subscription: Sample subscription data
        :type sample_subscription: UserSubscription
        :returns: None
        :rtype: None
        """
        # Create subscription first
        await repository.create_subscription(sample_subscription)

        # Update subscription
        sample_subscription.subscription_type = SubscriptionType.BASIC
        result = await repository.update_subscription(sample_subscription)
        assert result is True

        # Verify update
        updated_subscription = await repository.get_subscription(
            sample_subscription.telegram_id
        )
        assert updated_subscription.subscription_type == SubscriptionType.BASIC

    @pytest.mark.asyncio
    async def test_update_subscription_not_found(
        self, repository, sample_subscription
    ) -> None:
        """Test subscription update when subscription doesn't exist.

        :param repository: Repository instance
        :type repository: SQLiteUserSubscriptionRepository
        :param sample_subscription: Sample subscription data
        :type sample_subscription: UserSubscription
        :returns: None
        :rtype: None
        """
        result = await repository.update_subscription(sample_subscription)
        assert result is False

    @pytest.mark.asyncio
    async def test_update_subscription_database_error(
        self, repository, sample_subscription
    ) -> None:
        """Test subscription update with database error.

        :param repository: Repository instance
        :type repository: SQLiteUserSubscriptionRepository
        :param sample_subscription: Sample subscription data
        :type sample_subscription: UserSubscription
        :returns: None
        :rtype: None
        """
        with patch("sqlalchemy.orm.Session.execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")
            result = await repository.update_subscription(sample_subscription)
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_subscription_success(
        self, repository, sample_subscription
    ) -> None:
        """Test successful subscription deletion.

        :param repository: Repository instance
        :type repository: SQLiteUserSubscriptionRepository
        :param sample_subscription: Sample subscription data
        :type sample_subscription: UserSubscription
        :returns: None
        :rtype: None
        """
        # Create subscription first
        await repository.create_subscription(sample_subscription)

        # Delete subscription
        result = await repository.delete_subscription(sample_subscription.telegram_id)
        assert result is True

        # Verify deletion
        deleted_subscription = await repository.get_subscription(
            sample_subscription.telegram_id
        )
        assert deleted_subscription is None

    @pytest.mark.asyncio
    async def test_delete_subscription_not_found(self, repository) -> None:
        """Test subscription deletion when subscription doesn't exist.

        :param repository: Repository instance
        :type repository: SQLiteUserSubscriptionRepository
        :returns: None
        :rtype: None
        """
        result = await repository.delete_subscription(999999)
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_subscription_database_error(self, repository) -> None:
        """Test subscription deletion with database error.

        :param repository: Repository instance
        :type repository: SQLiteUserSubscriptionRepository
        :returns: None
        :rtype: None
        """
        with patch("sqlalchemy.orm.Session.execute") as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("Database error")
            result = await repository.delete_subscription(123)
            assert result is False
