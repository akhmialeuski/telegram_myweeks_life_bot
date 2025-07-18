"""Unit tests for SettingsHandler.

Tests the SettingsHandler class which handles /settings command.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from telegram import Update
from telegram.ext import ContextTypes

from src.bot.handlers.settings_handler import SettingsHandler


class TestSettingsHandler:
    """Test suite for SettingsHandler class."""

    @pytest.fixture
    def handler(self) -> SettingsHandler:
        """Create SettingsHandler instance.

        :returns: SettingsHandler instance
        :rtype: SettingsHandler
        """
        return SettingsHandler()

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

    def test_handler_creation(self, handler: SettingsHandler) -> None:
        """Test SettingsHandler creation.

        :param handler: SettingsHandler instance
        :returns: None
        """
        assert handler.command_name == "/settings"

    @pytest.mark.asyncio
    async def test_handle_premium_success(
        self, handler: SettingsHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with premium user.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_user_profile = Mock()
        mock_user_profile.subscription_type = "premium"
        mock_user_profile.is_active = True
        mock_user_profile.subscription = Mock()
        mock_user_profile.subscription.subscription_type = "premium"

        with patch(
            "src.bot.handlers.settings_handler.user_service"
        ) as mock_user_service:
            with patch(
                "src.bot.handlers.base_handler.user_service"
            ) as mock_base_user_service:
                with patch(
                    "src.bot.handlers.settings_handler.generate_message_settings_premium"
                ) as mock_generate_message:
                    with patch(
                        "src.bot.handlers.settings_handler.get_user_language"
                    ) as mock_get_language:
                        with patch(
                            "src.bot.handlers.settings_handler.generate_settings_buttons"
                        ) as mock_generate_buttons:
                            with patch(
                                "src.bot.handlers.settings_handler.InlineKeyboardButton"
                            ) as mock_button:
                                with patch(
                                    "src.bot.handlers.settings_handler.InlineKeyboardMarkup"
                                ) as mock_markup:
                                    mock_base_user_service.is_valid_user_profile.return_value = (
                                        True
                                    )
                                    mock_user_service.get_user_profile.return_value = (
                                        mock_user_profile
                                    )
                                    mock_generate_message.return_value = (
                                        "Premium settings!"
                                    )
                                    mock_get_language.return_value = "en"
                                    mock_generate_buttons.return_value = []
                                    mock_button.return_value = Mock()
                                    mock_markup.return_value = Mock()

                                    # Execute
                                    await handler.handle(mock_update, mock_context)

                                    # Assert
                                    mock_update.message.reply_text.assert_called_once()
                                    call_args = mock_update.message.reply_text.call_args
                                    assert (
                                        call_args.kwargs["text"] == "Premium settings!"
                                    )
                                    assert call_args.kwargs["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_handle_basic_success(
        self, handler: SettingsHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with basic user.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_user_profile = Mock()
        mock_user_profile.subscription_type = "basic"
        mock_user_profile.is_active = True

        with patch(
            "src.bot.handlers.settings_handler.user_service"
        ) as mock_user_service:
            with patch(
                "src.bot.handlers.base_handler.user_service"
            ) as mock_base_user_service:
                with patch(
                    "src.bot.handlers.settings_handler.generate_message_settings_basic"
                ) as mock_generate_message:
                    with patch(
                        "src.bot.handlers.settings_handler.get_user_language"
                    ) as mock_get_language:
                        with patch(
                            "src.bot.handlers.settings_handler.generate_settings_buttons"
                        ) as mock_generate_buttons:
                            with patch(
                                "src.bot.handlers.settings_handler.InlineKeyboardButton"
                            ) as mock_button:
                                with patch(
                                    "src.bot.handlers.settings_handler.InlineKeyboardMarkup"
                                ) as mock_markup:
                                    mock_base_user_service.is_valid_user_profile.return_value = (
                                        True
                                    )
                                    mock_user_service.get_user_profile.return_value = (
                                        mock_user_profile
                                    )
                                    mock_generate_message.return_value = (
                                        "Basic settings!"
                                    )
                                    mock_get_language.return_value = "en"
                                    mock_generate_buttons.return_value = []
                                    mock_button.return_value = Mock()
                                    mock_markup.return_value = Mock()

                                    # Execute
                                    await handler.handle(mock_update, mock_context)

                                    # Assert
                                    mock_update.message.reply_text.assert_called_once()
                                    call_args = mock_update.message.reply_text.call_args
                                    assert call_args.kwargs["text"] == "Basic settings!"
                                    assert call_args.kwargs["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_handle_no_profile(
        self, handler: SettingsHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with no user profile.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch(
            "src.bot.handlers.settings_handler.user_service"
        ) as mock_user_service:
            with patch(
                "src.bot.handlers.base_handler.user_service"
            ) as mock_base_user_service:
                with patch(
                    "src.bot.handlers.settings_handler.get_user_language"
                ) as mock_get_language:
                    with patch(
                        "src.bot.handlers.settings_handler.get_message"
                    ) as mock_get_message:
                        mock_base_user_service.is_valid_user_profile.return_value = True
                        mock_user_service.get_user_profile.return_value = None
                        mock_get_language.return_value = "en"
                        mock_get_message.return_value = "No profile found!"

                        # Execute
                        await handler.handle(mock_update, mock_context)

                        # Assert
                        mock_update.message.reply_text.assert_called_once_with(
                            "No profile found!"
                        )

    @pytest.mark.asyncio
    async def test_handle_exception(
        self, handler: SettingsHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with exception.

        :param handler: SettingsHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch(
            "src.bot.handlers.settings_handler.user_service"
        ) as mock_user_service:
            mock_user_service.get_user_profile.side_effect = Exception("Service error")

            # Execute and assert no exception is raised
            await handler.handle(mock_update, mock_context)
