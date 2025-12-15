"""Unit tests for contract protocols coverage.

These tests verify that the protocol definitions are valid and importable,
ensure runtime checkability, and help achieve code coverage for protocol files.
"""

from unittest.mock import MagicMock

from src.bot.contracts.handler_protocol import HandlerProtocol
from src.contracts.user_repository_protocol import UserRepositoryProtocol
from src.contracts.user_service_protocol import UserServiceProtocol


class TestContractsCoverage:
    """Test suite for protocol coverage."""

    def test_user_repository_protocol_runtime_check(self):
        """Verify UserRepositoryProtocol runtime checkability."""
        # Create a mock that satisfies the protocol
        mock_repo = MagicMock(spec=UserRepositoryProtocol)

        # Verify it passes isinstance check (because of @runtime_checkable)
        assert isinstance(mock_repo, UserRepositoryProtocol)

    def test_user_service_protocol_runtime_check(self):
        """Verify UserServiceProtocol runtime checkability."""
        mock_service = MagicMock(spec=UserServiceProtocol)
        assert isinstance(mock_service, UserServiceProtocol)

    def test_handler_protocol_runtime_check(self):
        """Verify HandlerProtocol runtime checkability."""
        mock_handler = MagicMock(spec=HandlerProtocol)
        assert isinstance(mock_handler, HandlerProtocol)

    def test_handler_protocol_attributes(self):
        """Verify HandlerProtocol attributes exist on mock."""
        mock_handler = MagicMock(spec=HandlerProtocol)

        # Access properties to ensure spec allows them
        _ = mock_handler.command
        _ = mock_handler.callbacks
        _ = mock_handler.text_input
        _ = mock_handler.waiting_states

        # Verify handle method is callable
        assert callable(mock_handler.handle)

    def test_protocol_imports(self):
        """Verify all protocols can be imported and are classes."""
        assert isinstance(UserRepositoryProtocol, type)
        assert isinstance(UserServiceProtocol, type)
        assert isinstance(HandlerProtocol, type)
