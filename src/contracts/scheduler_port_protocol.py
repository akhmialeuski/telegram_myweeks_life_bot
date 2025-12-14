"""Scheduler Port Protocol for scheduling operations.

This module defines the abstract interface for scheduling operations.
It enables decoupling the scheduler implementation (APScheduler, etc.)
from the business logic.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Coroutine, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class ScheduleTrigger:
    """Trigger configuration for a scheduled job.

    :ivar day_of_week: Day of week (0=Monday, 6=Sunday)
    :ivar hour: Hour of day (0-23)
    :ivar minute: Minute of hour (0-59)
    :ivar timezone: Timezone string (e.g., "UTC", "Europe/Minsk")
    """

    day_of_week: int
    hour: int
    minute: int
    timezone: str = "UTC"


@dataclass(frozen=True, slots=True)
class JobInfo:
    """Information about a scheduled job.

    :ivar job_id: Unique identifier for the job
    :ivar trigger: Trigger configuration
    :ivar next_run_time: Next scheduled execution time
    :ivar callback_name: Name of the callback function
    :ivar args: Positional arguments for the callback
    :ivar kwargs: Keyword arguments for the callback
    """

    job_id: str
    trigger: ScheduleTrigger | None = None
    next_run_time: datetime | None = None
    callback_name: str = ""
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)


# Type alias for async callback functions
AsyncCallback = Callable[..., Coroutine[Any, Any, None]]


@runtime_checkable
class SchedulerPortProtocol(Protocol):
    """Abstract interface for scheduling operations.

    This protocol enables decoupling from specific scheduler implementations.
    Implementations include APSchedulerAdapter for APScheduler.
    """

    def schedule_job(
        self,
        job_id: str,
        trigger: ScheduleTrigger,
        callback: AsyncCallback,
        args: tuple[Any, ...] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        """Schedule a new job.

        :param job_id: Unique identifier for the job
        :type job_id: str
        :param trigger: Trigger configuration
        :type trigger: ScheduleTrigger
        :param callback: Async function to call
        :type callback: AsyncCallback
        :param args: Positional arguments for callback
        :type args: tuple[Any, ...] | None
        :param kwargs: Keyword arguments for callback
        :type kwargs: dict[str, Any] | None
        :returns: None
        :raises SchedulerError: If job scheduling fails
        """
        ...

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job.

        :param job_id: Unique identifier of the job to remove
        :type job_id: str
        :returns: True if job was removed, False if not found
        :rtype: bool
        """
        ...

    def reschedule_job(
        self,
        job_id: str,
        trigger: ScheduleTrigger,
    ) -> bool:
        """Reschedule an existing job with a new trigger.

        :param job_id: Unique identifier of the job
        :type job_id: str
        :param trigger: New trigger configuration
        :type trigger: ScheduleTrigger
        :returns: True if job was rescheduled, False if not found
        :rtype: bool
        """
        ...

    def get_job(self, job_id: str) -> JobInfo | None:
        """Get information about a scheduled job.

        :param job_id: Unique identifier of the job
        :type job_id: str
        :returns: Job information or None if not found
        :rtype: JobInfo | None
        """
        ...

    def get_all_jobs(self) -> list[JobInfo]:
        """Get all scheduled jobs.

        :returns: List of all scheduled jobs
        :rtype: list[JobInfo]
        """
        ...

    def start(self) -> None:
        """Start the scheduler.

        :returns: None
        """
        ...

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the scheduler.

        :param wait: Whether to wait for running jobs to complete
        :type wait: bool
        :returns: None
        """
        ...

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running.

        :returns: True if scheduler is running
        :rtype: bool
        """
        ...
