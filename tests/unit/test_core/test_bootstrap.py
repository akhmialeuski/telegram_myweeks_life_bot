"""Unit tests for bootstrap module.

Tests the composition root functionality including container configuration
and service registration.
"""

from pathlib import Path

from src.bootstrap import AppConfig, configure_container
from src.contracts import UserServiceProtocol
from src.services.container import ServiceContainer


class TestAppConfig:
    """Test suite for AppConfig dataclass."""

    def test_default_values(self) -> None:
        """Test that AppConfig has sensible defaults.

        This test verifies that the dataclass provides
        working defaults for all configuration values.
        """
        config = AppConfig()

        assert config.database_path.name == "lifeweeks.db"
        assert config.bot_token == ""
        assert config.debug is False

    def test_custom_values(self) -> None:
        """Test that AppConfig accepts custom values.

        This test verifies that custom configuration values
        are properly stored.
        """
        config = AppConfig(
            database_path=Path("custom.db"),
            bot_token="test_token",
            debug=True,
        )

        assert config.database_path.name == "custom.db"
        assert config.bot_token == "test_token"
        assert config.debug is True


class TestConfigureContainer:
    """Test suite for configure_container function."""

    def test_returns_container(self) -> None:
        """Test that configure_container returns a Container.

        This test verifies that the function creates and returns
        a properly typed Container instance.
        """
        from src.core.di import Container

        container = configure_container()

        assert isinstance(container, Container)

    def test_registers_user_service_protocol(self) -> None:
        """Test that UserServiceProtocol is registered.

        This test verifies that the composition root properly
        registers the UserServiceProtocol.
        """
        container = configure_container()

        assert container.is_registered(protocol=UserServiceProtocol) is True

    def test_user_service_is_lazy_singleton(self) -> None:
        """Test that UserService is a lazy singleton.

        This test verifies that resolving UserServiceProtocol
        multiple times returns the same instance.
        """
        container = configure_container()

        service1 = container.get(protocol=UserServiceProtocol)
        service2 = container.get(protocol=UserServiceProtocol)

        assert service1 is service2

    def test_registers_service_container_for_backward_compatibility(self) -> None:
        """Test that ServiceContainer is registered for legacy code.

        This test verifies that the composition root registers
        ServiceContainer to support backward compatibility.
        """
        container = configure_container()

        assert container.is_registered(protocol=ServiceContainer) is True

    def test_registers_app_config(self) -> None:
        """Test that AppConfig is registered in the container.

        This test verifies that custom configuration is stored
        in the container and can be resolved by services.
        """
        config = AppConfig(
            database_path=Path("custom.db"),
            debug=True,
        )

        container = configure_container(config=config)

        resolved_config = container.get(protocol=AppConfig)
        assert resolved_config is config
        assert resolved_config.debug is True

    def test_accepts_custom_config(self) -> None:
        """Test that configure_container accepts custom config.

        This test verifies that custom configuration is properly
        passed to the container configuration.
        """
        config = AppConfig(
            database_path=Path("custom.db"),
            debug=True,
        )

        # Should not raise
        container = configure_container(config=config)

        assert container is not None
