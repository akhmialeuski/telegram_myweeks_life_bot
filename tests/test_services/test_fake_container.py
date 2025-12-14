"""Unit tests for FakeServiceContainer.

Tests the FakeServiceContainer class which provides mock services for testing.
"""

from unittest.mock import MagicMock

from src.enums import SupportedLanguage
from tests.utils.fake_container import FakeServiceContainer


class TestFakeServiceContainer:
    """Test suite for FakeServiceContainer class.

    This test class contains all tests for FakeServiceContainer functionality,
    including mock creation, behaviors, interface compatibility, and cleanup.
    """

    def test_fake_container_creation(self) -> None:
        """Test FakeServiceContainer creation.

        This test verifies that FakeServiceContainer can be created
        and all mock services are properly initialized.

        :returns: None
        :rtype: None
        """
        container = FakeServiceContainer()

        # Verify that all services are created
        assert container.user_service is not None
        assert container.life_calculator is not None
        assert container.config is not None

        # Verify that services are MagicMock instances
        assert isinstance(container.user_service, MagicMock)
        assert isinstance(container.life_calculator, MagicMock)
        assert isinstance(container.config, MagicMock)

    def test_mock_behaviors_setup(self) -> None:
        """Test that mock behaviors are properly set up.

        This test verifies that the mock services have the expected
        default return values and behaviors.

        :returns: None
        :rtype: None
        """
        container = FakeServiceContainer()

        # Test user service mock behaviors
        assert container.user_service.is_valid_user_profile.return_value is True
        assert container.user_service.get_user_profile.return_value is not None
        assert container.user_service.create_user_profile.return_value is not None

        # Test life calculator mock behaviors
        assert container.life_calculator.return_value.calculate_age.return_value == 30
        assert (
            container.life_calculator.return_value.calculate_weeks_lived.return_value
            == 1560
        )
        assert (
            container.life_calculator.return_value.calculate_remaining_weeks.return_value
            == 2340
        )
        assert (
            container.life_calculator.return_value.calculate_life_percentage.return_value
            == 0.4
        )

        # Test config mock behaviors
        assert container.config.DEFAULT_LANGUAGE == SupportedLanguage.RU.value
        assert container.config.SUPPORTED_LANGUAGES == [
            SupportedLanguage.RU.value,
            SupportedLanguage.EN.value,
            SupportedLanguage.UA.value,
            SupportedLanguage.BY.value,
        ]

    def test_get_user_service(self) -> None:
        """Test get_user_service method.

        This test verifies that the get_user_service method
        returns the correct mock user service.

        :returns: None
        :rtype: None
        """
        container = FakeServiceContainer()
        user_service = container.get_user_service()

        assert user_service is container.user_service
        assert isinstance(user_service, MagicMock)

    def test_get_life_calculator(self) -> None:
        """Test get_life_calculator method.

        This test verifies that the get_life_calculator method
        returns the correct mock life calculator.

        :returns: None
        :rtype: None
        """
        container = FakeServiceContainer()
        life_calculator = container.get_life_calculator()

        assert life_calculator is container.life_calculator
        assert isinstance(life_calculator, MagicMock)

    def test_get_message(self) -> None:
        """Test get_message method.

        This test verifies that the get_message method
        returns a properly formatted mock message.

        :returns: None
        :rtype: None
        """
        container = FakeServiceContainer()

        message = container.get_message(
            message_key="test_key",
            sub_key="test_sub_key",
            language=SupportedLanguage.EN.value,
        )

        assert isinstance(message, str)
        assert "Mock message: test_key.test_sub_key (en)" in message

    def test_cleanup(self) -> None:
        """Test cleanup method.

        This test verifies that the cleanup method
        resets all mocks to their initial state.

        :returns: None
        :rtype: None
        """
        container = FakeServiceContainer()

        # Call some methods to create call history
        container.user_service.get_user_profile(123)
        container.life_calculator.return_value.calculate_age()

        # Verify that methods were called
        assert container.user_service.get_user_profile.called
        assert container.life_calculator.return_value.calculate_age.called

        # Clean up
        container.cleanup()

        # Verify that mocks were reset
        assert not container.user_service.get_user_profile.called
        assert not container.life_calculator.return_value.calculate_age.called

    def test_custom_mock_behaviors(self) -> None:
        """Test that custom mock behaviors can be set.

        This test verifies that the mock services can be configured
        with custom behaviors for specific test scenarios.

        :returns: None
        :rtype: None
        """
        container = FakeServiceContainer()

        # Set custom behaviors
        container.user_service.is_valid_user_profile.return_value = False
        container.user_service.get_user_profile.return_value = None
        container.life_calculator.return_value.calculate_age.return_value = 25

        # Verify custom behaviors
        assert container.user_service.is_valid_user_profile.return_value is False
        assert container.user_service.get_user_profile.return_value is None
        assert container.life_calculator.return_value.calculate_age.return_value == 25

    def test_interface_compatibility(self) -> None:
        """Test that FakeServiceContainer has the same interface as ServiceContainer.

        This test verifies that FakeServiceContainer can be used
        as a drop-in replacement for ServiceContainer in tests.

        :returns: None
        :rtype: None
        """
        container = FakeServiceContainer()

        # Verify that all required methods exist
        assert hasattr(container, "get_user_service")
        assert hasattr(container, "get_life_calculator")
        assert hasattr(container, "get_message")
        assert hasattr(container, "cleanup")

        # Verify that all required attributes exist
        assert hasattr(container, "user_service")
        assert hasattr(container, "life_calculator")
        assert hasattr(container, "config")
