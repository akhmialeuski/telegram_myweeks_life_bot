"""Unit tests for scheduler worker.

Tests the SchedulerWorker class for process lifecycle, command handling,
and integration with the underlying scheduler adapter.
"""

import signal
from unittest.mock import MagicMock, patch

import pytest

from src.contracts.scheduler_port_protocol import SchedulerPortProtocol, ScheduleTrigger
from src.scheduler.commands import (
    SchedulerCommand,
    SchedulerCommandType,
)
from src.scheduler.worker import SchedulerWorker


class TestSchedulerWorker:
    """Test suite for SchedulerWorker class."""

    @pytest.fixture
    def mock_queues(self):
        """Create mock queues."""
        cmd_queue = MagicMock()
        resp_queue = MagicMock()
        return cmd_queue, resp_queue

    @pytest.fixture
    def mock_scheduler(self):
        """Create mock scheduler."""
        scheduler = MagicMock(spec=SchedulerPortProtocol)
        scheduler.start = MagicMock()
        scheduler.shutdown = MagicMock()
        scheduler.is_running = True
        return scheduler

    @pytest.fixture
    def worker(self, mock_queues, mock_scheduler):
        """Create SchedulerWorker instance."""
        cmd_queue, resp_queue = mock_queues
        return SchedulerWorker(
            command_queue=cmd_queue, response_queue=resp_queue, scheduler=mock_scheduler
        )

    def test_init_defaults(self, mock_queues):
        """Test initialization with defaults."""
        cmd_queue, resp_queue = mock_queues
        with patch("src.scheduler.worker.APSchedulerAdapter") as mock_adapter:
            worker = SchedulerWorker(command_queue=cmd_queue, response_queue=resp_queue)
            assert worker._scheduler == mock_adapter.return_value

    def test_run_exception_handling(self, worker):
        """Test run method exception handling."""
        # Mock signal to avoid actual signal handlers
        with patch("signal.signal"):
            # Mock asyncio.new_event_loop to raise exception immediately
            with patch(
                "asyncio.new_event_loop", side_effect=Exception("Startup failed")
            ):
                worker.run()
            # If no crash, exception was caught

    @patch("src.scheduler.worker.ServiceContainer")
    @pytest.mark.asyncio
    async def test_process_command_schedule_job(
        self, mock_container, worker, mock_scheduler
    ):
        """Test processing SCHEDULE_JOB command."""
        trigger_data = {
            "day_of_week": "mon",
            "hour": 10,
            "minute": 0,
            "timezone": "UTC",
        }
        payload = {
            "job_id": "job1",
            "trigger": trigger_data,
            "job_type": "notification",
            "user_id": 123,
        }
        command = SchedulerCommand(
            id="cmd1", type=SchedulerCommandType.SCHEDULE_JOB, payload=payload
        )

        await worker._process_command(command)

        mock_scheduler.schedule_job.assert_called_once()
        call_kwargs = mock_scheduler.schedule_job.call_args[1]
        assert call_kwargs["job_id"] == "job1"
        assert isinstance(call_kwargs["trigger"], ScheduleTrigger)
        assert call_kwargs["kwargs"] == {
            "message_type": "weekly_summary",
            "user_id": 123,
        }

        worker._response_queue.put.assert_called_once()
        response = worker._response_queue.put.call_args[0][0]
        assert response.success is True

    @pytest.mark.asyncio
    async def test_process_command_remove_job(self, worker, mock_scheduler):
        """Test processing REMOVE_JOB command."""
        mock_scheduler.remove_job.return_value = True
        command = SchedulerCommand(
            id="cmd1", type=SchedulerCommandType.REMOVE_JOB, payload={"job_id": "job1"}
        )

        await worker._process_command(command)

        mock_scheduler.remove_job.assert_called_with("job1")
        response = worker._response_queue.put.call_args[0][0]
        assert response.success is True

    @pytest.mark.asyncio
    async def test_process_command_remove_job_failure(self, worker, mock_scheduler):
        """Test processing REMOVE_JOB command when job not found."""
        mock_scheduler.remove_job.return_value = False
        command = SchedulerCommand(
            id="cmd1", type=SchedulerCommandType.REMOVE_JOB, payload={"job_id": "job1"}
        )

        await worker._process_command(command)

        response = worker._response_queue.put.call_args[0][0]
        assert response.success is False

    @pytest.mark.asyncio
    async def test_process_command_reschedule_job(self, worker, mock_scheduler):
        """Test processing RESCHEDULE_JOB command."""
        trigger_data = {
            "day_of_week": "mon",
            "hour": 10,
            "minute": 0,
            "timezone": "UTC",
        }
        command = SchedulerCommand(
            id="cmd1",
            type=SchedulerCommandType.RESCHEDULE_JOB,
            payload={"job_id": "job1", "trigger": trigger_data},
        )

        await worker._process_command(command)

        mock_scheduler.reschedule_job.assert_called_once()
        assert worker._response_queue.put.call_args[0][0].success is True

    @pytest.mark.asyncio
    async def test_process_command_get_job(self, worker, mock_scheduler):
        """Test processing GET_JOB command."""
        mock_scheduler.get_job.return_value = {"id": "job1"}
        command = SchedulerCommand(
            id="cmd1", type=SchedulerCommandType.GET_JOB, payload={"job_id": "job1"}
        )

        await worker._process_command(command)

        mock_scheduler.get_job.assert_called_with("job1")
        response = worker._response_queue.put.call_args[0][0]
        assert response.data == {"id": "job1"}

    @pytest.mark.asyncio
    async def test_process_command_get_all_jobs(self, worker, mock_scheduler):
        """Test processing GET_ALL_JOBS command."""
        mock_scheduler.get_all_jobs.return_value = [{"id": "job1"}]
        command = SchedulerCommand(
            id="cmd1", type=SchedulerCommandType.GET_ALL_JOBS, payload={}
        )

        await worker._process_command(command)

        mock_scheduler.get_all_jobs.assert_called_once()
        response = worker._response_queue.put.call_args[0][0]
        assert response.data == [{"id": "job1"}]

    @pytest.mark.asyncio
    async def test_process_command_health_check(self, worker, mock_scheduler):
        """Test processing HEALTH_CHECK command."""
        mock_scheduler.is_running = True
        command = SchedulerCommand(
            id="cmd1", type=SchedulerCommandType.HEALTH_CHECK, payload={}
        )

        await worker._process_command(command)

        response = worker._response_queue.put.call_args[0][0]
        assert response.success is True
        assert response.data["running"] is True

    @pytest.mark.asyncio
    async def test_process_command_shutdown(self, worker):
        """Test processing SHUTDOWN command."""
        worker._running = True
        command = SchedulerCommand(
            id="cmd1", type=SchedulerCommandType.SHUTDOWN, payload={}
        )

        await worker._process_command(command)

        assert worker._running is False

    @pytest.mark.asyncio
    async def test_process_command_unknown(self, worker):
        """Test processing unknown command type."""
        command = SchedulerCommand(
            id="cmd1", type=SchedulerCommandType.PAUSE, payload={}
        )

        await worker._process_command(command)
        response = worker._response_queue.put.call_args[0][0]
        assert response.success is True

    @pytest.mark.asyncio
    async def test_handle_schedule_job_unknown_type(self, worker, mock_scheduler):
        """Test scheduling job with unknown job type."""
        trigger_data = {
            "day_of_week": "mon",
            "hour": 10,
            "minute": 0,
            "timezone": "UTC",
        }
        payload = {
            "job_id": "job1",
            "trigger": trigger_data,
            "job_type": "unknown_type",
        }

        worker._handle_schedule_job(payload)

        mock_scheduler.schedule_job.assert_not_called()

    def test_handle_shutdown_signal(self, worker):
        """Test signal handler."""
        worker._running = True
        worker._handle_shutdown_signal(signal.SIGTERM, None)
        assert worker._running is False

    def test_cleanup(self, worker, mock_scheduler):
        """Test cleanup."""
        worker._scheduler = mock_scheduler
        worker._loop = MagicMock()

        worker._cleanup()

        mock_scheduler.shutdown.assert_called_once()
        worker._loop.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_command_exception(self, worker):
        """Test general exception handling in command payload processing."""
        # Use a real object or properly structured mock to avoid name error in logging
        command = MagicMock()
        command.id = "cmd-err"
        command.type = MagicMock()
        command.type.name = "INVALID_TYPE"

        # Trigger an exception by making property access fail
        type(command).payload = pytest.raises(
            Exception
        )  # Can't easily force exception on property access of Mock this way

        # Simpler: Make command a real object but force an error in logic
        # OR: Just ensure execution fails deeper.

        # Let's pass a command that causes an error in one of the branches?
        # A simpler way is to mock command.type to return something valid, then make the method logic fail.

        # Strategy: Mock _handle_schedule_job to raise exception
        real_command = SchedulerCommand(
            id="error-cmd", type=SchedulerCommandType.SCHEDULE_JOB, payload={}
        )

        with patch.object(
            worker, "_handle_schedule_job", side_effect=Exception("Validation failed")
        ):
            await worker._process_command(real_command)

        # Verify error response sent
        worker._response_queue.put.assert_called_once()
        response = worker._response_queue.put.call_args[0][0]
        assert response.success is False
        assert "Validation failed" in response.error
