"""Integration tests for scheduler job restoration.

This module tests the scheduler job restoration functionality using a real
database and actual bot application. Only the scheduler client is mocked to
avoid spawning real scheduler processes.

Test Scenarios:
    - Bot restores scheduled jobs from database on startup
"""

from datetime import date, time
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bot.application import LifeWeeksBot
from src.enums import SubscriptionType, WeekDay
from src.services.container import ServiceContainer


@pytest.mark.integration
@pytest.mark.asyncio
class TestSchedulerJobRestoration:
    """Integration tests for scheduler job restoration on bot startup.

    These tests verify the end-to-end job restoration process including:
    - Fetching users from real database
    - Filtering users with active notifications and subscriptions
    - Scheduling jobs via scheduler client
    - Correct job parameters (user_id, job_id, trigger configuration)
    """

    async def test_bot_restores_jobs_on_startup(
        self,
        test_service_container: ServiceContainer,
    ) -> None:
        """Test that bot restores scheduled jobs from database on startup.

        Preconditions:
            - User exists in database with notifications enabled
            - User has active subscription
            - User has notification schedule configured (Monday, 9:00 AM UTC)

        Test Steps:
            1. Create user profile with notifications enabled
               Expected: User profile created in database
               Response: User profile with notification settings

            2. Initialize bot with test container
               Expected: Bot instance created successfully

            3. Mock scheduler client and trigger job restoration
               Expected: Bot calls scheduler client to schedule job
               Response: schedule_job called with correct parameters

        Post-conditions:
            - Scheduler client received schedule_job call
            - Job parameters match user's notification settings

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :returns: None
        """
        # --- ARRANGE: Create user with enabled notifications ---
        user_service = test_service_container.user_service
        telegram_id = 123456

        # Create mock Telegram user
        mock_user = MagicMock()
        mock_user.id = telegram_id
        mock_user.username = "test_scheduler"
        mock_user.first_name = "Test"
        mock_user.last_name = "Scheduler"

        # Create user profile with notifications enabled
        await user_service.create_user_profile(
            user_info=mock_user,
            birth_date=date(1990, 1, 1),
            subscription_type=SubscriptionType.BASIC,
            notifications=True,
            notifications_day=WeekDay.MONDAY,
            notifications_time=time(9, 0),
            life_expectancy=80,
            timezone="UTC",
        )

        # --- ARRANGE: Initialize Bot ---
        bot = LifeWeeksBot(services=test_service_container)

        # --- ARRANGE: Mock Scheduler Client ---
        mock_scheduler_client = AsyncMock()
        bot._scheduler_client = mock_scheduler_client

        # --- ACT: Trigger Restoration ---
        await bot._restore_scheduled_jobs()

        # --- ASSERT: Verify schedule_job was called ---
        mock_scheduler_client.schedule_job.assert_awaited_once()

        call_args = mock_scheduler_client.schedule_job.call_args
        assert call_args is not None, "schedule_job should be called"
        _, kwargs = call_args

        # --- ASSERT: Verify job parameters ---
        assert kwargs["user_id"] == telegram_id, "User ID should match"
        assert kwargs["job_id"] == f"weekly_{telegram_id}", "Job ID should be correct"
        assert kwargs["job_type"] == "weekly_summary", "Job type should be correct"

        # --- ASSERT: Verify trigger configuration ---
        trigger = kwargs["trigger"]
        assert trigger.day_of_week == 0, "Day of week should be Monday (0)"
        assert trigger.hour == 9, "Hour should be 9"
        assert trigger.minute == 0, "Minute should be 0"
