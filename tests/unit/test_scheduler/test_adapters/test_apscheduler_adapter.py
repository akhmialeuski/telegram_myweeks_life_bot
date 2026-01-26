"""Tests for APSchedulerAdapter.

This module contains unit tests for the APSchedulerAdapter class,
verifying that it correctly interacts with the underlying AsyncIOScheduler.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.contracts.scheduler_port_protocol import ScheduleTrigger
from src.scheduler.adapters.apscheduler_adapter import APSchedulerAdapter


class TestAPSchedulerAdapter:
    """Test class for APSchedulerAdapter."""

    @pytest.fixture
    def mock_scheduler(self) -> MagicMock:
        """Provide mock AsyncIOScheduler."""
        scheduler = MagicMock(spec=AsyncIOScheduler)
        scheduler.running = False
        return scheduler

    @pytest.fixture
    def adapter(self, mock_scheduler: MagicMock) -> APSchedulerAdapter:
        """Provide APSchedulerAdapter instance with mock scheduler."""
        return APSchedulerAdapter(scheduler=mock_scheduler)

    def test_init_creates_default_scheduler(self) -> None:
        """Test initialization with default scheduler."""
        adapter = APSchedulerAdapter()
        assert isinstance(adapter._scheduler, AsyncIOScheduler)

    @pytest.mark.asyncio
    async def test_schedule_job_success(
        self,
        adapter: APSchedulerAdapter,
        mock_scheduler: MagicMock,
    ) -> None:
        """Test successful job scheduling."""
        # Setup
        job_id = "test_job"
        trigger = ScheduleTrigger(
            day_of_week=0,  # Monday
            hour=10,
            minute=30,
            timezone="UTC",
        )

        async def mock_callback() -> None:
            pass

        # Execute
        adapter.schedule_job(
            job_id=job_id,
            trigger=trigger,
            callback=mock_callback,
            args=("arg",),
            kwargs={"key": "val"},
        )

        # Verify
        mock_scheduler.add_job.assert_called_once()
        call_args = mock_scheduler.add_job.call_args
        assert call_args.kwargs["id"] == job_id
        assert call_args.kwargs["func"] == mock_callback
        assert call_args.kwargs["args"] == ("arg",)
        assert call_args.kwargs["kwargs"] == {"key": "val"}
        assert call_args.kwargs["replace_existing"] is True

        # Verify trigger creation
        cron_trigger = call_args.kwargs["trigger"]
        assert isinstance(cron_trigger, CronTrigger)
        # APScheduler CronTrigger fields are complex to check directly
        # but we can infer correctness if no error raised and day mapping correct

    def test_remove_job_success(
        self,
        adapter: APSchedulerAdapter,
        mock_scheduler: MagicMock,
    ) -> None:
        """Test successful job removal."""
        result = adapter.remove_job(job_id="test_job")

        assert result is True
        mock_scheduler.remove_job.assert_called_once_with(job_id="test_job")

    def test_remove_job_failure(
        self,
        adapter: APSchedulerAdapter,
        mock_scheduler: MagicMock,
    ) -> None:
        """Test job removal when job not found."""
        mock_scheduler.remove_job.side_effect = Exception("Job not found")

        result = adapter.remove_job(job_id="test_job")

        assert result is False

    def test_reschedule_job_success(
        self,
        adapter: APSchedulerAdapter,
        mock_scheduler: MagicMock,
    ) -> None:
        """Test successful job rescheduling."""
        trigger = ScheduleTrigger(day_of_week=1, hour=12, minute=0)

        result = adapter.reschedule_job(job_id="test_job", trigger=trigger)

        assert result is True
        mock_scheduler.reschedule_job.assert_called_once()
        call_args = mock_scheduler.reschedule_job.call_args
        assert call_args.kwargs["job_id"] == "test_job"
        assert isinstance(call_args.kwargs["trigger"], CronTrigger)

    def test_reschedule_job_failure(
        self,
        adapter: APSchedulerAdapter,
        mock_scheduler: MagicMock,
    ) -> None:
        """Test job rescheduling when job not found."""
        mock_scheduler.reschedule_job.side_effect = Exception("Job not found")
        trigger = ScheduleTrigger(day_of_week=1, hour=12, minute=0)

        result = adapter.reschedule_job(job_id="test_job", trigger=trigger)

        assert result is False

    def test_get_job_success(
        self,
        adapter: APSchedulerAdapter,
        mock_scheduler: MagicMock,
    ) -> None:
        """Test getting existing job info."""
        # Setup mock job
        mock_job = MagicMock()
        mock_job.id = "test_job"
        mock_job.next_run_time = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
        mock_job.func.__name__ = "mock_callback"
        mock_job.args = ("arg",)
        mock_job.kwargs = {"k": "v"}
        # Mock trigger structure
        mock_job.trigger = MagicMock()
        # Simulate CronTrigger fields structure for _job_to_info
        mock_job.trigger.fields = []

        mock_scheduler.get_job.return_value = mock_job

        # Execute
        job_info = adapter.get_job(job_id="test_job")

        # Verify
        assert job_info is not None
        assert job_info.job_id == "test_job"
        assert job_info.next_run_time == mock_job.next_run_time
        assert job_info.callback_name == "mock_callback"
        assert job_info.args == ("arg",)
        assert job_info.kwargs == {"k": "v"}

    def test_get_job_not_found(
        self,
        adapter: APSchedulerAdapter,
        mock_scheduler: MagicMock,
    ) -> None:
        """Test getting non-existent job."""
        mock_scheduler.get_job.return_value = None

        job_info = adapter.get_job(job_id="test_job")

        assert job_info is None

    def test_get_all_jobs(
        self,
        adapter: APSchedulerAdapter,
        mock_scheduler: MagicMock,
    ) -> None:
        """Test getting all jobs."""
        mock_job1 = MagicMock()
        mock_job1.id = "job1"
        mock_job1.func.__name__ = "f1"

        mock_job2 = MagicMock()
        mock_job2.id = "job2"
        mock_job2.func.__name__ = "f2"

        mock_scheduler.get_jobs.return_value = [mock_job1, mock_job2]

        jobs = adapter.get_all_jobs()

        assert len(jobs) == 2
        assert jobs[0].job_id == "job1"
        assert jobs[1].job_id == "job2"

    def test_start_starts_scheduler_if_not_running(
        self,
        adapter: APSchedulerAdapter,
        mock_scheduler: MagicMock,
    ) -> None:
        """Test starting scheduler."""
        mock_scheduler.running = False

        adapter.start()

        mock_scheduler.start.assert_called_once()

    def test_start_does_nothing_if_running(
        self,
        adapter: APSchedulerAdapter,
        mock_scheduler: MagicMock,
    ) -> None:
        """Test start is idempotent."""
        mock_scheduler.running = True

        adapter.start()

        mock_scheduler.start.assert_not_called()

    def test_shutdown_stops_scheduler_if_running(
        self,
        adapter: APSchedulerAdapter,
        mock_scheduler: MagicMock,
    ) -> None:
        """Test shutting down scheduler."""
        mock_scheduler.running = True

        adapter.shutdown(wait=True)

        mock_scheduler.shutdown.assert_called_once_with(wait=True)

    def test_is_running_property(
        self,
        adapter: APSchedulerAdapter,
        mock_scheduler: MagicMock,
    ) -> None:
        """Test is_running property delegates to scheduler."""
        mock_scheduler.running = True
        assert adapter.is_running is True

        mock_scheduler.running = False
        assert adapter.is_running is False

    def test_get_first_field_value_no_expressions(
        self,
        adapter: APSchedulerAdapter,
    ) -> None:
        """Test _get_first_field_value when field has no expressions.

        This test verifies that None is returned when the cron field
        doesn't have any expressions.
        """
        # Create mock field with no expressions
        mock_field = MagicMock()
        mock_field.expressions = []

        result = adapter._get_first_field_value(field=mock_field)

        assert result is None

    def test_get_first_field_value_no_expressions_attribute(
        self,
        adapter: APSchedulerAdapter,
    ) -> None:
        """Test _get_first_field_value when field has no expressions attribute.

        This test verifies that None is returned when the cron field
        doesn't have expressions attribute at all.
        """
        # Create mock field without expressions attribute
        mock_field = MagicMock(spec=[])

        result = adapter._get_first_field_value(field=mock_field)

        assert result is None
