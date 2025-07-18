"""Unit tests for HelpHandler.

Tests the HelpHandler class which handles /help command.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from telegram import Update
from telegram.ext import ContextTypes

from src.bot.handlers.help_handler import HelpHandler


class TestHelpHandler:
    """Test suite for HelpHandler class."""

    @pytest.fixture
    def handler(self) -> HelpHandler:
        """Create HelpHandler instance.

        :returns: HelpHandler instance
        :rtype: HelpHandler
        """
        return HelpHandler()

    @pytest.fixture
    def mock_update(self) -> Mock:
        """Create mock Update object.

        :returns: Mock Update object
        :rtype: Mock
        """
        update = Mock(spec=Update)
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.username = "testuser"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self) -> Mock:
        """Create mock ContextTypes object.

        :returns: Mock ContextTypes object
        :rtype: Mock
        """
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        return context

    def test_handler_creation(self, handler: HelpHandler) -> None:
        """Test HelpHandler creation.

        :param handler: HelpHandler instance
        :returns: None
        """
        assert handler.command_name == "/help"

    @pytest.mark.asyncio
    async def test_handle_success(
        self, handler: HelpHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with successful help message.

        :param handler: HelpHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch(
            "src.bot.handlers.help_handler.generate_message_help"
        ) as mock_generate_message:
            mock_generate_message.return_value = "Here's the help message!"

            # Execute
            await handler.handle(mock_update, mock_context)

            # Assert
            mock_update.message.reply_text.assert_called_once_with(
                text="Here's the help message!", parse_mode="HTML"
            )
