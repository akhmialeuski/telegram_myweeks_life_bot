"""Unit tests for SubscriptionHandler.

Tests the SubscriptionHandler class which handles /subscription command.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram.constants import ParseMode

from src.bot.constants import COMMAND_SUBSCRIPTION
from src.bot.handlers.subscription_handler import SubscriptionHandler
from src.core.enums import SubscriptionType
from src.database.service import UserSubscriptionUpdateError
from src.utils.localization import SupportedLanguage


class TestSubscriptionHandler:
    """Test suite for SubscriptionHandler class."""

    @pytest.fixture
    def handler(self) -> SubscriptionHandler:
        """Create SubscriptionHandler instance.

        :returns: SubscriptionHandler instance
        :rtype: SubscriptionHandler
        """
        return SubscriptionHandler()

    def test_handler_creation(self, handler: SubscriptionHandler) -> None:
        """Test SubscriptionHandler creation.

        :param handler: SubscriptionHandler instance
        :returns: None
        """
        assert handler.command_name == f"/{COMMAND_SUBSCRIPTION}"

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle method with successful subscription info.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = SupportedLanguage.EN.value

        # Create user profile mock
        mock_user_profile = MagicMock()
        mock_user_profile.subscription = MagicMock()
        mock_user_profile.subscription.subscription_type = SubscriptionType.BASIC

        # Mock all required functions in the module where they're imported
        with patch(
            "src.bot.handlers.subscription_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.base_handler.user_service"
        ) as mock_base_user_service, patch(
            "src.bot.handlers.subscription_handler.generate_message_subscription_current"
        ) as mock_generate_current, patch(
            "src.bot.handlers.subscription_handler.InlineKeyboardButton"
        ) as mock_button, patch(
            "src.bot.handlers.subscription_handler.InlineKeyboardMarkup"
        ) as mock_markup:

            # Setup mocks
            mock_user_service.is_valid_user_profile.return_value = True
            mock_base_user_service.is_valid_user_profile.return_value = True
            mock_base_user_service.get_user_profile.return_value = mock_user_profile
            mock_generate_current.return_value = "Current subscription info!"
            mock_button.return_value = MagicMock()
            mock_markup.return_value = MagicMock()

            # Execute
            await handler.handle(mock_update, mock_context)

            # Assert
            mock_generate_current.assert_called_once_with(
                user_info=mock_update.effective_user
            )
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert call_args.kwargs["text"] == "Current subscription info!"
            assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_no_profile(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle method with no user profile.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = SupportedLanguage.EN.value

        # Mock all required functions in the module where they're imported
        with patch(
            "src.bot.handlers.base_handler.user_service"
        ) as mock_base_user_service, patch(
            "src.bot.handlers.base_handler.get_message"
        ) as mock_get_message:

            # Setup mocks - user not registered
            mock_base_user_service.is_valid_user_profile.return_value = False
            mock_get_message.return_value = "You need to register first!"

            # Execute
            await handler.handle(mock_update, mock_context)

            # Assert
            mock_get_message.assert_called_once_with(
                message_key="common", sub_key="not_registered", language=SupportedLanguage.EN.value
            )
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            # Check if text was passed as positional argument or kwargs
            if call_args.args:
                assert call_args.args[0] == "You need to register first!"
            else:
                assert call_args.kwargs["text"] == "You need to register first!"

    @pytest.mark.asyncio
    async def test_handle_exception(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle method with exception.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = SupportedLanguage.EN.value

        # Create user profile mock
        mock_user_profile = MagicMock()
        mock_user_profile.subscription = MagicMock()
        mock_user_profile.subscription.subscription_type = SubscriptionType.BASIC

        # Mock all required functions in the module where they're imported
        with patch(
            "src.bot.handlers.subscription_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.subscription_handler.generate_message_subscription_current"
        ) as mock_generate_current:

            # Setup mocks
            mock_user_service.is_valid_user_profile.return_value = True
            mock_user_service.get_user_profile.return_value = mock_user_profile
            mock_generate_current.side_effect = Exception("Test exception")

            # Execute
            await handler.handle(mock_update, mock_context)

            # Assert that error message was sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Test exception" in call_args.kwargs["text"]
            assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_subscription_callback_same_subscription(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_subscription_callback when user selects same subscription.

        This test covers lines 160-169: handling when current subscription equals new subscription.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object with callback_query
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = SupportedLanguage.EN.value

        # Create mock callback query
        mock_query = MagicMock()
        mock_query.data = "subscription_basic"
        mock_query.answer = AsyncMock()
        mock_update.callback_query = mock_query

        # Create user profile mock with BASIC subscription
        mock_user_profile = MagicMock()
        mock_user_profile.subscription = MagicMock()
        mock_user_profile.subscription.subscription_type = SubscriptionType.BASIC

        # Mock all required functions
        with patch(
            "src.bot.handlers.base_handler.user_service"
        ) as mock_base_user_service, patch(
            "src.bot.handlers.subscription_handler.generate_message_subscription_already_active"
        ) as mock_generate_already_active:

            # Setup mocks
            mock_base_user_service.get_user_profile.return_value = mock_user_profile
            mock_generate_already_active.return_value = "Subscription already active!"

            # Mock edit_message method
            handler.edit_message = AsyncMock()

            # Execute
            await handler.handle_subscription_callback(mock_update, mock_context)

            # Assert
            mock_query.answer.assert_called_once()
            mock_generate_already_active.assert_called_once_with(
                user_info=mock_update.effective_user, subscription_type="basic"
            )
            handler.edit_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_subscription_callback_successful_change(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_subscription_callback with successful subscription change.

        This test covers lines 171-190: successful subscription update flow.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object with callback_query
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = SupportedLanguage.EN.value

        # Create mock callback query
        mock_query = MagicMock()
        mock_query.data = "subscription_premium"
        mock_query.answer = AsyncMock()
        mock_update.callback_query = mock_query

        # Create user profile mock with BASIC subscription (different from premium)
        mock_user_profile = MagicMock()
        mock_user_profile.subscription = MagicMock()
        mock_user_profile.subscription.subscription_type = SubscriptionType.BASIC

        # Mock all required functions
        with patch(
            "src.bot.handlers.subscription_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.base_handler.user_service"
        ) as mock_base_user_service, patch(
            "src.bot.handlers.subscription_handler.generate_message_subscription_change_success"
        ) as mock_generate_success:

            # Setup mocks
            mock_base_user_service.get_user_profile.return_value = mock_user_profile
            mock_user_service.update_user_subscription.return_value = None
            mock_generate_success.return_value = "Subscription updated successfully!"

            # Mock edit_message method
            handler.edit_message = AsyncMock()

            # Execute
            await handler.handle_subscription_callback(mock_update, mock_context)

            # Assert
            mock_query.answer.assert_called_once()
            mock_user_service.update_user_subscription.assert_called_once_with(
                mock_update.effective_user.id, SubscriptionType.PREMIUM
            )
            mock_generate_success.assert_called_once_with(
                user_info=mock_update.effective_user, subscription_type="premium"
            )
            handler.edit_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_subscription_callback_update_error(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_subscription_callback with UserSubscriptionUpdateError.

        This test covers lines 193-198: handling UserSubscriptionUpdateError.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object with callback_query
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = SupportedLanguage.EN.value

        # Create mock callback query
        mock_query = MagicMock()
        mock_query.data = "subscription_premium"
        mock_query.answer = AsyncMock()
        mock_update.callback_query = mock_query

        # Create user profile mock with BASIC subscription
        mock_user_profile = MagicMock()
        mock_user_profile.subscription = MagicMock()
        mock_user_profile.subscription.subscription_type = SubscriptionType.BASIC

        # Mock all required functions
        with patch(
            "src.bot.handlers.subscription_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.base_handler.user_service"
        ) as mock_base_user_service, patch(
            "src.bot.handlers.subscription_handler.generate_message_subscription_change_failed"
        ) as mock_generate_failed:

            # Setup mocks
            mock_base_user_service.get_user_profile.return_value = mock_user_profile
            mock_user_service.update_user_subscription.side_effect = (
                UserSubscriptionUpdateError("Update failed")
            )
            mock_generate_failed.return_value = "Failed to update subscription!"

            # Mock send_error_message method
            handler.send_error_message = AsyncMock()

            # Execute
            await handler.handle_subscription_callback(mock_update, mock_context)

            # Assert
            mock_query.answer.assert_called_once()
            mock_generate_failed.assert_called_once_with(
                user_info=mock_update.effective_user
            )
            handler.send_error_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_subscription_callback_general_exception(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle_subscription_callback with general exception.

        This test covers lines 200-204: handling general exceptions.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object with callback_query
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :returns: None
        """
        # Setup
        mock_get_user_language.return_value = SupportedLanguage.EN.value

        # Create mock callback query
        mock_query = MagicMock()
        mock_query.data = "subscription_premium"
        mock_query.answer = AsyncMock()
        mock_update.callback_query = mock_query

        # Create user profile mock with BASIC subscription
        mock_user_profile = MagicMock()
        mock_user_profile.subscription = MagicMock()
        mock_user_profile.subscription.subscription_type = SubscriptionType.BASIC

        # Mock all required functions
        with patch(
            "src.bot.handlers.subscription_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.base_handler.user_service"
        ) as mock_base_user_service, patch(
            "src.bot.handlers.subscription_handler.generate_message_subscription_change_error"
        ) as mock_generate_error:

            # Setup mocks
            mock_base_user_service.get_user_profile.return_value = mock_user_profile
            mock_user_service.update_user_subscription.side_effect = Exception(
                "General error"
            )
            mock_generate_error.return_value = "An error occurred!"

            # Mock send_error_message method
            handler.send_error_message = AsyncMock()

            # Execute
            await handler.handle_subscription_callback(mock_update, mock_context)

            # Assert
            mock_query.answer.assert_called_once()
            mock_generate_error.assert_called_once_with(
                user_info=mock_update.effective_user
            )
            handler.send_error_message.assert_called_once()
