"""Unit tests for scheduler job restoration in bot application."""

from copy import deepcopy
from datetime import datetime, time
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bot.application import LifeWeeksBot
from src.contracts.scheduler_port_protocol import ScheduleTrigger
from src.core.dtos import UserProfileDTO, UserSettingsDTO, UserSubscriptionDTO
from src.enums import SubscriptionType, WeekDay


@pytest.fixture
def mock_container():
    """Mock service container."""
    container = MagicMock()
    container.user_service = AsyncMock()
    return container


@pytest.fixture
def mock_scheduler_client():
    """Mock scheduler client."""
    client = AsyncMock()
    return client


@pytest.fixture
def bot(mock_container, mock_scheduler_client):
    """Create bot instance with mocks."""
    bot = LifeWeeksBot(services=mock_container)
    bot._scheduler_client = mock_scheduler_client
    return bot


@pytest.mark.asyncio
class TestSchedulerRestoration:
    """Tests for _restore_scheduled_jobs method."""

    async def test_restore_jobs_success(
        self, bot, mock_container, mock_scheduler_client
    ):
        """Test successful restoration of scheduled jobs."""
        # Setup mock users
        user_enabled = UserProfileDTO(
            telegram_id=123,
            username="enabled",
            first_name="Test",
            last_name="Enabled",
            created_at=datetime.now(),
            settings=UserSettingsDTO(
                birth_date=datetime.now().date(),
                notifications=True,
                notifications_day=WeekDay.MONDAY,
                notifications_time=time(9, 0),
                life_expectancy=80,
                timezone="UTC",
                language="en",
            ),
            subscription=UserSubscriptionDTO(
                subscription_type=SubscriptionType.BASIC,
                is_active=True,
                expires_at=datetime.now(),
            ),
        )

        user_disabled = deepcopy(user_enabled)
        object.__setattr__(user_disabled, "telegram_id", 456)
        object.__setattr__(user_disabled.settings, "notifications", False)

        user_inactive = deepcopy(user_enabled)
        object.__setattr__(user_inactive, "telegram_id", 789)
        object.__setattr__(user_inactive.subscription, "is_active", False)

        mock_container.user_service.get_all_users.return_value = [
            user_enabled,
            user_disabled,
            user_inactive,
        ]

        # Execute
        await bot._restore_scheduled_jobs()

        # Verify
        # Should only be called once for user_enabled
        assert mock_scheduler_client.schedule_job.call_count == 1

        call_args = mock_scheduler_client.schedule_job.call_args
        assert call_args is not None
        _, kwargs = call_args

        assert kwargs["user_id"] == 123
        assert kwargs["job_id"] == "weekly_123"
        assert kwargs["job_type"] == "weekly_summary"

        trigger = kwargs["trigger"]
        assert isinstance(trigger, ScheduleTrigger)
        assert trigger.day_of_week == 0  # Monday
        assert trigger.hour == 9
        assert trigger.minute == 0
        assert trigger.timezone == "UTC"

    async def test_restore_jobs_no_client(self, bot, mock_container):
        """Test restoration skips if client is missing."""
        bot._scheduler_client = None

        await bot._restore_scheduled_jobs()

        mock_container.user_service.get_all_users.assert_not_called()

    async def test_restore_jobs_handle_error(
        self, bot, mock_container, mock_scheduler_client
    ):
        """Test single job failure doesn't stop restoration."""
        user1 = UserProfileDTO(
            telegram_id=1,
            username="u1",
            first_name="U",
            last_name="1",
            created_at=datetime.now(),
            settings=UserSettingsDTO(
                birth_date=datetime.now().date(),
                notifications=True,
                notifications_day=WeekDay.MONDAY,
                notifications_time=time(9, 0),
                life_expectancy=80,
                timezone="UTC",
                language="en",
            ),
            subscription=UserSubscriptionDTO(
                subscription_type=SubscriptionType.BASIC,
                is_active=True,
                expires_at=datetime.now(),
            ),
        )
        user2 = deepcopy(user1)
        object.__setattr__(user2, "telegram_id", 2)

        mock_container.user_service.get_all_users.return_value = [user1, user2]

        # First call fails, second succeeds
        mock_scheduler_client.schedule_job.side_effect = [Exception("Fail"), None]

        await bot._restore_scheduled_jobs()

        assert mock_scheduler_client.schedule_job.call_count == 2
