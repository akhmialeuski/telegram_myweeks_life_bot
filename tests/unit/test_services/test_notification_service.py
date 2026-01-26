"""Unit tests for NotificationService.

Tests the NotificationService class which generates notification payloads
for weekly summaries and milestones.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.events.domain_events import NotificationPayload
from src.services.notification_service import (
    MESSAGE_TYPE_MILESTONE,
    MESSAGE_TYPE_WEEKLY_SUMMARY,
    NotificationService,
)


class TestNotificationService:
    """Test suite for NotificationService class."""

    @pytest.fixture
    def mock_user_service(self) -> AsyncMock:
        """Create mock user service.

        :returns: Mocked user service
        :rtype: AsyncMock
        """
        return AsyncMock()

    @pytest.fixture
    def mock_calculate_life_statistics(self) -> MagicMock:
        """Mock calculate_life_statistics function.

        :returns: Mocked function
        :rtype: MagicMock
        """
        stats_mock = MagicMock()
        stats_mock.age = 30
        stats_mock.life_expectancy = 80
        stats_mock.total_weeks_lived = 1560
        stats_mock.remaining_weeks = 2600
        stats_mock.total_weeks_expected = 4160
        stats_mock.percentage_lived = 0.375

        with patch(
            "src.services.notification_service.calculate_life_statistics",
            return_value=stats_mock,
        ) as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_use_locale(self) -> MagicMock:
        """Mock use_locale to control translations.

        :returns: Mocked pgettext function
        :rtype: MagicMock
        """
        mock_pgettext = MagicMock(
            side_effect=lambda c, m: f"pgettext_{c}_{m}" if c else m
        )
        with patch(
            "src.services.notification_service.use_locale",
            return_value=(None, None, mock_pgettext),
        ):
            yield mock_pgettext

    @pytest.fixture
    def service(
        self,
        mock_user_service: AsyncMock,
        mock_calculate_life_statistics: MagicMock,
    ) -> NotificationService:
        """Create NotificationService instance for testing.

        :param mock_user_service: Mocked user service
        :type mock_user_service: AsyncMock
        :param mock_calculate_life_statistics: Mocked calculator
        :type mock_calculate_life_statistics: MagicMock
        :returns: NotificationService instance
        :rtype: NotificationService
        """
        return NotificationService(
            user_service=mock_user_service,
        )

    @pytest.mark.asyncio
    async def test_generate_weekly_summary_success(
        self,
        service: NotificationService,
        mock_user_service: AsyncMock,
        mock_calculate_life_statistics: MagicMock,
    ) -> None:
        """Test successful generation of weekly summary.

        Verifies that a correct NotificationPayload is generated when
        user exists and has valid data.
        """
        user_id = 123
        mock_user = MagicMock()
        mock_user.birth_date = date(1990, 1, 1)
        mock_user.settings.language = "en"
        mock_user_service.get_user_profile.return_value = mock_user

        payload = await service.generate_weekly_summary(user_id)

        assert payload is not None
        assert isinstance(payload, NotificationPayload)
        assert payload.recipient_id == user_id
        assert payload.message_type == MESSAGE_TYPE_WEEKLY_SUMMARY
        assert payload.metadata["language"] == "en"
        assert payload.metadata["stats"]["age"] == 30

        # Verify life calculator was used
        mock_calculate_life_statistics.assert_called_once()
        # Verify call args
        call_args = mock_calculate_life_statistics.call_args
        assert call_args.kwargs["birth_date"] == mock_user.birth_date

    @pytest.mark.asyncio
    async def test_generate_weekly_summary_user_not_found(
        self,
        service: NotificationService,
        mock_user_service: AsyncMock,
    ) -> None:
        """Test generation when user is not found.

        Verifies that None is returned if user service returns None.
        """
        mock_user_service.get_user_profile.return_value = None

        payload = await service.generate_weekly_summary(123)

        assert payload is None

    @pytest.mark.asyncio
    async def test_generate_weekly_summary_no_birth_date(
        self,
        service: NotificationService,
        mock_user_service: AsyncMock,
    ) -> None:
        """Test generation when user has no birth date.

        Verifies that None is returned if user has no birth date set.
        """
        mock_user = MagicMock()
        mock_user.birth_date = None
        mock_user_service.get_user_profile.return_value = mock_user

        payload = await service.generate_weekly_summary(123)

        assert payload is None

    @pytest.mark.asyncio
    async def test_generate_weekly_summary_exception(
        self,
        service: NotificationService,
        mock_user_service: AsyncMock,
    ) -> None:
        """Test exception handling during generation.

        Verifies that exceptions are caught and logged, returning None.
        """
        mock_user_service.get_user_profile.side_effect = Exception("db error")

        with patch("src.services.notification_service.logger") as mock_logger:
            payload = await service.generate_weekly_summary(123)

            assert payload is None
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_milestone_notification_success(
        self,
        service: NotificationService,
        mock_user_service: AsyncMock,
    ) -> None:
        """Test successful generation of milestone notification.

        Verifies that a valid payload is returned for a milestone event.
        """
        user_id = 123
        mock_user = MagicMock()
        mock_user.settings.language = "en"
        mock_user_service.get_user_profile.return_value = mock_user

        payload = await service.generate_milestone_notification(
            user_id=user_id,
            milestone_type="weeks_lived",
            milestone_value=1000,
        )

        assert payload is not None
        assert payload.recipient_id == user_id
        assert payload.message_type == MESSAGE_TYPE_MILESTONE
        assert payload.metadata["milestone_type"] == "weeks_lived"
        assert payload.metadata["milestone_value"] == 1000

    @pytest.mark.asyncio
    async def test_generate_milestone_notification_user_not_found(
        self,
        service: NotificationService,
        mock_user_service: AsyncMock,
    ) -> None:
        """Test milestone generation when user is not found.

        Verifies that None is returned if user service returns None.
        """
        mock_user_service.get_user_profile.return_value = None

        payload = await service.generate_milestone_notification(
            user_id=123,
            milestone_type="weeks_lived",
            milestone_value=1000,
        )

        assert payload is None

    @pytest.mark.asyncio
    async def test_generate_milestone_notification_exception(
        self,
        service: NotificationService,
        mock_user_service: AsyncMock,
    ) -> None:
        """Test exception handling during milestone generation.

        Verifies that exceptions are caught and logged.
        """
        mock_user_service.get_user_profile.side_effect = Exception("db error")

        with patch("src.services.notification_service.logger") as mock_logger:
            payload = await service.generate_milestone_notification(
                user_id=123,
                milestone_type="weeks_lived",
                milestone_value=1000,
            )

            assert payload is None
            mock_logger.error.assert_called_once()
