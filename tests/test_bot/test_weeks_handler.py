"""Unit tests for WeeksHandler.

Tests the WeeksHandler class which handles /weeks command.
"""

from unittest.mock import MagicMock

import pytest
from telegram.constants import ParseMode

from src.bot.constants import COMMAND_WEEKS
from src.bot.handlers.weeks_handler import WeeksHandler
from tests.utils.fake_container import FakeServiceContainer


class TestWeeksHandler:
    """Test suite for WeeksHandler class."""

    @pytest.fixture
    def handler(self) -> WeeksHandler:
        """Create WeeksHandler instance."""
        services = FakeServiceContainer()
        return WeeksHandler(services)

    @pytest.fixture(autouse=True)
    def mock_use_locale(self, mocker):
        """Mock use_locale to control translations."""
        mock_pgettext = MagicMock(side_effect=lambda c, m: f"pgettext_{c}_{m}")
        mocker.patch(
            "src.bot.handlers.weeks_handler.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return mock_pgettext

    def test_handler_creation(self, handler: WeeksHandler) -> None:
        """Test WeeksHandler creation."""
        assert handler.command_name == f"/{COMMAND_WEEKS}"

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: WeeksHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_user_profile: MagicMock,
    ) -> None:
        """Test handle method with successful week calculation."""
        handler.services.user_service.is_valid_user_profile.return_value = True
        handler.services.user_service.get_user_profile.return_value = mock_user_profile
        # Ensure nested settings structure
        if not getattr(mock_user_profile, "settings", None):
            mock_user_profile.settings = MagicMock()
        mock_user_profile.settings.language = "en"
        mock_user_profile.settings.birth_date = (
            mock_user_profile.birth_date
            if hasattr(mock_user_profile, "birth_date")
            else None
        )
        if not getattr(mock_user_profile.settings, "life_expectancy", None):
            mock_user_profile.settings.life_expectancy = 80

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "pgettext_weeks.statistics_" in call_args.kwargs["text"]
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_not_registered(
        self,
        handler: WeeksHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handle method with unregistered user."""
        handler.services.user_service.is_valid_user_profile.return_value = False

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        # Specific message is handled by the wrapper, just check for the call
