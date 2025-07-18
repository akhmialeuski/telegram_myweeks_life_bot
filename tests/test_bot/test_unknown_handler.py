"""Unit tests for UnknownHandler.

Tests the UnknownHandler class which handles unknown messages.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from telegram import Update
from telegram.ext import ContextTypes

from src.bot.handlers.unknown_handler import UnknownHandler


class TestUnknownHandler:
    """Test suite for UnknownHandler class."""

    @pytest.fixture
    def handler(self) -> UnknownHandler:
        """Create UnknownHandler instance.

        :returns: UnknownHandler instance
        :rtype: UnknownHandler
        """
        return UnknownHandler()

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
        update.effective_user.language_code = "en"
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

    def test_handler_creation(self, handler: UnknownHandler) -> None:
        """Test UnknownHandler creation.

        :param handler: UnknownHandler instance
        :returns: None
        """
        assert handler.command_name == "/unknown"

    @pytest.mark.asyncio
    async def test_handle_success(
        self, handler: UnknownHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with successful unknown message handling.

        :param handler: UnknownHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch(
            "src.bot.handlers.unknown_handler.generate_message_unknown_command"
        ) as mock_generate_message:
            mock_generate_message.return_value = "Unknown command!"

            # Execute
            await handler.handle(mock_update, mock_context)

            # Assert
            mock_update.message.reply_text.assert_called_once_with("Unknown command!")

    @pytest.mark.asyncio
    async def test_handle_with_russian_user(
        self, handler: UnknownHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with Russian user.

        :param handler: UnknownHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_update.effective_user.language_code = "ru"
        with patch(
            "src.bot.handlers.unknown_handler.generate_message_unknown_command"
        ) as mock_generate_message:
            mock_generate_message.return_value = "Неизвестная команда!"

            # Execute
            await handler.handle(mock_update, mock_context)

            # Assert
            mock_update.message.reply_text.assert_called_once_with(
                "Неизвестная команда!"
            )

    @pytest.mark.asyncio
    async def test_handle_with_no_language_code(
        self, handler: UnknownHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with no language code.

        :param handler: UnknownHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_update.effective_user.language_code = None
        with patch(
            "src.bot.handlers.unknown_handler.generate_message_unknown_command"
        ) as mock_generate_message:
            mock_generate_message.return_value = "Unknown command!"

            # Execute
            await handler.handle(mock_update, mock_context)

            # Assert
            mock_update.message.reply_text.assert_called_once_with("Unknown command!")

    @pytest.mark.asyncio
    async def test_handle_with_ukrainian_user(
        self, handler: UnknownHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with Ukrainian user.

        :param handler: UnknownHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_update.effective_user.language_code = "uk"
        with patch(
            "src.bot.handlers.unknown_handler.generate_message_unknown_command"
        ) as mock_generate_message:
            mock_generate_message.return_value = "Невідома команда!"

            # Execute
            await handler.handle(mock_update, mock_context)

            # Assert
            mock_update.message.reply_text.assert_called_once_with("Невідома команда!")

    @pytest.mark.asyncio
    async def test_handle_with_belarusian_user(
        self, handler: UnknownHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with Belarusian user.

        :param handler: UnknownHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_update.effective_user.language_code = "be"
        with patch(
            "src.bot.handlers.unknown_handler.generate_message_unknown_command"
        ) as mock_generate_message:
            mock_generate_message.return_value = "Невядомая каманда!"

            # Execute
            await handler.handle(mock_update, mock_context)

            # Assert
            mock_update.message.reply_text.assert_called_once_with("Невядомая каманда!")

    @pytest.mark.asyncio
    async def test_handle_error_handling(
        self, handler: UnknownHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with error handling.

        :param handler: UnknownHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_update.message.reply_text.side_effect = Exception("Reply failed")
        with patch(
            "src.bot.handlers.unknown_handler.generate_message_unknown_command"
        ) as mock_generate_message:
            mock_generate_message.return_value = "Unknown command!"

            # Execute and assert exception is raised
            with pytest.raises(Exception, match="Reply failed"):
                await handler.handle(mock_update, mock_context)
