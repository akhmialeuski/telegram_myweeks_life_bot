"""Fake service container for testing.

This module provides a fake service container that can be used in tests
to replace the real ServiceContainer with mock objects and simplified
implementations.
"""

from unittest.mock import MagicMock


class FakeServiceContainer:
    """Fake service container for testing purposes.

    This class provides mock implementations of all services used in the
    application, making it easy to test handlers without requiring real
    database connections or external dependencies.

    Attributes:
        user_service: Mock user service
        life_calculator: Mock life calculator
        config: Mock configuration object
    """

    def __init__(self) -> None:
        """Initialize the fake service container with mock services.

        Creates mock objects for all services that would normally be
        provided by the real ServiceContainer.

        :returns: None
        """
        # Create mock user service
        self.user_service = MagicMock()

        # Create mock life calculator
        self.life_calculator = MagicMock()

        # Create mock configuration
        self.config = MagicMock()

        # Set up common mock behaviors
        self._setup_mock_behaviors()

    def _setup_mock_behaviors(self) -> None:
        """Set up common mock behaviors for testing.

        This method configures default return values and behaviors
        for the mock services to make testing easier.

        :returns: None
        """
        # Set up user service mock behaviors
        self.user_service.is_valid_user_profile.return_value = True
        self.user_service.get_user_profile.return_value = MagicMock()
        self.user_service.create_user_profile.return_value = MagicMock()
        self.user_service.update_user_settings.return_value = None
        self.user_service.update_user_subscription.return_value = None
        self.user_service.delete_user_profile.return_value = None

        # Set up life calculator mock behaviors
        self.life_calculator.return_value.calculate_age.return_value = 30
        self.life_calculator.return_value.calculate_weeks_lived.return_value = 1560
        self.life_calculator.return_value.calculate_remaining_weeks.return_value = 2340
        self.life_calculator.return_value.calculate_life_percentage.return_value = 40.0

        # Set up config mock behaviors
        self.config.DEFAULT_LANGUAGE = "ru"
        self.config.SUPPORTED_LANGUAGES = ["ru", "en", "ua", "by"]

    def get_user_service(self) -> MagicMock:
        """Get the mock user service.

        :returns: Mock user service
        :rtype: MagicMock
        """
        return self.user_service

    def get_life_calculator(self) -> MagicMock:
        """Get the mock life calculator.

        :returns: Mock life calculator
        :rtype: MagicMock
        """
        return self.life_calculator

    def get_message_builder(self, lang_code: str = "ru") -> "FakeMessageBuilder":
        """Get a fake message builder for tests.

        This provides a minimal implementation compatible with
        ``ServiceContainer.get_message_builder`` used by ``BaseHandler``.
        It delegates actual text retrieval to ``self.get_message`` so tests can
        patch that method and control returned strings.

        :param lang_code: Language code to use for messages
        :type lang_code: str
        :returns: Fake message builder instance
        :rtype: FakeMessageBuilder
        """
        return FakeMessageBuilder(container=self, lang_code=lang_code)

    def get_message(
        self, message_key: str, sub_key: str, language: str = "ru", **kwargs
    ) -> str:
        """Get a mock localized message.

        :param message_key: Message key
        :type message_key: str
        :param sub_key: Sub key
        :type sub_key: str
        :param language: Language code
        :type language: str
        :param kwargs: Additional parameters
        :returns: Mock message
        :rtype: str
        """
        return f"Mock message: {message_key}.{sub_key} ({language})"

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages.

        :returns: List of supported language codes
        :rtype: list[str]
        """
        return ["ru", "en", "ua", "by"]

    def cleanup(self) -> None:
        """Clean up mock resources.

        This method is called when shutting down tests to clean up
        any mock resources or reset mock states.

        :returns: None
        """
        # Reset all mocks to their initial state
        self.user_service.reset_mock()
        self.life_calculator.reset_mock()
        self.config.reset_mock()


class FakeMessageBuilder:
    """Fake message builder used in tests to emulate ``MessageBuilder``.

    The builder exposes only methods that are exercised by unit tests, and each
    method pulls text from the parent container's ``get_message`` so that test
    patches applied to ``FakeServiceContainer.get_message`` are respected.

    :param container: Parent fake service container
    :type container: FakeServiceContainer
    :param lang_code: Language code for produced messages
    :type lang_code: str
    """

    def __init__(self, container: "FakeServiceContainer", lang_code: str) -> None:
        """Initialize builder with container and language.

        :param container: Parent fake container that supplies messages
        :type container: FakeServiceContainer
        :param lang_code: Language code for messages
        :type lang_code: str
        :returns: None
        :rtype: None
        """
        self._container: FakeServiceContainer = container
        self._lang: str = lang_code

    def not_registered(self) -> str:
        """Produce generic "not registered" message.

        :returns: Localized not-registered message
        :rtype: str
        """
        return self._container.get_message(
            message_key="common", sub_key="not_registered", language=self._lang
        )

    def not_registered_weeks(self) -> str:
        """Produce weeks-specific "not registered" message.

        :returns: Localized not-registered message for weeks
        :rtype: str
        """
        return self._container.get_message(
            message_key="weeks", sub_key="not_registered", language=self._lang
        )

    def not_registered_visualize(self) -> str:
        """Produce visualize-specific "not registered" message.

        :returns: Localized not-registered message for visualize
        :rtype: str
        """
        return self._container.get_message(
            message_key="visualize", sub_key="not_registered", language=self._lang
        )
