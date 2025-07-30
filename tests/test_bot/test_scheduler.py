"""Unit tests for the bot scheduler, focusing on notification job management."""

from unittest.mock import MagicMock, patch

import pytest
from telegram.constants import ParseMode

from src.bot.scheduler import (
    NotificationScheduler,
    SchedulerOperationError,
    SchedulerSetupError,
    add_user_to_scheduler,
    remove_user_from_scheduler,
    setup_user_notification_schedules,
    start_scheduler,
    stop_scheduler,
    update_user_schedule,
)
from src.core.enums import WeekDay
from tests.conftest import TEST_USER_ID

# --- Test Constants ---
TEST_JOB_ID = f"weekly_notification_user_{TEST_USER_ID}"
TEST_MESSAGE = "Test weekly message"
DB_ERROR = "Database error"
SCHEDULER_ERROR = "Scheduler error"


# --- Test Classes ---


class TestSendWeeklyMessageToUser:
    """Tests for the send_weekly_message_to_user method."""

    @pytest.mark.asyncio
    async def test_sends_message_if_user_found(
        self,
        mock_app: MagicMock,
        mock_user_with_settings: MagicMock,
        mock_user_service: MagicMock,
        mock_generate_message: MagicMock,
    ) -> None:
        """Verify that a weekly message is generated and sent if the user profile is found.

        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        :param mock_user_with_settings: Mocked user object
        :type mock_user_with_settings: MagicMock
        :param mock_user_service: Mocked user_service
        :type mock_user_service: MagicMock
        :param mock_generate_message: Mocked generate_message_week function
        :type mock_generate_message: MagicMock
        """
        mock_user_service.get_user_profile.return_value = mock_user_with_settings
        notification_scheduler = NotificationScheduler(mock_app)

        await notification_scheduler.send_weekly_message_to_user(TEST_USER_ID)

        mock_app.bot.send_message.assert_called_once_with(
            chat_id=TEST_USER_ID,
            text=TEST_MESSAGE,
            parse_mode=ParseMode.HTML,
        )
        mock_generate_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_logs_warning_if_user_not_found(
        self,
        mock_app: MagicMock,
        mock_user_service: MagicMock,
        mock_scheduler_logger: MagicMock,
    ) -> None:
        """Verify that a warning is logged if the user profile is not found.

        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        :param mock_user_service: Mocked user_service
        :type mock_user_service: MagicMock
        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        mock_user_service.get_user_profile.return_value = None
        notification_scheduler = NotificationScheduler(mock_app)

        await notification_scheduler.send_weekly_message_to_user(TEST_USER_ID)

        mock_scheduler_logger.warning.assert_called_once_with(
            f"User {TEST_USER_ID} not found for weekly notification"
        )
        mock_app.bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_logs_error_on_exception(
        self,
        mock_app: MagicMock,
        mock_user_service: MagicMock,
        mock_scheduler_logger: MagicMock,
    ) -> None:
        """Verify that an error is logged if an exception occurs during execution.

        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        :param mock_user_service: Mocked user_service
        :type mock_user_service: MagicMock
        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        mock_user_service.get_user_profile.side_effect = Exception(DB_ERROR)
        notification_scheduler = NotificationScheduler(mock_app)

        await notification_scheduler.send_weekly_message_to_user(TEST_USER_ID)

        mock_scheduler_logger.error.assert_called_once_with(
            f"Failed to send weekly notification to user {TEST_USER_ID}: {DB_ERROR}"
        )


class TestCreateUserNotificationJob:
    """Tests for the private _create_user_notification_job method."""

    def test_creates_job_if_settings_are_valid(
        self,
        mock_user_with_settings: MagicMock,
        mock_app: MagicMock,
        mock_scheduler: MagicMock,
        mock_scheduler_logger: MagicMock,
    ) -> None:
        """Verify that a scheduler job is created when a user has valid notification settings.

        :param mock_user_with_settings: Mocked user with valid settings
        :type mock_user_with_settings: MagicMock
        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        :param mock_scheduler: Mocked scheduler instance
        :type mock_scheduler: MagicMock
        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        notification_scheduler = NotificationScheduler(mock_app, mock_scheduler)
        notification_scheduler._create_user_notification_job(mock_user_with_settings)

        mock_scheduler.add_job.assert_called_once()
        # Check that info was called twice: once for adding job, once for success
        assert mock_scheduler_logger.info.call_count == 2

    def test_raises_exception_if_settings_are_missing(
        self,
        mock_app: MagicMock,
        mock_scheduler: MagicMock,
        mock_scheduler_logger: MagicMock,
    ) -> None:
        """Verify that the method raises exception if the user has no settings attribute.

        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        :param mock_scheduler: Mocked scheduler instance
        :type mock_scheduler: MagicMock
        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        user_no_settings = MagicMock(telegram_id=TEST_USER_ID, settings=None)
        notification_scheduler = NotificationScheduler(mock_app, mock_scheduler)

        with pytest.raises(SchedulerOperationError):
            notification_scheduler._create_user_notification_job(user_no_settings)

        mock_scheduler_logger.warning.assert_called_once_with(
            f"No settings found for user {TEST_USER_ID}"
        )

    def test_returns_none_if_notifications_disabled(
        self,
        mock_app: MagicMock,
        mock_scheduler: MagicMock,
        mock_scheduler_logger: MagicMock,
    ) -> None:
        """Verify that the method returns None if user notifications are disabled.

        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        :param mock_scheduler: Mocked scheduler instance
        :type mock_scheduler: MagicMock
        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        user_disabled = MagicMock(telegram_id=TEST_USER_ID)
        user_disabled.settings.notifications = False
        notification_scheduler = NotificationScheduler(mock_app, mock_scheduler)

        result = notification_scheduler._create_user_notification_job(user_disabled)

        assert result is None
        mock_scheduler_logger.debug.assert_called_once_with(
            f"Notifications disabled for user {TEST_USER_ID}"
        )

    @pytest.mark.parametrize(
        "missing_field",
        ["day", "time", "both"],
        ids=["missing_day", "missing_time", "missing_both"],
    )
    def test_raises_exception_if_settings_are_incomplete(
        self,
        missing_field: str,
        mock_app: MagicMock,
        mock_scheduler: MagicMock,
        mock_scheduler_logger: MagicMock,
    ) -> None:
        """Verify that the method raises exception if notification day or time is missing.

        :param missing_field: Which field is missing
        :type missing_field: str
        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        :param mock_scheduler: Mocked scheduler instance
        :type mock_scheduler: MagicMock
        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        user = MagicMock(telegram_id=TEST_USER_ID)
        user.settings.notifications = True
        user.settings.notifications_day = (
            WeekDay.MONDAY
            if missing_field != "day" and missing_field != "both"
            else None
        )
        user.settings.notifications_time = (
            MagicMock(hour=10, minute=30)
            if missing_field != "time" and missing_field != "both"
            else None
        )
        notification_scheduler = NotificationScheduler(mock_app, mock_scheduler)

        with pytest.raises(SchedulerOperationError):
            notification_scheduler._create_user_notification_job(user)

        mock_scheduler_logger.warning.assert_called_once_with(
            f"Incomplete notification settings for user {TEST_USER_ID}"
        )

    def test_raises_exception_on_job_creation_exception(
        self,
        mock_user_with_settings: MagicMock,
        mock_app: MagicMock,
        mock_scheduler: MagicMock,
        mock_scheduler_logger: MagicMock,
    ) -> None:
        """Verify that an exception is raised if scheduler.add_job() raises an exception.

        :param mock_user_with_settings: Mocked user with valid settings
        :type mock_user_with_settings: MagicMock
        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        :param mock_scheduler: Mocked scheduler instance
        :type mock_scheduler: MagicMock
        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        mock_scheduler.add_job.side_effect = Exception(SCHEDULER_ERROR)
        notification_scheduler = NotificationScheduler(mock_app, mock_scheduler)

        with pytest.raises(SchedulerOperationError):
            notification_scheduler._create_user_notification_job(
                mock_user_with_settings
            )

        mock_scheduler_logger.error.assert_called_once_with(
            f"Failed to create notification job for user {TEST_USER_ID}: {SCHEDULER_ERROR}"
        )


class TestSchedulerManagementFunctions:
    """Tests for functions that add, remove, and update user jobs in the scheduler."""

    def test_add_user_success(
        self,
        mock_globals: dict[str, MagicMock],
        mock_user_with_settings: MagicMock,
        mock_user_service: MagicMock,
        mock_scheduler_logger: MagicMock,
    ) -> None:
        """Verify that a user is successfully added to the scheduler.

        :param mock_globals: Mocked global scheduler instance
        :type mock_globals: dict[str, MagicMock]
        :param mock_user_with_settings: Mocked user with valid settings
        :type mock_user_with_settings: MagicMock
        :param mock_user_service: Mocked user_service
        :type mock_user_service: MagicMock
        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        add_user_to_scheduler(TEST_USER_ID)
        mock_globals["instance"].add_user.assert_called_once_with(TEST_USER_ID)

    def test_add_user_raises_exception_if_job_creation_fails(
        self,
        mock_globals: dict[str, MagicMock],
        mock_user_with_settings: MagicMock,
        mock_user_service: MagicMock,
    ) -> None:
        """Verify that add_user raises exception if the job creation fails.

        :param mock_globals: Mocked global scheduler instance
        :type mock_globals: dict[str, MagicMock]
        :param mock_user_with_settings: Mocked user with valid settings
        :type mock_user_with_settings: MagicMock
        :param mock_user_service: Mocked user_service
        :type mock_user_service: MagicMock
        """
        mock_globals["instance"].add_user.side_effect = SchedulerOperationError(
            "Job creation failed", TEST_USER_ID, "create_notification_job"
        )
        with pytest.raises(SchedulerOperationError):
            add_user_to_scheduler(TEST_USER_ID)

    def test_add_user_raises_exception_on_exception(
        self,
        mock_globals: dict[str, MagicMock],
        mock_user_service: MagicMock,
        mock_scheduler_logger: MagicMock,
    ) -> None:
        """Verify that add_user_to_scheduler raises exception on exception.

        :param mock_globals: Mocked global scheduler instance
        :type mock_globals: dict[str, MagicMock]
        :param mock_user_service: Mocked user_service
        :type mock_user_service: MagicMock
        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        mock_globals["instance"].add_user.side_effect = Exception(DB_ERROR)

        with pytest.raises(SchedulerOperationError):
            add_user_to_scheduler(TEST_USER_ID)

    def test_add_user_raises_exception_when_user_not_found(
        self,
        mock_globals: dict[str, MagicMock],
        mock_user_service: MagicMock,
        mock_scheduler_logger: MagicMock,
    ) -> None:
        """Verify that add_user_to_scheduler raises exception when user is not found.

        :param mock_globals: Mocked global scheduler instance
        :type mock_globals: dict[str, MagicMock]
        :param mock_user_service: Mocked user_service
        :type mock_user_service: MagicMock
        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        mock_globals["instance"].add_user.side_effect = SchedulerOperationError(
            f"User {TEST_USER_ID} not found for scheduler addition",
            TEST_USER_ID,
            "add_user",
        )

        with pytest.raises(SchedulerOperationError):
            add_user_to_scheduler(TEST_USER_ID)

    def test_add_user_raises_exception_when_scheduler_not_initialized(self) -> None:
        """Verify that add_user_to_scheduler raises exception when scheduler is not initialized.

        :returns: None
        :rtype: None
        """
        with patch("src.bot.scheduler._global_scheduler_instance", None):
            with pytest.raises(SchedulerOperationError):
                add_user_to_scheduler(TEST_USER_ID)

    def test_remove_user_success(
        self, mock_globals: dict[str, MagicMock], mock_scheduler_logger: MagicMock
    ) -> None:
        """Verify that a user's job is successfully removed.

        :param mock_globals: Mocked global scheduler instance
        :type mock_globals: dict[str, MagicMock]
        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        remove_user_from_scheduler(TEST_USER_ID)
        mock_globals["instance"].remove_user.assert_called_once_with(TEST_USER_ID)

    def test_remove_user_handles_nonexistent_job(
        self, mock_globals: dict[str, MagicMock], mock_scheduler_logger: MagicMock
    ) -> None:
        """Verify that non-existent job is handled gracefully.

        :param mock_globals: Mocked global scheduler instance
        :type mock_globals: dict[str, MagicMock]
        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        mock_globals["instance"].remove_user.side_effect = SchedulerOperationError(
            f"Error removing user {TEST_USER_ID} from scheduler: Job not found",
            TEST_USER_ID,
            "remove_user",
        )

        with pytest.raises(SchedulerOperationError) as exc:
            remove_user_from_scheduler(user_id=TEST_USER_ID)

        assert (
            f"Error removing user {TEST_USER_ID} from scheduler: Job not found"
            in str(exc.value)
        )

    def test_remove_user_raises_if_not_initialized(self) -> None:
        """Verify that SchedulerOperationError is raised if scheduler is not initialized."""
        with patch("src.bot.scheduler._global_scheduler_instance", None):
            with pytest.raises(SchedulerOperationError):
                remove_user_from_scheduler(TEST_USER_ID)

    def test_remove_user_logger_error_handling(
        self, mock_globals: dict[str, MagicMock], mock_scheduler_logger: MagicMock
    ) -> None:
        """Verify that logger.error exceptions are properly handled.

        :param mock_globals: Mocked global scheduler instance
        :type mock_globals: dict[str, MagicMock]
        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        # Mock remove_user to raise an exception directly
        mock_globals["instance"].remove_user.side_effect = Exception("Job not found")

        # This should raise SchedulerOperationError from global function
        with pytest.raises(SchedulerOperationError) as exc:
            remove_user_from_scheduler(TEST_USER_ID)

        # Check if the original error is wrapped
        assert "Job not found" in str(exc.value)

    def test_update_user_success(
        self,
        mock_globals: dict[str, MagicMock],
        mock_user_with_settings: MagicMock,
        mock_user_service: MagicMock,
        mock_scheduler_logger: MagicMock,
    ) -> None:
        """Verify that a user's schedule is successfully updated.

        :param mock_globals: Mocked global scheduler instance
        :type mock_globals: dict[str, MagicMock]
        :param mock_user_with_settings: Mocked user with valid settings
        :type mock_user_with_settings: MagicMock
        :param mock_user_service: Mocked user_service
        :type mock_user_service: MagicMock
        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        update_user_schedule(TEST_USER_ID)
        mock_globals["instance"].update_user_schedule.assert_called_once_with(
            TEST_USER_ID
        )

    def test_update_user_handles_nonexistent_job(
        self,
        mock_globals: dict[str, MagicMock],
        mock_user_with_settings: MagicMock,
        mock_user_service: MagicMock,
        mock_scheduler_logger: MagicMock,
    ) -> None:
        """Verify that non-existent job is handled during update.

        :param mock_globals: Mocked global scheduler instance
        :type mock_globals: dict[str, MagicMock]
        :param mock_user_with_settings: Mocked user with valid settings
        :type mock_user_with_settings: MagicMock
        :param mock_user_service: Mocked user_service
        :type mock_user_service: MagicMock
        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        mock_globals["instance"].update_user_schedule.side_effect = (
            SchedulerOperationError(
                f"Error updating schedule for user {TEST_USER_ID}: Job not found",
                TEST_USER_ID,
                "update_schedule",
            )
        )

        with pytest.raises(SchedulerOperationError) as exc:
            update_user_schedule(TEST_USER_ID)

        assert f"Error updating schedule for user {TEST_USER_ID}: Job not found" in str(
            exc.value
        )

    def test_update_user_raises_if_not_initialized(self) -> None:
        """Verify that SchedulerOperationError is raised if scheduler is not initialized."""
        with patch("src.bot.scheduler._global_scheduler_instance", None):
            with pytest.raises(SchedulerOperationError):
                update_user_schedule(TEST_USER_ID)

    def test_update_user_raises_if_user_not_found(
        self, mock_globals: dict[str, MagicMock], mock_user_service: MagicMock
    ) -> None:
        """Verify that SchedulerOperationError is raised if user not found.

        :param mock_globals: Mocked global scheduler instance
        :type mock_globals: dict[str, MagicMock]
        :param mock_user_service: Mocked user_service
        :type mock_user_service: MagicMock
        """
        mock_globals["instance"].update_user_schedule.side_effect = (
            SchedulerOperationError(
                f"User {TEST_USER_ID} not found for schedule update",
                TEST_USER_ID,
                "update_schedule",
            )
        )

        with pytest.raises(SchedulerOperationError):
            update_user_schedule(TEST_USER_ID)

    def test_update_user_raises_if_job_creation_fails(
        self,
        mock_globals: dict[str, MagicMock],
        mock_user_with_settings: MagicMock,
        mock_user_service: MagicMock,
    ) -> None:
        """Verify that SchedulerOperationError is raised if job creation fails.

        :param mock_globals: Mocked global scheduler instance
        :type mock_globals: dict[str, MagicMock]
        :param mock_user_with_settings: Mocked user with valid settings
        :type mock_user_with_settings: MagicMock
        :param mock_user_service: Mocked user_service
        :type mock_user_service: MagicMock
        """
        mock_globals["instance"].update_user_schedule.side_effect = (
            SchedulerOperationError(
                "Job creation failed", TEST_USER_ID, "create_notification_job"
            )
        )

        with pytest.raises(SchedulerOperationError):
            update_user_schedule(TEST_USER_ID)

    def test_update_user_raises_on_exception(
        self, mock_globals: dict[str, MagicMock], mock_user_service: MagicMock
    ) -> None:
        """Verify that SchedulerOperationError is raised on unexpected exception.

        :param mock_globals: Mocked global scheduler instance
        :type mock_globals: dict[str, MagicMock]
        :param mock_user_service: Mocked user_service
        :type mock_user_service: MagicMock
        """
        mock_globals["instance"].update_user_schedule.side_effect = (
            SchedulerOperationError(
                f"Error updating schedule for user {TEST_USER_ID}: {DB_ERROR}",
                TEST_USER_ID,
                "update_schedule",
            )
        )

        with pytest.raises(SchedulerOperationError) as exc:
            update_user_schedule(TEST_USER_ID)
        assert f"Error updating schedule for user {TEST_USER_ID}: {DB_ERROR}" in str(
            exc.value
        )


@patch("src.bot.scheduler.user_service.get_all_users")
class TestSetupUserNotificationSchedules:
    """Tests for the setup_user_notification_schedules function."""

    def test_schedules_jobs_for_all_users(
        self,
        mock_get_all_users: MagicMock,
        mock_app: MagicMock,
        mock_user_with_settings: MagicMock,
    ) -> None:
        """Verify that jobs are created for all users with settings.

        :param mock_get_all_users: Mocked user_service.get_all_users
        :type mock_get_all_users: MagicMock
        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        :param mock_user_with_settings: Mocked user with valid settings
        :type mock_user_with_settings: MagicMock
        """
        mock_get_all_users.return_value = [mock_user_with_settings]
        mock_create_job = MagicMock()

        with patch.object(
            NotificationScheduler, "_create_user_notification_job", mock_create_job
        ):
            setup_user_notification_schedules(mock_app)

        mock_create_job.assert_called_once()

    def test_logs_info_if_no_users_found(
        self,
        mock_get_all_users: MagicMock,
        mock_app: MagicMock,
        mock_scheduler_logger: MagicMock,
    ) -> None:
        """Verify an info message is logged when no users are in the database.

        :param mock_get_all_users: Mocked user_service.get_all_users
        :type mock_get_all_users: MagicMock
        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        mock_get_all_users.return_value = []

        setup_user_notification_schedules(mock_app)
        mock_scheduler_logger.info.assert_called_once_with(
            "No users found for notification schedules"
        )

    def test_raises_scheduler_setup_error_on_exception(
        self, mock_get_all_users: MagicMock, mock_app: MagicMock
    ) -> None:
        """Verify that a SchedulerSetupError is raised on database failure.

        :param mock_get_all_users: Mocked user_service.get_all_users
        :type mock_get_all_users: MagicMock
        :param mock_app: Mocked Application instance
        :type mock_app: MagicMock
        """
        mock_get_all_users.side_effect = Exception(DB_ERROR)

        with pytest.raises(SchedulerSetupError):
            setup_user_notification_schedules(mock_app)


class TestSchedulerLifecycle:
    """Tests for start_scheduler and stop_scheduler functions."""

    def test_start_scheduler_calls_start(
        self, mock_scheduler_logger: MagicMock
    ) -> None:
        """Verify that start_scheduler calls the scheduler's start method.

        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        mock_scheduler = MagicMock()
        start_scheduler(mock_scheduler)
        mock_scheduler.start.assert_called_once()
        mock_scheduler_logger.info.assert_called_once_with(
            "User notification scheduler started successfully"
        )

    def test_stop_scheduler_calls_shutdown(
        self, mock_scheduler_logger: MagicMock
    ) -> None:
        """Verify that stop_scheduler calls the scheduler's shutdown method.

        :param mock_scheduler_logger: Mocked logger for scheduler module
        :type mock_scheduler_logger: MagicMock
        """
        mock_scheduler = MagicMock()
        stop_scheduler(mock_scheduler)
        mock_scheduler.shutdown.assert_called_once()
        mock_scheduler_logger.info.assert_called_once_with(
            "User notification scheduler stopped successfully"
        )
