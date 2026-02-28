"""Scheduler jobs execution logic.

This module defines the callable functions that execute scheduler jobs.
These functions are run by the scheduler worker process when a job is triggered.
"""

from ..services.container import ServiceContainer
from ..services.notification_service import (
    MESSAGE_TYPE_DAILY_SUMMARY,
    MESSAGE_TYPE_MONTHLY_SUMMARY,
    MESSAGE_TYPE_WEEKLY_SUMMARY,
)
from ..utils.config import BOT_NAME
from ..utils.logger import get_logger

logger = get_logger(f"{BOT_NAME}.SchedulerJobs")


async def execute_notification_job(
    user_id: int,
    message_type: str = MESSAGE_TYPE_WEEKLY_SUMMARY,
) -> None:
    """Execute a notification job for a user.

    This function is called by the scheduler when a scheduled notification
    job is triggered. It gets necessary services from the container and
    executes the notification generation and delivery workflow.

    :param user_id: Telegram user ID
    :type user_id: int
    :param message_type: Type of notification to send
    :type message_type: str
    :returns: None
    """
    logger.info(f"Executing {message_type} job for user {user_id}")

    try:
        container = ServiceContainer()
        notification_service = container.get_notification_service()
        gateway = container.get_notification_gateway()

        # Supported summary types
        summary_types = [
            MESSAGE_TYPE_DAILY_SUMMARY,
            MESSAGE_TYPE_WEEKLY_SUMMARY,
            MESSAGE_TYPE_MONTHLY_SUMMARY,
        ]

        # Determine payload generation based on message type
        payload = None
        if message_type in summary_types:
            payload = await notification_service.generate_summary(
                user_id=user_id, message_type=message_type
            )
        else:
            logger.warning(f"Unknown message type: {message_type}")
            return

        if not payload:
            logger.warning(f"No payload generated for user {user_id} ({message_type})")
            return

        # Send notification
        result = await gateway.send_notification(payload)

        if result.success:
            logger.info(f"Successfully sent {message_type} to user {user_id}")
            # Optional: Publish NotificationSentEvent if needed in worker process
            # await container.event_bus.publish(NotificationSentEvent(...))
        else:
            logger.error(
                f"Failed to send {message_type} to user {user_id}: {result.error}"
            )

    except Exception as error:
        logger.error(
            f"Error executing {message_type} job for user {user_id}: {error}",
            exc_info=True,
        )


def execute_scheduler_job_wrapper(
    job_type: str,
    kwargs: dict,
) -> None:
    """Wrapper function to execute jobs from scheduler.

    This wrapper handles the async execution in a sync callback if needed,
    but APScheduler's AsyncIOScheduler supports async/await directly.

    :param job_type: Type of job
    :param kwargs: Job arguments
    :raises Exception: If job execution fails
    """
    logger.info(f"Executing {job_type} job with kwargs: {kwargs}")
    # This wrapper might not be needed if we pass execute_notification_job directly
    # But useful for routing if we have a single entry point
    pass
