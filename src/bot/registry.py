"""Handler registry for centralized handler management.

This module provides the HandlerRegistry class for managing command handlers,
their callbacks, text input handlers, and waiting states. It replaces the
previous dict-based approach with a more structured registry pattern.
"""

import logging
from typing import Any, Callable

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Type alias for handler methods
HandlerMethod = Callable[[Update, ContextTypes.DEFAULT_TYPE], Any]


class HandlerRegistry:
    """Registry for managing bot command handlers.

    This class provides centralized management for all registered handlers,
    including command handlers, callback handlers, text input handlers,
    and waiting state mappings.

    The registry allows:
    - Registering handlers by command name
    - Looking up handlers by command
    - Managing text input handlers for waiting states
    - Resolving waiting states to their target commands

    :ivar _handlers: Dictionary mapping command names to handler instances
    :type _handlers: dict[str, Any]
    :ivar _text_input_handlers: Dictionary mapping commands to text input methods
    :type _text_input_handlers: dict[str, HandlerMethod]
    :ivar _waiting_states: Dictionary mapping waiting states to command names
    :type _waiting_states: dict[str, str]
    """

    def __init__(self) -> None:
        """Initialize the handler registry with empty registrations.

        :returns: None
        """
        self._handlers: dict[str, Any] = {}
        self._text_input_handlers: dict[str, HandlerMethod] = {}
        self._waiting_states: dict[str, str] = {}

    def register(
        self,
        command: str,
        handler: Any,
        text_input_method: HandlerMethod | None = None,
        waiting_states: list[str] | None = None,
    ) -> None:
        """Register a handler for a command.

        :param command: Command name (without leading slash)
        :type command: str
        :param handler: Handler instance to register
        :type handler: Any
        :param text_input_method: Optional method for handling text input
        :type text_input_method: HandlerMethod | None
        :param waiting_states: Optional list of waiting state identifiers
        :type waiting_states: list[str] | None
        :returns: None
        """
        self._handlers[command] = handler
        logger.debug(f"Registered handler for command: /{command}")

        if text_input_method is not None:
            self._text_input_handlers[command] = text_input_method
            logger.debug(f"Registered text input handler for: /{command}")

        if waiting_states:
            for state in waiting_states:
                self._waiting_states[state] = command
            logger.debug(f"Registered waiting states for /{command}: {waiting_states}")

    def get_handler(self, command: str) -> Any | None:
        """Get handler instance by command name.

        :param command: Command name to look up
        :type command: str
        :returns: Handler instance or None if not found
        :rtype: Any | None
        """
        return self._handlers.get(command)

    def get_text_input_handler(self, command: str) -> HandlerMethod | None:
        """Get text input handler method by command name.

        :param command: Command name to look up
        :type command: str
        :returns: Text input handler method or None if not found
        :rtype: HandlerMethod | None
        """
        return self._text_input_handlers.get(command)

    def get_command_for_state(self, waiting_state: str) -> str | None:
        """Get command name for a waiting state.

        :param waiting_state: Waiting state identifier to look up
        :type waiting_state: str
        :returns: Command name or None if state not found
        :rtype: str | None
        """
        return self._waiting_states.get(waiting_state)

    def has_waiting_state(self, waiting_state: str) -> bool:
        """Check if a waiting state is registered.

        :param waiting_state: Waiting state identifier to check
        :type waiting_state: str
        :returns: True if state is registered, False otherwise
        :rtype: bool
        """
        return waiting_state in self._waiting_states

    def get_all_handlers(self) -> dict[str, Any]:
        """Get all registered handlers.

        :returns: Dictionary mapping command names to handler instances
        :rtype: dict[str, Any]
        """
        return self._handlers.copy()

    def get_all_waiting_states(self) -> dict[str, str]:
        """Get all registered waiting states.

        :returns: Dictionary mapping waiting states to command names
        :rtype: dict[str, str]
        """
        return self._waiting_states.copy()

    def clear(self) -> None:
        """Clear all registrations.

        Primarily useful for testing to reset registry state.

        :returns: None
        """
        self._handlers.clear()
        self._text_input_handlers.clear()
        self._waiting_states.clear()
        logger.debug("Cleared all handler registrations")
