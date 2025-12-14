"""State persistence protocol and implementations for conversation state storage.

This module provides an abstract protocol for state storage and a Telegram-specific
implementation that uses context.user_data for persistence.
"""

import time
import uuid
from typing import Any, Protocol

from telegram.ext import ContextTypes

from .states import ConversationState

# Constants for state storage keys
STATE_KEY = "waiting_for"
TIMESTAMP_KEY = "waiting_timestamp"
STATE_ID_KEY = "waiting_state_id"
CONTEXT_DATA_KEY = "conversation_context"

# Default timeout for state expiration (5 minutes)
DEFAULT_STATE_TIMEOUT_SECONDS: float = 300.0


class StatePersistenceProtocol(Protocol):
    """Protocol for conversation state storage.

    Implementations can store state in various backends:
    - TelegramContextPersistence: Uses context.user_data
    - RedisPersistence: For scalable deployments
    - DatabasePersistence: For persistent storage
    """

    async def get_state(
        self,
        user_id: int,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> ConversationState:
        """Get current conversation state for user.

        :param user_id: Telegram user ID
        :type user_id: int
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: Current conversation state
        :rtype: ConversationState
        """
        ...

    async def set_state(
        self,
        user_id: int,
        state: ConversationState,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Set conversation state for user.

        :param user_id: Telegram user ID
        :type user_id: int
        :param state: New conversation state
        :type state: ConversationState
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        ...

    async def clear_state(
        self,
        user_id: int,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Clear conversation state for user.

        :param user_id: Telegram user ID
        :type user_id: int
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        ...

    async def is_state_valid(
        self,
        user_id: int,
        expected_state: ConversationState,
        context: ContextTypes.DEFAULT_TYPE,
        max_age_seconds: float = DEFAULT_STATE_TIMEOUT_SECONDS,
    ) -> bool:
        """Check if current state matches expected and is not expired.

        :param user_id: Telegram user ID
        :type user_id: int
        :param expected_state: Expected conversation state
        :type expected_state: ConversationState
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :param max_age_seconds: Maximum age of state in seconds
        :type max_age_seconds: float
        :returns: True if state is valid and matches, False otherwise
        :rtype: bool
        """
        ...


class TelegramContextPersistence:
    """State persistence implementation using Telegram context.user_data.

    This implementation stores state directly in context.user_data with
    timestamp tracking for expiration and unique ID for race condition prevention.
    """

    async def get_state(
        self,
        user_id: int,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> ConversationState:
        """Get current conversation state for user.

        :param user_id: Telegram user ID (unused, kept for protocol compatibility)
        :type user_id: int
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: Current conversation state
        :rtype: ConversationState
        """
        state_value = context.user_data.get(STATE_KEY)
        return ConversationState.from_string(value=state_value)

    async def set_state(
        self,
        user_id: int,
        state: ConversationState,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Set conversation state for user with timestamp and ID.

        :param user_id: Telegram user ID (unused, kept for protocol compatibility)
        :type user_id: int
        :param state: New conversation state
        :type state: ConversationState
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        current_time = time.time()
        state_id = str(uuid.uuid4())

        context.user_data[STATE_KEY] = state.value
        context.user_data[TIMESTAMP_KEY] = current_time
        context.user_data[STATE_ID_KEY] = state_id

    async def clear_state(
        self,
        user_id: int,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Clear conversation state and associated metadata.

        :param user_id: Telegram user ID (unused, kept for protocol compatibility)
        :type user_id: int
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        context.user_data.pop(STATE_KEY, None)
        context.user_data.pop(TIMESTAMP_KEY, None)
        context.user_data.pop(STATE_ID_KEY, None)
        context.user_data.pop(CONTEXT_DATA_KEY, None)

    async def is_state_valid(
        self,
        user_id: int,
        expected_state: ConversationState,
        context: ContextTypes.DEFAULT_TYPE,
        max_age_seconds: float = DEFAULT_STATE_TIMEOUT_SECONDS,
    ) -> bool:
        """Check if current state matches expected and is not expired.

        Validates:
        - State matches expected state
        - Timestamp exists and is not expired
        - State ID exists (for race condition detection)

        :param user_id: Telegram user ID (unused, kept for protocol compatibility)
        :type user_id: int
        :param expected_state: Expected conversation state
        :type expected_state: ConversationState
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :param max_age_seconds: Maximum age of state in seconds
        :type max_age_seconds: float
        :returns: True if state is valid and matches, False otherwise
        :rtype: bool
        """
        waiting_for = context.user_data.get(STATE_KEY)
        timestamp = context.user_data.get(TIMESTAMP_KEY)
        state_id = context.user_data.get(STATE_ID_KEY)

        # Check if state matches expected
        if waiting_for != expected_state.value:
            return False

        # Check if timestamp exists and is not expired
        if timestamp is None:
            return False

        current_time = time.time()
        age = current_time - timestamp
        if age > max_age_seconds:
            return False

        # Check if state_id exists
        if state_id is None:
            return False

        return True

    async def get_context_data(
        self,
        user_id: int,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> dict[str, Any]:
        """Get conversation context data.

        :param user_id: Telegram user ID (unused, kept for protocol compatibility)
        :type user_id: int
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: Context data dictionary
        :rtype: dict[str, Any]
        """
        return context.user_data.get(CONTEXT_DATA_KEY, {})

    async def set_context_data(
        self,
        user_id: int,
        data: dict[str, Any],
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Set conversation context data.

        :param user_id: Telegram user ID (unused, kept for protocol compatibility)
        :type user_id: int
        :param data: Context data to store
        :type data: dict[str, Any]
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        context.user_data[CONTEXT_DATA_KEY] = data
