"""Test fake implementations for dependency injection.

This module provides in-memory implementations of service protocols
that can be used for testing without requiring real databases or
external services.
"""

from .fake_notification_gateway import FakeNotificationGateway
from .fake_user_service import FakeUserService
from .in_memory_user_repository import InMemoryUserRepository

__all__: list[str] = [
    "FakeNotificationGateway",
    "FakeUserService",
    "InMemoryUserRepository",
]
