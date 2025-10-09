"""Unit tests for VisualizeHandler.

This module contains tests for the VisualizeHandler class which handles
the /visualize command and generates life grid visualizations.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.bot.handlers.visualize_handler import VisualizeHandler
from tests.utils.fake_container import FakeServiceContainer


class TestVisualizeHandler:
    """Test suite for VisualizeHandler class.

    This class contains tests verifying that the VisualizeHandler correctly
    generates and sends life grid visualizations to registered users and
    handles unregistered users appropriately.
    """

    @pytest.fixture
    def handler(self) -> VisualizeHandler:
        """Create VisualizeHandler instance for testing.

        :returns: Configured VisualizeHandler with fake service container
        :rtype: VisualizeHandler
        """
        services = FakeServiceContainer()
        return VisualizeHandler(services)

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
            "src.bot.handlers.visualize_handler.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return mock_pgettext

    def test_handler_creation(self, handler: VisualizeHandler) -> None:
        """Test that VisualizeHandler is created with correct command name.

        This test verifies that the handler is properly initialized
        with the /visualize command name.

        :param handler: VisualizeHandler instance
        :type handler: VisualizeHandler
        :returns: None
        :rtype: None
        """
        assert handler.command_name == "/visualize"

    @pytest.mark.asyncio
    async def test_handle_success(
        self, handler: VisualizeHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test successful visualization generation and sending.

        This test verifies that the handle method correctly generates
        a life grid visualization and sends it as a photo with caption.

        :param handler: VisualizeHandler instance
        :type handler: VisualizeHandler
        :param mock_update: Mocked Telegram Update object
        :type mock_update: Mock
        :param mock_context: Mocked Telegram Context object
        :type mock_context: Mock
        :returns: None
        :rtype: None
        """
        with patch(
            "src.bot.handlers.visualize_handler.generate_visualization"
        ) as mock_generate_visualization:
            handler.services.user_service.is_valid_user_profile.return_value = True
            profile = Mock()
            profile.settings = Mock(language="en")
            handler.services.user_service.get_user_profile.return_value = profile
            mock_generate_visualization.return_value = Mock()

            await handler.handle(mock_update, mock_context)

            mock_update.message.reply_photo.assert_called_once()
            call_args = mock_update.message.reply_photo.call_args
            assert "pgettext_visualize.info_" in call_args.kwargs["caption"]

    @pytest.mark.asyncio
    async def test_handle_not_registered(
        self,
        handler: VisualizeHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handling of /visualize command from unregistered user.

        This test verifies that the handler correctly identifies unregistered
        users and returns None while sending appropriate message through wrapper.

        :param handler: VisualizeHandler instance
        :type handler: VisualizeHandler
        :param mock_update: Mocked Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        handler.services.user_service.is_valid_user_profile.return_value = False

        result = await handler.handle(mock_update, mock_context)

        assert result is None
        # The specific message is checked within the base handler wrapper
        mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_visualize_returns_none(
        self,
        handler: VisualizeHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_user_profile: MagicMock,
    ) -> None:
        """Test visualization generation with mocked image data.

        This test verifies that the handler correctly processes visualization
        generation and sends the image with proper caption when image data
        is returned.

        :param handler: VisualizeHandler instance
        :type handler: VisualizeHandler
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

        # Ensure mock user profile has proper settings structure
        if not getattr(mock_user_profile, "settings", None):
            mock_user_profile.settings = MagicMock()
        mock_user_profile.settings.language = "en"

        with patch(
            "src.bot.handlers.visualize_handler.generate_visualization",
            return_value=b"img",
        ):
            await handler.handle(mock_update, mock_context)
        mock_update.message.reply_photo.assert_called_once()
        call_args = mock_update.message.reply_photo.call_args
        assert "pgettext_visualize.info_" in call_args.kwargs["caption"]
