"""Dependency Injection container and protocols.

This module implements a lightweight DI container based on Protocols/Contracts.
It allows registering factories and singletons, and resolving them by Protocol.

The container supports three lifetimes:
    - Singleton: One instance per container lifetime
    - Transient: New instance per resolution
    - Scoped: New instance per scope (not yet implemented)

Example usage:
    >>> container = Container()
    >>> container.register_singleton(UserServiceProtocol, user_service)
    >>> service = container.get(UserServiceProtocol)
"""

import asyncio
import logging
from typing import (
    Any,
    Callable,
    Protocol,
    Type,
    TypeVar,
    runtime_checkable,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DependencyNotRegisteredError(Exception):
    """Exception raised when attempting to resolve an unregistered dependency.

    This exception is raised when the container cannot find a registration
    for the requested protocol/type.
    """

    def __init__(self, protocol: type) -> None:
        """Initialize the exception with the missing protocol.

        :param protocol: The protocol type that was not registered
        :type protocol: type
        """
        self.protocol = protocol
        # Handle GenericAlias (e.g., type[X]) which doesn't have __name__
        protocol_name = getattr(protocol, "__name__", repr(protocol))
        super().__init__(f"No registration found for {protocol_name}")


@runtime_checkable
class ServiceProvider(Protocol):
    """Protocol for a service provider that can resolve dependencies.

    This protocol defines the minimal interface for dependency resolution.
    Any container implementation must provide this interface.
    """

    def get(self, protocol: Type[T]) -> T:
        """Resolve a service by its protocol/type.

        :param protocol: The protocol type to resolve
        :type protocol: Type[T]
        :returns: The resolved service instance
        :rtype: T
        :raises DependencyNotRegisteredError: If protocol is not registered
        """
        ...


class Container(ServiceProvider):
    """Dependency Injection container with multiple lifetime support.

    This container supports singleton, transient, and lazy singleton lifetimes.
    It provides type-safe resolution via Protocol types and includes
    async disposal for proper resource cleanup.

    Attributes:
        _factories: Registry of factory functions for transient services
        _singletons: Cache of singleton instances

    Example:
        >>> container = Container()
        >>> container.register_singleton(UserServiceProtocol, user_service)
        >>> container.register_factory(
        ...     CalculatorProtocol,
        ...     lambda: LifeCalculatorEngine()
        ... )
        >>> service = container.get(UserServiceProtocol)
    """

    def __init__(self) -> None:
        """Initialize the container with empty registries.

        :returns: None
        """
        self._factories: dict[Type[Any], Callable[[], Any]] = {}
        self._singletons: dict[Type[Any], Any] = {}

    def register_factory(
        self,
        protocol: Type[T],
        factory: Callable[[], T],
    ) -> None:
        """Register a factory for transient service resolution.

        The factory will be called every time the service is requested,
        creating a new instance each time.

        :param protocol: The protocol type to register
        :type protocol: Type[T]
        :param factory: Factory function that creates service instances
        :type factory: Callable[[], T]
        :returns: None
        """
        self._factories[protocol] = factory

    def register_singleton(
        self,
        protocol: Type[T],
        instance: T,
    ) -> None:
        """Register a singleton instance for a protocol.

        The same instance will be returned every time the service is requested.

        :param protocol: The protocol type to register
        :type protocol: Type[T]
        :param instance: The singleton instance to register
        :type instance: T
        :returns: None
        """
        self._singletons[protocol] = instance

    def register_lazy_singleton(
        self,
        protocol: Type[T],
        factory: Callable[[], T],
    ) -> None:
        """Register a lazy singleton factory.

        The factory is called once on the first request, and the result
        is cached for subsequent requests.

        :param protocol: The protocol type to register
        :type protocol: Type[T]
        :param factory: Factory function that creates the singleton
        :type factory: Callable[[], T]
        :returns: None
        """

        def _lazy_wrapper() -> T:
            if protocol not in self._singletons:
                self._singletons[protocol] = factory()
            return self._singletons[protocol]

        self._factories[protocol] = _lazy_wrapper

    def get(self, protocol: Type[T]) -> T:
        """Resolve a service by its protocol.

        Resolution order:
        1. Check singletons cache first
        2. Check factories (includes lazy singletons)
        3. Raise DependencyNotRegisteredError if not found

        :param protocol: The protocol type to resolve
        :type protocol: Type[T]
        :returns: The resolved service instance
        :rtype: T
        :raises DependencyNotRegisteredError: If the protocol is not registered
        """
        # Check singletons first
        if protocol in self._singletons:
            return self._singletons[protocol]

        # Check factories
        if protocol in self._factories:
            return self._factories[protocol]()

        raise DependencyNotRegisteredError(protocol=protocol)

    def is_registered(self, protocol: Type[T]) -> bool:
        """Check if a protocol is registered.

        :param protocol: The protocol type to check
        :type protocol: Type[T]
        :returns: True if registered, False otherwise
        :rtype: bool
        """
        return protocol in self._singletons or protocol in self._factories

    async def dispose(self) -> None:
        """Dispose all singleton instances implementing cleanup methods.

        This method handles both sync and async close/dispose methods.
        It should be called during application shutdown to properly
        release resources held by singletons.

        :returns: None
        """
        for protocol, instance in list(self._singletons.items()):
            try:
                if hasattr(instance, "close"):
                    close_method = getattr(instance, "close")
                    if asyncio.iscoroutinefunction(close_method):
                        await close_method()
                    else:
                        close_method()
                elif hasattr(instance, "dispose"):
                    dispose_method = getattr(instance, "dispose")
                    if asyncio.iscoroutinefunction(dispose_method):
                        await dispose_method()
                    else:
                        dispose_method()
            except Exception as error:
                # Handle GenericAlias (e.g., type[X]) which doesn't have __name__
                protocol_name = getattr(protocol, "__name__", repr(protocol))
                logger.warning(f"Error disposing {protocol_name}: {error}")
        self._singletons.clear()

    def clear(self) -> None:
        """Clear all registrations and cached singletons.

        This is primarily useful for testing to reset the container state.

        :returns: None
        """
        self._factories.clear()
        self._singletons.clear()
