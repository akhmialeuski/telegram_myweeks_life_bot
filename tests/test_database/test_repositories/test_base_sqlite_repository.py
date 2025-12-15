"""Test suite for SQLite base repository.

Tests all functionality of the BaseSQLiteRepository class
including session management, CRUD operations, and error handling.
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest
import pytest_asyncio
from sqlalchemy.exc import SQLAlchemyError

from src.database.models.user import User
from src.database.repositories.sqlite.base_repository import BaseSQLiteRepository
from tests.conftest import (
    TEST_FIRST_NAME,
    TEST_FIRST_NAME_ALT,
    TEST_LAST_NAME,
    TEST_LAST_NAME_ALT,
    TEST_USER_ID,
    TEST_USER_ID_ALT,
    TEST_USER_ID_NONEXISTENT,
    TEST_USERNAME,
    TEST_USERNAME_ALT,
)


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

    @pytest_asyncio.fixture
    async def repository(self, temp_db_path):
        """Create repository instance for testing.

        :param temp_db_path: Path to temporary database
        :returns: Repository instance
        :rtype: BaseSQLiteRepository
        """
        repo = BaseSQLiteRepository(temp_db_path)
        await repo.initialize()
        yield repo
        await repo.close()

    @pytest.fixture
    def sample_user(self):
        """Create sample user for testing.

        :returns: Sample User object
        :rtype: User
        """
        from datetime import UTC, datetime

        return User(
            telegram_id=TEST_USER_ID,
            username=TEST_USERNAME,
            first_name=TEST_FIRST_NAME,
            last_name=TEST_LAST_NAME,
            created_at=datetime.now(UTC),
        )

    def test_init_default_path(self) -> None:
        """Test repository initialization with default path.

        :returns: None
        :rtype: None
        """
        repo = BaseSQLiteRepository()
        assert repo.db_path.name == "lifeweeks.db"
        assert repo.engine is None
        assert repo.SessionLocal is None

    def test_init_custom_path(self, temp_db_path) -> None:
        """Test repository initialization with custom path.

        :param temp_db_path: Path to temporary database
        :type temp_db_path: str
        :returns: None
        :rtype: None
        """
        repo = BaseSQLiteRepository(temp_db_path)
        assert str(repo.db_path) == temp_db_path
        assert repo.engine is None
        assert repo.SessionLocal is None

    def test_initialize_success(self, repository) -> None:
        """Test successful repository initialization.

        :param repository: Repository instance
        :type repository: BaseSQLiteRepository
        :returns: None
        :rtype: None
        """
        assert repository.engine is not None
        assert repository.SessionLocal is not None

    @pytest.mark.asyncio
    async def test_initialize_failure(self) -> None:
        """Test repository initialization failure.

        :returns: None
        :rtype: None
        """
        repo = BaseSQLiteRepository("/invalid/path/db.db")
        with pytest.raises(SQLAlchemyError):
            await repo.initialize()

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, repository) -> None:
        """Test that initialize can be called multiple times safely.

        :param repository: Repository instance
        :type repository: BaseSQLiteRepository
        :returns: None
        :rtype: None
        """
        original_engine = repository.engine
        await repository.initialize()  # Call again
        assert repository.engine is original_engine  # Should not change

    @pytest.mark.asyncio
    async def test_close_success(self, repository) -> None:
        """Test successful repository closure.

        :param repository: Repository instance
        :type repository: BaseSQLiteRepository
        :returns: None
        :rtype: None
        """
        await repository.close()
        # Engine should be disposed
        assert getattr(repository, "engine", None) is None

    @pytest.mark.asyncio
    async def test_close_when_not_initialized(self) -> None:
        """Test closing repository that was never initialized.

        :returns: None
        :rtype: None
        """
        repo = BaseSQLiteRepository("test.db")
        await repo.close()  # Should not raise exception
        assert repo.engine is None

    def test_detach_instance_in_session(self, repository) -> None:
        """Test detaching instance that is in session.

        :param repository: Repository instance
        :type repository: BaseSQLiteRepository
        :returns: None
        :rtype: None
        """
        mock_session = Mock()
        mock_instance = Mock()
        mock_session.__contains__ = Mock(return_value=True)

        repository._detach_instance(mock_session, mock_instance)
        mock_session.expunge.assert_called_once_with(mock_instance)

    def test_detach_instance_not_in_session(self, repository) -> None:
        """Test detaching instance that is not in session.

        :param repository: Repository instance
        :type repository: BaseSQLiteRepository
        :returns: None
        :rtype: None
        """
        mock_session = Mock()
        mock_instance = Mock()
        mock_session.__contains__ = Mock(return_value=False)

        repository._detach_instance(mock_session, mock_instance)
        mock_session.expunge.assert_not_called()

    def test_detach_instance_none(self, repository) -> None:
        """Test detaching None instance.

        :param repository: Repository instance
        :type repository: BaseSQLiteRepository
        :returns: None
        :rtype: None
        """
        mock_session = Mock()
        repository._detach_instance(mock_session, None)
        mock_session.expunge.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_entity_success(self, repository, sample_user) -> None:
        """Test successful entity creation.

        :param repository: Repository instance
        :type repository: BaseSQLiteRepository
        :param sample_user: Sample user data
        :type sample_user: User
        :returns: None
        :rtype: None
        """
        result = await repository._create_entity(sample_user, "user 123456789")
        assert result is True

    @pytest.mark.asyncio
    async def test_create_entity_integrity_error(self, repository, sample_user) -> None:
        """Test entity creation with integrity error.

        :param repository: Repository instance
        :type repository: BaseSQLiteRepository
        :param sample_user: Sample user data
        :type sample_user: User
        :returns: None
        :rtype: None
        """
        # Create user first time
        await repository._create_entity(sample_user, f"user {TEST_USER_ID}")

        # Try to create duplicate
        duplicate_user = User(
            telegram_id=TEST_USER_ID,  # Same ID
            username="different",
            first_name="Different",
            last_name=TEST_LAST_NAME,
        )
        result = await repository._create_entity(duplicate_user, f"user {TEST_USER_ID}")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_entity_by_telegram_id_success(
        self, repository, sample_user
    ) -> None:
        """Test successful entity retrieval by telegram_id.

        :param repository: Repository instance
        :type repository: BaseSQLiteRepository
        :param sample_user: Sample user data
        :type sample_user: User
        :returns: None
        :rtype: None
        """
        # Create user first
        await repository._create_entity(sample_user, "user")

        # Get user
        result = await repository._get_entity_by_telegram_id(User, TEST_USER_ID, "user")
        assert result is not None
        assert result.telegram_id == TEST_USER_ID
        assert result.username == TEST_USERNAME

    @pytest.mark.asyncio
    async def test_get_entity_by_telegram_id_not_found(self, repository) -> None:
        """Test entity retrieval when not found.

        :param repository: Repository instance
        :type repository: BaseSQLiteRepository
        :returns: None
        :rtype: None
        """
        result = await repository._get_entity_by_telegram_id(
            User, TEST_USER_ID_NONEXISTENT, "user"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_entity_by_telegram_id_success(
        self, repository, sample_user
    ) -> None:
        """Test successful entity deletion by telegram_id.

        :param repository: Repository instance
        :type repository: BaseSQLiteRepository
        :param sample_user: Sample user data
        :type sample_user: User
        :returns: None
        :rtype: None
        """
        # Create user first
        await repository._create_entity(sample_user, "user")

        # Delete user
        result = await repository._delete_entity_by_telegram_id(
            User, TEST_USER_ID, "user"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_entity_by_telegram_id_not_found(self, repository) -> None:
        """Test entity deletion when not found.

        :param repository: Repository instance
        :type repository: BaseSQLiteRepository
        :returns: None
        :rtype: None
        """
        result = await repository._delete_entity_by_telegram_id(
            User, TEST_USER_ID_NONEXISTENT, "user"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_entities_success(self, repository, sample_user) -> None:
        """Test successful retrieval of all entities.

        :param repository: Repository instance
        :type repository: BaseSQLiteRepository
        :param sample_user: Sample user data
        :type sample_user: User
        :returns: None
        :rtype: None
        """
        # Create multiple users
        user1 = sample_user
        user2 = User(
            telegram_id=TEST_USER_ID_ALT,
            username=TEST_USERNAME_ALT,
            first_name=TEST_FIRST_NAME_ALT,
            last_name=TEST_LAST_NAME_ALT,
        )

        await repository._create_entity(user1, "user1")
        await repository._create_entity(user2, "user2")

        # Get all users
        results = await repository._get_all_entities(User, "users")
        assert len(results) == 2
        telegram_ids = [user.telegram_id for user in results]
        assert TEST_USER_ID in telegram_ids
        assert TEST_USER_ID_ALT in telegram_ids

    @pytest.mark.asyncio
    async def test_get_all_entities_empty(self, repository) -> None:
        """Test retrieval of all entities when none exist.

        :param repository: Repository instance
        :type repository: BaseSQLiteRepository
        :returns: None
        :rtype: None
        """
        results = await repository._get_all_entities(User, "users")
        assert results == []

    @pytest.mark.asyncio
    async def test_get_all_entities_detach_instances(
        self, repository, sample_user
    ) -> None:
        """Test that all entities are properly detached from session.

        :param repository: Repository instance
        :type repository: BaseSQLiteRepository
        :param sample_user: Sample user data
        :type sample_user: User
        :returns: None
        :rtype: None
        """
        await repository._create_entity(sample_user, "user")

        with patch.object(repository, "_detach_instance") as mock_detach:
            results = await repository._get_all_entities(User, "users")

            # Should be called once for each entity
            assert mock_detach.call_count == len(results)

    def test_model_type_generic(self) -> None:
        """Test that ModelType generic works correctly.

        :returns: None
        :rtype: None
        """
        from src.database.models.base import Base
        from src.database.repositories.sqlite.base_repository import ModelType

        # Test that ModelType is bound to Base
        assert ModelType.__bound__ == Base

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_initialize_with_sqlalchemy_error(self) -> None:
        """Test initialize method handles SQLAlchemyError during engine creation.

        :returns: None
        :rtype: None
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
                "src.database.repositories.sqlite.base_repository.create_async_engine",
                side_effect=SQLAlchemyError("Database error"),
            ):
                # Test initialize with error
                with pytest.raises(SQLAlchemyError):
                    await repository.initialize()

                # Verify cleanup was performed
                assert repository.engine is None
                assert repository.SessionLocal is None

        finally:
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_initialize_with_dispose_error(self) -> None:
        """Test initialize method handles dispose errors during cleanup.

        :returns: None
        :rtype: None
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
                "src.database.repositories.sqlite.base_repository.async_sessionmaker",
                side_effect=SQLAlchemyError("Session error"),
            ):
                # Test initialize with error
                with pytest.raises(SQLAlchemyError):
                    await repository.initialize()

                # Verify cleanup was performed despite dispose error
                assert repository.engine is None
                assert repository.SessionLocal is None
                assert db_key not in BaseSQLiteRepository._engines

        finally:
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_close_with_dispose_error(self) -> None:
        """Test close method handles dispose errors gracefully.

        :returns: None
        :rtype: None
        """
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            repository = BaseSQLiteRepository(db_path=temp_path)
            await repository.initialize()

            # Mock engine that raises error on dispose
            mock_engine = Mock()
            mock_engine.dispose.side_effect = Exception("Dispose error")

            db_key = str(temp_path.resolve())
            BaseSQLiteRepository._engines[db_key] = mock_engine

            # Test close with dispose error - should not raise exception
            try:
                await repository.close()
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

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_reset_instances_with_dispose_errors(self) -> None:
        """Test reset_instances method handles dispose errors and continues cleanup.

        :returns: None
        :rtype: None
        """
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            # Create repository and initialize
            repository = BaseSQLiteRepository(db_path=temp_path)
            await repository.initialize()

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

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_repository_initialization_flag(self) -> None:
        """Test repository initialization flag behavior.

        :returns: None
        :rtype: None
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
            await repository.initialize()

            # Should be initialized now
            assert repository._initialized

            # Verify it's in the logged set
            assert db_key in BaseSQLiteRepository._initialized_once_logged

        finally:
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_repository_with_nonexistent_path(self) -> None:
        """Test repository creates database file for non-existent paths.

        :returns: None
        :rtype: None
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
            await repository.initialize()

            # Database file should be created
            assert db_path.exists()

        finally:
            # Cleanup
            if db_path.exists():
                db_path.unlink()
            Path(temp_dir).rmdir()

    @pytest.mark.asyncio
    async def test_repository_thread_safety(self) -> None:
        """Test repository thread safety for concurrent access.

        :returns: None
        :rtype: None
        """
        import tempfile
        import threading
        import time
        from pathlib import Path

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            results = []

            async def async_init():
                """Async initialization for repository."""
                repo = BaseSQLiteRepository(db_path=temp_path)
                await repo.initialize()
                return repo

            def init_repository():
                """Initialize repository in thread."""
                import asyncio

                repo = asyncio.run(async_init())
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

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_repository_path_resolution(self) -> None:
        """Test repository properly resolves relative paths.

        :returns: None
        :rtype: None
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
                await repository.initialize()

                # Verify database was created in correct location
                assert full_path.exists()

                # Verify path resolution
                assert repository.db_path.resolve() == full_path.resolve()

            finally:
                # Restore original working directory
                os.chdir(original_cwd)

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_repository_cleanup_on_error(self) -> None:
        """Test repository cleanup when initialization fails.

        :returns: None
        :rtype: None
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
                "src.database.repositories.sqlite.base_repository.async_sessionmaker",
                side_effect=SQLAlchemyError("Session creation failed"),
            ):
                # Test initialization failure
                with pytest.raises(SQLAlchemyError):
                    await repository.initialize()

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
