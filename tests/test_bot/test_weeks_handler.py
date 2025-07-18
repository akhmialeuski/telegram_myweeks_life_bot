"""Unit tests for WeeksHandler.

Tests the WeeksHandler class which handles /weeks command.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from telegram import Update
from telegram.ext import ContextTypes

from src.bot.handlers.weeks_handler import WeeksHandler


class TestWeeksHandler:
    """Test suite for WeeksHandler class."""

    @pytest.fixture
    def handler(self) -> WeeksHandler:
        """Create WeeksHandler instance.

        :returns: WeeksHandler instance
        :rtype: WeeksHandler
        """
        return WeeksHandler()

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

    def test_handler_creation(self, handler: WeeksHandler) -> None:
        """Test WeeksHandler creation.

        :param handler: WeeksHandler instance
        :returns: None
        """
        assert handler.command_name == "/weeks"

    @pytest.mark.asyncio
    async def test_handle_success(
        self, handler: WeeksHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with successful weeks calculation.

        :param handler: WeeksHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.base_handler.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.weeks_handler.generate_message_week"
            ) as mock_generate_message:
                mock_user_service.is_valid_user_profile.return_value = True
                mock_generate_message.return_value = "You have lived 1234 weeks!"

                # Execute
                await handler.handle(mock_update, mock_context)

                # Assert
                mock_update.message.reply_text.assert_called_once_with(
                    text="You have lived 1234 weeks!", parse_mode="HTML"
                )

    @pytest.mark.asyncio
    async def test_handle_not_registered(
        self, handler: WeeksHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with unregistered user.

        :param handler: WeeksHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.base_handler.user_service") as mock_user_service:
            with patch("src.bot.handlers.base_handler.get_message") as mock_get_message:
                mock_user_service.is_valid_user_profile.return_value = False
                mock_get_message.return_value = "Please register first!"

                # Execute
                await handler.handle(mock_update, mock_context)

                # Assert
                mock_update.message.reply_text.assert_called_once_with(
                    "Please register first!"
                )
