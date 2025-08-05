"""Service container for dependency injection.

This module provides a centralized container for managing all application
dependencies, including database services, schedulers, and utilities.
It implements the Dependency Injection pattern to reduce coupling between
modules and simplify testing.
"""
from ..bot.scheduler import NotificationScheduler
from ..core.life_calculator import LifeCalculatorEngine
from ..database.service import UserService
from ..utils.config import DEFAULT_LANGUAGE
from ..utils.localization import get_message, get_supported_languages


class ServiceContainer:
    """Centralized container for all application services and dependencies.

    This class manages the creation and lifecycle of all application services,
    providing a single point of configuration and dependency management.
    It implements the Dependency Injection pattern to reduce coupling between
    modules and simplify testing.

    Attributes:
        config: Application configuration object
        user_service: User management service
        notification_scheduler: Weekly notification scheduler
        life_calculator: Life statistics calculator
        localization_service: Message localization service
    """

    def __init__(self) -> None:
        """Initialize the service container with all dependencies.

        Creates instances of all services and utilities. This centralizes
        dependency creation and makes it easy to swap implementations
        for testing or different environments.

        :returns: None
        """
        # Initialize database services
        self.user_service = UserService()

        # Initialize life calculator
        self.life_calculator = LifeCalculatorEngine

        # Initialize services that depend on other services
        self._initialize_service_dependencies()

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

    def get_notification_scheduler(self) -> NotificationScheduler:
        """Get the notification scheduler instance.

        :returns: Notification scheduler instance
        :rtype: NotificationScheduler
        """
        return self.notification_scheduler

    def get_life_calculator(self) -> type[LifeCalculatorEngine]:
        """Get the life calculator class.

        :returns: Life calculator class
        :rtype: type[LifeCalculatorEngine]
        """
        return self.life_calculator

    def get_message(
        self, message_key: str, sub_key: str, language: str = DEFAULT_LANGUAGE, **kwargs
    ) -> str:
        """Get localized message.

        :param message_key: Message key
        :type message_key: str
        :param sub_key: Sub key
        :type sub_key: str
        :param language: Language code
        :type language: str
        :param kwargs: Additional parameters for message formatting
        :returns: Localized message
        :rtype: str
        """
        return get_message(
            message_key=message_key, sub_key=sub_key, language=language, **kwargs
        )

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages.

        :returns: List of supported language codes
        :rtype: list[str]
        """
        return get_supported_languages()

    def cleanup(self) -> None:
        """Clean up resources and close connections.

        This method should be called when shutting down the application
        to properly close database connections and other resources.

        :returns: None
        """
        if hasattr(self.user_service, "close"):
            self.user_service.close()

        # Note: NotificationScheduler is initialized separately in application.py
        # as it requires the Application instance
