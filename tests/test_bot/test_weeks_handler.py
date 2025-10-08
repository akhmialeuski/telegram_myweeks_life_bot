"""Unit tests for WeeksHandler.

This module contains tests for the WeeksHandler class which handles
the /weeks command and displays life statistics in weeks format.
"""

from unittest.mock import MagicMock

import pytest
from telegram.constants import ParseMode

from src.bot.constants import COMMAND_WEEKS
from src.bot.handlers.weeks_handler import WeeksHandler
from tests.utils.fake_container import FakeServiceContainer


class TestWeeksHandler:
    """Test suite for WeeksHandler class.

    This class contains tests verifying that the WeeksHandler correctly
    calculates and displays life statistics in weeks for registered users
    and handles unregistered users appropriately.
    """

    @pytest.fixture
    def handler(self) -> WeeksHandler:
        """Create WeeksHandler instance for testing.

        :returns: Configured WeeksHandler with fake service container
        :rtype: WeeksHandler
        """
        services = FakeServiceContainer()
        return WeeksHandler(services)

    @pytest.fixture(autouse=True)
    def mock_use_locale(self, mocker):
        """Mock use_locale function to control translation behavior.

        This fixture automatically mocks the use_locale function to return
        predictable translation strings for testing purposes.

        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        :returns: Mocked pgettext function
        :rtype: MagicMock
        """
        mock_pgettext = MagicMock(side_effect=lambda c, m: f"pgettext_{c}_{m}")
        mocker.patch(
            "src.bot.handlers.weeks_handler.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return mock_pgettext

    def test_handler_creation(self, handler: WeeksHandler) -> None:
        """Test that WeeksHandler is created with correct command name.

        This test verifies that the handler is properly initialized
        with the /weeks command name constant.

        :param handler: WeeksHandler instance
        :type handler: WeeksHandler
        :returns: None
        :rtype: None
        """
        assert handler.command_name == f"/{COMMAND_WEEKS}"

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: WeeksHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_user_profile: MagicMock,
    ) -> None:
        """Test successful life weeks statistics calculation and display.

        This test verifies that the handle method correctly retrieves
        user profile, calculates life statistics, and sends formatted
        message with HTML parse mode.

        :param handler: WeeksHandler instance
        :type handler: WeeksHandler
        :param mock_update: Mocked Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram Context object
        :type mock_context: MagicMock
        :param mock_user_profile: Mocked user profile with settings
        :type mock_user_profile: MagicMock
        :returns: None
        :rtype: None
        """
        handler.services.user_service.is_valid_user_profile.return_value = True
        handler.services.user_service.get_user_profile.return_value = mock_user_profile

        # Ensure nested settings structure for proper attribute access
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
        """Test handling of /weeks command from unregistered user.

        This test verifies that the handler correctly identifies unregistered
        users and responds with appropriate message through the wrapper.

        :param handler: WeeksHandler instance
        :type handler: WeeksHandler
        :param mock_update: Mocked Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        handler.services.user_service.is_valid_user_profile.return_value = False

        await handler.handle(mock_update, mock_context)

        # Specific message is handled by the base handler wrapper
        mock_update.message.reply_text.assert_called_once()
