"""Test suite for abstract base repository.

Tests all functionality of the AbstractBaseRepository class
including abstract method definitions and interface compliance.
"""

from abc import ABC
from unittest.mock import Mock

import pytest

from src.database.repositories.abstract.base_repository import AbstractBaseRepository


class ConcreteRepository(AbstractBaseRepository):
    """Concrete implementation of AbstractBaseRepository for testing."""

    def __init__(self, db_path: str = "test.db"):
        """Initialize concrete repository.

        :param db_path: Path to database file
        """
        super().__init__(db_path)
        self.initialized = False
        self.closed = False

    def initialize(self) -> None:
        """Mock implementation of initialize.

        :returns: None
        """
        self.initialized = True

    def close(self) -> None:
        """Mock implementation of close.

        :returns: None
        """
        self.closed = True

    def session(self):
        """Mock implementation of session context manager.

        :yields: Mock session object
        """
        from contextlib import contextmanager

        @contextmanager
        def _session():
            mock_session = Mock()
            try:
                yield mock_session
            finally:
                pass

        return _session()

    def _detach_instance(self, session, instance) -> None:
        """Mock implementation of _detach_instance.

        :param session: Database session
        :param instance: Instance to detach
        :returns: None
        """
        pass


class TestAbstractBaseRepository:
    """Test class for AbstractBaseRepository."""

    def test_abstract_class_inheritance(self):
        """Test that AbstractBaseRepository inherits from ABC.

        :returns: None
        """
        assert issubclass(AbstractBaseRepository, ABC)

    def test_cannot_instantiate_abstract_class(self):
        """Test that AbstractBaseRepository cannot be instantiated directly.

        :returns: None
        """
        with pytest.raises(TypeError):
            AbstractBaseRepository("test.db")

    def test_concrete_implementation_initialization(self):
        """Test concrete implementation initialization.

        :returns: None
        """
        repo = ConcreteRepository("test_path.db")
        assert repo.db_path == "test_path.db"
        assert not repo.initialized
        assert not repo.closed

    def test_concrete_implementation_default_path(self):
        """Test concrete implementation with default path.

        :returns: None
        """
        repo = ConcreteRepository()
        assert repo.db_path == "test.db"

    def test_concrete_implementation_initialize(self):
        """Test concrete implementation initialize method.

        :returns: None
        """
        repo = ConcreteRepository("test.db")
        repo.initialize()
        assert repo.initialized

    def test_concrete_implementation_close(self):
        """Test concrete implementation close method.

        :returns: None
        """
        repo = ConcreteRepository("test.db")
        repo.close()
        assert repo.closed

    def test_concrete_implementation_session(self):
        """Test concrete implementation session context manager.

        :returns: None
        """
        repo = ConcreteRepository("test.db")
        with repo.session() as session:
            assert session is not None

    def test_concrete_implementation_detach_instance(self):
        """Test concrete implementation _detach_instance method.

        :returns: None
        """
        repo = ConcreteRepository("test.db")
        mock_session = Mock()
        mock_instance = Mock()

        # Should not raise any exception
        repo._detach_instance(mock_session, mock_instance)

    def test_abstract_methods_exist(self):
        """Test that all required abstract methods are defined.

        :returns: None
        """
        abstract_methods = AbstractBaseRepository.__abstractmethods__
        expected_methods = {"initialize", "close", "session", "_detach_instance"}
        assert abstract_methods == expected_methods

    def test_concrete_class_implements_all_methods(self):
        """Test that concrete class implements all abstract methods.

        :returns: None
        """
        repo = ConcreteRepository("test.db")

        # Check that all abstract methods are implemented
        assert hasattr(repo, "initialize")
        assert hasattr(repo, "close")
        assert hasattr(repo, "session")
        assert hasattr(repo, "_detach_instance")

        # Check that methods are callable
        assert callable(repo.initialize)
        assert callable(repo.close)
        assert callable(repo.session)
        assert callable(repo._detach_instance)

    def test_init_stores_db_path(self):
        """Test that __init__ properly stores db_path.

        :returns: None
        """
        test_path = "/custom/path/to/database.db"
        repo = ConcreteRepository(test_path)
        assert repo.db_path == test_path
