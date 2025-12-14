"""Protocol contracts for Dependency Injection.

This module provides Protocol-based interfaces for all services in the application.
Using Protocols (PEP 544) enables structural subtyping, allowing implementations
to satisfy contracts without explicit inheritance.

All protocols are runtime-checkable for use with isinstance() checks.
"""

from .i18n_service_protocol import I18nServiceProtocol
from .life_calculator_protocol import LifeCalculatorProtocol
from .notification_gateway_protocol import NotificationGatewayProtocol
from .scheduler_port_protocol import JobInfo, SchedulerPortProtocol, ScheduleTrigger
from .user_repository_protocol import UserRepositoryProtocol
from .user_service_protocol import UserServiceProtocol

__all__: list[str] = [
    "I18nServiceProtocol",
    "LifeCalculatorProtocol",
    "NotificationGatewayProtocol",
    "SchedulerPortProtocol",
    "ScheduleTrigger",
    "JobInfo",
    "UserRepositoryProtocol",
    "UserServiceProtocol",
]
