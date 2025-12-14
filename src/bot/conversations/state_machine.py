"""Conversation state machine for FSM-based conversation flow management.

This module provides the core state machine engine that processes conversation
events and executes state transitions based on workflow configuration.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from telegram.ext import ContextTypes

from .persistence import TelegramContextPersistence
from .states import ConversationState

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Type of conversation event.

    :cvar TEXT_INPUT: Plain text message from user
    :cvar CALLBACK: Callback query from inline keyboard
    :cvar COMMAND: Bot command (e.g., /start, /settings)
    """

    TEXT_INPUT = "text_input"
    CALLBACK = "callback"
    COMMAND = "command"


@dataclass(frozen=True, slots=True)
class ConversationEvent:
    """Incoming conversation event.

    Represents an event that triggers state machine processing,
    decoupled from Telegram-specific types.

    :ivar event_type: Type of the event (text, callback, command)
    :type event_type: EventType
    :ivar data: Event data (text content, callback data, or command)
    :type data: str
    :ivar user_id: Telegram user ID
    :type user_id: int
    """

    event_type: EventType
    data: str
    user_id: int


@dataclass(slots=True)
class TransitionResult:
    """Result of state machine transition.

    Contains the new state, action to execute, and optional error information.

    :ivar new_state: The state after transition
    :type new_state: ConversationState
    :ivar action: Action name to execute, or None
    :type action: str | None
    :ivar error_key: Error message key if transition failed
    :type error_key: str | None
    :ivar context: Additional context data for the action
    :type context: dict[str, Any]
    """

    new_state: ConversationState
    action: str | None = None
    error_key: str | None = None
    context: dict[str, Any] = field(default_factory=dict)

    @property
    def has_error(self) -> bool:
        """Check if this result represents an error.

        :returns: True if error_key is set
        :rtype: bool
        """
        return self.error_key is not None


class ConversationStateMachine:
    """Finite State Machine for managing conversation flows.

    Decoupled from transport layer - works with abstract events.
    Provides centralized state management and transition logic.
    """

    def __init__(
        self,
        persistence: TelegramContextPersistence | None = None,
    ) -> None:
        """Initialize the state machine.

        :param persistence: State persistence implementation
        :type persistence: TelegramContextPersistence | None
        """
        self._persistence = persistence or TelegramContextPersistence()

    async def get_current_state(
        self,
        user_id: int,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> ConversationState:
        """Retrieve current conversation state for user.

        :param user_id: Telegram user ID
        :type user_id: int
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: Current conversation state
        :rtype: ConversationState
        """
        return await self._persistence.get_state(
            user_id=user_id,
            context=context,
        )

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
        await self._persistence.set_state(
            user_id=user_id,
            state=state,
            context=context,
        )
        logger.debug(f"State machine: Set state to {state.value} for user {user_id}")

    async def clear_state(
        self,
        user_id: int,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Clear conversation state for user (set to IDLE).

        :param user_id: Telegram user ID
        :type user_id: int
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        await self._persistence.clear_state(
            user_id=user_id,
            context=context,
        )
        logger.debug(f"State machine: Cleared state for user {user_id}")

    async def is_state_valid(
        self,
        user_id: int,
        expected_state: ConversationState,
        context: ContextTypes.DEFAULT_TYPE,
        max_age_seconds: float = 300.0,
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
        :returns: True if state is valid and matches
        :rtype: bool
        """
        return await self._persistence.is_state_valid(
            user_id=user_id,
            expected_state=expected_state,
            context=context,
            max_age_seconds=max_age_seconds,
        )

    async def transition_to(
        self,
        user_id: int,
        target_state: ConversationState,
        context: ContextTypes.DEFAULT_TYPE,
        action: str | None = None,
        action_context: dict[str, Any] | None = None,
    ) -> TransitionResult:
        """Execute transition to a new state.

        :param user_id: Telegram user ID
        :type user_id: int
        :param target_state: State to transition to
        :type target_state: ConversationState
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :param action: Action name to execute
        :type action: str | None
        :param action_context: Additional context for the action
        :type action_context: dict[str, Any] | None
        :returns: Transition result
        :rtype: TransitionResult
        """
        await self.set_state(
            user_id=user_id,
            state=target_state,
            context=context,
        )

        return TransitionResult(
            new_state=target_state,
            action=action,
            context=action_context or {},
        )

    async def transition_with_error(
        self,
        user_id: int,
        current_state: ConversationState,
        error_key: str,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> TransitionResult:
        """Create error transition result, staying in current state.

        :param user_id: Telegram user ID
        :type user_id: int
        :param current_state: Current conversation state
        :type current_state: ConversationState
        :param error_key: Error message key for localization
        :type error_key: str
        :param context: Telegram context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: Transition result with error
        :rtype: TransitionResult
        """
        logger.debug(
            f"State machine: Error transition for user {user_id}, "
            f"staying in {current_state.value}, error: {error_key}"
        )
        return TransitionResult(
            new_state=current_state,
            error_key=error_key,
        )
