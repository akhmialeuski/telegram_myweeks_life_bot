"""Tests for SchedulerWorker.

This module contains unit tests for the SchedulerWorker class,
verifying IPC command handling and lifecycle management.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.contracts.scheduler_port_protocol import SchedulerPortProtocol
from src.scheduler.commands import (
    SchedulerCommand,
    SchedulerCommandType,
    SchedulerResponse,
)
from src.scheduler.worker import SchedulerWorker


class TestSchedulerWorker:
    """Test class for SchedulerWorker."""

    @pytest.fixture
    def mock_command_queue(self) -> MagicMock:
        """Provide mock command Queue."""
        return MagicMock()

    @pytest.fixture
    def mock_response_queue(self) -> MagicMock:
        """Provide mock response Queue."""
        return MagicMock()

    @pytest.fixture
    def mock_scheduler(self) -> MagicMock:
        """Provide mock SchedulerPortProtocol."""
        scheduler = MagicMock(spec=SchedulerPortProtocol)
        scheduler.is_running = False
        return scheduler

    @pytest.fixture
    def worker(
        self,
        mock_command_queue: MagicMock,
        mock_response_queue: MagicMock,
        mock_scheduler: MagicMock,
    ) -> SchedulerWorker:
        """Provide SchedulerWorker instance."""
        return SchedulerWorker(
            command_queue=mock_command_queue,
            response_queue=mock_response_queue,
            scheduler=mock_scheduler,
        )

    def test_init_sets_up_queues_and_scheduler(
        self,
        worker: SchedulerWorker,
        mock_command_queue: MagicMock,
        mock_response_queue: MagicMock,
        mock_scheduler: MagicMock,
    ) -> None:
        """Test initialization stores queues and scheduler."""
        assert worker._command_queue == mock_command_queue
        assert worker._response_queue == mock_response_queue
        assert worker._scheduler == mock_scheduler
        assert worker._running is False

    @pytest.mark.asyncio
    async def test_process_command_schedule_job(
        self,
        worker: SchedulerWorker,
        mock_scheduler: MagicMock,
        mock_response_queue: MagicMock,
    ) -> None:
        """Test processing SCHEDULE_JOB command."""
        command = SchedulerCommand(
            id="cmd1",
            type=SchedulerCommandType.SCHEDULE_JOB,
            payload={"job_data": "dummy"},
        )

        # Mock handle_schedule_job since strict implementation is pending
        with patch.object(worker, "_handle_schedule_job") as mock_handle:
            await worker._process_command(command)

            mock_handle.assert_called_once_with({"job_data": "dummy"})

            mock_response_queue.put.assert_called_once()
            response = mock_response_queue.put.call_args[0][0]
            assert isinstance(response, SchedulerResponse)
            assert response.command_id == "cmd1"
            assert response.success is True

    @pytest.mark.asyncio
    async def test_process_command_remove_job_success(
        self,
        worker: SchedulerWorker,
        mock_scheduler: MagicMock,
        mock_response_queue: MagicMock,
    ) -> None:
        """Test processing REMOVE_JOB command successfully."""
        mock_scheduler.remove_job.return_value = True
        command = SchedulerCommand(
            id="cmd1",
            type=SchedulerCommandType.REMOVE_JOB,
            payload={"job_id": "job123"},
        )

        await worker._process_command(command)

        mock_scheduler.remove_job.assert_called_once_with("job123")

        mock_response_queue.put.assert_called_once()
        response = mock_response_queue.put.call_args[0][0]
        assert response.success is True

    @pytest.mark.asyncio
    async def test_process_command_remove_job_failure(
        self,
        worker: SchedulerWorker,
        mock_scheduler: MagicMock,
        mock_response_queue: MagicMock,
    ) -> None:
        """Test processing REMOVE_JOB command when job not found."""
        mock_scheduler.remove_job.return_value = False
        command = SchedulerCommand(
            id="cmd1",
            type=SchedulerCommandType.REMOVE_JOB,
            payload={"job_id": "job123"},
        )

        await worker._process_command(command)

        mock_response_queue.put.assert_called_once()
        response = mock_response_queue.put.call_args[0][0]
        assert response.success is False
        assert "not found" in response.error

    @pytest.mark.asyncio
    async def test_process_command_get_job(
        self,
        worker: SchedulerWorker,
        mock_scheduler: MagicMock,
        mock_response_queue: MagicMock,
    ) -> None:
        """Test processing GET_JOB command."""
        mock_scheduler.get_job.return_value = "job_info_obj"
        command = SchedulerCommand(
            id="cmd1",
            type=SchedulerCommandType.GET_JOB,
            payload={"job_id": "job123"},
        )

        await worker._process_command(command)

        mock_scheduler.get_job.assert_called_once_with("job123")

        mock_response_queue.put.assert_called_once()
        response = mock_response_queue.put.call_args[0][0]
        assert response.success is True
        assert response.data == "job_info_obj"

    @pytest.mark.asyncio
    async def test_process_command_health_check(
        self,
        worker: SchedulerWorker,
        mock_scheduler: MagicMock,
        mock_response_queue: MagicMock,
    ) -> None:
        """Test processing HEALTH_CHECK command."""
        mock_scheduler.is_running = True
        command = SchedulerCommand(
            id="cmd1",
            type=SchedulerCommandType.HEALTH_CHECK,
        )

        await worker._process_command(command)

        mock_response_queue.put.assert_called_once()
        response = mock_response_queue.put.call_args[0][0]
        assert response.success is True
        assert response.data["running"] is True

    @pytest.mark.asyncio
    async def test_process_command_shutdown(
        self,
        worker: SchedulerWorker,
        mock_response_queue: MagicMock,
    ) -> None:
        """Test processing SHUTDOWN command."""
        worker._running = True
        command = SchedulerCommand(
            id="cmd1",
            type=SchedulerCommandType.SHUTDOWN,
        )

        await worker._process_command(command)

        assert worker._running is False
        assert mock_response_queue.put.called

    def test_handle_shutdown_signal(self, worker: SchedulerWorker) -> None:
        """Test shutdown signal handling."""
        worker._running = True
        worker._handle_shutdown_signal(15, None)
        assert worker._running is False
