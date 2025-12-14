"""Unit tests for TelegramContextPersistence.

Tests the state persistence implementation that uses
Telegram context.user_data for storing conversation state.
"""

from unittest.mock import MagicMock

import pytest

from src.bot.conversations.persistence import (
    STATE_KEY,
    TIMESTAMP_KEY,
    TelegramContextPersistence,
)
from src.bot.conversations.states import ConversationState


class TestTelegramContextPersistence:
    """Test suite for TelegramContextPersistence class.

    Tests state storage, retrieval, timeout handling, and
    concurrent access protection.
    """

    @pytest.fixture
    def persistence(self) -> TelegramContextPersistence:
        """Create TelegramContextPersistence instance for testing.

        :returns: TelegramContextPersistence instance
        :rtype: TelegramContextPersistence
        """
        return TelegramContextPersistence()

    @pytest.fixture
    def mock_context(self) -> MagicMock:
        """Create mock Telegram context with user_data.

        :returns: Mock context with empty user_data dict
        :rtype: MagicMock
        """
        context = MagicMock()
        context.user_data = {}
        return context

    @pytest.mark.asyncio
    async def test_get_state_returns_idle_when_empty(
        self,
        persistence: TelegramContextPersistence,
        mock_context: MagicMock,
    ) -> None:
        """Test get_state returns IDLE for new users.

        This test verifies that when no state is set,
        get_state returns ConversationState.IDLE.
        """
        state = await persistence.get_state(user_id=12345, context=mock_context)
        assert state == ConversationState.IDLE

    @pytest.mark.asyncio
    async def test_set_and_get_state(
        self,
        persistence: TelegramContextPersistence,
        mock_context: MagicMock,
    ) -> None:
        """Test setting and retrieving state.

        This test verifies that set_state stores the state
        and get_state retrieves it correctly.
        """
        await persistence.set_state(
            user_id=12345,
            state=ConversationState.AWAITING_START_BIRTH_DATE,
            context=mock_context,
        )
        state = await persistence.get_state(user_id=12345, context=mock_context)
        assert state == ConversationState.AWAITING_START_BIRTH_DATE

    @pytest.mark.asyncio
    async def test_clear_state(
        self,
        persistence: TelegramContextPersistence,
        mock_context: MagicMock,
    ) -> None:
        """Test clearing state returns to IDLE.

        This test verifies that clear_state removes the state
        and subsequent get_state returns IDLE.
        """
        await persistence.set_state(
            user_id=12345,
            state=ConversationState.AWAITING_START_BIRTH_DATE,
            context=mock_context,
        )
        await persistence.clear_state(user_id=12345, context=mock_context)
        state = await persistence.get_state(user_id=12345, context=mock_context)
        assert state == ConversationState.IDLE

    @pytest.mark.asyncio
    async def test_is_state_valid_true(
        self,
        persistence: TelegramContextPersistence,
        mock_context: MagicMock,
    ) -> None:
        """Test is_state_valid returns True for valid state.

        This test verifies that is_state_valid returns True
        when the state is set and not expired.
        """
        await persistence.set_state(
            user_id=12345,
            state=ConversationState.AWAITING_START_BIRTH_DATE,
            context=mock_context,
        )
        is_valid = await persistence.is_state_valid(
            user_id=12345,
            expected_state=ConversationState.AWAITING_START_BIRTH_DATE,
            context=mock_context,
        )
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_is_state_valid_false_wrong_state(
        self,
        persistence: TelegramContextPersistence,
        mock_context: MagicMock,
    ) -> None:
        """Test is_state_valid returns False for wrong state.

        This test verifies that is_state_valid returns False
        when the actual state differs from expected.
        """
        await persistence.set_state(
            user_id=12345,
            state=ConversationState.AWAITING_START_BIRTH_DATE,
            context=mock_context,
        )
        is_valid = await persistence.is_state_valid(
            user_id=12345,
            expected_state=ConversationState.AWAITING_SETTINGS_BIRTH_DATE,
            context=mock_context,
        )
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_is_state_valid_false_no_state(
        self,
        persistence: TelegramContextPersistence,
        mock_context: MagicMock,
    ) -> None:
        """Test is_state_valid returns False when no state set.

        This test verifies that is_state_valid returns False
        when no state has been set.
        """
        is_valid = await persistence.is_state_valid(
            user_id=12345,
            expected_state=ConversationState.AWAITING_START_BIRTH_DATE,
            context=mock_context,
        )
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_state_stores_timestamp(
        self,
        persistence: TelegramContextPersistence,
        mock_context: MagicMock,
    ) -> None:
        """Test state storage includes timestamp.

        This test verifies that set_state stores a timestamp
        with the state for timeout checking.
        """
        await persistence.set_state(
            user_id=12345,
            state=ConversationState.AWAITING_START_BIRTH_DATE,
            context=mock_context,
        )
        assert STATE_KEY in mock_context.user_data
        assert TIMESTAMP_KEY in mock_context.user_data

    @pytest.mark.asyncio
    async def test_waiting_for_value_is_string(
        self,
        persistence: TelegramContextPersistence,
        mock_context: MagicMock,
    ) -> None:
        """Test waiting_for stores string value for compatibility.

        This test verifies that the stored waiting_for value
        is a string for backward compatibility with handlers.yaml.
        """
        await persistence.set_state(
            user_id=12345,
            state=ConversationState.AWAITING_START_BIRTH_DATE,
            context=mock_context,
        )
        assert mock_context.user_data[STATE_KEY] == "start_birth_date"
