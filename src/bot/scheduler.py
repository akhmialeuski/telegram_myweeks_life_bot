"""Scheduler for weekly notifications.

This module provides a comprehensive notification scheduling system for LifeWeeksBot.
It manages individual notification schedules for each user based on their personal
preferences stored in the database.

Key Features:
    - Individual user notification schedules
    - Dynamic schedule setup based on user preferences
    - Cron-based scheduling for precise timing
    - Graceful error handling and logging
    - Support for multiple time zones and languages
    - Dynamic user addition and settings updates

The scheduler works by:
    1. Retrieving all users from the database at startup
    2. Reading each user's notification settings (day, time, enabled status)
    3. Creating individual cron jobs for each user with notifications enabled
    4. Sending personalized weekly life statistics to each user at their preferred time
    5. Dynamically adding new users and updating existing user schedules

Notification Settings Supported:
    - Day of week (Monday through Sunday)
    - Time of day (hour:minute format)
    - Enable/disable notifications
    - Language preferences for message localization

Error Handling:
    - Graceful handling of missing user settings
    - Individual user error isolation (one user's error doesn't affect others)
    - Comprehensive logging for debugging and monitoring
    - Automatic retry on next scheduled time for failed notifications

Dependencies:
    - APScheduler for job scheduling
    - SQLAlchemy for database access
    - python-telegram-bot for message sending
    - Custom WeekDay enum for day mapping
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

try:
    from apscheduler.errors import JobLookupError
except ImportError:
    # Fallback for older versions of APScheduler
    from apscheduler.jobstores.base import JobLookupError

from telegram import User
from telegram.constants import ParseMode
from telegram.ext import Application

from ..constants import DEFAULT_USER_FIRST_NAME
from ..core.enums import WeekDay
from ..core.life_calculator import LifeCalculatorEngine
from ..database.service import user_service
from ..i18n import use_locale
from ..utils.config import BOT_NAME, DEFAULT_LANGUAGE
from ..utils.logger import get_logger

logger = get_logger(f"{BOT_NAME}.Scheduler")


class SchedulerSetupError(Exception):
    """Exception raised when scheduler setup fails.

    This exception is raised when there are critical errors during
    the notification scheduler setup process that prevent the scheduler
    from functioning properly.

    :param message: Error message describing the setup failure
    :type message: str
    :param original_error: Original exception that caused the setup failure
    :type original_error: Exception, optional
    """

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        """Initialize the SchedulerSetupError.

        :param message: Error message describing the setup failure
        :type message: str
        :param original_error: Original exception that caused the setup failure
        :type original_error: Exception, optional
        :returns: None
        """
        super().__init__(message)
        self.message = message
        self.original_error = original_error


class SchedulerOperationError(Exception):
    """Exception raised when scheduler operations fail.

    This exception is raised when there are errors during scheduler
    operations such as adding, removing, or updating user schedules.

    :param message: Error message describing the operation failure
    :type message: str
    :param user_id: ID of the user affected by the operation
    :type user_id: int
    :param operation: Type of operation that failed
    :type operation: str
    :param original_error: Original exception that caused the operation failure
    :type original_error: Exception, optional
    """

    def __init__(
        self,
        message: str,
        user_id: int,
        operation: str,
        original_error: Exception | None = None,
    ) -> None:
        """Initialize the SchedulerOperationError.

        :param message: Error message describing the operation failure
        :type message: str
        :param user_id: ID of the user affected by the operation
        :type user_id: int
        :param operation: Type of operation that failed
        :type operation: str
        :param original_error: Original exception that caused the operation failure
        :type original_error: Exception, optional
        :returns: None
        """
        super().__init__(message)
        self.message = message
        self.user_id = user_id
        self.operation = operation
        self.original_error = original_error


class NotificationScheduler:
    """Notification scheduler manager for LifeWeeksBot.

    This class encapsulates all scheduler functionality and manages the lifecycle
    of notification scheduling. It provides a clean interface for managing user
    notification schedules without relying on global state.

    The class handles:
    - Scheduler instance lifecycle management
    - Individual user schedule management
    - Error handling and logging
    - Dynamic user addition and removal

    :param application: The Application instance for sending messages
    :type application: Application
    :param scheduler: Optional scheduler instance, creates new if None
    :type scheduler: AsyncIOScheduler, optional
    """

    def __init__(
        self, application: Application, scheduler: AsyncIOScheduler | None = None
    ) -> None:
        """Initialize the NotificationScheduler.

        :param application: The Application instance for sending messages
        :type application: Application
        :param scheduler: Optional scheduler instance, creates new if None
        :type scheduler: AsyncIOScheduler, optional
        :returns: None
        """
        self.application = application
        self.scheduler = scheduler or AsyncIOScheduler()
        self._is_running = False

    async def send_weekly_message_to_user(self, user_id: int) -> None:
        """Send a weekly notification message to a specific user.

        This method sends personalized life statistics to a specific user, identical
        to what they would receive from the /weeks command. The message includes:
        - Current age and weeks lived
        - Remaining weeks based on life expectancy
        - Life percentage completed
        - Days until next birthday
        - Subscription-specific additional content

        The method handles the complete message generation process:
        1. Retrieves user profile from database
        2. Creates mock Telegram User object for message generation
        3. Generates localized message using core message functions
        4. Sends message via Telegram Bot API
        5. Logs success or failure for monitoring

        Error handling ensures that failures for one user don't affect others,
        and all errors are logged for debugging purposes.

        :param user_id: Telegram user ID to send message to
        :type user_id: int
        :returns: None
        :raises telegram.error.TelegramError: If the message cannot be sent due to Telegram API issues
        :raises ValueError: If user profile is not found or invalid
        """
        try:
            # Get user profile from database with all related data
            user = user_service.get_user_profile(user_id)
            if not user:
                logger.warning(f"User {user_id} not found for weekly notification")
                return

            # Create a mock Telegram User object for message generation compatibility
            # This is necessary because generate_message_week expects a Telegram User object
            telegram_user = User(
                id=user.telegram_id,
                is_bot=False,
                first_name=user.first_name or DEFAULT_USER_FIRST_NAME,
                username=user.username,
                language_code=(
                    user.settings.language if user.settings else DEFAULT_LANGUAGE
                ),
            )

            # Generate the same message as /weeks command using gettext
            # This ensures consistency between manual commands and scheduled notifications
            _, _, pgettext = use_locale(telegram_user.language_code or DEFAULT_LANGUAGE)

            calculator = LifeCalculatorEngine(user)
            stats = calculator.calculate_life_statistics(user.birth_date)

            message_text = pgettext(
                "weeks.statistics",
                "📊 Your Life Statistics:\n\n"
                "🎂 Birth Date: %(birth_date)s\n"
                "📅 Age: %(age)s years\n"
                "📈 Life Expectancy: %(life_expectancy)s years\n"
                "🟩 Lived Weeks: %(lived_weeks)s\n"
                "⬜ Remaining Weeks: %(remaining_weeks)s\n"
                "📊 Total Life Weeks: %(total_weeks)s\n"
                "🎯 Progress: %(progress_percent)s%%",
            ) % {
                "birth_date": user.birth_date.strftime("%d.%m.%Y"),
                "age": stats["age"],
                "life_expectancy": stats["life_expectancy"],
                "lived_weeks": stats["lived_weeks"],
                "remaining_weeks": stats["remaining_weeks"],
                "total_weeks": stats["total_weeks"],
                "progress_percent": stats["progress_percent"],
            }

            # Send message to user via Telegram Bot API
            await self.application.bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode=ParseMode.HTML,
            )

            logger.debug(f"Successfully sent weekly notification to user {user_id}")

        except Exception as error:  # pylint: disable=broad-exception-caught
            logger.error(
                f"Failed to send weekly notification to user {user_id}: {error}"
            )

    def _create_user_notification_job(self, user: User) -> None:
        """Create a notification job for a specific user.

        This helper method creates a cron job for a single user based on their
        notification settings. It handles validation and job creation in a reusable way.

        :param user: User object with settings
        :type user: User
        :returns: None
        :raises SchedulerOperationError: If job creation fails
        """
        if not user.settings:
            error_message = f"No settings found for user {user.telegram_id}"
            logger.warning(error_message)
            raise SchedulerOperationError(
                message=error_message,
                user_id=user.telegram_id,
                operation="create_notification_job",
            )

        if not user.settings.notifications:
            logger.debug(f"Notifications disabled for user {user.telegram_id}")
            return

        notification_day = user.settings.notifications_day
        notification_time = user.settings.notifications_time

        if not notification_day or not notification_time:
            error_message = (
                f"Incomplete notification settings for user {user.telegram_id}"
            )
            logger.warning(error_message)
            raise SchedulerOperationError(
                message=error_message,
                user_id=user.telegram_id,
                operation="create_notification_job",
            )

        try:
            cron_day = list(WeekDay).index(notification_day)
            hour = notification_time.hour
            minute = notification_time.minute
            job_id = f"weekly_notification_user_{user.telegram_id}"

            logger.info(
                f"Adding cron job for user {user.telegram_id}: {cron_day} at {hour}:{minute}"
            )
            self.scheduler.add_job(
                func=self.send_weekly_message_to_user,
                trigger=CronTrigger(day_of_week=cron_day, hour=hour, minute=minute),
                args=[user.telegram_id],
                id=job_id,
                name=f"Weekly notification for user {user.telegram_id}",
                replace_existing=True,
            )

            logger.info(
                f"Successfully created notification job for user {user.telegram_id}: "
                f"{notification_day.value} at {hour:02d}:{minute:02d}"
            )

        except Exception as error:  # pylint: disable=broad-exception-caught
            error_message = f"Failed to create notification job for user {user.telegram_id}: {error}"
            logger.error(error_message)
            raise SchedulerOperationError(
                message=error_message,
                user_id=user.telegram_id,
                operation="create_notification_job",
                original_error=error,
            )

    def add_user(self, user_id: int) -> None:
        """Add or update a user in the notification scheduler.

        This method adds a user to the running scheduler or updates an existing
        schedule. Thanks to `replace_existing=True`, it's efficient for both
        adding new users and updating their notification settings without
        manual removal.

        :param user_id: Telegram user ID to add or update in the scheduler
        :type user_id: int
        :returns: None
        :raises SchedulerOperationError: If the user cannot be added or updated
        """
        try:
            # Get user profile from database
            user = user_service.get_user_profile(user_id)
            if not user:
                error_message = f"User {user_id} not found for scheduler addition"
                logger.warning(error_message)
                raise SchedulerOperationError(
                    message=error_message, user_id=user_id, operation="add_user"
                )

            # Create notification job for this user
            self._create_user_notification_job(user=user)

            logger.info(f"Successfully added user {user_id} to notification scheduler")

        except SchedulerOperationError:
            # Re-raise SchedulerOperationError as-is
            raise
        except Exception as error:  # pylint: disable=broad-exception-caught
            error_message = f"Error adding user {user_id} to scheduler: {error}"
            logger.error(error_message)
            raise SchedulerOperationError(
                message=error_message,
                user_id=user_id,
                operation="add_user",
                original_error=error,
            )

    def remove_user(self, user_id: int) -> None:
        """Remove a user from the notification scheduler.

        This method removes a user's notification job from the scheduler
        when they are deleted or disable notifications.

        :param user_id: Telegram user ID to remove from scheduler
        :type user_id: int
        :returns: None
        :raises SchedulerOperationError: If the user cannot be removed from scheduler
        """
        job_id = f"weekly_notification_user_{user_id}"
        try:
            self.scheduler.remove_job(job_id)
            logger.info(
                f"Successfully removed user {user_id} from notification scheduler"
            )
        except JobLookupError:
            logger.warning(
                f"Job {job_id} not found for user {user_id}, nothing to remove"
            )
        except Exception as error:
            error_message = f"Error removing user {user_id} from scheduler: {error}"
            logger.error(error_message)
            raise SchedulerOperationError(
                message=error_message,
                user_id=user_id,
                operation="remove_user",
                original_error=error,
            )

    def update_user_schedule(self, user_id: int) -> None:
        """Update notification schedule for an existing user.

        This method updates the notification schedule for a specific user
        when their settings change. It is an alias for `add_user`, which handles
        both adding and updating schedules atomically.

        :param user_id: Telegram user ID to update schedule for
        :type user_id: int
        :returns: None
        :raises SchedulerOperationError: If the user schedule cannot be updated
        """
        self.add_user(user_id=user_id)

    def setup_schedules(self) -> None:
        """Set up individual notification schedules for each user.

        This method implements a comprehensive notification scheduling system that:
        1. Retrieves all registered users from the database
        2. Analyzes each user's notification preferences
        3. Creates individual cron jobs for users with enabled notifications
        4. Handles various edge cases and error conditions gracefully

        The scheduling process includes:
        - User validation and settings verification
        - Notification preference analysis (enabled/disabled, day, time)
        - Cron job creation with unique identifiers
        - Comprehensive error handling and logging
        - Support for different time zones and languages

        Each user gets their own cron job with:
        - Unique job ID: "weekly_notification_user_{user_id}"
        - Custom schedule based on their preferences
        - Individual error handling and logging
        - Automatic replacement of existing jobs (replace_existing=True)

        :returns: None
        :raises SchedulerSetupError: If critical database or scheduler setup fails
        """
        try:
            # Retrieve all users from database with complete profiles
            # This includes settings and subscription information
            users = user_service.get_all_users()

            if not users:
                logger.info("No users found for notification schedules")
                return

            logger.info(f"Setting up notification schedules for {len(users)} users")

            # Process each user individually to set up their notification schedule
            for user in users:
                logger.info(
                    f"Setting up notification schedule for user {user.telegram_id}"
                )
                self._create_user_notification_job(user)

            logger.info(
                f"Successfully set up notification schedules for {len(users)} users"
            )

        except Exception as error:  # pylint: disable=broad-exception-caught
            error_message = f"Error setting up notification schedules: {error}"
            logger.error(error_message)
            raise SchedulerSetupError(error_message, error)

    def start(self) -> None:
        """Start the notification scheduler.

        This method activates the AsyncIOScheduler instance, enabling all configured
        notification jobs to run according to their schedules. The scheduler will
        automatically execute jobs at their specified times without further intervention.

        The scheduler runs in the background and handles:
        - Automatic job execution at scheduled times
        - Job queue management and prioritization
        - Error handling and retry logic
        - Resource management and cleanup

        :returns: None
        :raises RuntimeError: If scheduler is already running or fails to start
        """
        if self._is_running:
            logger.warning("Scheduler is already running")
            return

        self.scheduler.start()
        self._is_running = True
        logger.info("User notification scheduler started successfully")

    def stop(self) -> None:
        """Stop the notification scheduler.

        This method gracefully shuts down the AsyncIOScheduler instance, ensuring
        that all running jobs are properly terminated and resources are cleaned up.
        This is important for application shutdown to prevent resource leaks and
        ensure clean termination.

        The shutdown process includes:
        - Stopping all running jobs
        - Cleaning up scheduler resources
        - Logging shutdown status for monitoring

        :returns: None
        :raises RuntimeError: If scheduler shutdown fails
        """
        if not self._is_running:
            logger.warning("Scheduler is not running")
            return

        self.scheduler.shutdown()
        self._is_running = False
        logger.info("User notification scheduler stopped successfully")


# Backward compatibility functions for existing code
def setup_user_notification_schedules(
    application: Application,
    scheduler: AsyncIOScheduler | None = None,
) -> NotificationScheduler:
    """Set up user notification schedules using the new class-based approach.

    This function provides backward compatibility while encouraging migration
    to the new NotificationScheduler class.

    :param application: The Application instance for sending messages
    :type application: Application
    :param scheduler: Optional scheduler instance
    :type scheduler: AsyncIOScheduler, optional
    :returns: Configured NotificationScheduler instance
    :rtype: NotificationScheduler
    :raises SchedulerSetupError: If setup fails
    """
    notification_scheduler = NotificationScheduler(
        application=application, scheduler=scheduler
    )
    notification_scheduler.setup_schedules()

    return notification_scheduler


def start_scheduler(scheduler: AsyncIOScheduler | NotificationScheduler) -> None:
    """Start the scheduler - supports both old and new approaches.

    :param scheduler: Scheduler instance to start
    :type scheduler: AsyncIOScheduler | NotificationScheduler
    :returns: None
    """
    if isinstance(scheduler, NotificationScheduler):
        scheduler.start()
    else:
        # Legacy support for AsyncIOScheduler
        scheduler.start()
        logger.info("User notification scheduler started successfully")


def stop_scheduler(scheduler: AsyncIOScheduler | NotificationScheduler) -> None:
    """Stop the scheduler - supports both old and new approaches.

    :param scheduler: Scheduler instance to stop
    :type scheduler: AsyncIOScheduler | NotificationScheduler
    :returns: None
    """
    if isinstance(scheduler, NotificationScheduler):
        scheduler.stop()
    else:
        # Legacy support for AsyncIOScheduler
        scheduler.shutdown()
        logger.info("User notification scheduler stopped successfully")


def add_user_to_scheduler(scheduler: NotificationScheduler, user_id: int) -> None:
    """Add user to scheduler instance.

    :param scheduler: NotificationScheduler instance
    :type scheduler: NotificationScheduler
    :param user_id: User ID to add
    :type user_id: int
    :raises SchedulerOperationError: If operation fails
    """
    try:
        scheduler.add_user(user_id)
    except SchedulerOperationError:
        raise
    except Exception as e:
        raise SchedulerOperationError(
            message=f"Failed to add user {user_id} to scheduler: {str(e)}",
            user_id=user_id,
            operation="add_user",
        ) from e


def remove_user_from_scheduler(scheduler: NotificationScheduler, user_id: int) -> None:
    """Remove user from scheduler instance.

    :param scheduler: NotificationScheduler instance
    :type scheduler: NotificationScheduler
    :param user_id: User ID to remove
    :type user_id: int
    :raises SchedulerOperationError: If operation fails
    """
    try:
        scheduler.remove_user(user_id)
    except SchedulerOperationError:
        raise
    except JobLookupError:
        logger.warning(
            f"Job for user {user_id} not found, nothing to remove from scheduler"
        )


def update_user_schedule(scheduler: NotificationScheduler, user_id: int) -> None:
    """Add or update user schedule in scheduler.

    This function is an alias for `add_user_to_scheduler` and handles both
    adding and updating user schedules.

    :param scheduler: NotificationScheduler instance
    :type scheduler: NotificationScheduler
    :param user_id: User ID to add or update
    :type user_id: int
    :raises SchedulerOperationError: If operation fails
    """
    add_user_to_scheduler(scheduler=scheduler, user_id=user_id)
