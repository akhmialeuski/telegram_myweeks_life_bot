"""Scheduler client for sending IPC commands.

This module provides the SchedulerClient class which allows the main application
to communicate with the scheduler worker process via IPC queues.
"""

import asyncio
import uuid
from multiprocessing import Queue
from typing import Any

from ..contracts.scheduler_port_protocol import (
    ScheduleTrigger,
)
from ..utils.config import BOT_NAME
from ..utils.logger import get_logger
from .commands import SchedulerCommand, SchedulerCommandType, SchedulerResponse

logger = get_logger(f"{BOT_NAME}.SchedulerClient")


class SchedulerClient:
    """Client for communicating with the scheduler worker.

    This class provides a high-level interface for sending commands
    to the scheduler worker process and receiving responses.

    :ivar _command_queue: Queue for sending commands
    :ivar _response_queue: Queue for receiving responses
    :ivar _response_futures: Dictionary mapping command IDs to futures
    """

    def __init__(
        self,
        command_queue: Queue,
        response_queue: Queue,
    ) -> None:
        """Initialize the scheduler client.

        :param command_queue: Queue to send commands to
        :type command_queue: Queue
        :param response_queue: Queue to receive responses from
        :type response_queue: Queue
        :returns: None
        """
        self._command_queue = command_queue
        self._response_queue = response_queue
        # We need a way to route responses to the correct awaiter
        # Since response queue is shared, we might need a background listener
        # or simplified approach (e.g. assume 1-to-1 if possible, but it's async)
        # For now, we'll implement a polling mechanism or just fire-and-forget for some
        # To strictly implement request-response over queues in async, we need a reader loop.
        self._response_futures: dict[str, asyncio.Future] = {}
        self._listening = False

    async def start_listening(self) -> None:
        """Start listening for responses in the background.

        This method should be called when the client is initialized.
        """
        if self._listening:
            return
        self._listening = True
        logger.info("Scheduler client listener started")
        asyncio.create_task(self._listen_loop())

    async def _listen_loop(self) -> None:
        """Background loop to listen for responses."""
        while self._listening:
            try:
                if not self._response_queue.empty():
                    response: SchedulerResponse = self._response_queue.get_nowait()
                    self._handle_response(response)
                else:
                    await asyncio.sleep(0.1)
            except Exception as error:
                logger.error(f"Error in scheduler client listener: {error}")
                await asyncio.sleep(1)

    def _handle_response(self, response: SchedulerResponse) -> None:
        """Handle a received response.

        :param response: Received response
        :type response: SchedulerResponse
        :returns: None
        """
        if response.command_id in self._response_futures:
            future = self._response_futures.pop(response.command_id)
            if not future.done():
                future.set_result(response)

    async def _send_command(
        self,
        command_type: SchedulerCommandType,
        payload: dict[str, Any] | None = None,
        wait_for_response: bool = True,
        timeout: float = 5.0,
    ) -> SchedulerResponse | None:
        """Send a command and optionally wait for response.

        :param command_type: Type of command to send
        :type command_type: SchedulerCommandType
        :param payload: Command payload
        :type payload: dict[str, Any] | None
        :param wait_for_response: Whether to wait for a response
        :type wait_for_response: bool
        :param timeout: Timeout in seconds
        :type timeout: float
        :returns: Response if waited, otherwise None
        :rtype: SchedulerResponse | None
        :raises TimeoutError: If response not received in time
        """
        command_id = str(uuid.uuid4())
        command = SchedulerCommand(
            id=command_id,
            type=command_type,
            payload=payload or {},
        )

        if wait_for_response:
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            self._response_futures[command_id] = future

        self._command_queue.put(command)
        logger.debug(f"Sent command {command_type.name} (ID: {command_id})")

        if wait_for_response:
            try:
                return await asyncio.wait_for(future, timeout=timeout)
            except asyncio.TimeoutError:
                if command_id in self._response_futures:
                    del self._response_futures[command_id]
                logger.error(f"Timeout waiting for response to {command_type.name}")
                raise

        return None

    async def schedule_job(
        self,
        job_id: str,
        trigger: ScheduleTrigger,
        # Note: callback is not sent as it's not pickleable across processes easily
        # We assume the worker knows how to "execute_notification_job"
        job_type: str = "notification",  # Metadata for worker
        user_id: int | None = None,
    ) -> bool:
        """Schedule a job.

        :param job_id: Job ID
        :type job_id: str
        :param trigger: Schedule trigger
        :type trigger: ScheduleTrigger
        :param job_type: Type of job
        :type job_type: str
        :param user_id: User ID associated with job
        :type user_id: int | None
        :returns: True if successful
        :rtype: bool
        """
        # Convert trigger to dict for JSON serialization if needed, or stick to pickle
        # Queue uses pickle, so objects are fine.
        payload = {
            "job_id": job_id,
            "trigger": {
                "day_of_week": trigger.day_of_week,
                "hour": trigger.hour,
                "minute": trigger.minute,
                "timezone": trigger.timezone,
            },
            "job_type": job_type,
            "user_id": user_id,
        }

        response = await self._send_command(
            SchedulerCommandType.SCHEDULE_JOB,
            payload=payload,
        )
        return response.success if response else False

    async def remove_job(self, job_id: str) -> bool:
        """Remove a job.

        :param job_id: Job ID
        :type job_id: str
        :returns: True if successful
        :rtype: bool
        """
        response = await self._send_command(
            SchedulerCommandType.REMOVE_JOB,
            payload={"job_id": job_id},
        )
        return response.success if response else False

    async def reschedule_job(
        self,
        job_id: str,
        trigger: ScheduleTrigger,
    ) -> bool:
        """Reschedule a job.

        :param job_id: Job ID
        :type job_id: str
        :param trigger: New trigger
        :type trigger: ScheduleTrigger
        :returns: True if successful
        :rtype: bool
        """
        payload = {
            "job_id": job_id,
            "trigger": {
                "day_of_week": trigger.day_of_week,
                "hour": trigger.hour,
                "minute": trigger.minute,
                "timezone": trigger.timezone,
            },
        }
        response = await self._send_command(
            SchedulerCommandType.RESCHEDULE_JOB,
            payload=payload,
        )
        return response.success if response else False

    async def health_check(self) -> bool:
        """Check if scheduler worker is healthy.

        :returns: True if healthy
        :rtype: bool
        """
        try:
            response = await self._send_command(
                SchedulerCommandType.HEALTH_CHECK,
                timeout=2.0,
            )
            return response.success if response else False
        except Exception:
            return False

    async def shutdown(self) -> None:
        """Shutdown the scheduler worker.

        :returns: None
        """
        await self._send_command(
            SchedulerCommandType.SHUTDOWN,
            wait_for_response=False,
        )
