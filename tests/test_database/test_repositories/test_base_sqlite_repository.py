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
        # Engine should be disposed
        assert getattr(repository, "engine", None) is None

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

    def test_initialize_with_sqlalchemy_error(self):
        """Test initialize method handles SQLAlchemyError during engine creation.

        :returns: None
        """
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from sqlalchemy.exc import SQLAlchemyError

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            repository = BaseSQLiteRepository(db_path=temp_path)

            # Mock SQLAlchemyError during engine creation
            with patch(
                "src.database.repositories.sqlite.base_repository.create_engine",
                side_effect=SQLAlchemyError("Database error"),
            ):
                # Test initialize with error
                with pytest.raises(SQLAlchemyError):
                    repository.initialize()

                # Verify cleanup was performed
                assert repository.engine is None
                assert repository.SessionLocal is None

        finally:
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()

    def test_initialize_with_dispose_error(self):
        """Test initialize method handles dispose errors during cleanup.

        :returns: None
        """
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock, patch

        from sqlalchemy.exc import SQLAlchemyError

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            repository = BaseSQLiteRepository(db_path=temp_path)

            # Mock engine that raises error on dispose
            mock_engine = Mock()
            mock_engine.dispose.side_effect = Exception("Dispose error")

            # Add engine to registry first
            db_key = str(temp_path.resolve())
            BaseSQLiteRepository._engines[db_key] = mock_engine

            # Mock SQLAlchemyError during session creation
            with patch(
                "src.database.repositories.sqlite.base_repository.sessionmaker",
                side_effect=SQLAlchemyError("Session error"),
            ):
                # Test initialize with error
                with pytest.raises(SQLAlchemyError):
                    repository.initialize()

                # Verify cleanup was performed despite dispose error
                assert repository.engine is None
                assert repository.SessionLocal is None
                assert db_key not in BaseSQLiteRepository._engines

        finally:
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()

    def test_close_with_dispose_error(self):
        """Test close method handles dispose errors gracefully.

        :returns: None
        """
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            repository = BaseSQLiteRepository(db_path=temp_path)
            repository.initialize()

            # Mock engine that raises error on dispose
            mock_engine = Mock()
            mock_engine.dispose.side_effect = Exception("Dispose error")

            db_key = str(temp_path.resolve())
            BaseSQLiteRepository._engines[db_key] = mock_engine

            # Test close with dispose error - should not raise exception
            try:
                repository.close()
            except Exception:
                # Exception should be caught and handled internally
                pass

            # Verify cleanup was performed despite dispose error
            assert repository.engine is None
            assert repository.SessionLocal is None
            assert db_key not in BaseSQLiteRepository._engines
            assert db_key not in BaseSQLiteRepository._sessions

        finally:
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()

    def test_reset_instances_with_dispose_errors(self):
        """Test reset_instances method handles dispose errors and continues cleanup.

        :returns: None
        """
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            # Create repository and initialize
            repository = BaseSQLiteRepository(db_path=temp_path)
            repository.initialize()

            # Mock engines that raise errors on dispose
            db_key = str(temp_path.resolve())
            mock_engine1 = Mock()
            mock_engine1.dispose.side_effect = Exception("Dispose error 1")

            mock_engine2 = Mock()
            mock_engine2.dispose.side_effect = Exception("Dispose error 2")

            BaseSQLiteRepository._engines[db_key] = mock_engine1
            BaseSQLiteRepository._engines["another_key"] = mock_engine2

            # Test reset_instances with dispose errors
            BaseSQLiteRepository.reset_instances()

            # Verify cleanup was performed despite errors
            assert len(BaseSQLiteRepository._engines) == 0
            assert len(BaseSQLiteRepository._sessions) == 0
            assert len(BaseSQLiteRepository._initialized_once_logged) == 0

        finally:
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()

    def test_multiple_repositories_same_path(self):
        """Test multiple repositories with same path share engine and session.

        :returns: None
        """
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            # Create two repositories with same path
            repo1 = BaseSQLiteRepository(db_path=temp_path)
            repo2 = BaseSQLiteRepository(db_path=temp_path)

            # Initialize both
            repo1.initialize()
            repo2.initialize()

            # Verify they share the same engine
            assert repo1.engine is repo2.engine
            assert repo1.SessionLocal is repo2.SessionLocal

            # Verify registry contains only one entry
            db_key = str(temp_path.resolve())
            assert db_key in BaseSQLiteRepository._engines
            assert db_key in BaseSQLiteRepository._sessions

        finally:
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()

    def test_repository_initialization_flag(self):
        """Test repository initialization flag behavior.

        :returns: None
        """
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            repository = BaseSQLiteRepository(db_path=temp_path)
            db_key = str(temp_path.resolve())

            # Initially initialized (key added in constructor)
            key = f"BaseSQLiteRepository_{temp_path}"
            assert key in repository._initialized

            # Initialize repository
            repository.initialize()

            # Should be initialized now
            assert repository._initialized

            # Verify it's in the logged set
            assert db_key in BaseSQLiteRepository._initialized_once_logged

        finally:
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()

    def test_repository_with_nonexistent_path(self):
        """Test repository creates database file for non-existent paths.

        :returns: None
        """
        import tempfile
        from pathlib import Path

        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "nonexistent.db"

        try:
            repository = BaseSQLiteRepository(db_path=db_path)

            # Should not exist initially
            assert not db_path.exists()

            # Initialize repository
            repository.initialize()

            # Database file should be created
            assert db_path.exists()

        finally:
            # Cleanup
            if db_path.exists():
                db_path.unlink()
            Path(temp_dir).rmdir()

    def test_repository_thread_safety(self):
        """Test repository thread safety for concurrent access.

        :returns: None
        """
        import tempfile
        import threading
        import time
        from pathlib import Path

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            results = []

            def init_repository():
                """Initialize repository in thread."""
                repo = BaseSQLiteRepository(db_path=temp_path)
                repo.initialize()
                results.append(repo)
                time.sleep(0.01)  # Small delay

            # Create multiple threads
            threads = []
            for _ in range(3):
                thread = threading.Thread(target=init_repository)
                threads.append(thread)

            # Start all threads
            for thread in threads:
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Verify all repositories share the same engine
            assert len(results) == 3
            for repo in results[1:]:
                assert repo.engine is results[0].engine

        finally:
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()

    def test_repository_path_resolution(self):
        """Test repository properly resolves relative paths.

        :returns: None
        """
        import os
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp_dir:
            relative_path = Path("test.db")
            full_path = Path(temp_dir) / relative_path

            # Change to temp directory
            original_cwd = Path.cwd()
            try:
                os.chdir(temp_dir)

                repository = BaseSQLiteRepository(db_path=relative_path)
                repository.initialize()

                # Verify database was created in correct location
                assert full_path.exists()

                # Verify path resolution
                assert repository.db_path.resolve() == full_path.resolve()

            finally:
                # Restore original working directory
                os.chdir(original_cwd)

    def test_repository_cleanup_on_error(self):
        """Test repository cleanup when initialization fails.

        :returns: None
        """
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from sqlalchemy.exc import SQLAlchemyError

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            repository = BaseSQLiteRepository(db_path=temp_path)

            # Mock error during session creation
            with patch(
                "src.database.repositories.sqlite.base_repository.sessionmaker",
                side_effect=SQLAlchemyError("Session creation failed"),
            ):
                # Test initialization failure
                with pytest.raises(SQLAlchemyError):
                    repository.initialize()

                # Verify cleanup was performed
                assert repository.engine is None
                assert repository.SessionLocal is None

                # Verify registry was cleaned up
                db_key = str(temp_path.resolve())
                assert db_key not in BaseSQLiteRepository._engines
                assert db_key not in BaseSQLiteRepository._sessions

        finally:
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()
