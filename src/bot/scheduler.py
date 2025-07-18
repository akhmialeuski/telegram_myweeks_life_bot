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
from telegram.ext import Application
from telegram import User as TelegramUser

from ..core.messages import generate_message_week
from ..database.models import WeekDay
from ..database.service import user_service
from ..utils.config import BOT_NAME, DEFAULT_LANGUAGE
from ..utils.logger import get_logger

logger = get_logger(f"{BOT_NAME}.Scheduler")

# Global scheduler instance for dynamic updates
_scheduler_instance: AsyncIOScheduler = None
_application_instance: Application = None


async def send_weekly_message_to_user(application: Application, user_id: int) -> None:
    """Send a weekly notification message to a specific user.

    This function sends personalized life statistics to a specific user, identical
    to what they would receive from the /weeks command. The message includes:
    - Current age and weeks lived
    - Remaining weeks based on life expectancy
    - Life percentage completed
    - Days until next birthday
    - Subscription-specific additional content

    The function handles the complete message generation process:
    1. Retrieves user profile from database
    2. Creates mock Telegram User object for message generation
    3. Generates localized message using core message functions
    4. Sends message via Telegram Bot API
    5. Logs success or failure for monitoring

    Error handling ensures that failures for one user don't affect others,
    and all errors are logged for debugging purposes.

    :param application: The running Application instance containing bot credentials
    :type application: Application
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
        telegram_user = TelegramUser(
            id=user.telegram_id,
            is_bot=False,
            first_name=user.first_name or "User",
            username=user.username,
            language_code=user.settings.language if user.settings else DEFAULT_LANGUAGE,
        )

        # Generate the same message as /weeks command using core message functions
        # This ensures consistency between manual commands and scheduled notifications
        message_text = generate_message_week(user_info=telegram_user)

        # Send message to user via Telegram Bot API
        # Uses HTML parse mode for rich text formatting
        await application.bot.send_message(
            chat_id=user_id,
            text=message_text,
            parse_mode="HTML",
        )

        logger.debug(f"Successfully sent weekly notification to user {user_id}")

    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.error(f"Failed to send weekly notification to user {user_id}: {error}")


def _create_user_notification_job(user, application: Application, scheduler: AsyncIOScheduler) -> bool:
    """Create a notification job for a specific user.

    This helper function creates a cron job for a single user based on their
    notification settings. It handles validation and job creation in a reusable way.

    :param user: User object with settings
    :type user: User
    :param application: The running Application instance
    :type application: Application
    :param scheduler: The scheduler instance to add the job to
    :type scheduler: AsyncIOScheduler
    :returns: True if job was created successfully, False otherwise
    :rtype: bool
    """
    try:
        # Validate user has settings configured
        if not user.settings:
            logger.warning(f"No settings found for user {user.telegram_id}")
            return False

        # Check if notifications are enabled for this user
        if not user.settings.notifications:
            logger.debug(f"Notifications disabled for user {user.telegram_id}")
            return False

        # Extract notification preferences from user settings
        notification_day = user.settings.notifications_day
        notification_time = user.settings.notifications_time

        # Validate that both day and time are configured
        if not notification_day or not notification_time:
            logger.warning(f"Incomplete notification settings for user {user.telegram_id}")
            return False

        # Convert WeekDay enum to cron-compatible weekday number (0-6)
        # Uses the built-in WeekDay class method for consistency
        cron_day = WeekDay.get_weekday_number(notification_day)

        # Extract hour and minute from time object for cron trigger
        hour = notification_time.hour
        minute = notification_time.minute

        # Create unique job identifier for this user
        # This prevents job conflicts and allows individual management
        job_id = f"weekly_notification_user_{user.telegram_id}"

        # Add cron job to scheduler for this specific user
        # CronTrigger provides precise scheduling based on day and time
        scheduler.add_job(
            func=send_weekly_message_to_user,
            trigger=CronTrigger(
                day_of_week=cron_day,
                hour=hour,
                minute=minute,
            ),
            args=[application, user.telegram_id],
            id=job_id,
            name=f"Weekly notification for user {user.telegram_id}",
            replace_existing=True,  # Replace existing job if user reconfigures
        )

        logger.info(
            f"Successfully created notification job for user {user.telegram_id}: "
            f"{notification_day.value} at {hour:02d}:{minute:02d}"
        )
        return True

    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.error(f"Failed to create notification job for user {user.telegram_id}: {error}")
        return False


def add_user_to_scheduler(user_id: int) -> bool:
    """Add a new user to the notification scheduler.

    This function adds a single user to the running scheduler without
    affecting other users' schedules. It's efficient for adding new users
    without regenerating all schedules.

    :param user_id: Telegram user ID to add to scheduler
    :type user_id: int
    :returns: True if user was added successfully, False otherwise
    :rtype: bool
    """
    global _scheduler_instance, _application_instance

    if not _scheduler_instance or not _application_instance:
        logger.error("Scheduler not initialized, cannot add user")
        return False

    try:
        # Get user profile from database
        user = user_service.get_user_profile(user_id)
        if not user:
            logger.warning(f"User {user_id} not found for scheduler addition")
            return False

        # Create notification job for this user
        success = _create_user_notification_job(user, _application_instance, _scheduler_instance)

        if success:
            logger.info(f"Successfully added user {user_id} to notification scheduler")
        else:
            logger.warning(f"Failed to add user {user_id} to notification scheduler")

        return success

    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.error(f"Error adding user {user_id} to scheduler: {error}")
        return False


def remove_user_from_scheduler(user_id: int) -> bool:
    """Remove a user from the notification scheduler.

    This function removes a user's notification job from the scheduler
    when they are deleted or disable notifications.

    :param user_id: Telegram user ID to remove from scheduler
    :type user_id: int
    :returns: True if user was removed successfully, False otherwise
    :rtype: bool
    """
    global _scheduler_instance

    if not _scheduler_instance:
        logger.error("Scheduler not initialized, cannot remove user")
        return False

    try:
        # Remove existing job for this user
        # Create job_id outside of inner try to allow outer except coverage
        job_id = f"weekly_notification_user_{user_id}"

        # Try to remove the job - if it doesn't exist, it will raise an exception
        try:
            _scheduler_instance.remove_job(job_id)
            logger.info(f"Successfully removed user {user_id} from notification scheduler")
        except Exception as job_error:
            # Job might not exist, which is fine
            logger.debug(f"Job for user {user_id} not found in scheduler (already removed): {job_error}")

        return True

    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.error(f"Error removing user {user_id} from scheduler: {error}")
        return False


def update_user_schedule(user_id: int) -> bool:
    """Update notification schedule for an existing user.

    This function updates the notification schedule for a specific user
    when their settings change. It removes the old job and creates a new one
    with updated settings.

    :param user_id: Telegram user ID to update schedule for
    :type user_id: int
    :returns: True if schedule was updated successfully, False otherwise
    :rtype: bool
    """
    global _scheduler_instance, _application_instance

    if not _scheduler_instance or not _application_instance:
        logger.error("Scheduler not initialized, cannot update user schedule")
        return False

    try:
        # Remove existing job for this user
        job_id = f"weekly_notification_user_{user_id}"

        # Try to remove the job - if it doesn't exist, it will raise an exception
        try:
            _scheduler_instance.remove_job(job_id)
            logger.debug(f"Removed existing notification job for user {user_id}")
        except Exception as job_error:
            # Job might not exist, which is fine
            logger.debug(f"Job for user {user_id} not found in scheduler (already removed): {job_error}")

        # Get updated user profile from database
        user = user_service.get_user_profile(user_id)
        if not user:
            logger.warning(f"User {user_id} not found for schedule update")
            return False

        # Create new notification job with updated settings
        success = _create_user_notification_job(user, _application_instance, _scheduler_instance)

        if success:
            logger.info(f"Successfully updated notification schedule for user {user_id}")
        else:
            logger.warning(f"Failed to update notification schedule for user {user_id}")

        return success

    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.error(f"Error updating schedule for user {user_id}: {error}")
        return False


def setup_user_notification_schedules(
    application: Application,
    scheduler: AsyncIOScheduler = None,
) -> bool:
    """Set up individual notification schedules for each user.

    This function implements a comprehensive notification scheduling system that:
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

    The function returns a configured AsyncIOScheduler instance that can be
    started and stopped by the application lifecycle management.

    :param application: The running Application instance for message sending
    :type application: Application
    :param scheduler: Optional existing scheduler instance to use
    :type scheduler: AsyncIOScheduler
    :returns: True if setup was successful, False otherwise
    :rtype: bool
    :raises Exception: If critical database or scheduler setup fails
    """
    global _scheduler_instance, _application_instance

    # Use provided scheduler or create new one
    if scheduler is None:
        scheduler = AsyncIOScheduler()

    # Store global references for dynamic updates
    _scheduler_instance = scheduler
    _application_instance = application

    try:
        # Retrieve all users from database with complete profiles
        # This includes settings and subscription information
        users = user_service.get_all_users()

        if not users:
            logger.info("No users found for notification schedules")
            return True

        logger.info(f"Setting up notification schedules for {len(users)} users")

        # Process each user individually to set up their notification schedule
        for user in users:
            logger.info(f"Setting up notification schedule for user {user.telegram_id}")
            _create_user_notification_job(user, application, scheduler)

        logger.info(f"Successfully set up notification schedules for {len(users)} users")
        return True

    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.error(f"Error setting up notification schedules: {error}")
        return False


def start_scheduler(scheduler: AsyncIOScheduler) -> None:
    """Start the notification scheduler.

    This function activates the AsyncIOScheduler instance, enabling all configured
    notification jobs to run according to their schedules. The scheduler will
    automatically execute jobs at their specified times without further intervention.

    The scheduler runs in the background and handles:
    - Automatic job execution at scheduled times
    - Job queue management and prioritization
    - Error handling and retry logic
    - Resource management and cleanup

    :param scheduler: The configured AsyncIOScheduler instance to start
    :type scheduler: AsyncIOScheduler
    :returns: None
    :raises RuntimeError: If scheduler is already running or fails to start
    """
    scheduler.start()
    logger.info("User notification scheduler started successfully")


def stop_scheduler(scheduler: AsyncIOScheduler) -> None:
    """Stop the notification scheduler.

    This function gracefully shuts down the AsyncIOScheduler instance, ensuring
    that all running jobs are properly terminated and resources are cleaned up.
    This is important for application shutdown to prevent resource leaks and
    ensure clean termination.

    The shutdown process includes:
    - Stopping all running jobs
    - Cleaning up scheduler resources
    - Logging shutdown status for monitoring

    :param scheduler: The running AsyncIOScheduler instance to stop
    :type scheduler: AsyncIOScheduler
    :returns: None
    :raises RuntimeError: If scheduler shutdown fails
    """
    global _scheduler_instance, _application_instance

    scheduler.shutdown()
    _scheduler_instance = None
    _application_instance = None
    logger.info("User notification scheduler stopped successfully")
