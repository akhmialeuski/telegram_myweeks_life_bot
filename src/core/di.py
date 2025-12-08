"""Dependency Injection container and protocols.

This module implements a lightweight DI container based on Protocols/Contracts.
It allows registering factories and singletons, and resolving them by Protocol.
"""

import logging
from typing import (
    Any,
    Callable,
    Dict,
    Protocol,
    Type,
    TypeVar,
    runtime_checkable,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


@runtime_checkable
class ServiceProvider(Protocol):
    """Protocol for a service provider that can resolve dependencies."""

    def get(self, protocol: Type[T]) -> T:
        """Resolve a service by its protocol/type."""
        ...


class Container(ServiceProvider):
    """Simple dependency injection container."""

    def __init__(self) -> None:
        self._factories: Dict[Type[Any], Callable[[], Any]] = {}
        self._singletons: Dict[Type[Any], Any] = {}

    def register_factory(self, protocol: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory for a protocol.

        The factory will be called every time the service is requested.
        """
        self._factories[protocol] = factory

    def register_singleton(self, protocol: Type[T], instance: T) -> None:
        """Register a singleton instance for a protocol.

        The same instance will be returned every time the service is requested.
        """
        self._singletons[protocol] = instance

    def register_lazy_singleton(
        self, protocol: Type[T], factory: Callable[[], T]
    ) -> None:
        """Register a factory that results in a singleton.

        The factory is called once on the first request, and the result is cached.
        """

        def _lazy_wrapper() -> T:
            if protocol not in self._singletons:
                self._singletons[protocol] = factory()
            return self._singletons[protocol]

        self._factories[protocol] = _lazy_wrapper

    def get(self, protocol: Type[T]) -> T:
        """Resolve a service by its protocol.

        :raises KeyError: If the protocol is not registered.
        """
        # Check singletons first
        if protocol in self._singletons:
            return self._singletons[protocol]

        # Check factories
        if protocol in self._factories:
            return self._factories[protocol]()

        raise KeyError(f"Service not registered: {protocol}")
