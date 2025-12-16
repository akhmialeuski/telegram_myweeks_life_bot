"""Unit tests for application bootstrap.

Tests the configuration of the DI container and application setup.
"""

from pathlib import Path
from unittest.mock import patch

from src.bootstrap import (
    AppConfig,
    configure_container,
    configure_test_container,
)
from src.contracts import (
    NotificationGatewayProtocol,
    UserServiceProtocol,
)
from src.core.di import Container
from src.services.container import ServiceContainer


class TestBootstrap:
    """Test suite for application bootstrap functions."""

    def test_app_config_defaults(self):
        """Test AppConfig default values."""
        config = AppConfig()
        assert config.database_path == Path("lifeweeks.db")
        assert config.bot_token == ""
        assert config.debug is False

    def test_configure_container_defaults(self):
        """Test container configuration with default settings."""
        container = configure_container()

        # Verify container type
        assert isinstance(container, Container)

        # Verify AppConfig registration
        config = container.get(AppConfig)
        assert isinstance(config, AppConfig)
        assert config.database_path == Path("lifeweeks.db")

        # Verify ServiceContainer registration (legacy)
        service_container = container.get(ServiceContainer)
        assert isinstance(service_container, ServiceContainer)

    def test_configure_container_custom_config(self):
        """Test container configuration with custom settings."""
        custom_config = AppConfig(
            database_path=Path("custom.db"), bot_token="test_token", debug=True
        )
        container = configure_container(config=custom_config)

        config = container.get(AppConfig)
        assert config.database_path == Path("custom.db")
        assert config.bot_token == "test_token"
        assert config.debug is True

    @patch("src.bootstrap.UserService")
    def test_configure_container_user_service_factory(self, mock_user_service):
        """Test lazy loading of UserService."""
        container = configure_container()

        # Should be lazy, mock not called yet
        mock_user_service.assert_not_called()

        # Request service
        service = container.get(UserServiceProtocol)

        # Now mock called
        mock_user_service.assert_called_once()
        assert service == mock_user_service.return_value

    @patch("src.bootstrap.ServiceContainer")
    def test_configure_container_legacy_container_factory(self, mock_service_container):
        """Test lazy loading of legacy ServiceContainer."""
        container = configure_container()

        # Should be lazy
        mock_service_container.assert_not_called()

        # Request service
        # Since we patched ServiceContainer in src.bootstrap, the container used that mock as the key
        service = container.get(mock_service_container)

        # Now mock called
        mock_service_container.assert_called_once()
        assert service == mock_service_container.return_value

    def test_configure_test_container(self):
        """Test test container configuration."""
        container = configure_test_container()

        # Verify fakes are registered
        user_service = container.get(UserServiceProtocol)
        # Check if it's the fake one (checking class name as simple verification)
        assert user_service.__class__.__name__ == "FakeUserService"

        gateway = container.get(NotificationGatewayProtocol)
        assert gateway.__class__.__name__ == "FakeNotificationGateway"
