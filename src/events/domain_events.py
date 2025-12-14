"""Domain events for notification system.

This module defines domain events and data transfer objects for the
notification scheduling system. Events enable loose coupling between
handlers and the scheduler through publish/subscribe pattern.

All events are immutable dataclasses with frozen=True for thread safety.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

# --- Data Transfer Objects ---


@dataclass(frozen=True, slots=True)
class NotificationPayload:
    """Transport-agnostic notification content.

    This dataclass represents notification content that can be sent
    via any delivery channel (Telegram, email, Obsidian toast, etc.).

    :ivar recipient_id: Unique identifier of the recipient
    :ivar message_type: Type of notification (weekly_summary, milestone, reminder)
    :ivar title: Short title for the notification
    :ivar body: Main message body
    :ivar metadata: Additional data for specific delivery channels
    :ivar scheduled_at: When the notification was scheduled
    """

    recipient_id: int
    message_type: str
    title: str
    body: str
    metadata: dict[str, Any] = field(default_factory=dict)
    scheduled_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    """Result of notification delivery attempt.

    :ivar success: Whether the delivery was successful
    :ivar recipient_id: ID of the recipient
    :ivar error: Error message if delivery failed
    :ivar delivered_at: Timestamp of delivery
    """

    success: bool
    recipient_id: int
    error: str | None = None
    delivered_at: datetime = field(default_factory=datetime.now)


# --- Base Event ---


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """Base class for all domain events.

    All domain events inherit from this class to ensure consistent
    structure with timestamp and correlation ID for tracing.

    :ivar timestamp: When the event was created
    :ivar correlation_id: Unique ID for tracing related events
    """

    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: str = field(default_factory=lambda: str(uuid4()))


# --- User Events ---


@dataclass(frozen=True, slots=True)
class UserSettingsChangedEvent(DomainEvent):
    """Published when user updates notification-related settings.

    Handlers publish this event instead of directly calling scheduler
    methods. The event bus routes it to the appropriate handler that
    updates the scheduler.

    :ivar user_id: Telegram user ID whose settings changed
    :ivar setting_name: Name of the changed setting
    :ivar old_value: Previous value (None if not applicable)
    :ivar new_value: New value (None if not applicable)
    """

    user_id: int = 0
    setting_name: str = ""
    old_value: Any = None
    new_value: Any = None


@dataclass(frozen=True, slots=True)
class UserRegisteredEvent(DomainEvent):
    """Published when a new user completes registration.

    :ivar user_id: Telegram user ID of the newly registered user
    """

    user_id: int = 0


@dataclass(frozen=True, slots=True)
class UserDeletedEvent(DomainEvent):
    """Published when a user is deleted from the system.

    :ivar user_id: Telegram user ID of the deleted user
    """

    user_id: int = 0


# --- Scheduler Events ---


@dataclass(frozen=True, slots=True)
class ScheduleRecalculationRequestedEvent(DomainEvent):
    """Published when scheduler needs to recalculate jobs for a user.

    :ivar user_id: Telegram user ID for schedule recalculation
    """

    user_id: int = 0


@dataclass(frozen=True, slots=True)
class NotificationSentEvent(DomainEvent):
    """Published after a notification is sent (success or failure).

    :ivar user_id: Telegram user ID who received the notification
    :ivar message_type: Type of notification sent
    :ivar success: Whether the delivery was successful
    :ivar error: Error message if delivery failed
    """

    user_id: int = 0
    message_type: str = ""
    success: bool = True
    error: str | None = None


# --- Scheduler Command Events (for IPC) ---


@dataclass(frozen=True, slots=True)
class SchedulerCommand:
    """Command sent from main process to scheduler process.

    :ivar command_type: Type of command (RESCHEDULE, PAUSE, RESUME, SHUTDOWN)
    :ivar user_id: User ID if command is user-specific
    :ivar payload: Additional command data
    :ivar command_id: Unique ID for command tracking
    """

    command_type: str
    user_id: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    command_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True, slots=True)
class SchedulerResponse:
    """Response from scheduler process to main process.

    :ivar success: Whether the command was executed successfully
    :ivar command_id: ID of the command this responds to
    :ivar error: Error message if command failed
    :ivar data: Additional response data
    """

    success: bool
    command_id: str
    error: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
