"""Unit tests for enhanced DI Container.

Tests the Container class including registration, resolution, disposal,
and error handling functionality.
"""

import pytest

from src.core.di import Container, DependencyNotRegisteredError


class TestContainer:
    """Test suite for Container class.

    This test class contains all tests for Container functionality,
    including registration, resolution, and lifecycle management.
    """

    def test_register_singleton_and_resolve(self) -> None:
        """Test registering and resolving a singleton.

        This test verifies that a singleton instance is returned
        on every resolution request.
        """
        container = Container()

        class SampleService:
            pass

        instance = SampleService()
        container.register_singleton(protocol=SampleService, instance=instance)

        resolved = container.get(protocol=SampleService)
        assert resolved is instance

    def test_register_factory_creates_new_instance(self) -> None:
        """Test that factory registration creates new instances.

        This test verifies that the factory is called on each resolution,
        creating a new instance each time.
        """
        container = Container()

        class TransientService:
            pass

        container.register_factory(
            protocol=TransientService,
            factory=lambda: TransientService(),
        )

        instance1 = container.get(protocol=TransientService)
        instance2 = container.get(protocol=TransientService)

        assert instance1 is not instance2
        assert isinstance(instance1, TransientService)
        assert isinstance(instance2, TransientService)

    def test_register_lazy_singleton(self) -> None:
        """Test lazy singleton registration.

        This test verifies that the factory is called only once
        and the result is cached for subsequent requests.
        """
        container = Container()
        call_count = 0

        class LazyService:
            pass

        def factory() -> LazyService:
            nonlocal call_count
            call_count += 1
            return LazyService()

        container.register_lazy_singleton(protocol=LazyService, factory=factory)

        # Factory not called until first resolution
        assert call_count == 0

        instance1 = container.get(protocol=LazyService)
        assert call_count == 1

        instance2 = container.get(protocol=LazyService)
        assert call_count == 1  # Still 1, not called again

        assert instance1 is instance2

    def test_get_unregistered_raises_error(self) -> None:
        """Test that resolving unregistered service raises error.

        This test verifies that DependencyNotRegisteredError is raised
        when attempting to resolve a service that was not registered.
        """
        container = Container()

        class UnregisteredService:
            pass

        with pytest.raises(DependencyNotRegisteredError) as exc_info:
            container.get(protocol=UnregisteredService)

        assert exc_info.value.protocol is UnregisteredService
        assert "UnregisteredService" in str(exc_info.value)

    def test_is_registered_returns_true_for_registered(self) -> None:
        """Test is_registered returns True for registered services.

        This test verifies that is_registered correctly identifies
        registered protocols.
        """
        container = Container()

        class RegisteredService:
            pass

        container.register_singleton(
            protocol=RegisteredService,
            instance=RegisteredService(),
        )

        assert container.is_registered(protocol=RegisteredService) is True

    def test_is_registered_returns_false_for_unregistered(self) -> None:
        """Test is_registered returns False for unregistered services.

        This test verifies that is_registered correctly identifies
        unregistered protocols.
        """
        container = Container()

        class UnregisteredService:
            pass

        assert container.is_registered(protocol=UnregisteredService) is False

    def test_clear_removes_all_registrations(self) -> None:
        """Test that clear removes all registrations.

        This test verifies that after calling clear(), no services
        are registered in the container.
        """
        container = Container()

        class Service1:
            pass

        class Service2:
            pass

        container.register_singleton(protocol=Service1, instance=Service1())
        container.register_factory(protocol=Service2, factory=lambda: Service2())

        container.clear()

        assert container.is_registered(protocol=Service1) is False
        assert container.is_registered(protocol=Service2) is False


class TestContainerDisposal:
    """Test suite for Container disposal functionality."""

    @pytest.mark.asyncio
    async def test_dispose_calls_close_method(self) -> None:
        """Test that dispose calls close() on singletons.

        This test verifies that the container properly disposes
        singletons that have a close() method.
        """
        container = Container()

        class DisposableService:
            closed = False

            def close(self) -> None:
                self.closed = True

        instance = DisposableService()
        container.register_singleton(protocol=DisposableService, instance=instance)

        await container.dispose()

        assert instance.closed is True

    @pytest.mark.asyncio
    async def test_dispose_calls_async_close_method(self) -> None:
        """Test that dispose awaits async close() methods.

        This test verifies that the container properly awaits
        async close methods during disposal.
        """
        container = Container()

        class AsyncDisposableService:
            closed = False

            async def close(self) -> None:
                self.closed = True

        instance = AsyncDisposableService()
        container.register_singleton(protocol=AsyncDisposableService, instance=instance)

        await container.dispose()

        assert instance.closed is True

    @pytest.mark.asyncio
    async def test_dispose_clears_singletons(self) -> None:
        """Test that dispose clears singleton cache.

        This test verifies that after disposal, singletons are
        removed from the container cache.
        """
        container = Container()

        class Service:
            pass

        container.register_singleton(protocol=Service, instance=Service())

        await container.dispose()

        # After dispose, singletons should be cleared
        # is_registered checks both factories and singletons
        # Since we only registered as singleton, it should now be False
        assert container.is_registered(protocol=Service) is False

    @pytest.mark.asyncio
    async def test_dispose_handles_errors_gracefully(self) -> None:
        """Test that dispose handles errors during cleanup.

        This test verifies that if a service's close() method raises
        an exception, the container logs the error and continues
        disposing other services.

        :returns: None
        :rtype: None
        """
        container = Container()

        class FailingService:
            def close(self) -> None:
                raise RuntimeError("Close failed")

        class WorkingService:
            closed = False

            def close(self) -> None:
                self.closed = True

        failing_instance = FailingService()
        working_instance = WorkingService()

        container.register_singleton(protocol=FailingService, instance=failing_instance)
        container.register_singleton(protocol=WorkingService, instance=working_instance)

        # Should not raise, should handle error gracefully
        await container.dispose()

        # Working service should still be closed despite failing service
        assert working_instance.closed is True
        # Singletons should be cleared even with errors
        assert container.is_registered(protocol=FailingService) is False
        assert container.is_registered(protocol=WorkingService) is False

    @pytest.mark.asyncio
    async def test_dispose_calls_dispose_method(self) -> None:
        """Test that dispose calls dispose() on singletons.

        This test verifies that the container properly disposes
        singletons that have a dispose() method instead of close().

        :returns: None
        :rtype: None
        """
        container = Container()

        class DisposableService:
            disposed = False

            def dispose(self) -> None:
                self.disposed = True

        instance = DisposableService()
        container.register_singleton(protocol=DisposableService, instance=instance)

        await container.dispose()

        assert instance.disposed is True

    @pytest.mark.asyncio
    async def test_dispose_calls_async_dispose_method(self) -> None:
        """Test that dispose awaits async dispose() methods.

        This test verifies that the container properly awaits
        async dispose methods during disposal.

        :returns: None
        :rtype: None
        """
        container = Container()

        class AsyncDisposableService:
            disposed = False

            async def dispose(self) -> None:
                self.disposed = True

        instance = AsyncDisposableService()
        container.register_singleton(protocol=AsyncDisposableService, instance=instance)

        await container.dispose()

        assert instance.disposed is True


class TestDependencyNotRegisteredError:
    """Test suite for DependencyNotRegisteredError exception."""

    def test_error_stores_protocol(self) -> None:
        """Test that the error stores the protocol type.

        This test verifies that the exception has access to the
        protocol that was not found.
        """

        class MissingService:
            pass

        error = DependencyNotRegisteredError(protocol=MissingService)

        assert error.protocol is MissingService

    def test_error_message_includes_protocol_name(self) -> None:
        """Test that error message includes protocol name.

        This test verifies that the error message is informative
        and includes the name of the missing protocol.
        """

        class MissingService:
            pass

        error = DependencyNotRegisteredError(protocol=MissingService)

        assert "MissingService" in str(error)
        assert "No registration found" in str(error)

    def test_error_handles_generic_alias(self) -> None:
        """Test that error handles GenericAlias types.

        This test verifies that the error doesn't crash when
        the protocol is a GenericAlias like type[X] which has
        no __name__ attribute.
        """

        class SomeProtocol:
            pass

        # Create a GenericAlias - type[X] doesn't have __name__
        generic_alias = type[SomeProtocol]

        # Should not raise AttributeError
        error = DependencyNotRegisteredError(protocol=generic_alias)

        # Should contain some representation of the type
        assert "No registration found" in str(error)
