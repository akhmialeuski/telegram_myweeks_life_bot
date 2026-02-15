"""Unit tests for scheduler jobs.

Tests the execute_notification_job function and its error handling paths.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.scheduler.jobs import execute_notification_job


class TestSchedulerJobs:
    """Test suite for scheduler jobs."""

    @pytest.mark.asyncio
    async def test_execute_notification_job_success(self):
        """Test successful execution of notification job."""
        user_id = 123
        message_type = "weekly_summary"

        with patch("src.scheduler.jobs.ServiceContainer") as mock_container:
            mock_notification_service = MagicMock()
            mock_notification_service.generate_summary = AsyncMock(
                return_value="payload"
            )

            mock_gateway = MagicMock()
            mock_gateway.send_notification = AsyncMock(
                return_value=MagicMock(success=True)
            )

            mock_container.return_value.get_notification_service.return_value = (
                mock_notification_service
            )
            mock_container.return_value.get_notification_gateway.return_value = (
                mock_gateway
            )

            await execute_notification_job(user_id=user_id, message_type=message_type)

            mock_notification_service.generate_summary.assert_called_once_with(
                user_id=user_id, message_type=message_type
            )
            mock_gateway.send_notification.assert_called_once_with("payload")

    @pytest.mark.asyncio
    async def test_execute_notification_job_no_payload(self):
        """Test notification job when no payload is generated."""
        user_id = 123

        with patch("src.scheduler.jobs.ServiceContainer") as mock_container:
            mock_notification_service = MagicMock()
            mock_notification_service.generate_summary = AsyncMock(return_value=None)

            mock_container.return_value.get_notification_service.return_value = (
                mock_notification_service
            )

            await execute_notification_job(
                user_id=user_id, message_type="weekly_summary"
            )

            mock_notification_service.generate_summary.assert_called_once()
            # Gateway should not be called

    @pytest.mark.asyncio
    async def test_execute_notification_job_unknown_type(self):
        """Test notification job with unknown message type."""
        await execute_notification_job(user_id=123, message_type="unknown")
        # Should just log warning and return

    @pytest.mark.asyncio
    async def test_execute_notification_job_send_failure(self):
        """Test notification job when sending fails."""
        user_id = 123

        with patch("src.scheduler.jobs.ServiceContainer") as mock_container:
            mock_notification_service = MagicMock()
            mock_notification_service.generate_summary = AsyncMock(
                return_value="payload"
            )

            mock_gateway = MagicMock()
            mock_gateway.send_notification = AsyncMock(
                return_value=MagicMock(success=False, error="API Error")
            )

            mock_container.return_value.get_notification_service.return_value = (
                mock_notification_service
            )
            mock_container.return_value.get_notification_gateway.return_value = (
                mock_gateway
            )

            await execute_notification_job(
                user_id=user_id, message_type="weekly_summary"
            )

            assert mock_gateway.send_notification.called

    @pytest.mark.asyncio
    async def test_execute_notification_job_exception(self):
        """Test notification job handling general exception."""
        user_id = 123

        with patch(
            "src.scheduler.jobs.ServiceContainer",
            side_effect=Exception("Container error"),
        ):
            # Should catch and log
            await execute_notification_job(
                user_id=user_id, message_type="weekly_summary"
            )

    @pytest.mark.asyncio
    async def test_execute_scheduler_job_wrapper(self):
        """Test the execute_scheduler_job_wrapper function."""
        from src.scheduler.jobs import execute_scheduler_job_wrapper

        execute_scheduler_job_wrapper(job_type="test", kwargs={})
