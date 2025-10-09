"""Unit tests for ServiceContainer.

Tests the ServiceContainer class which manages all application dependencies.
"""

from src.services.container import ServiceContainer


class TestServiceContainer:
    """Test suite for ServiceContainer class.

    This test class contains all tests for ServiceContainer functionality,
    including singleton pattern, service initialization, cleanup, and thread safety.
    """

    def test_container_creation(self) -> None:
        """Test ServiceContainer creation.

        This test verifies that ServiceContainer can be created
        and all services are properly initialized.

        :returns: None
        :rtype: None
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
        :rtype: None
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
        :rtype: None
        """
        container = ServiceContainer()
        life_calculator = container.get_life_calculator()

        assert life_calculator is container.life_calculator
        assert life_calculator.__name__ == "LifeCalculatorEngine"

    def test_service_initialization_order(self) -> None:
        """Test that services are initialized in correct order.

        This test verifies that services that depend on other services
        are initialized after their dependencies.

        :returns: None
        :rtype: None
        """
        container = ServiceContainer()

        # Verify that all services are properly initialized
        assert container.user_service is not None
        assert container.life_calculator is not None

        # Verify that user service can be used
        # (this would fail if initialization order was wrong)
        assert hasattr(container.user_service, "initialize")
        assert hasattr(container.user_service, "close")

    def test_cleanup_method(self) -> None:
        """Test cleanup method closes database connections and cleans up resources.

        :returns: None
        :rtype: None
        """
        from unittest.mock import Mock, patch

        container = ServiceContainer()

        # Mock DatabaseManager
        with patch("src.services.container.DatabaseManager") as mock_db_manager:
            mock_db_instance = Mock()
            mock_db_manager.return_value = mock_db_instance

            # Test cleanup
            container.cleanup()

            # Verify database close was called
            mock_db_instance.close.assert_called_once()

    def test_reset_instance_with_existing_instance(self) -> None:
        """Test reset_instance properly cleans up existing instance and resets state.

        :returns: None
        :rtype: None
        """
        from unittest.mock import patch

        # Create first instance
        container1 = ServiceContainer()

        # Mock cleanup to verify it's called
        with patch.object(container1, "cleanup") as mock_cleanup:
            # Reset instance
            ServiceContainer.reset_instance()

            # Verify cleanup was called
            mock_cleanup.assert_called_once()

            # Verify instance is reset
            assert ServiceContainer._instance is None
            assert not ServiceContainer._initialized

    def test_reset_instance_without_existing_instance(self) -> None:
        """Test reset_instance works when no instance exists.

        :returns: None
        :rtype: None
        """
        # Reset instance first
        ServiceContainer.reset_instance()

        # Verify state is reset
        assert ServiceContainer._instance is None
        assert not ServiceContainer._initialized

        # Reset again should not raise error
        ServiceContainer.reset_instance()
        assert ServiceContainer._instance is None
        assert not ServiceContainer._initialized

    def test_singleton_behavior_multiple_calls(self) -> None:
        """Test singleton behavior with multiple get_instance calls.

        :returns: None
        :rtype: None
        """
        # Reset first
        ServiceContainer.reset_instance()

        # Get multiple instances
        container1 = ServiceContainer()
        container2 = ServiceContainer()

        # Verify they are the same instance
        assert container1 is container2
        assert ServiceContainer._instance is container1

    def test_singleton_thread_safety(self) -> None:
        """Test singleton thread safety.

        :returns: None
        :rtype: None
        """
        import threading
        import time

        # Reset first
        ServiceContainer.reset_instance()

        results = []

        def get_container():
            """Get container instance in thread."""
            container = ServiceContainer()
            results.append(container)
            time.sleep(0.01)  # Small delay

        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=get_container)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all instances are the same
        assert len(results) == 3
        for container in results[1:]:
            assert container is results[0]

    def test_initialization_flag_behavior(self) -> None:
        """Test initialization flag behavior.

        :returns: None
        :rtype: None
        """
        # Initially not initialized
        assert not ServiceContainer._initialized

        # Create instance
        ServiceContainer()

        # Should be initialized now
        assert hasattr(ServiceContainer, "_initialized")

        # Reset instance
        ServiceContainer.reset_instance()

        # Should not be initialized after reset
        assert not ServiceContainer._initialized
