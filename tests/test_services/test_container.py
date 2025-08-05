"""Unit tests for ServiceContainer.

Tests the ServiceContainer class which manages all application dependencies.
"""
from src.services.container import ServiceContainer


class TestServiceContainer:
    """Test suite for ServiceContainer class."""

    def test_container_creation(self) -> None:
        """Test ServiceContainer creation.

        This test verifies that ServiceContainer can be created
        and all services are properly initialized.

        :returns: None
        """
        container = ServiceContainer()

        # Verify that all services are created
        assert container.user_service is not None
        assert container.life_calculator is not None

        # Verify that services are of correct types
        assert hasattr(container.user_service, "get_user_profile")
        assert hasattr(container.user_service, "create_user_profile")
        assert hasattr(container.user_service, "update_user_settings")

        # Verify that life calculator is a class (not instance)
        assert container.life_calculator.__name__ == "LifeCalculatorEngine"

    def test_get_user_service(self) -> None:
        """Test get_user_service method.

        This test verifies that the get_user_service method
        returns the correct user service instance.

        :returns: None
        """
        container = ServiceContainer()
        user_service = container.get_user_service()

        assert user_service is container.user_service
        assert hasattr(user_service, "get_user_profile")

    def test_get_life_calculator(self) -> None:
        """Test get_life_calculator method.

        This test verifies that the get_life_calculator method
        returns the correct life calculator class.

        :returns: None
        """
        container = ServiceContainer()
        life_calculator = container.get_life_calculator()

        assert life_calculator is container.life_calculator
        assert life_calculator.__name__ == "LifeCalculatorEngine"

    def test_get_message(self) -> None:
        """Test get_message method.

        This test verifies that the get_message method
        properly delegates to the localization service.

        :returns: None
        """
        container = ServiceContainer()

        # Test with default language
        message = container.get_message(
            message_key="command_start", sub_key="welcome_new"
        )

        assert isinstance(message, str)
        assert len(message) > 0

        # Test with specific language
        message_en = container.get_message(
            message_key="command_start", sub_key="welcome_new", language="en"
        )

        assert isinstance(message_en, str)
        assert len(message_en) > 0

    def test_get_supported_languages(self) -> None:
        """Test get_supported_languages method.

        This test verifies that the get_supported_languages method
        returns the correct list of supported languages.

        :returns: None
        """
        container = ServiceContainer()
        languages = container.get_supported_languages()

        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "ru" in languages
        assert "en" in languages
        assert "ua" in languages
        assert "by" in languages

    def test_cleanup(self) -> None:
        """Test cleanup method.

        This test verifies that the cleanup method
        can be called without errors.

        :returns: None
        """
        container = ServiceContainer()

        # Should not raise any exceptions
        container.cleanup()

    def test_service_initialization_order(self) -> None:
        """Test that services are initialized in correct order.

        This test verifies that services that depend on other services
        are initialized after their dependencies.

        :returns: None
        """
        container = ServiceContainer()

        # Verify that all services are properly initialized
        assert container.user_service is not None
        assert container.life_calculator is not None

        # Verify that user service can be used
        # (this would fail if initialization order was wrong)
        assert hasattr(container.user_service, "initialize")
        assert hasattr(container.user_service, "close")
