"""Events package for domain events and event bus.

This package provides the event-driven architecture components for
decoupling handlers from the scheduler.
"""

from .domain_events import (
    DeliveryResult,
    DomainEvent,
    NotificationPayload,
    NotificationSentEvent,
    SchedulerCommand,
    ScheduleRecalculationRequestedEvent,
    SchedulerResponse,
    UserDeletedEvent,
    UserRegisteredEvent,
    UserSettingsChangedEvent,
)
from .event_bus import EventBus

__all__: list[str] = [
    # Event Bus
    "EventBus",
    # DTOs
    "NotificationPayload",
    "DeliveryResult",
    # Base Event
    "DomainEvent",
    # User Events
    "UserSettingsChangedEvent",
    "UserRegisteredEvent",
    "UserDeletedEvent",
    # Scheduler Events
    "ScheduleRecalculationRequestedEvent",
    "NotificationSentEvent",
    # IPC Commands
    "SchedulerCommand",
    "SchedulerResponse",
]
