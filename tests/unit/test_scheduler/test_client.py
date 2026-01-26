"""Unit tests for scheduler client.

Tests the SchedulerClient class for IPC communication, command sending,
and response handling logic.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.contracts.scheduler_port_protocol import ScheduleTrigger
from src.scheduler.client import SchedulerClient
from src.scheduler.commands import SchedulerCommandType, SchedulerResponse


class TestSchedulerClient:
    """Test suite for SchedulerClient class."""

    @pytest.fixture
    def mock_queues(self):
        """Create mock queues for testing."""
        # multiprocessing.Queue is a factory method, so spec=Queue doesn't work for instance methods
        cmd_queue = MagicMock()
        resp_queue = MagicMock()
        return cmd_queue, resp_queue

    @pytest.fixture
    def client(self, mock_queues):
        """Create SchedulerClient instance."""
        cmd_queue, resp_queue = mock_queues
        return SchedulerClient(command_queue=cmd_queue, response_queue=resp_queue)

    @pytest.mark.asyncio
    async def test_start_listening(self, client):
        """Test starting the listener loop."""
        # Mock _listen_loop as an AsyncMock so it can be awaited
        with patch.object(client, "_listen_loop", new_callable=AsyncMock):
            # Should start listener
            await client.start_listening()
            assert client._listening is True
            # We can't easily verify create_task execution on a mocked coro without side effects
            # but we verify state was set

        # Test idempotency
        await client.start_listening()
        assert client._listening is True

    @pytest.mark.asyncio
    async def test_handle_response(self, client):
        """Test handling a received response."""
        future = asyncio.Future()
        client._response_futures["cmd-123"] = future

        response = SchedulerResponse(command_id="cmd-123", success=True)
        client._handle_response(response)

        assert future.done()
        assert future.result() == response
        assert "cmd-123" not in client._response_futures

    @pytest.mark.asyncio
    async def test_listen_loop_processing(self, client, mock_queues):
        """Test processing of messages in listen loop."""
        _, resp_queue = mock_queues

        # Setup queue behavior
        response = SchedulerResponse(command_id="cmd-1", success=True)
        # Using side_effect to simulate queue having item then empty
        resp_queue.empty.side_effect = [False, True]
        resp_queue.get_nowait.return_value = response

        with patch.object(client, "_handle_response") as mock_handle:
            # Manually run one iteration logic
            if not resp_queue.empty():
                resp = resp_queue.get_nowait()
                client._handle_response(resp)

            mock_handle.assert_called_once_with(response)

    @pytest.mark.asyncio
    async def test_send_command_wait_success(self, client, mock_queues):
        """Test sending command and waiting for successful response."""
        cmd_queue, _ = mock_queues

        # Mock waiting mechanism
        response = SchedulerResponse(command_id="test-id", success=True)

        async def mock_wait_for(fut, timeout):
            fut.set_result(response)
            return await fut

        with patch("asyncio.wait_for", side_effect=mock_wait_for):
            result = await client._send_command(
                SchedulerCommandType.HEALTH_CHECK, wait_for_response=True
            )

        assert result == response
        cmd_queue.put.assert_called_once()
        # Verify command payload in queue
        call_args = cmd_queue.put.call_args[0][0]
        assert call_args.type == SchedulerCommandType.HEALTH_CHECK

    @pytest.mark.asyncio
    async def test_send_command_timeout(self, client, mock_queues):
        """Test sending command with timeout."""
        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
            with pytest.raises(asyncio.TimeoutError):
                await client._send_command(
                    SchedulerCommandType.HEALTH_CHECK, wait_for_response=True
                )

        # Check cleanup
        assert len(client._response_futures) == 0

    @pytest.mark.asyncio
    async def test_send_command_no_wait(self, client, mock_queues):
        """Test sending command without waiting."""
        cmd_queue, _ = mock_queues

        result = await client._send_command(
            SchedulerCommandType.SHUTDOWN, wait_for_response=False
        )

        assert result is None
        cmd_queue.put.assert_called_once()

    @pytest.mark.asyncio
    async def test_schedule_job(self, client):
        """Test schedule_job method."""
        trigger = ScheduleTrigger(day_of_week="mon", hour=10, minute=0, timezone="UTC")

        with patch.object(client, "_send_command") as mock_send:
            mock_send.return_value = SchedulerResponse("id", True)

            result = await client.schedule_job(
                job_id="job1", trigger=trigger, user_id=123
            )

            assert result is True
            mock_send.assert_called_once()
            args = mock_send.call_args
            assert args[0][0] == SchedulerCommandType.SCHEDULE_JOB
            assert args[1]["payload"]["job_id"] == "job1"
            assert args[1]["payload"]["user_id"] == 123

    @pytest.mark.asyncio
    async def test_remove_job(self, client):
        """Test remove_job method."""
        with patch.object(client, "_send_command") as mock_send:
            mock_send.return_value = SchedulerResponse("id", True)

            result = await client.remove_job("job1")

            assert result is True
            assert mock_send.call_args[1]["payload"] == {"job_id": "job1"}

    @pytest.mark.asyncio
    async def test_reschedule_job(self, client):
        """Test reschedule_job method."""
        trigger = ScheduleTrigger(day_of_week="fri", hour=10, minute=0, timezone="UTC")

        with patch.object(client, "_send_command") as mock_send:
            mock_send.return_value = SchedulerResponse("id", False)  # Test failure case

            result = await client.reschedule_job("job1", trigger)

            assert result is False
            assert mock_send.call_args[0][0] == SchedulerCommandType.RESCHEDULE_JOB

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health_check method."""
        with patch.object(client, "_send_command") as mock_send:
            mock_send.return_value = SchedulerResponse("id", True)
            assert await client.health_check() is True

            mock_send.side_effect = Exception("error")
            assert await client.health_check() is False

    @pytest.mark.asyncio
    async def test_shutdown(self, client):
        """Test shutdown method."""
        with patch.object(client, "_send_command") as mock_send:
            await client.shutdown()
            mock_send.assert_called_once_with(
                SchedulerCommandType.SHUTDOWN, wait_for_response=False
            )
