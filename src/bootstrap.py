"""Application bootstrap and composition root.

This module provides the Composition Root pattern implementation for the
application. It is the single place where all dependencies are wired together.

The composition root should be called once at application startup to create
a fully configured DI container with all production dependencies registered.

Example usage:
    >>> from src.bootstrap import configure_container
    >>> container = configure_container()
    >>> user_service = container.get(UserServiceProtocol)
"""

from dataclasses import dataclass, field
from pathlib import Path

from .contracts import (
    UserServiceProtocol,
)
from .core.di import Container
from .database.service import UserService
from .services.container import ServiceContainer


@dataclass
class AppConfig:
    """Application configuration for dependency injection.

    This dataclass holds all configuration values needed for setting up
    the application's dependencies. It provides sensible defaults for
    development but should be configured explicitly for production.

    Attributes:
        database_path: Path to the SQLite database file
        bot_token: Telegram bot API token
        debug: Enable debug mode
    """

    database_path: Path = field(default_factory=lambda: Path("lifeweeks.db"))
    bot_token: str = ""
    debug: bool = False


def configure_container(config: AppConfig | None = None) -> Container:
    """Configure and return the dependency injection container.

    This is the Composition Root — the single place where all dependencies
    are wired together. It creates and configures the DI container with
    all production implementations.

    :param config: Application configuration, uses defaults if None
    :type config: AppConfig | None
    :returns: Configured DI container ready for use
    :rtype: Container

    Example:
        >>> config = AppConfig(database_path=Path("prod.db"))
        >>> container = configure_container(config=config)
        >>> user_service = container.get(UserServiceProtocol)
    """
    if config is None:
        config = AppConfig()

    container = Container()

    # Store config for services that need it
    container.register_singleton(
        protocol=AppConfig,
        instance=config,
    )

    # Register User Service as a lazy singleton
    # The service is created on first request and cached for subsequent requests
    # Note: UserService currently doesn't accept database_path in constructor,
    # but config is stored for future migrations
    container.register_lazy_singleton(
        protocol=UserServiceProtocol,
        factory=lambda: UserService(),
    )

    # Register legacy ServiceContainer for backward compatibility
    # This allows code using the old pattern to continue working
    container.register_lazy_singleton(
        protocol=ServiceContainer,
        factory=lambda: ServiceContainer(),
    )

    return container


def configure_test_container() -> Container:
    """Configure a container for testing with in-memory implementations.

    This function creates a container configured with test doubles
    that don't require external dependencies like databases or network.

    :returns: Container configured with test implementations
    :rtype: Container
    """
    # Import here to avoid circular imports and keep test deps separate
    from tests.fakes import FakeNotificationGateway, FakeUserService

    from .contracts import NotificationGatewayProtocol

    container = Container()

    # Register fake user service
    container.register_singleton(
        protocol=UserServiceProtocol,
        instance=FakeUserService(),
    )

    # Register fake notification gateway
    container.register_singleton(
        protocol=NotificationGatewayProtocol,
        instance=FakeNotificationGateway(),
    )

    return container
