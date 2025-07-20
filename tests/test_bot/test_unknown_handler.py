"""Unit tests for UnknownHandler.

Tests the UnknownHandler class which handles unknown messages.
"""

from unittest.mock import MagicMock

import pytest
from telegram.constants import ParseMode

from src.bot.constants import COMMAND_UNKNOWN
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

    def test_handler_creation(self, handler: UnknownHandler) -> None:
        """Test UnknownHandler creation.

        :param handler: UnknownHandler instance
        :type handler: UnknownHandler
        :returns: None
        :rtype: None
        """
        assert handler.command_name == f"/{COMMAND_UNKNOWN}"

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: UnknownHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_generate_message_unknown_command: MagicMock,
    ) -> None:
        """Test handle method with successful unknown message handling.

        :param handler: UnknownHandler instance
        :type handler: UnknownHandler
        :param mock_update: Mock Update object
        :type mock_update: MagicMock
        :param mock_context: Mock ContextTypes object
        :type mock_context: MagicMock
        :param mock_generate_message_unknown_command: Mocked generate_message_unknown_command function
        :type mock_generate_message_unknown_command: MagicMock
        :returns: None
        :rtype: None
        """
        mock_generate_message_unknown_command.return_value = "Unknown command!"

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Unknown command!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_with_russian_user(
        self,
        handler: UnknownHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_generate_message_unknown_command: MagicMock,
    ) -> None:
        """Test handle method with Russian user.

        :param handler: UnknownHandler instance
        :type handler: UnknownHandler
        :param mock_update: Mock Update object
        :type mock_update: MagicMock
        :param mock_context: Mock ContextTypes object
        :type mock_context: MagicMock
        :param mock_generate_message_unknown_command: Mocked generate_message_unknown_command function
        :type mock_generate_message_unknown_command: MagicMock
        :returns: None
        :rtype: None
        """
        mock_update.effective_user.language_code = "ru"
        mock_generate_message_unknown_command.return_value = "Неизвестная команда!"

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Неизвестная команда!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_with_no_language_code(
        self,
        handler: UnknownHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_generate_message_unknown_command: MagicMock,
    ) -> None:
        """Test handle method with no language code.

        :param handler: UnknownHandler instance
        :type handler: UnknownHandler
        :param mock_update: Mock Update object
        :type mock_update: MagicMock
        :param mock_context: Mock ContextTypes object
        :type mock_context: MagicMock
        :param mock_generate_message_unknown_command: Mocked generate_message_unknown_command function
        :type mock_generate_message_unknown_command: MagicMock
        :returns: None
        :rtype: None
        """
        mock_update.effective_user.language_code = None
        mock_generate_message_unknown_command.return_value = "Unknown command!"

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Unknown command!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_with_ukrainian_user(
        self,
        handler: UnknownHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_generate_message_unknown_command: MagicMock,
    ) -> None:
        """Test handle method with Ukrainian user.

        :param handler: UnknownHandler instance
        :type handler: UnknownHandler
        :param mock_update: Mock Update object
        :type mock_update: MagicMock
        :param mock_context: Mock ContextTypes object
        :type mock_context: MagicMock
        :param mock_generate_message_unknown_command: Mocked generate_message_unknown_command function
        :type mock_generate_message_unknown_command: MagicMock
        :returns: None
        :rtype: None
        """
        mock_update.effective_user.language_code = "uk"
        mock_generate_message_unknown_command.return_value = "Невідома команда!"

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Невідома команда!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_with_belarusian_user(
        self,
        handler: UnknownHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_generate_message_unknown_command: MagicMock,
    ) -> None:
        """Test handle method with Belarusian user.

        :param handler: UnknownHandler instance
        :type handler: UnknownHandler
        :param mock_update: Mock Update object
        :type mock_update: MagicMock
        :param mock_context: Mock ContextTypes object
        :type mock_context: MagicMock
        :param mock_generate_message_unknown_command: Mocked generate_message_unknown_command function
        :type mock_generate_message_unknown_command: MagicMock
        :returns: None
        :rtype: None
        """
        mock_update.effective_user.language_code = "be"
        mock_generate_message_unknown_command.return_value = "Невядомая каманда!"

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Невядомая каманда!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_error_handling(
        self,
        handler: UnknownHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_generate_message_unknown_command: MagicMock,
    ) -> None:
        """Test handle method with error handling.

        :param handler: UnknownHandler instance
        :type handler: UnknownHandler
        :param mock_update: Mock Update object
        :type mock_update: MagicMock
        :param mock_context: Mock ContextTypes object
        :type mock_context: MagicMock
        :param mock_generate_message_unknown_command: Mocked generate_message_unknown_command function
        :type mock_generate_message_unknown_command: MagicMock
        :returns: None
        :rtype: None
        """
        mock_update.message.reply_text.side_effect = Exception("Reply failed")
        mock_generate_message_unknown_command.return_value = "Unknown command!"

        with pytest.raises(Exception, match="Reply failed"):
            await handler.handle(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_handle_with_text_message_non_command(
        self,
        handler: UnknownHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_generate_message_unknown_command: MagicMock,
    ) -> None:
        """Test handle method with text message that is not a command.

        :param handler: UnknownHandler instance
        :type handler: UnknownHandler
        :param mock_update: Mock Update object
        :type mock_update: MagicMock
        :param mock_context: Mock ContextTypes object
        :type mock_context: MagicMock
        :param mock_generate_message_unknown_command: Mocked generate_message_unknown_command function
        :type mock_generate_message_unknown_command: MagicMock
        :returns: None
        :rtype: None
        """
        text_message = "Hello, this is just a regular text message that is quite long"
        mock_update.message.text = text_message
        mock_generate_message_unknown_command.return_value = "Unknown message!"

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Unknown message!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_with_other_message_type(
        self,
        handler: UnknownHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_generate_message_unknown_command: MagicMock,
    ) -> None:
        """Test handle method with non-text message type.

        :param handler: UnknownHandler instance
        :type handler: UnknownHandler
        :param mock_update: Mock Update object
        :type mock_update: MagicMock
        :param mock_context: Mock ContextTypes object
        :type mock_context: MagicMock
        :param mock_generate_message_unknown_command: Mocked generate_message_unknown_command function
        :type mock_generate_message_unknown_command: MagicMock
        :returns: None
        :rtype: None
        """
        mock_update.message.text = None
        mock_generate_message_unknown_command.return_value = "Unknown message type!"

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Unknown message type!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_with_simple_text_message(
        self,
        handler: UnknownHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_generate_message_unknown_command: MagicMock,
    ) -> None:
        """Test handle method with simple text message.

        :param handler: UnknownHandler instance
        :type handler: UnknownHandler
        :param mock_update: Mock Update object
        :type mock_update: MagicMock
        :param mock_context: Mock ContextTypes object
        :type mock_context: MagicMock
        :param mock_generate_message_unknown_command: Mocked generate_message_unknown_command function
        :type mock_generate_message_unknown_command: MagicMock
        :returns: None
        :rtype: None
        """
        mock_update.message.text = "hello"
        mock_generate_message_unknown_command.return_value = "Unknown text message!"

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Unknown text message!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_with_unknown_command(
        self,
        handler: UnknownHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_generate_message_unknown_command: MagicMock,
    ) -> None:
        """Test handle method with unknown command.

        :param handler: UnknownHandler instance
        :type handler: UnknownHandler
        :param mock_update: Mock Update object
        :type mock_update: MagicMock
        :param mock_context: Mock ContextTypes object
        :type mock_context: MagicMock
        :param mock_generate_message_unknown_command: Mocked generate_message_unknown_command function
        :type mock_generate_message_unknown_command: MagicMock
        :returns: None
        :rtype: None
        """
        mock_update.message.text = "/unknown_command"
        mock_generate_message_unknown_command.return_value = "Unknown command!"

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Unknown command!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML
