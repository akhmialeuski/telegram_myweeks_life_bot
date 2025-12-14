"""Unit tests for ConversationState enum.

Tests the ConversationState enum including its values,
string representation, and helper methods.
"""

from src.bot.conversations.states import (
    CALLBACK_INPUT_STATES,
    STATE_TO_COMMAND,
    TEXT_INPUT_STATES,
    ConversationState,
)


class TestConversationState:
    """Test suite for ConversationState enum.

    Tests the conversation state enum values, string representation,
    and state category helper methods.
    """

    def test_state_values_exist(self) -> None:
        """Test that all expected state values are defined.

        This test verifies that the ConversationState enum has all
        required state values for the bot's conversation flows.
        """
        assert ConversationState.IDLE is not None
        assert ConversationState.AWAITING_START_BIRTH_DATE is not None
        assert ConversationState.AWAITING_SETTINGS_BIRTH_DATE is not None
        assert ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY is not None

    def test_state_value_property(self) -> None:
        """Test that states have correct value property.

        This test verifies that each state's value property
        matches the expected string for use in handlers.yaml.
        """
        assert ConversationState.IDLE.value == "idle"
        assert ConversationState.AWAITING_START_BIRTH_DATE.value == "start_birth_date"
        assert (
            ConversationState.AWAITING_SETTINGS_BIRTH_DATE.value
            == "settings_birth_date"
        )
        assert (
            ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY.value
            == "settings_life_expectancy"
        )

    def test_state_equality_with_string(self) -> None:
        """Test that state values equal their string equivalents.

        This test verifies backward compatibility where states
        can be compared directly with string values.
        """
        assert ConversationState.IDLE == "idle"
        assert ConversationState.AWAITING_START_BIRTH_DATE == "start_birth_date"

    def test_from_string_valid_state(self) -> None:
        """Test from_string parses valid state strings.

        This test verifies that valid state string values
        are correctly converted to ConversationState enums.
        """
        assert ConversationState.from_string("idle") == ConversationState.IDLE
        assert (
            ConversationState.from_string("start_birth_date")
            == ConversationState.AWAITING_START_BIRTH_DATE
        )
        assert (
            ConversationState.from_string("settings_birth_date")
            == ConversationState.AWAITING_SETTINGS_BIRTH_DATE
        )

    def test_from_string_invalid_state(self) -> None:
        """Test from_string returns IDLE for invalid strings.

        This test verifies that invalid state strings default
        to the IDLE state rather than raising an exception.
        """
        assert ConversationState.from_string("invalid_state") == ConversationState.IDLE
        assert ConversationState.from_string("") == ConversationState.IDLE
        assert ConversationState.from_string(None) == ConversationState.IDLE

    def test_is_awaiting_input_true_for_active_states(self) -> None:
        """Test is_awaiting_input returns True for non-idle states.

        This test verifies that active states correctly indicate
        they are awaiting user input.
        """
        assert ConversationState.AWAITING_START_BIRTH_DATE.is_awaiting_input() is True
        assert (
            ConversationState.AWAITING_SETTINGS_BIRTH_DATE.is_awaiting_input() is True
        )

    def test_is_awaiting_input_false_for_idle(self) -> None:
        """Test is_awaiting_input returns False for IDLE.

        This test verifies that the IDLE state correctly indicates
        it is not awaiting user input.
        """
        assert ConversationState.IDLE.is_awaiting_input() is False

    def test_text_input_states_contains_expected(self) -> None:
        """Test TEXT_INPUT_STATES contains text input states.

        This test verifies that the TEXT_INPUT_STATES frozenset
        contains all states that expect text input.
        """
        assert ConversationState.AWAITING_START_BIRTH_DATE in TEXT_INPUT_STATES
        assert ConversationState.AWAITING_SETTINGS_BIRTH_DATE in TEXT_INPUT_STATES
        assert ConversationState.AWAITING_SETTINGS_LIFE_EXPECTANCY in TEXT_INPUT_STATES
        assert ConversationState.IDLE not in TEXT_INPUT_STATES

    def test_callback_input_states_contains_expected(self) -> None:
        """Test CALLBACK_INPUT_STATES contains callback states.

        This test verifies that the CALLBACK_INPUT_STATES frozenset
        contains all states that expect callback input.
        """
        assert ConversationState.AWAITING_SETTINGS_LANGUAGE in CALLBACK_INPUT_STATES
        assert ConversationState.IDLE not in CALLBACK_INPUT_STATES

    def test_state_to_command_mapping(self) -> None:
        """Test STATE_TO_COMMAND maps states to handlers.

        This test verifies that active states are correctly
        mapped to their handler command names.
        """
        assert STATE_TO_COMMAND[ConversationState.AWAITING_START_BIRTH_DATE] == "start"
        assert (
            STATE_TO_COMMAND[ConversationState.AWAITING_SETTINGS_BIRTH_DATE]
            == "settings"
        )
