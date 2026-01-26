"""Integration tests for unknown command handler.

This module tests handling of unrecognized commands and messages.

Test Scenarios:
    - Unknown command handling
    - Unknown text message handling
    - Unknown message type handling
"""

from unittest.mock import MagicMock

import pytest

from src.bot.handlers.unknown_handler import UnknownHandler
from src.services.container import ServiceContainer
from tests.integration.conftest import (
    get_reply_text,
    set_message_text,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestUnknownHandler:
    """Integration tests for the unknown handler.

    These tests verify that the bot gracefully handles unexpected inputs:
    - Unknown commands
    - Plain text messages (when not expected)
    """

    async def test_unknown_command_shows_error_suggestion(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that an unknown command triggers an error message.

        Preconditions:
            - Any user state (registered or not)

        Test Steps:
            1. User sends /invalid_command
               Expected: Bot responds with error/suggestion
               Response: Message suggesting /help

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        """
        # --- ARRANGE ---
        handler = UnknownHandler(services=test_service_container)
        set_message_text(mock_update=mock_update, text="/invalid_command")

        # --- ACT ---
        await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT ---
        mock_update.message.reply_text.assert_called_once()
        reply_text = get_reply_text(mock_message=mock_update.message)
        assert reply_text is not None
        assert "Unknown command" in reply_text
        assert "/help" in reply_text

    async def test_unknown_text_message_shows_error_suggestion(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that an unexpected text message triggers an error message.

        Preconditions:
            - Any user state

        Test Steps:
            1. User sends random text "Hello bot"
               Expected: Bot responds with error/suggestion
               Response: Message suggesting /help

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        """
        # --- ARRANGE ---
        handler = UnknownHandler(services=test_service_container)
        set_message_text(mock_update=mock_update, text="Hello bot")

        # --- ACT ---
        await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT ---
        mock_update.message.reply_text.assert_called_once()
        reply_text = get_reply_text(mock_message=mock_update.message)
        assert reply_text is not None
        assert "Unknown command" in reply_text
