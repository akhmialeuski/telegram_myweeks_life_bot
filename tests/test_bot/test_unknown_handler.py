"""Unit tests for UnknownHandler.

Tests the UnknownHandler class which handles unknown messages.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bot.constants import COMMAND_UNKNOWN
from src.bot.handlers.unknown_handler import UnknownHandler
from tests.utils.fake_container import FakeServiceContainer


class TestUnknownHandler:
    """Test suite for UnknownHandler class."""

    @pytest.fixture
    def handler(self) -> UnknownHandler:
        """Create UnknownHandler instance."""
        services = FakeServiceContainer()
        return UnknownHandler(services)

    @pytest.fixture(autouse=True)
    def mock_use_locale(self, mocker):
        """Mock use_locale to control translations."""
        mock_pgettext = MagicMock(side_effect=lambda c, m: f"pgettext_{c}_{m}")
        mocker.patch(
            "src.bot.handlers.unknown_handler.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return mock_pgettext

    def test_handler_creation(self, handler: UnknownHandler) -> None:
        """Test UnknownHandler creation."""
        assert handler.command_name == f"/{COMMAND_UNKNOWN}"

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: UnknownHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handle method with successful unknown message handling."""
        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "pgettext_unknown.command_" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_uses_message_context(
        self,
        handler: UnknownHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that handle method properly uses MessageContext."""
        handler.send_message = AsyncMock()
        mock_update.effective_user.language_code = "en"

        await handler.handle(mock_update, mock_context)

        handler.send_message.assert_called_once()
        call_args = handler.send_message.call_args
        message_text = call_args.kwargs["message_text"]
        assert "pgettext_unknown.command_" in message_text
