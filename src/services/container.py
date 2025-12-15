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
from ..core.life_calculator import LifeCalculatorEngine
from ..database.service import DatabaseManager, UserService
from ..events.event_bus import EventBus
from ..scheduler.client import SchedulerClient
from ..utils.config import TOKEN
from .notification_service import NotificationService


class ServiceContainer:
    """Centralized container for all application services and dependencies.

    This class manages the creation and lifecycle of all application services,
    providing a single point of configuration and dependency management.
    It implements the Dependency Injection pattern to reduce coupling between
    modules and simplify testing.

    Attributes:
        config: Application configuration object
        user_service: User management service
        life_calculator: Life statistics calculator
        localization_service: Message localization service
        event_bus: Event bus for domain events
        notification_service: Notification generation service
        notification_gateway: Notification delivery gateway
        scheduler_client: Client for communicating with scheduler worker
    """

    _instance = None
    _initialized = False
    _lock = threading.Lock()

    def __new__(cls):
        """Create singleton instance of ServiceContainer.

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

    def __init__(self) -> None:
        """Initialize the service container with all dependencies.

        Creates instances of all services and utilities. This centralizes
        dependency creation and makes it easy to swap implementations
        for testing or different environments.

        :returns: None
        """
        if self._initialized:
            return

        # Initialize database services
        self.user_service = UserService()

        # Initialize life calculator
        self.life_calculator = LifeCalculatorEngine

        # Initialize event bus
        self.event_bus = EventBus()

        # Initialize notification gateway
        # In a real app, we might want to lazy-load this or allow swapping for testing
        self.notification_gateway = TelegramNotificationGateway(bot=Bot(token=TOKEN))

        # Initialize notification service
        self.notification_service = NotificationService(
            user_service=self.user_service,
            life_calculator_class=self.life_calculator,
        )

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

    def get_life_calculator(self) -> type[LifeCalculatorEngine]:
        """Get the life calculator class.

        :returns: Life calculator class
        :rtype: type[LifeCalculatorEngine]
        """
        return self.life_calculator

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
