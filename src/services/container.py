"""Service container for dependency injection.

This module provides a centralized container for managing all application
dependencies, including database services, schedulers, and utilities.
It implements the Dependency Injection pattern to reduce coupling between
modules and simplify testing.
"""

import threading
from typing import Optional

from telegram import Bot

from ..bot.gateways.telegram_gateway import TelegramNotificationGateway
from ..contracts.notification_gateway_protocol import NotificationGatewayProtocol
from ..database.service import DatabaseManager, UserService
from ..events.event_bus import EventBus
from ..scheduler.client import SchedulerClient
from ..utils.config import TOKEN
from .i18n_adapter import BabelI18nAdapter
from .notification_service import NotificationService


class ServiceContainer:
    """Centralized container for all application services and dependencies.

    This class manages the creation and lifecycle of all application services,
    providing a single point of configuration and dependency management.
    It implements the Dependency Injection pattern to reduce coupling between
    modules and simplify testing.

    :param db_path: Optional path to SQLite database file for testing
    :type db_path: str | None
    :param skip_telegram: If True, skip Telegram gateway initialization (for testing)
    :type skip_telegram: bool

    Attributes:
        config: Application configuration object
        user_service: User management service
        localization_service: Message localization service
        event_bus: Event bus for domain events
        notification_service: Notification generation service
        notification_gateway: Notification delivery gateway
        scheduler_client: Client for communicating with scheduler worker
    """

    _instance = None
    _initialized = False
    _lock = threading.Lock()

    def __new__(
        cls,
        db_path: str | None = None,
        skip_telegram: bool = False,
    ) -> "ServiceContainer":
        """Create singleton instance of ServiceContainer.

        :param db_path: Optional path to SQLite database file
        :type db_path: str | None
        :param skip_telegram: If True, skip Telegram gateway initialization
        :type skip_telegram: bool
        :returns: ServiceContainer instance
        :rtype: ServiceContainer
        """
        # Double-checked locking to ensure thread-safe singleton
        instance = cls._instance
        if instance is None:
            with cls._lock:
                instance = cls._instance
                if instance is None:
                    instance = super().__new__(cls)
                    cls._instance = instance
        return instance

    def __init__(
        self,
        db_path: str | None = None,
        skip_telegram: bool = False,
    ) -> None:
        """Initialize the service container with all dependencies.

        Creates instances of all services and utilities. This centralizes
        dependency creation and makes it easy to swap implementations
        for testing or different environments.

        :param db_path: Optional path to SQLite database file for testing
        :type db_path: str | None
        :param skip_telegram: If True, skip Telegram gateway initialization
        :type skip_telegram: bool
        :returns: None
        """
        if self._initialized:
            return

        # Store configuration
        self._db_path = db_path
        self._skip_telegram = skip_telegram

        # Initialize database services with custom db_path if provided
        if db_path:
            db_manager = DatabaseManager(db_path=db_path)
            self.user_service = UserService(
                user_repository=db_manager.user_repository,
                settings_repository=db_manager.settings_repository,
                subscription_repository=db_manager.subscription_repository,
            )
        else:
            self.user_service = UserService()

        # Initialize event bus
        self.event_bus = EventBus()

        # Initialize notification gateway (skip for testing)
        if skip_telegram:
            self.notification_gateway: NotificationGatewayProtocol | None = None
        else:
            self.notification_gateway = TelegramNotificationGateway(
                bot=Bot(token=TOKEN)
            )

        # Initialize notification service
        self.notification_service = NotificationService(
            user_service=self.user_service,
        )

        # Initialize localization service with default language
        self.localization_service = BabelI18nAdapter(lang="en")

        # Scheduler client (initialized externally)
        self.scheduler_client: Optional[SchedulerClient] = None

        # Initialize services that depend on other services
        self._initialize_service_dependencies()

        self._initialized = True

    def _initialize_service_dependencies(self) -> None:
        """Initialize services that depend on other services.

        This method sets up any cross-service dependencies after all
        basic services have been created.

        :returns: None
        """
        # Dependencies that don't require async initialization can be set here
        pass

    async def initialize(self) -> None:
        """Initialize all async services.

        This method must be called within an async context (e.g., bot startup).

        :returns: None
        :rtype: None
        """
        # Initialize user service (database connections)
        if hasattr(self.user_service, "initialize"):
            await self.user_service.initialize()

    def get_user_service(self) -> UserService:
        """Get the user service instance.

        :returns: User service instance
        :rtype: UserService
        """
        return self.user_service

    def get_event_bus(self) -> EventBus:
        """Get the event bus instance.

        :returns: Event bus instance
        :rtype: EventBus
        """
        return self.event_bus

    def get_notification_service(self) -> NotificationService:
        """Get the notification service instance.

        :returns: Notification service instance
        :rtype: NotificationService
        """
        return self.notification_service

    def get_notification_gateway(self) -> NotificationGatewayProtocol:
        """Get the notification gateway instance.

        :returns: Notification gateway instance
        :rtype: NotificationGatewayProtocol
        """
        return self.notification_gateway

    def set_scheduler_client(self, client: SchedulerClient) -> None:
        """Set the scheduler client instance.

        :param client: Scheduler client instance
        :type client: SchedulerClient
        :returns: None
        """
        self.scheduler_client = client

    def get_scheduler_client(self) -> Optional[SchedulerClient]:
        """Get the scheduler client instance.

        :returns: Scheduler client instance or None
        :rtype: Optional[SchedulerClient]
        """
        return self.scheduler_client

    async def cleanup(self) -> None:
        """Cleanup resources and close connections.

        This method should be called when shutting down the application
        to properly close database connections and cleanup resources.

        :returns: None
        """
        await DatabaseManager().close()

    @classmethod
    async def reset_instance(cls) -> None:
        """Reset the singleton instance (mainly for testing).

        :returns: None
        """
        with cls._lock:
            if cls._instance:
                await cls._instance.cleanup()
            cls._instance = None
            cls._initialized = False
            DatabaseManager.reset_instance()

    @classmethod
    def create_for_testing(
        cls,
        db_path: str,
    ) -> "ServiceContainer":
        """Create a new ServiceContainer instance for testing (bypasses singleton).

        This factory method creates a fresh ServiceContainer instance that
        is not stored as the singleton. Use this for integration tests
        that need isolated database connections.

        :param db_path: Path to test SQLite database file
        :type db_path: str
        :returns: New ServiceContainer instance configured for testing
        :rtype: ServiceContainer
        """
        # Create a new instance directly, bypassing singleton
        instance = object.__new__(cls)

        # Initialize with test configuration
        instance._db_path = db_path
        instance._skip_telegram = True

        # Initialize database services with test db_path
        db_manager = DatabaseManager(db_path=db_path)
        instance.user_service = UserService(
            user_repository=db_manager.user_repository,
            settings_repository=db_manager.settings_repository,
            subscription_repository=db_manager.subscription_repository,
        )

        # Initialize event bus
        instance.event_bus = EventBus()

        # Skip notification gateway for testing
        instance.notification_gateway = None

        # Initialize notification service
        instance.notification_service = NotificationService(
            user_service=instance.user_service,
        )

        # Initialize localization service
        instance.localization_service = BabelI18nAdapter(lang="en")

        # No scheduler client for testing
        instance.scheduler_client = None

        return instance
