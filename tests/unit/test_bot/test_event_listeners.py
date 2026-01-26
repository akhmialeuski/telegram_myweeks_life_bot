"""Unit tests for bot event listeners.

Tests the event handlers that bridge domain events to scheduler actions.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot.event_listeners import (
    handle_user_deleted,
    handle_user_settings_changed,
    register_event_listeners,
)
from src.contracts.scheduler_port_protocol import ScheduleTrigger
from src.events.domain_events import UserDeletedEvent, UserSettingsChangedEvent


class TestEventListeners:
    """Test suite for event listeners."""

    @pytest.fixture
    def mock_container(self):
        """Mock ServiceContainer."""
        with patch("src.bot.event_listeners.ServiceContainer") as mock_cls:
            container = MagicMock()
            mock_cls.return_value = container
            yield container

    @pytest.fixture
    def mock_client(self, mock_container):
        """Mock SchedulerClient."""
        client = AsyncMock()
        mock_container.get_scheduler_client.return_value = client
        return client

    @pytest.fixture
    def mock_user_service(self, mock_container):
        """Mock UserService."""
        service = AsyncMock()
        mock_container.get_user_service.return_value = service
        return service

    @pytest.mark.asyncio
    async def test_handle_settings_changed_client_unavailable(
        self,
        mock_container: MagicMock,
    ):
        """Test handling settings change when client is unavailable."""
        mock_container.get_scheduler_client.return_value = None
        event = UserSettingsChangedEvent(user_id=123, setting_name="birth_date")

        await handle_user_settings_changed(event)

        # Should return early without error
        mock_container.get_user_service.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_settings_changed_user_not_found(
        self,
        mock_client: AsyncMock,
        mock_user_service: AsyncMock,
    ):
        """Test handling settings change when user profile not found."""
        mock_user_service.get_user_profile.return_value = None
        event = UserSettingsChangedEvent(user_id=123, setting_name="birth_date")

        await handle_user_settings_changed(event)

        mock_client.schedule_job.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_settings_changed_success(
        self,
        mock_client: AsyncMock,
        mock_user_service: AsyncMock,
    ):
        """Test successful scheduling on settings change."""
        mock_user_service.get_user_profile.return_value = MagicMock()
        mock_client.schedule_job.return_value = True
        event = UserSettingsChangedEvent(user_id=123, setting_name="birth_date")

        await handle_user_settings_changed(event)

        mock_client.schedule_job.assert_awaited_once()
        call_kwargs = mock_client.schedule_job.call_args[1]
        assert call_kwargs["job_id"] == "weekly_123"
        assert call_kwargs["user_id"] == 123
        assert isinstance(call_kwargs["trigger"], ScheduleTrigger)

    @pytest.mark.asyncio
    async def test_handle_settings_changed_schedule_failure(
        self,
        mock_client: AsyncMock,
        mock_user_service: AsyncMock,
    ):
        """Test handling schedule failure (logs error)."""
        mock_user_service.get_user_profile.return_value = MagicMock()
        mock_client.schedule_job.return_value = False
        event = UserSettingsChangedEvent(user_id=123, setting_name="birth_date")

        # Should complete without raising exception
        await handle_user_settings_changed(event)

        mock_client.schedule_job.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_user_deleted_client_unavailable(
        self,
        mock_container: MagicMock,
    ):
        """Test handling user deletion when client is unavailable."""
        mock_container.get_scheduler_client.return_value = None
        event = UserDeletedEvent(user_id=123)

        await handle_user_deleted(event)
        # Should return early

    @pytest.mark.asyncio
    async def test_handle_user_deleted_success(
        self,
        mock_client: AsyncMock,
    ):
        """Test successful job removal on user deletion."""
        mock_client.remove_job.return_value = True
        event = UserDeletedEvent(user_id=123)

        await handle_user_deleted(event)

        mock_client.remove_job.assert_awaited_once_with("weekly_123")

    @pytest.mark.asyncio
    async def test_handle_user_deleted_not_found(
        self,
        mock_client: AsyncMock,
    ):
        """Test job removal when job doesn't exist."""
        mock_client.remove_job.return_value = False
        event = UserDeletedEvent(user_id=123)

        await handle_user_deleted(event)

        mock_client.remove_job.assert_awaited_once()

    def test_register_event_listeners(
        self,
        mock_container: MagicMock,
    ):
        """Test registration of listeners."""
        event_bus = MagicMock()
        mock_container.get_event_bus.return_value = event_bus

        register_event_listeners(mock_container)

        assert event_bus.subscribe.call_count == 2
        # Verify subscriptions
        calls = event_bus.subscribe.call_args_list
        assert calls[0][1]["event_type"] == UserSettingsChangedEvent
        assert calls[0][1]["handler"] == handle_user_settings_changed
        assert calls[1][1]["event_type"] == UserDeletedEvent
        assert calls[1][1]["handler"] == handle_user_deleted
