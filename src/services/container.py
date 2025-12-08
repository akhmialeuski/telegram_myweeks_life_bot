"""Service container for dependency injection.

This module provides a centralized container for managing all application
dependencies, including database services, schedulers, and utilities.
It implements the Dependency Injection pattern to reduce coupling between
modules and simplify testing.
"""

import threading

from ..core.life_calculator import LifeCalculatorEngine
from ..database.service import DatabaseManager, UserService


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

        # Initialize services that depend on other services
        self._initialize_service_dependencies()

        self._initialized = True

    def _initialize_service_dependencies(self) -> None:
        """Initialize services that depend on other services.

        This method sets up any cross-service dependencies after all
        basic services have been created.

        :returns: None
        """
        # Initialize user service if it has dependencies
        if hasattr(self.user_service, "initialize"):
            self.user_service.initialize()

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

    def cleanup(self) -> None:
        """Cleanup resources and close connections.

        This method should be called when shutting down the application
        to properly close database connections and cleanup resources.

        :returns: None
        """
        DatabaseManager().close()

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (mainly for testing).

        :returns: None
        """
        with cls._lock:
            if cls._instance:
                cls._instance.cleanup()
            cls._instance = None
            cls._initialized = False
            DatabaseManager.reset_instance()
