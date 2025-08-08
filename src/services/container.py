"""Service container for dependency injection.

This module provides a centralized container for managing all application
dependencies, including database services, schedulers, and utilities.
It implements the Dependency Injection pattern to reduce coupling between
modules and simplify testing.
"""
import threading

from ..bot.scheduler import NotificationScheduler
from ..core.life_calculator import LifeCalculatorEngine
from ..database.service import DatabaseManager, UserService
from ..utils.config import DEFAULT_LANGUAGE
from ..utils.localization import MessageBuilder, get_supported_languages
from .message_service import MessageService


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

    _instance = None
    _initialized = False
    _lock = threading.Lock()

    def __new__(cls):
        """Create singleton instance of ServiceContainer.

        :returns: ServiceContainer instance
        :rtype: ServiceContainer
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

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

        # Messaging service for caching builders
        self.message_service: MessageService = MessageService()

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

    def get_notification_scheduler(self) -> "NotificationScheduler":
        """Get the notification scheduler instance.

        :returns: Notification scheduler instance
        :rtype: NotificationScheduler
        """
        from ..bot.scheduler import NotificationScheduler

        return NotificationScheduler

    def get_life_calculator(self) -> type[LifeCalculatorEngine]:
        """Get the life calculator class.

        :returns: Life calculator class
        :rtype: type[LifeCalculatorEngine]
        """
        return self.life_calculator

    def get_message_builder(self, lang_code: str = DEFAULT_LANGUAGE) -> MessageBuilder:
        """Get message builder for the specified language.

        :param lang_code: Language code (ru, en, ua, by)
        :type lang_code: str
        :returns: MessageBuilder instance for the specified language
        :rtype: MessageBuilder
        """
        # Normalize provided language to a supported string value.
        # Tests may pass Enum or MagicMock; default safely to DEFAULT_LANGUAGE.
        normalized_lang: str
        try:
            # Extract value from Enum-like objects
            if hasattr(lang_code, "value"):
                normalized_lang = str(getattr(lang_code, "value"))
            elif isinstance(lang_code, str):
                normalized_lang = lang_code
            else:
                normalized_lang = DEFAULT_LANGUAGE
        except Exception:
            normalized_lang = DEFAULT_LANGUAGE

        try:
            supported_languages: list[str] = get_supported_languages()
            if normalized_lang not in supported_languages:
                normalized_lang = DEFAULT_LANGUAGE
        except Exception:
            normalized_lang = DEFAULT_LANGUAGE

        return self.message_service.get_builder(normalized_lang)

    def get_localizer(self, user_id: int) -> MessageBuilder:
        """Get message builder for user based on their language preference.

        :param user_id: Telegram user ID
        :type user_id: int
        :returns: MessageBuilder instance for user's language
        :rtype: MessageBuilder
        """
        # Get user profile to determine language
        user_profile = self.user_service.get_user_profile(telegram_id=user_id)
        lang_code = DEFAULT_LANGUAGE

        if user_profile and user_profile.settings and user_profile.settings.language:
            lang_code = user_profile.settings.language

        return self.get_message_builder(lang_code)

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages.

        :returns: List of supported language codes
        :rtype: list[str]
        """
        return get_supported_languages()

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
        if cls._instance:
            cls._instance.cleanup()
        cls._instance = None
        cls._initialized = False
        DatabaseManager.reset_instance()
