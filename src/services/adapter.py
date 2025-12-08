"""Adapter for legacy ServiceContainer to implementing ServiceProvider protocol.

This module provides a compatibility layer to allow the new DI system to work
with the existing ServiceContainer until it is fully refactored.
"""

from typing import Type, TypeVar

from ..core.di import ServiceProvider
from ..core.life_calculator import LifeCalculatorEngine
from ..database.service import UserService
from ..services.container import ServiceContainer

T = TypeVar("T")


class LegacyServiceAdapter(ServiceProvider):
    """Adapter that makes ServiceContainer look like a ServiceProvider."""

    def __init__(self, container: ServiceContainer):
        self._container = container

    def get(self, protocol: Type[T]) -> T:
        """Resolve legacy services by type."""
        # Mapping types to container attributes
        if protocol is UserService:
            return self._container.user_service
        if protocol is LifeCalculatorEngine:
            return self._container.life_calculator
        if protocol is ServiceContainer:
            return self._container

        # Fallback to direct attribute access if the protocol matches a property name (unlikely but possible)
        # or just error out.
        raise KeyError(f"Service {protocol} not found in LegacyServiceAdapter")
