"""Event bus for in-process publish/subscribe pattern.

This module provides a simple event bus for decoupling handlers from
the scheduler. Handlers publish events, and the event bus routes them
to registered subscribers.
"""

from collections.abc import Callable, Coroutine
from typing import Any

from ..utils.config import BOT_NAME
from ..utils.logger import get_logger

logger = get_logger(f"{BOT_NAME}.EventBus")

# Type alias for async event handlers
EventHandler = Callable[..., Coroutine[Any, Any, None]]


class EventBus:
    """Simple in-process event bus with async handler support.

    Handlers subscribe to event types and receive notifications when
    events of that type are published. All handlers are executed
    asynchronously.

    Example usage::

        event_bus = EventBus()

        async def handle_settings_changed(event: UserSettingsChangedEvent) -> None:
            await scheduler.update_user_schedule(event.user_id)

        event_bus.subscribe(UserSettingsChangedEvent, handle_settings_changed)

        # Later, in a handler:
        await event_bus.publish(UserSettingsChangedEvent(user_id=123, ...))

    :ivar _handlers: Mapping of event types to list of handlers
    """

    def __init__(self) -> None:
        """Initialize the event bus with empty handler registry.

        :returns: None
        """
        self._handlers: dict[type, list[EventHandler]] = {}

    def subscribe(
        self,
        event_type: type,
        handler: EventHandler,
    ) -> None:
        """Subscribe a handler to an event type.

        Multiple handlers can subscribe to the same event type.
        Handlers are called in subscription order.

        :param event_type: Type of event to subscribe to
        :type event_type: type
        :param handler: Async function to call when event is published
        :type handler: EventHandler
        :returns: None
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)
        logger.debug(f"Subscribed handler {handler.__name__} to {event_type.__name__}")

    def unsubscribe(
        self,
        event_type: type,
        handler: EventHandler,
    ) -> None:
        """Unsubscribe a handler from an event type.

        :param event_type: Type of event to unsubscribe from
        :type event_type: type
        :param handler: Handler function to remove
        :type handler: EventHandler
        :returns: None
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.debug(
                    f"Unsubscribed handler {handler.__name__} from {event_type.__name__}"
                )
            except ValueError:
                logger.warning(
                    f"Handler {handler.__name__} not found for {event_type.__name__}"
                )

    async def publish(self, event: object) -> None:
        """Publish an event to all subscribed handlers.

        All handlers for the event type are called asynchronously.
        Errors in individual handlers are logged but don't prevent
        other handlers from executing.

        :param event: Event instance to publish
        :type event: object
        :returns: None
        """
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        if not handlers:
            logger.debug(f"No handlers registered for {event_type.__name__}")
            return

        logger.debug(f"Publishing {event_type.__name__} to {len(handlers)} handler(s)")

        for handler in handlers:
            try:
                await handler(event)
            except Exception as error:
                logger.error(
                    f"Error in handler {handler.__name__} for "
                    f"{event_type.__name__}: {error}",
                    exc_info=True,
                )

    def clear(self) -> None:
        """Remove all registered handlers.

        :returns: None
        """
        self._handlers.clear()
        logger.debug("Cleared all event handlers")

    def get_handlers(self, event_type: type) -> list[EventHandler]:
        """Get list of handlers for an event type.

        :param event_type: Type of event to get handlers for
        :type event_type: type
        :returns: List of registered handlers
        :rtype: list[EventHandler]
        """
        return self._handlers.get(event_type, []).copy()
