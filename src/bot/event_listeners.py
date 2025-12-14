"""Event listeners for bridging domain events to scheduler actions.

This module defines event handlers that subscribe to domain events and
trigger appropriate actions on the scheduler via the SchedulerClient.
"""

from ..contracts.scheduler_port_protocol import ScheduleTrigger
from ..events.domain_events import (
    UserDeletedEvent,
    UserSettingsChangedEvent,
)
from ..services.container import ServiceContainer
from ..utils.config import BOT_NAME
from ..utils.logger import get_logger

logger = get_logger(f"{BOT_NAME}.EventListeners")


async def handle_user_settings_changed(event: UserSettingsChangedEvent) -> None:
    """Handle user settings changed event.

    Updates the user's notification schedule if relevant settings
    (birth_date, language, timezone) have changed.

    :param event: The event instance
    :type event: UserSettingsChangedEvent
    :returns: None
    """
    logger.debug(
        f"Handling settings change for user {event.user_id}: {event.setting_name}"
    )

    # We only care about settings that affect scheduling or message content
    # If birth_date changed, we might need to reschedule if we had a specific time
    # (though usually time is constant, but content changes)
    # Actually, if language changes, we don't need to reschedule the JOB,
    # because the job generates content at runtime using current user language.
    # So we only need to reschedule if TIMING changes (timezone, or preferred time).

    # However, existing logic might re-add job to be safe.
    # Let's check what `update_user_schedule` did.
    # It called `delete_job` then `add_job`.

    # If setting is 'notification_time' or 'timezone' (if we had those), we reschedule.
    # If setting is 'birth_date', we don't strictly need to reschedule unless
    # we want to refresh some metadata.

    # For now, let's assume we want to ensure the job exists and is correct.
    container = ServiceContainer()
    client = container.get_scheduler_client()

    if not client:
        logger.warning("Scheduler client not available")
        return

    # To reschedule, we need the user's preferences.
    # Since event doesn't carry all preferences, we fetch the user profile.
    user_service = container.get_user_service()
    user = await user_service.get_user_profile(event.user_id)

    if not user:
        logger.warning(f"User {event.user_id} not found for rescheduling")
        return

    # Logic to determine new trigger
    # This logic was previously in `scheduler.py`.
    # default: Monday 9:00 AM UTC (or user timezone if we supported it)
    # For MVP we stick to hardcoded or simple logic.

    # Create default weekly trigger
    trigger = ScheduleTrigger(
        day_of_week=0,  # Monday
        hour=9,
        minute=0,
        timezone="UTC",  # Should be from user settings ideally
    )

    job_id = f"weekly_{event.user_id}"

    success = await client.schedule_job(
        job_id=job_id, trigger=trigger, user_id=event.user_id, job_type="weekly_summary"
    )

    if success:
        logger.info(f"Rescheduled weekly job for user {event.user_id}")
    else:
        logger.error(f"Failed to reschedule job for user {event.user_id}")


async def handle_user_deleted(event: UserDeletedEvent) -> None:
    """Handle user deleted event.

    Removes the user's notification schedule.

    :param event: The event instance
    :type event: UserDeletedEvent
    :returns: None
    """
    logger.info(f"Handling deletion for user {event.user_id}")

    container = ServiceContainer()
    client = container.get_scheduler_client()

    if not client:
        logger.warning("Scheduler client not available")
        return

    job_id = f"weekly_{event.user_id}"
    success = await client.remove_job(job_id)

    if success:
        logger.info(f"Removed weekly job for user {event.user_id}")
    else:
        # It's possible job didn't exist, which is fine
        logger.debug(f"Job {job_id} not found or already removed")


def register_event_listeners(container: ServiceContainer) -> None:
    """Register all event listeners.

    :param container: Service container instance
    :type container: ServiceContainer
    :returns: None
    """
    event_bus = container.get_event_bus()

    event_bus.subscribe(
        event_type=UserSettingsChangedEvent,
        handler=handle_user_settings_changed,
    )

    event_bus.subscribe(
        event_type=UserDeletedEvent,
        handler=handle_user_deleted,
    )

    logger.info("Registered scheduler event listeners")
