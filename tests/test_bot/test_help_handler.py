"""Unit tests for HelpHandler.

Tests the HelpHandler class which handles /help command.
"""

from unittest.mock import MagicMock

import pytest
from telegram.constants import ParseMode

from src.bot.constants import COMMAND_HELP
from src.bot.handlers.help_handler import HelpHandler
from tests.utils.fake_container import FakeServiceContainer


class TestHelpHandler:
    """Test suite for HelpHandler class."""

    @pytest.fixture
    def handler(self) -> HelpHandler:
        """Create HelpHandler instance."""
        services = FakeServiceContainer()
        return HelpHandler(services)

    @pytest.fixture(autouse=True)
    def mock_use_locale(self, mocker):
        """Mock use_locale to control translations."""
        mock_pgettext = MagicMock(side_effect=lambda c, m: f"pgettext_{c}_{m}")
        mocker.patch(
            "src.bot.handlers.help_handler.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return mock_pgettext

    def test_handler_creation(self, handler: HelpHandler) -> None:
        """Test HelpHandler creation."""
        assert handler.command_name == f"/{COMMAND_HELP}"

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: HelpHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handle method with successful help message."""
        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "pgettext_help.text" in call_args.kwargs["text"]
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML
