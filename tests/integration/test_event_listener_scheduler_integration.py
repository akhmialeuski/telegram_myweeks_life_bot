"""Integration tests for scheduler event listener behavior.

These tests verify that user settings from the database are propagated to
scheduler jobs when settings-changed events are handled.
"""

from datetime import date, time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot.event_listeners import handle_user_settings_changed
from src.enums import WeekDay
from src.events.domain_events import UserSettingsChangedEvent
from src.services.container import ServiceContainer


@pytest.mark.integration
@pytest.mark.asyncio
class TestEventListenerSchedulerIntegration:
    """Integration tests for event listener to scheduler flow."""

    async def test_user_settings_change_uses_persisted_schedule(
        self,
        test_service_container: ServiceContainer,
    ) -> None:
        """Ensure scheduler trigger uses user's persisted day/time/timezone.

        This test verifies that when a `UserSettingsChangedEvent` occurs, the
        event listener fetches the complete user profile (including settings)
        and uses those specific settings to reschedule the notification job,
        rather than using default values.

        :param test_service_container: The service container fixture.
        :type test_service_container: ServiceContainer
        :return: None
        """
        # Arrange: Create a user with specific non-default notification settings
        user_service = test_service_container.user_service
        telegram_id = 401030178

        mock_user = MagicMock()
        mock_user.id = telegram_id
        mock_user.username = "integration_scheduler"
        mock_user.first_name = "Integration"
        mock_user.last_name = "User"

        await user_service.create_user_profile(
            user_info=mock_user,
            birth_date=date(year=1991, month=2, day=3),
            notifications=True,
            notifications_day=WeekDay.WEDNESDAY,
            notifications_time=time(hour=14, minute=30),
            timezone="Europe/Warsaw",
        )

        # Arrange: Mock the scheduler client to capture the schedule_job call
        scheduler_client = AsyncMock()
        scheduler_client.schedule_job.return_value = True

        container_for_listener = MagicMock()
        container_for_listener.get_scheduler_client.return_value = scheduler_client
        container_for_listener.get_user_service.return_value = user_service

        event = UserSettingsChangedEvent(
            user_id=telegram_id,
            setting_name="notifications_time",
        )

        # Act: Trigger the event listener
        with patch(
            target="src.bot.event_listeners.ServiceContainer",
            return_value=container_for_listener,
        ):
            await handle_user_settings_changed(event=event)

        # Assert: Verify schedule_job was called with the correct trigger params
        scheduler_client.schedule_job.assert_awaited_once()
        call_kwargs = scheduler_client.schedule_job.call_args.kwargs
        trigger = call_kwargs["trigger"]

        assert call_kwargs["job_id"] == f"notification_{telegram_id}"
        assert call_kwargs["user_id"] == telegram_id
        assert call_kwargs["job_type"] == "weekly_summary"

        # Verify specific settings were used (Wednesday=2, 14:30, Warsaw)
        assert trigger.day_of_week == 2
        assert trigger.hour == 14
        assert trigger.minute == 30
        assert trigger.timezone == "Europe/Warsaw"

    async def test_user_settings_change_to_monthly_updates_job_type(
        self,
        test_service_container: ServiceContainer,
    ) -> None:
        """Ensure job_type changes when frequency changes to monthly.

        :param test_service_container: The service container fixture.
        :type test_service_container: ServiceContainer
        :return: None
        """
        # Arrange
        user_service = test_service_container.user_service
        telegram_id = 401030179
        from src.enums import NotificationFrequency

        mock_user = MagicMock()
        mock_user.id = telegram_id
        mock_user.username = "monthly_test"
        mock_user.first_name = "Monthly"
        mock_user.last_name = "Test"

        await user_service.create_user_profile(
            user_info=mock_user,
            birth_date=date(year=1991, month=2, day=3),
            notifications=True,
            notification_frequency=NotificationFrequency.MONTHLY,
        )

        scheduler_client = AsyncMock()
        scheduler_client.schedule_job.return_value = True

        container_for_listener = MagicMock()
        container_for_listener.get_scheduler_client.return_value = scheduler_client
        container_for_listener.get_user_service.return_value = user_service

        event = UserSettingsChangedEvent(
            user_id=telegram_id,
            setting_name="notification_frequency",
        )

        # Act
        with patch(
            target="src.bot.event_listeners.ServiceContainer",
            return_value=container_for_listener,
        ):
            await handle_user_settings_changed(event=event)

        # Assert
        scheduler_client.schedule_job.assert_awaited_once()
        call_kwargs = scheduler_client.schedule_job.call_args.kwargs
        assert call_kwargs["job_type"] == "monthly_summary"
