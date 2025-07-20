"""Test suite for SQLite base repository.

Tests all functionality of the BaseSQLiteRepository class
including session management, CRUD operations, and error handling.
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.database.models.user import User
from src.database.repositories.sqlite.base_repository import BaseSQLiteRepository


class TestBaseSQLiteRepository:
    """Test class for BaseSQLiteRepository."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing.

        :returns: Path to temporary database file
        :rtype: str
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp_file:
            yield tmp_file.name
        if os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)

    @pytest.fixture
    def repository(self, temp_db_path):
        """Create repository instance for testing.

        :param temp_db_path: Path to temporary database
        :returns: Repository instance
        :rtype: BaseSQLiteRepository
        """
        repo = BaseSQLiteRepository(temp_db_path)
        repo.initialize()
        yield repo
        repo.close()

    @pytest.fixture
    def sample_user(self):
        """Create sample user for testing.

        :returns: Sample User object
        :rtype: User
        """
        from datetime import UTC, datetime

        return User(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User",
            created_at=datetime.now(UTC),
        )

    def test_init_default_path(self):
        """Test repository initialization with default path.

        :returns: None
        """
        repo = BaseSQLiteRepository()
        assert repo.db_path.name == "lifeweeks.db"
        assert repo.engine is None
        assert repo.SessionLocal is None

    def test_init_custom_path(self, temp_db_path):
        """Test repository initialization with custom path.

        :param temp_db_path: Path to temporary database
        :returns: None
        """
        repo = BaseSQLiteRepository(temp_db_path)
        assert str(repo.db_path) == temp_db_path
        assert repo.engine is None
        assert repo.SessionLocal is None

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
        repo = BaseSQLiteRepository("/invalid/path/db.db")
        with pytest.raises(SQLAlchemyError):
            repo.initialize()

    def test_initialize_idempotent(self, repository):
        """Test that initialize can be called multiple times safely.

        :param repository: Repository instance
        :returns: None
        """
        original_engine = repository.engine
        repository.initialize()  # Call again
        assert repository.engine is original_engine  # Should not change

    def test_close_success(self, repository):
        """Test successful repository closure.

        :param repository: Repository instance
        :returns: None
        """
        repository.close()
        assert repository.engine is None

    def test_close_when_not_initialized(self):
        """Test closing repository that was never initialized.

        :returns: None
        """
        repo = BaseSQLiteRepository("test.db")
        repo.close()  # Should not raise exception
        assert repo.engine is None

    def test_session_context_manager_success(self, repository):
        """Test successful session context manager usage.

        :param repository: Repository instance
        :returns: None
        """
        from sqlalchemy import text

        with repository.session() as session:
            assert isinstance(session, Session)
            # Test that we can execute a simple query
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_session_not_initialized(self):
        """Test session usage when repository not initialized.

        :returns: None
        """
        repo = BaseSQLiteRepository("test.db")
        with pytest.raises(RuntimeError, match="Repository not initialized"):
            with repo.session():
                pass

    def test_session_rollback_on_error(self, repository):
        """Test that session rolls back on error.

        :param repository: Repository instance
        :returns: None
        """
        with patch.object(repository, "SessionLocal") as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session
            mock_session.execute.side_effect = SQLAlchemyError("Test error")

            with pytest.raises(SQLAlchemyError):
                with repository.session() as session:
                    session.execute("SELECT 1")

            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()

    def test_detach_instance_in_session(self, repository):
        """Test detaching instance that is in session.

        :param repository: Repository instance
        :returns: None
        """
        mock_session = Mock()
        mock_instance = Mock()
        mock_session.__contains__ = Mock(return_value=True)

        repository._detach_instance(mock_session, mock_instance)
        mock_session.expunge.assert_called_once_with(mock_instance)

    def test_detach_instance_not_in_session(self, repository):
        """Test detaching instance that is not in session.

        :param repository: Repository instance
        :returns: None
        """
        mock_session = Mock()
        mock_instance = Mock()
        mock_session.__contains__ = Mock(return_value=False)

        repository._detach_instance(mock_session, mock_instance)
        mock_session.expunge.assert_not_called()

    def test_detach_instance_none(self, repository):
        """Test detaching None instance.

        :param repository: Repository instance
        :returns: None
        """
        mock_session = Mock()
        repository._detach_instance(mock_session, None)
        mock_session.expunge.assert_not_called()

    def test_create_entity_success(self, repository, sample_user):
        """Test successful entity creation.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        result = repository._create_entity(sample_user, "user 123456789")
        assert result is True

    def test_create_entity_integrity_error(self, repository, sample_user):
        """Test entity creation with integrity error.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        # Create user first time
        repository._create_entity(sample_user, "user 123456789")

        # Try to create duplicate
        duplicate_user = User(
            telegram_id=123456789,  # Same ID
            username="different",
            first_name="Different",
            last_name="User",
        )
        result = repository._create_entity(duplicate_user, "user 123456789")
        assert result is False

    def test_create_entity_general_error(self, repository):
        """Test entity creation with general error.

        :param repository: Repository instance
        :returns: None
        """
        with patch.object(repository, "session") as mock_session:
            mock_session.side_effect = Exception("Test error")

            result = repository._create_entity(Mock(), "test entity")
            assert result is False

    def test_get_entity_by_telegram_id_success(self, repository, sample_user):
        """Test successful entity retrieval by telegram_id.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        # Create user first
        repository._create_entity(sample_user, "user")

        # Get user
        result = repository._get_entity_by_telegram_id(User, 123456789, "user")
        assert result is not None
        assert result.telegram_id == 123456789
        assert result.username == "testuser"

    def test_get_entity_by_telegram_id_not_found(self, repository):
        """Test entity retrieval when not found.

        :param repository: Repository instance
        :returns: None
        """
        result = repository._get_entity_by_telegram_id(User, 999999, "user")
        assert result is None

    def test_get_entity_by_telegram_id_error(self, repository):
        """Test entity retrieval with error.

        :param repository: Repository instance
        :returns: None
        """
        with patch.object(repository, "session") as mock_session:
            mock_session.side_effect = Exception("Test error")

            result = repository._get_entity_by_telegram_id(User, 123456789, "user")
            assert result is None

    def test_delete_entity_by_telegram_id_success(self, repository, sample_user):
        """Test successful entity deletion by telegram_id.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        # Create user first
        repository._create_entity(sample_user, "user")

        # Delete user
        result = repository._delete_entity_by_telegram_id(User, 123456789, "user")
        assert result is True

    def test_delete_entity_by_telegram_id_not_found(self, repository):
        """Test entity deletion when not found.

        :param repository: Repository instance
        :returns: None
        """
        result = repository._delete_entity_by_telegram_id(User, 999999, "user")
        assert result is False

    def test_delete_entity_by_telegram_id_error(self, repository):
        """Test entity deletion with error.

        :param repository: Repository instance
        :returns: None
        """
        with patch.object(repository, "session") as mock_session:
            mock_session.side_effect = Exception("Test error")

            result = repository._delete_entity_by_telegram_id(User, 123456789, "user")
            assert result is False

    def test_get_all_entities_success(self, repository, sample_user):
        """Test successful retrieval of all entities.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        # Create multiple users
        user1 = sample_user
        user2 = User(
            telegram_id=987654321,
            username="testuser2",
            first_name="Test2",
            last_name="User2",
        )

        repository._create_entity(user1, "user1")
        repository._create_entity(user2, "user2")

        # Get all users
        results = repository._get_all_entities(User, "users")
        assert len(results) == 2
        telegram_ids = [user.telegram_id for user in results]
        assert 123456789 in telegram_ids
        assert 987654321 in telegram_ids

    def test_get_all_entities_empty(self, repository):
        """Test retrieval of all entities when none exist.

        :param repository: Repository instance
        :returns: None
        """
        results = repository._get_all_entities(User, "users")
        assert results == []

    def test_get_all_entities_error(self, repository):
        """Test retrieval of all entities with error.

        :param repository: Repository instance
        :returns: None
        """
        with patch.object(repository, "session") as mock_session:
            mock_session.side_effect = Exception("Test error")

            results = repository._get_all_entities(User, "users")
            assert results == []

    def test_get_all_entities_detach_instances(self, repository, sample_user):
        """Test that all entities are properly detached from session.

        :param repository: Repository instance
        :param sample_user: Sample user object
        :returns: None
        """
        repository._create_entity(sample_user, "user")

        with patch.object(repository, "_detach_instance") as mock_detach:
            results = repository._get_all_entities(User, "users")

            # Should be called once for each entity
            assert mock_detach.call_count == len(results)

    def test_session_expire_on_commit_false(self, repository):
        """Test that session is configured with expire_on_commit=False.

        :param repository: Repository instance
        :returns: None
        """
        # Check the session configuration
        assert repository.SessionLocal is not None
        session = repository.SessionLocal()
        try:
            assert session.expire_on_commit is False
        finally:
            session.close()

    def test_model_type_generic(self, repository):
        """Test that ModelType generic works correctly.

        :param repository: Repository instance
        :returns: None
        """
        from src.database.models.base import Base
        from src.database.repositories.sqlite.base_repository import ModelType

        # Test that ModelType is bound to Base
        assert ModelType.__bound__ == Base
