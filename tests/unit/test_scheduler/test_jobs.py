"""Unit tests for scheduler jobs execution.

Tests the execution logic of notification jobs under various conditions,
including success, validation failures, and messaging errors.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.scheduler.jobs import execute_notification_job, execute_scheduler_job_wrapper


class TestSchedulerJobs:
    """Test suite for scheduler jobs."""

    @pytest.fixture
    def mock_container(self):
        """Mock ServiceContainer."""
        with patch("src.scheduler.jobs.ServiceContainer") as mock_cls:
            mock_container = MagicMock()
            mock_cls.return_value = mock_container
            yield mock_container

    @pytest.fixture
    def mock_notification_service(self, mock_container):
        """Mock NotificationService."""
        service = AsyncMock()
        mock_container.get_notification_service.return_value = service
        return service

    @pytest.fixture
    def mock_gateway(self, mock_container):
        """Mock NotificationGateway."""
        gateway = AsyncMock()
        mock_container.get_notification_gateway.return_value = gateway
        return gateway

    @pytest.mark.asyncio
    async def test_execute_notification_job_success(
        self,
        mock_notification_service: AsyncMock,
        mock_gateway: AsyncMock,
    ):
        """Test successful weekly summary execution."""
        mock_notification_service.generate_weekly_summary.return_value = "payload"
        mock_gateway.send_notification.return_value.success = True

        await execute_notification_job(user_id=123, message_type="weekly_summary")

        mock_notification_service.generate_weekly_summary.assert_awaited_once_with(123)
        mock_gateway.send_notification.assert_awaited_once_with("payload")

    @pytest.mark.asyncio
    async def test_execute_notification_job_unknown_type(
        self,
        mock_notification_service: AsyncMock,
        mock_gateway: AsyncMock,
    ):
        """Test execution with unknown message type."""
        await execute_notification_job(user_id=123, message_type="unknown")

        mock_notification_service.generate_weekly_summary.assert_not_called()
        mock_gateway.send_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_notification_job_no_payload(
        self,
        mock_notification_service: AsyncMock,
        mock_gateway: AsyncMock,
    ):
        """Test execution when payload generation returns None."""
        mock_notification_service.generate_weekly_summary.return_value = None

        await execute_notification_job(user_id=123, message_type="weekly_summary")

        mock_notification_service.generate_weekly_summary.assert_awaited_once_with(123)
        mock_gateway.send_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_notification_job_send_validation_failure(
        self,
        mock_notification_service: AsyncMock,
        mock_gateway: AsyncMock,
    ):
        """Test execution when sending fails safely (log error)."""
        mock_notification_service.generate_weekly_summary.return_value = "payload"
        mock_gateway.send_notification.return_value.success = False
        mock_gateway.send_notification.return_value.error = "Sending failed"

        # Should not raise exception, just log error
        await execute_notification_job(user_id=123, message_type="weekly_summary")

        mock_gateway.send_notification.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_notification_job_exception_handling(
        self,
        mock_container: MagicMock,
    ):
        """Test validation of exception handling during execution."""
        # Setup container to raise exception
        mock_container.get_notification_service.side_effect = Exception(
            "Critical failure"
        )

        # Should catch and log exception
        await execute_notification_job(user_id=123)

    def test_execute_scheduler_job_wrapper(self):
        """Test execution wrapper function."""
        # Simply verifying it runs without error as it's a pass-through/placeholder
        execute_scheduler_job_wrapper(job_type="test", kwargs={"arg": 1})
