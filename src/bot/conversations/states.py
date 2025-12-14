"""Conversation state enum for FSM-based conversation management.

This module defines all valid conversation states as a typed enum,
replacing string-based state keys for compile-time safety.
"""

from enum import Enum


class ConversationState(str, Enum):
    """Enumeration of all valid conversation states.

    Each state represents a point in user interaction flow.
    Using str as base class allows direct comparison with string values
    for backward compatibility with YAML configuration.

    :cvar IDLE: No active conversation, user is not awaiting any input
    :cvar AWAITING_START_BIRTH_DATE: Waiting for birth date during /start registration
    :cvar AWAITING_SETTINGS_BIRTH_DATE: Waiting for birth date change in /settings
    :cvar AWAITING_SETTINGS_LIFE_EXPECTANCY: Waiting for life expectancy input
    :cvar AWAITING_SETTINGS_LANGUAGE: Waiting for language selection (callback-based)
    """

    IDLE = "idle"
    AWAITING_START_BIRTH_DATE = "start_birth_date"
    AWAITING_SETTINGS_BIRTH_DATE = "settings_birth_date"
    AWAITING_SETTINGS_LIFE_EXPECTANCY = "settings_life_expectancy"
    AWAITING_SETTINGS_LANGUAGE = "settings_language"

    @classmethod
    def from_string(cls, value: str | None) -> "ConversationState":
        """Convert a string value to ConversationState enum.

        :param value: String representation of the state
        :type value: str | None
        :returns: Corresponding ConversationState, defaults to IDLE
        :rtype: ConversationState
        """
        if value is None:
            return cls.IDLE
        for member in cls:
            if member.value == value:
                return member
        return cls.IDLE

    def is_awaiting_input(self) -> bool:
        """Check if this state indicates waiting for user input.

        :returns: True if state is waiting for input, False otherwise
        :rtype: bool
        """
        return self != ConversationState.IDLE


# State categories for validation and routing
TEXT_INPUT_STATES: frozenset[ConversationState] = frozenset(
    [
        ConversationState.AWAITING_START_BIRTH_DATE,
        ConversationState.AWAITING_SETTINGS_BIRTH_DATE,
        ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY,
    ]
)

CALLBACK_INPUT_STATES: frozenset[ConversationState] = frozenset(
    [
        ConversationState.AWAITING_SETTINGS_LANGUAGE,
    ]
)

# Mapping from states to their handler commands
STATE_TO_COMMAND: dict[ConversationState, str] = {
    ConversationState.AWAITING_START_BIRTH_DATE: "start",
    ConversationState.AWAITING_SETTINGS_BIRTH_DATE: "settings",
    ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY: "settings",
    ConversationState.AWAITING_SETTINGS_LANGUAGE: "settings",
}
