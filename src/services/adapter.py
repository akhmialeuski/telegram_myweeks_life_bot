"""Adapter for legacy ServiceContainer to implementing ServiceProvider protocol.

This module provides a compatibility layer to allow the new DI system to work
with the existing ServiceContainer until it is fully refactored.
"""

from typing import Type, TypeVar

from ..contracts import LifeCalculatorProtocol, UserServiceProtocol
from ..core.di import DependencyNotRegisteredError, ServiceProvider
from ..core.life_calculator import LifeCalculatorEngine
from ..database.service import UserService
from ..services.container import ServiceContainer

T = TypeVar("T")


class LegacyServiceAdapter(ServiceProvider):
    """Adapter that makes ServiceContainer work with both old and new DI patterns.

    This adapter bridges the legacy ServiceContainer with the new Protocol-based
    DI system. It can resolve services by their concrete types (for legacy code)
    or by their Protocol types (for new code).

    :param container: Legacy ServiceContainer instance to adapt
    :type container: ServiceContainer
    """

    def __init__(self, container: ServiceContainer) -> None:
        """Initialize adapter with a legacy container.

        :param container: ServiceContainer instance to wrap
        :type container: ServiceContainer
        :returns: None
        """
        self._container = container

    def get(self, protocol: Type[T]) -> T:
        """Resolve services by type or protocol.

        Resolution order:
        1. Check for concrete types (legacy support)
        2. Check for Protocol types (new DI support)
        3. Raise DependencyNotRegisteredError if not found

        :param protocol: The type or protocol to resolve
        :type protocol: Type[T]
        :returns: The resolved service instance
        :rtype: T
        :raises DependencyNotRegisteredError: If service is not found
        """
        # Legacy concrete type mappings
        if protocol is UserService:
            return self._container.user_service  # type: ignore[return-value]
        if protocol is LifeCalculatorEngine:
            return self._container.life_calculator  # type: ignore[return-value]
        if protocol is ServiceContainer:
            return self._container  # type: ignore[return-value]

        # New Protocol type mappings
        if protocol is UserServiceProtocol:
            return self._container.user_service  # type: ignore[return-value]
        if protocol is LifeCalculatorProtocol:
            return self._container.life_calculator  # type: ignore[return-value]

        raise DependencyNotRegisteredError(protocol=protocol)
