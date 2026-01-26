"""Tests for the EventBus and domain events.

This module contains unit tests for the EventBus publish/subscribe
pattern and domain event dataclasses.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.events import (
    DeliveryResult,
    DomainEvent,
    EventBus,
    NotificationPayload,
    NotificationSentEvent,
    SchedulerCommand,
    ScheduleRecalculationRequestedEvent,
    SchedulerResponse,
    UserDeletedEvent,
    UserRegisteredEvent,
    UserSettingsChangedEvent,
)

# Test constants
TEST_USER_ID = 123456789
TEST_CORRELATION_ID = "test-correlation-id"


class TestNotificationPayload:
    """Test class for NotificationPayload dataclass."""

    def test_creates_with_required_fields(self) -> None:
        """Test creating payload with required fields only."""
        payload = NotificationPayload(
            recipient_id=TEST_USER_ID,
            message_type="weekly_summary",
            title="Your Week",
            body="Life statistics here",
        )

        assert payload.recipient_id == TEST_USER_ID
        assert payload.message_type == "weekly_summary"
        assert payload.title == "Your Week"
        assert payload.body == "Life statistics here"
        assert payload.metadata == {}
        assert isinstance(payload.scheduled_at, datetime)

    def test_creates_with_all_fields(self) -> None:
        """Test creating payload with all fields."""
        scheduled = datetime(2024, 1, 15, 10, 30)
        payload = NotificationPayload(
            recipient_id=TEST_USER_ID,
            message_type="milestone",
            title="Milestone",
            body="Achievement unlocked",
            metadata={"milestone_type": "half_life"},
            scheduled_at=scheduled,
        )

        assert payload.metadata == {"milestone_type": "half_life"}
        assert payload.scheduled_at == scheduled

    def test_is_immutable(self) -> None:
        """Test that payload is frozen and cannot be modified."""
        payload = NotificationPayload(
            recipient_id=TEST_USER_ID,
            message_type="test",
            title="Test",
            body="Test body",
        )

        with pytest.raises(AttributeError):
            payload.recipient_id = 999  # type: ignore[misc]


class TestDeliveryResult:
    """Test class for DeliveryResult dataclass."""

    def test_creates_success_result(self) -> None:
        """Test creating successful delivery result."""
        result = DeliveryResult(
            success=True,
            recipient_id=TEST_USER_ID,
        )

        assert result.success is True
        assert result.recipient_id == TEST_USER_ID
        assert result.error is None
        assert isinstance(result.delivered_at, datetime)

    def test_creates_failure_result(self) -> None:
        """Test creating failed delivery result."""
        result = DeliveryResult(
            success=False,
            recipient_id=TEST_USER_ID,
            error="Network timeout",
        )

        assert result.success is False
        assert result.error == "Network timeout"


class TestDomainEvents:
    """Test class for domain event dataclasses."""

    def test_domain_event_has_timestamp_and_correlation_id(self) -> None:
        """Test base DomainEvent provides timestamp and correlation_id."""
        event = DomainEvent()

        assert isinstance(event.timestamp, datetime)
        assert isinstance(event.correlation_id, str)
        assert len(event.correlation_id) > 0

    def test_user_settings_changed_event(self) -> None:
        """Test UserSettingsChangedEvent creation."""
        event = UserSettingsChangedEvent(
            user_id=TEST_USER_ID,
            setting_name="notifications_time",
            old_value="10:00",
            new_value="14:00",
        )

        assert event.user_id == TEST_USER_ID
        assert event.setting_name == "notifications_time"
        assert event.old_value == "10:00"
        assert event.new_value == "14:00"

    def test_user_registered_event(self) -> None:
        """Test UserRegisteredEvent creation."""
        event = UserRegisteredEvent(user_id=TEST_USER_ID)

        assert event.user_id == TEST_USER_ID

    def test_user_deleted_event(self) -> None:
        """Test UserDeletedEvent creation."""
        event = UserDeletedEvent(user_id=TEST_USER_ID)

        assert event.user_id == TEST_USER_ID

    def test_schedule_recalculation_requested_event(self) -> None:
        """Test ScheduleRecalculationRequestedEvent creation."""
        event = ScheduleRecalculationRequestedEvent(user_id=TEST_USER_ID)

        assert event.user_id == TEST_USER_ID

    def test_notification_sent_event(self) -> None:
        """Test NotificationSentEvent creation."""
        event = NotificationSentEvent(
            user_id=TEST_USER_ID,
            message_type="weekly_summary",
            success=True,
        )

        assert event.user_id == TEST_USER_ID
        assert event.message_type == "weekly_summary"
        assert event.success is True
        assert event.error is None

    def test_notification_sent_event_with_error(self) -> None:
        """Test NotificationSentEvent with failure."""
        event = NotificationSentEvent(
            user_id=TEST_USER_ID,
            message_type="weekly_summary",
            success=False,
            error="User blocked bot",
        )

        assert event.success is False
        assert event.error == "User blocked bot"


class TestSchedulerCommands:
    """Test class for IPC command/response dataclasses."""

    def test_scheduler_command_creation(self) -> None:
        """Test SchedulerCommand creation."""
        command = SchedulerCommand(
            command_type="RESCHEDULE",
            user_id=TEST_USER_ID,
        )

        assert command.command_type == "RESCHEDULE"
        assert command.user_id == TEST_USER_ID
        assert command.payload == {}
        assert len(command.command_id) > 0

    def test_scheduler_response_success(self) -> None:
        """Test SchedulerResponse for success."""
        response = SchedulerResponse(
            success=True,
            command_id="cmd-123",
        )

        assert response.success is True
        assert response.command_id == "cmd-123"
        assert response.error is None

    def test_scheduler_response_failure(self) -> None:
        """Test SchedulerResponse for failure."""
        response = SchedulerResponse(
            success=False,
            command_id="cmd-123",
            error="Job not found",
        )

        assert response.success is False
        assert response.error == "Job not found"


class TestEventBus:
    """Test class for EventBus functionality."""

    @pytest.fixture
    def event_bus(self) -> EventBus:
        """Provide fresh EventBus instance for each test."""
        return EventBus()

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, event_bus: EventBus) -> None:
        """Test subscribing handler and publishing events."""
        handler_calls: list[UserSettingsChangedEvent] = []

        async def handler(event: UserSettingsChangedEvent) -> None:
            handler_calls.append(event)

        event_bus.subscribe(
            event_type=UserSettingsChangedEvent,
            handler=handler,
        )

        event = UserSettingsChangedEvent(user_id=TEST_USER_ID, setting_name="test")
        await event_bus.publish(event=event)

        assert len(handler_calls) == 1
        assert handler_calls[0].user_id == TEST_USER_ID

    @pytest.mark.asyncio
    async def test_multiple_handlers_same_event(self, event_bus: EventBus) -> None:
        """Test multiple handlers for same event type."""
        calls: list[str] = []

        async def handler1(event: UserRegisteredEvent) -> None:
            calls.append("handler1")

        async def handler2(event: UserRegisteredEvent) -> None:
            calls.append("handler2")

        event_bus.subscribe(event_type=UserRegisteredEvent, handler=handler1)
        event_bus.subscribe(event_type=UserRegisteredEvent, handler=handler2)

        await event_bus.publish(event=UserRegisteredEvent(user_id=TEST_USER_ID))

        assert calls == ["handler1", "handler2"]

    @pytest.mark.asyncio
    async def test_no_handlers_for_event_type(self, event_bus: EventBus) -> None:
        """Test publishing event with no handlers registered."""
        # Should not raise, just log debug message
        await event_bus.publish(event=UserDeletedEvent(user_id=TEST_USER_ID))

    @pytest.mark.asyncio
    @patch("src.events.event_bus.logger")
    async def test_handler_error_is_logged(
        self,
        mock_logger: MagicMock,
        event_bus: EventBus,
    ) -> None:
        """Test that handler errors are logged but don't stop other handlers."""
        calls: list[str] = []

        async def failing_handler(event: UserRegisteredEvent) -> None:
            raise ValueError("Handler failed")

        async def success_handler(event: UserRegisteredEvent) -> None:
            calls.append("success")

        event_bus.subscribe(event_type=UserRegisteredEvent, handler=failing_handler)
        event_bus.subscribe(event_type=UserRegisteredEvent, handler=success_handler)

        await event_bus.publish(event=UserRegisteredEvent(user_id=TEST_USER_ID))

        # Second handler should still be called
        assert calls == ["success"]
        # Error should be logged
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_unsubscribe_handler(self, event_bus: EventBus) -> None:
        """Test unsubscribing handler stops receiving events."""
        calls: list[int] = []

        async def handler(event: UserRegisteredEvent) -> None:
            calls.append(event.user_id)

        event_bus.subscribe(event_type=UserRegisteredEvent, handler=handler)
        await event_bus.publish(event=UserRegisteredEvent(user_id=1))

        event_bus.unsubscribe(event_type=UserRegisteredEvent, handler=handler)
        await event_bus.publish(event=UserRegisteredEvent(user_id=2))

        assert calls == [1]

    @pytest.mark.asyncio
    async def test_clear_removes_all_handlers(self, event_bus: EventBus) -> None:
        """Test clear() removes all registered handlers."""
        handler = AsyncMock()

        event_bus.subscribe(event_type=UserRegisteredEvent, handler=handler)
        event_bus.subscribe(event_type=UserDeletedEvent, handler=handler)

        event_bus.clear()

        await event_bus.publish(event=UserRegisteredEvent(user_id=TEST_USER_ID))
        await event_bus.publish(event=UserDeletedEvent(user_id=TEST_USER_ID))

        handler.assert_not_awaited()

    def test_get_handlers_returns_copy(self, event_bus: EventBus) -> None:
        """Test get_handlers returns a copy of handler list."""

        async def handler(event: UserRegisteredEvent) -> None:
            pass

        event_bus.subscribe(event_type=UserRegisteredEvent, handler=handler)

        handlers = event_bus.get_handlers(event_type=UserRegisteredEvent)
        handlers.clear()

        # Original list should not be affected
        assert len(event_bus.get_handlers(event_type=UserRegisteredEvent)) == 1

    @patch("src.events.event_bus.logger")
    def test_unsubscribe_nonexistent_handler_logs_warning(
        self,
        mock_logger: MagicMock,
        event_bus: EventBus,
    ) -> None:
        """Test unsubscribing a handler that was never subscribed.

        This test verifies that attempting to unsubscribe a handler
        that is not registered logs a warning message.
        """

        async def handler(event: UserRegisteredEvent) -> None:
            pass

        async def other_handler(event: UserRegisteredEvent) -> None:
            pass

        # Subscribe only one handler
        event_bus.subscribe(event_type=UserRegisteredEvent, handler=handler)

        # Try to unsubscribe a different handler that was never subscribed
        event_bus.unsubscribe(event_type=UserRegisteredEvent, handler=other_handler)

        # Should log a warning
        mock_logger.warning.assert_called_once()
        assert "other_handler" in str(mock_logger.warning.call_args)
