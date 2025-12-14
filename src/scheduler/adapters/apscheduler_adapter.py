"""APScheduler adapter implementing SchedulerPortProtocol.

This module provides an adapter for APScheduler's AsyncIOScheduler that
implements the SchedulerPortProtocol for scheduling operations.
"""

from typing import Any

from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ...contracts.scheduler_port_protocol import (
    AsyncCallback,
    JobInfo,
    ScheduleTrigger,
)
from ...utils.config import BOT_NAME
from ...utils.logger import get_logger

logger = get_logger(f"{BOT_NAME}.APSchedulerAdapter")

# Day of week mapping (ScheduleTrigger uses 0=Monday)
DAY_OF_WEEK_MAP = {
    0: "mon",
    1: "tue",
    2: "wed",
    3: "thu",
    4: "fri",
    5: "sat",
    6: "sun",
}


class APSchedulerAdapter:
    """APScheduler implementation of SchedulerPortProtocol.

    This adapter wraps AsyncIOScheduler and provides the SchedulerPortProtocol
    interface for scheduling operations.

    :ivar _scheduler: The underlying APScheduler instance
    """

    def __init__(
        self,
        scheduler: AsyncIOScheduler | None = None,
    ) -> None:
        """Initialize the APScheduler adapter.

        :param scheduler: Optional APScheduler instance to wrap
        :type scheduler: AsyncIOScheduler | None
        :returns: None
        """
        self._scheduler = scheduler or AsyncIOScheduler()

    def schedule_job(
        self,
        job_id: str,
        trigger: ScheduleTrigger,
        callback: AsyncCallback,
        args: tuple[Any, ...] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        """Schedule a new job using APScheduler.

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
        """
        cron_trigger = self._create_cron_trigger(trigger=trigger)

        self._scheduler.add_job(
            func=callback,
            trigger=cron_trigger,
            id=job_id,
            args=args or (),
            kwargs=kwargs or {},
            replace_existing=True,
        )

        logger.debug(f"Scheduled job {job_id} with trigger {trigger}")

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job.

        :param job_id: Unique identifier of the job to remove
        :type job_id: str
        :returns: True if job was removed, False if not found
        :rtype: bool
        """
        try:
            self._scheduler.remove_job(job_id=job_id)
            logger.debug(f"Removed job {job_id}")
            return True
        except Exception:
            logger.debug(f"Job {job_id} not found for removal")
            return False

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
        try:
            cron_trigger = self._create_cron_trigger(trigger=trigger)
            self._scheduler.reschedule_job(
                job_id=job_id,
                trigger=cron_trigger,
            )
            logger.debug(f"Rescheduled job {job_id} with trigger {trigger}")
            return True
        except Exception:
            logger.debug(f"Job {job_id} not found for rescheduling")
            return False

    def get_job(self, job_id: str) -> JobInfo | None:
        """Get information about a scheduled job.

        :param job_id: Unique identifier of the job
        :type job_id: str
        :returns: Job information or None if not found
        :rtype: JobInfo | None
        """
        job = self._scheduler.get_job(job_id=job_id)
        if job is None:
            return None

        return self._job_to_info(job=job)

    def get_all_jobs(self) -> list[JobInfo]:
        """Get all scheduled jobs.

        :returns: List of all scheduled jobs
        :rtype: list[JobInfo]
        """
        jobs = self._scheduler.get_jobs()
        return [self._job_to_info(job=job) for job in jobs]

    def start(self) -> None:
        """Start the scheduler.

        :returns: None
        """
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the scheduler.

        :param wait: Whether to wait for running jobs to complete
        :type wait: bool
        :returns: None
        """
        if self._scheduler.running:
            self._scheduler.shutdown(wait=wait)
            logger.info("Scheduler shutdown")

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running.

        :returns: True if scheduler is running
        :rtype: bool
        """
        return self._scheduler.running

    def _create_cron_trigger(self, trigger: ScheduleTrigger) -> CronTrigger:
        """Create APScheduler CronTrigger from ScheduleTrigger.

        :param trigger: Schedule trigger configuration
        :type trigger: ScheduleTrigger
        :returns: APScheduler CronTrigger
        :rtype: CronTrigger
        """
        day_of_week = DAY_OF_WEEK_MAP.get(trigger.day_of_week, "mon")

        return CronTrigger(
            day_of_week=day_of_week,
            hour=trigger.hour,
            minute=trigger.minute,
            timezone=trigger.timezone,
        )

    def _job_to_info(self, job: Job) -> JobInfo:
        """Convert APScheduler Job to JobInfo.

        :param job: APScheduler Job object
        :type job: Job
        :returns: JobInfo representation
        :rtype: JobInfo
        """
        # Extract trigger info if it's a CronTrigger
        trigger_info: ScheduleTrigger | None = None

        if hasattr(job.trigger, "fields"):
            # CronTrigger has fields
            try:
                fields = job.trigger.fields
                day_of_week_field = fields[4]  # day_of_week is 5th field
                hour_field = fields[5]
                minute_field = fields[6]

                # Get first value from expression
                day_of_week = self._get_first_field_value(day_of_week_field)
                hour = self._get_first_field_value(hour_field)
                minute = self._get_first_field_value(minute_field)

                if all(v is not None for v in [day_of_week, hour, minute]):
                    trigger_info = ScheduleTrigger(
                        day_of_week=day_of_week,
                        hour=hour,
                        minute=minute,
                        timezone=str(job.trigger.timezone),
                    )
            except (IndexError, AttributeError):
                pass

        return JobInfo(
            job_id=job.id,
            trigger=trigger_info,
            next_run_time=job.next_run_time,
            callback_name=job.func.__name__ if job.func else "",
            args=job.args or (),
            kwargs=job.kwargs or {},
        )

    def _get_first_field_value(self, field: Any) -> int | None:
        """Extract first value from a cron field expression.

        :param field: Cron field expression
        :type field: Any
        :returns: First numeric value or None
        :rtype: int | None
        """
        if hasattr(field, "expressions"):
            expressions = field.expressions
            if expressions:
                first_expr = expressions[0]
                if hasattr(first_expr, "first"):
                    return first_expr.first
        return None
