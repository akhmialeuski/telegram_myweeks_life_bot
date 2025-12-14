"""Scheduler worker process.

This module provides the SchedulerWorker class which runs in a separate process
and manages the scheduler lifecycle, handling IPC commands from the main application.
"""

import asyncio
import signal
from multiprocessing import Queue
from typing import Any

from ..contracts.scheduler_port_protocol import (
    SchedulerPortProtocol,
    ScheduleTrigger,
)
from ..services.container import ServiceContainer
from ..utils.config import BOT_NAME
from ..utils.logger import get_logger
from .adapters.apscheduler_adapter import APSchedulerAdapter
from .commands import SchedulerCommand, SchedulerCommandType, SchedulerResponse
from .jobs import execute_notification_job

logger = get_logger(f"{BOT_NAME}.SchedulerWorker")


class SchedulerWorker:
    """Worker process for running the scheduler.

    Manages the lifecycle of the scheduler and handles IPC commands.

    :ivar _command_queue: Queue for receiving commands
    :ivar _response_queue: Queue for sending responses
    :ivar _scheduler: The underlying scheduler implementation
    :ivar _running: Whether the worker loop is running
    """

    def __init__(
        self,
        command_queue: Queue,
        response_queue: Queue,
        scheduler: SchedulerPortProtocol | None = None,
    ) -> None:
        """Initialize the scheduler worker.

        :param command_queue: Queue to receive commands from
        :type command_queue: Queue
        :param response_queue: Queue to send responses to
        :type response_queue: Queue
        :param scheduler: Scheduler implementation (default: APSchedulerAdapter)
        :type scheduler: SchedulerPortProtocol | None
        :returns: None
        """
        self._command_queue = command_queue
        self._response_queue = response_queue
        self._scheduler = scheduler or APSchedulerAdapter()
        self._running = False
        self._loop: asyncio.AbstractEventLoop | None = None

    def run(self) -> None:
        """Run the worker process.

        This is the entry point for the separate process.
        It sets up signal handlers and starts the main loop.
        """
        self._running = True
        logger.info("Scheduler worker started")

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown_signal)
        signal.signal(signal.SIGINT, self._handle_shutdown_signal)

        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            # Start scheduler
            self._scheduler.start()

            # Run main loop
            self._loop.run_until_complete(self._main_loop())

        except Exception as error:
            logger.critical(f"Scheduler worker failed: {error}")
        finally:
            self._cleanup()

    async def _main_loop(self) -> None:
        """Main execution loop processing commands."""
        # Initialize services in the worker process
        container = ServiceContainer()
        await container.initialize()
        logger.info("Worker services initialized")

        while self._running:
            try:
                # Non-blocking get from queue
                if not self._command_queue.empty():
                    command: SchedulerCommand = self._command_queue.get_nowait()
                    await self._process_command(command)

                # Sleep briefly to avoid busy loop
                await asyncio.sleep(0.1)

            except Exception as error:
                logger.error(f"Error in scheduler worker loop: {error}")
                await asyncio.sleep(1)

    async def _process_command(self, command: SchedulerCommand) -> None:  # noqa: C901
        """Process a received command.

        :param command: Command to process
        :type command: SchedulerCommand
        :returns: None
        """
        logger.debug(f"Received command: {command.type.name} (ID: {command.id})")
        response = SchedulerResponse(command_id=command.id, success=True)

        try:
            if command.type == SchedulerCommandType.SCHEDULE_JOB:
                self._handle_schedule_job(command.payload)

            elif command.type == SchedulerCommandType.REMOVE_JOB:
                job_id = command.payload["job_id"]
                if not self._scheduler.remove_job(job_id):
                    response = SchedulerResponse(
                        command_id=command.id,
                        success=False,
                        error=f"Job {job_id} not found",
                    )

            elif command.type == SchedulerCommandType.RESCHEDULE_JOB:
                self._handle_reschedule_job(command.payload)

            elif command.type == SchedulerCommandType.GET_JOB:
                job_id = command.payload["job_id"]
                job_info = self._scheduler.get_job(job_id)
                response = SchedulerResponse(
                    command_id=command.id,
                    success=True,
                    data=job_info,
                )

            elif command.type == SchedulerCommandType.GET_ALL_JOBS:
                jobs = self._scheduler.get_all_jobs()
                response = SchedulerResponse(
                    command_id=command.id,
                    success=True,
                    data=jobs,
                )

            elif command.type == SchedulerCommandType.PAUSE:
                # APScheduler adapter specific, or general?
                # Protocol doesn't have pause/resume yet, assuming adapter handles it or we skip for now
                # For now, let's just log
                logger.warning("Pause command not fully implemented in protocol")

            elif command.type == SchedulerCommandType.RESUME:
                logger.warning("Resume command not fully implemented in protocol")

            elif command.type == SchedulerCommandType.SHUTDOWN:
                self._running = False

            elif command.type == SchedulerCommandType.HEALTH_CHECK:
                response = SchedulerResponse(
                    command_id=command.id,
                    success=self._scheduler.is_running,
                    data={"running": self._scheduler.is_running},
                )

            else:
                response = SchedulerResponse(
                    command_id=command.id,
                    success=False,
                    error=f"Unknown command type: {command.type}",
                )

        except Exception as error:
            logger.error(f"Command execution failed: {error}")
            response = SchedulerResponse(
                command_id=command.id,
                success=False,
                error=str(error),
            )

        self._response_queue.put(response)

    def _handle_schedule_job(self, payload: dict[str, Any]) -> None:
        """Handle schedule job command.

        :param payload: Command payload
        :type payload: dict[str, Any]
        :returns: None
        """
        job_id = payload["job_id"]
        trigger_data = payload["trigger"]
        job_type = payload.get("job_type", "notification")
        user_id = payload.get("user_id")

        trigger = ScheduleTrigger(**trigger_data)

        # Select callback based on job type
        if job_type == "notification" or job_type == "weekly_summary":
            # We use a partial or lambda? No, APScheduler stores args.
            # We pass the function and args.
            callback = execute_notification_job
            kwargs = {"message_type": "weekly_summary"}
            if user_id:
                kwargs["user_id"] = user_id

            self._scheduler.schedule_job(
                job_id=job_id,
                trigger=trigger,
                callback=callback,
                kwargs=kwargs,
            )
        else:
            logger.warning(f"Unknown job type: {job_type}")

    def _handle_reschedule_job(self, payload: dict[str, Any]) -> None:
        """Handle reschedule job command.

        :param payload: Command payload
        :type payload: dict[str, Any]
        :returns: None
        """
        job_id = payload["job_id"]
        trigger_data = payload["trigger"]
        trigger = ScheduleTrigger(**trigger_data)

        self._scheduler.reschedule_job(job_id, trigger)

    def _handle_shutdown_signal(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals.

        :param signum: Signal number
        :type signum: int
        :param frame: Current stack frame
        :type frame: Any
        :returns: None
        """
        logger.info(f"Received signal {signum}, shutting down...")
        self._running = False

    def _cleanup(self) -> None:
        """Cleanup resources on shutdown."""
        if self._scheduler and self._scheduler.is_running:
            self._scheduler.shutdown()

        if self._loop:
            self._loop.close()

        logger.info("Scheduler worker stopped")
