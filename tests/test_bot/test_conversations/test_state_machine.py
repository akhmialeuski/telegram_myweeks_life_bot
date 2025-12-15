"""Unit tests for ConversationStateMachine.

Tests state management, transitions, and event handling logic.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bot.conversations.persistence import TelegramContextPersistence
from src.bot.conversations.state_machine import (
    ConversationEvent,
    ConversationState,
    ConversationStateMachine,
    EventType,
    TransitionResult,
)


class TestConversationStateMachine:
    """Test suite for ConversationStateMachine class."""

    @pytest.fixture
    def mock_persistence(self) -> MagicMock:
        """Create mock persistence.

        :returns: Mocked persistence
        :rtype: MagicMock
        """
        persistence = MagicMock(spec=TelegramContextPersistence)
        persistence.get_state = AsyncMock()
        persistence.set_state = AsyncMock()
        persistence.clear_state = AsyncMock()
        persistence.is_state_valid = AsyncMock()
        return persistence

    @pytest.fixture
    def state_machine(self, mock_persistence: MagicMock) -> ConversationStateMachine:
        """Create state machine instance with mock persistence.

        :param mock_persistence: Mocked persistence
        :type mock_persistence: MagicMock
        :returns: Configured state machine
        :rtype: ConversationStateMachine
        """
        return ConversationStateMachine(persistence=mock_persistence)

    @pytest.fixture
    def mock_context(self) -> MagicMock:
        """Create mock context.

        :returns: Mocked context
        :rtype: MagicMock
        """
        return MagicMock()

    @pytest.mark.asyncio
    async def test_get_current_state(
        self,
        state_machine: ConversationStateMachine,
        mock_persistence: MagicMock,
        mock_context: MagicMock,
    ):
        """Test retrieving current state."""
        mock_persistence.get_state.return_value = ConversationState.IDLE

        state = await state_machine.get_current_state(user_id=123, context=mock_context)

        assert state == ConversationState.IDLE
        mock_persistence.get_state.assert_called_once_with(
            user_id=123, context=mock_context
        )

    @pytest.mark.asyncio
    async def test_set_state(
        self,
        state_machine: ConversationStateMachine,
        mock_persistence: MagicMock,
        mock_context: MagicMock,
    ):
        """Test setting state."""
        await state_machine.set_state(
            user_id=123,
            state=ConversationState.AWAITING_START_BIRTH_DATE,
            context=mock_context,
        )

        mock_persistence.set_state.assert_called_once_with(
            user_id=123,
            state=ConversationState.AWAITING_START_BIRTH_DATE,
            context=mock_context,
        )

    @pytest.mark.asyncio
    async def test_clear_state(
        self,
        state_machine: ConversationStateMachine,
        mock_persistence: MagicMock,
        mock_context: MagicMock,
    ):
        """Test clearing state."""
        await state_machine.clear_state(user_id=123, context=mock_context)

        mock_persistence.clear_state.assert_called_once_with(
            user_id=123, context=mock_context
        )

    @pytest.mark.asyncio
    async def test_is_state_valid(
        self,
        state_machine: ConversationStateMachine,
        mock_persistence: MagicMock,
        mock_context: MagicMock,
    ):
        """Test state validity check."""
        mock_persistence.is_state_valid.return_value = True

        is_valid = await state_machine.is_state_valid(
            user_id=123,
            expected_state=ConversationState.IDLE,
            context=mock_context,
            max_age_seconds=60.0,
        )

        assert is_valid is True
        mock_persistence.is_state_valid.assert_called_once_with(
            user_id=123,
            expected_state=ConversationState.IDLE,
            context=mock_context,
            max_age_seconds=60.0,
        )

    @pytest.mark.asyncio
    async def test_transition_to(
        self,
        state_machine: ConversationStateMachine,
        mock_persistence: MagicMock,
        mock_context: MagicMock,
    ):
        """Test transition to new state."""
        result = await state_machine.transition_to(
            user_id=123,
            target_state=ConversationState.IDLE,
            context=mock_context,
            action="some_action",
            action_context={"key": "val"},
        )

        assert result.new_state == ConversationState.IDLE
        assert result.action == "some_action"
        assert result.context == {"key": "val"}
        assert not result.has_error

        mock_persistence.set_state.assert_called_once_with(
            user_id=123, state=ConversationState.IDLE, context=mock_context
        )

    @pytest.mark.asyncio
    async def test_transition_with_error(
        self,
        state_machine: ConversationStateMachine,
        mock_context: MagicMock,
    ):
        """Test transition with error."""
        result = await state_machine.transition_with_error(
            user_id=123,
            current_state=ConversationState.AWAITING_START_BIRTH_DATE,
            error_key="error_msg",
            context=mock_context,
        )

        assert result.new_state == ConversationState.AWAITING_START_BIRTH_DATE
        assert result.error_key == "error_msg"
        assert result.has_error

    def test_transition_result_properties(self):
        """Test TransitionResult properties."""
        res_ok = TransitionResult(ConversationState.IDLE)
        assert not res_ok.has_error

        res_err = TransitionResult(ConversationState.IDLE, error_key="err")
        assert res_err.has_error

    def test_conversation_event_dataclass(self):
        """Test ConversationEvent dataclass."""
        event = ConversationEvent(
            event_type=EventType.TEXT_INPUT, data="hello", user_id=123
        )
        assert event.event_type == "text_input"
        assert event.data == "hello"
        assert event.user_id == 123
