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


class TestSubscriptionHandler:
    """Test suite for SubscriptionHandler class."""

    @pytest.fixture
    def handler(self) -> SubscriptionHandler:
        """Create SubscriptionHandler instance.

        :returns: SubscriptionHandler instance
        :rtype: SubscriptionHandler
        """
        from tests.utils.fake_container import FakeServiceContainer

        services = FakeServiceContainer()
        return SubscriptionHandler(services)

    @pytest.fixture
    def mock_update(self) -> MagicMock:
        mock = MagicMock()
        mock.effective_user.id = 123456
        mock.effective_user.username = "testuser"
        mock.message.reply_text = AsyncMock()
        return mock

    @pytest.fixture
    def mock_context(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def make_mock_callback_query(self, mock_update: MagicMock):
        def _make(subscription_key: str):
            query = MagicMock()
            query.data = f"subscription_{subscription_key}"
            query.answer = AsyncMock()
            mock_update.callback_query = query
            return query

        return _make

    def test_handler_creation(self, handler: SubscriptionHandler) -> None:
        """Test SubscriptionHandler creation.

        :param handler: SubscriptionHandler instance
        """
        assert handler.command_name == f"/{COMMAND_SUBSCRIPTION}"

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
        make_mock_user_profile,
    ) -> None:
        """Test handle method with successful subscription info.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :param make_mock_user_profile: Factory for mock user profiles
        """
        mock_user_profile = make_mock_user_profile(SubscriptionType.BASIC)

        with patch(
            "src.bot.handlers.subscription_handler.generate_message_subscription_current"
        ) as mock_generate_current, patch(
            "src.bot.handlers.subscription_handler.InlineKeyboardButton"
        ) as mock_button, patch(
            "src.bot.handlers.subscription_handler.InlineKeyboardMarkup"
        ) as mock_markup:
            handler.services.user_service.is_valid_user_profile.return_value = True
            handler.services.user_service.get_user_profile.return_value = (
                mock_user_profile
            )
            mock_generate_current.return_value = "Current subscription info!"
            mock_button.return_value = MagicMock()
            mock_markup.return_value = MagicMock()

            await handler.handle(mock_update, mock_context)

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
        """Test handle method when user profile not found.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        """
        handler.services.user_service.is_valid_user_profile.return_value = False

        # Mock the message builder
        mock_builder = MagicMock()
        mock_builder.get.return_value = "You need to register first!"
        handler.services.get_message_builder = MagicMock(return_value=mock_builder)

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
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
        make_mock_user_profile,
    ) -> None:
        """Test handle method with exception.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :param make_mock_user_profile: Factory for mock user profiles
        """
        mock_user_profile = make_mock_user_profile(SubscriptionType.BASIC)

        with patch(
            "src.bot.handlers.subscription_handler.generate_message_subscription_current"
        ) as mock_generate_current:
            handler.services.user_service.is_valid_user_profile.return_value = True
            handler.services.user_service.get_user_profile.return_value = (
                mock_user_profile
            )
            mock_generate_current.side_effect = Exception("Test exception")
            handler.send_error_message = AsyncMock()

            await handler.handle(mock_update, mock_context)

            handler.send_error_message.assert_called_once()
            call_args = handler.send_error_message.call_args
            assert call_args.kwargs["error_message"] == "Test exception"

    @pytest.mark.asyncio
    async def test_handle_subscription_callback_same_subscription(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
        make_mock_user_profile,
        make_mock_callback_query,
    ) -> None:
        """Test handle_subscription_callback when user selects same subscription.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object with callback_query
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :param make_mock_user_profile: Factory for mock user profiles
        :param make_mock_callback_query: Factory for callback queries
        """
        mock_user_profile = make_mock_user_profile(SubscriptionType.BASIC)
        mock_callback_query = make_mock_callback_query("basic")

        with patch(
            "src.bot.handlers.subscription_handler.generate_message_subscription_already_active"
        ) as mock_generate_already_active:
            handler.services.user_service.get_user_profile.return_value = (
                mock_user_profile
            )
            mock_generate_already_active.return_value = "Subscription already active!"
            handler.edit_message = AsyncMock()

            await handler.handle_subscription_callback(mock_update, mock_context)

            mock_callback_query.answer.assert_called_once()
            mock_generate_already_active.assert_called_once_with(
                user_info=mock_update.effective_user,
                subscription_type=SubscriptionType.BASIC.value,
            )
            handler.edit_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_subscription_callback_successful_change(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
        make_mock_user_profile,
        make_mock_callback_query,
    ) -> None:
        """Test handle_subscription_callback with successful subscription change.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object with callback_query
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :param make_mock_user_profile: Factory for mock user profiles
        :param make_mock_callback_query: Factory for callback queries
        """
        mock_user_profile = make_mock_user_profile(SubscriptionType.BASIC)
        mock_callback_query = make_mock_callback_query("premium")

        with patch(
            "src.bot.handlers.subscription_handler.generate_message_subscription_change_success"
        ) as mock_generate_success, patch(
            "src.bot.handlers.subscription_handler.logger"
        ) as mock_logger:
            handler.services.user_service.get_user_profile.return_value = (
                mock_user_profile
            )
            handler.services.user_service.update_user_subscription.return_value = None
            mock_generate_success.return_value = "Subscription updated successfully!"
            handler.edit_message = AsyncMock()

            await handler.handle_subscription_callback(mock_update, mock_context)

            mock_callback_query.answer.assert_called_once()
            handler.services.user_service.update_user_subscription.assert_called_once_with(
                mock_update.effective_user.id, SubscriptionType.PREMIUM
            )
            mock_generate_success.assert_called_once_with(
                user_info=mock_update.effective_user,
                subscription_type=SubscriptionType.PREMIUM.value,
            )
            handler.edit_message.assert_called_once()

            # Verify that the success log message is called
            mock_logger.info.assert_called()
            log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
            assert any(
                "Subscription changed from" in log_call for log_call in log_calls
            )

    @pytest.mark.asyncio
    async def test_handle_subscription_callback_update_error(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
        make_mock_user_profile,
        make_mock_callback_query,
    ) -> None:
        """Test handle_subscription_callback with UserSubscriptionUpdateError.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object with callback_query
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :param make_mock_user_profile: Factory for mock user profiles
        :param make_mock_callback_query: Factory for callback queries
        """
        mock_user_profile = make_mock_user_profile(SubscriptionType.BASIC)
        mock_callback_query = make_mock_callback_query("premium")

        with patch(
            "src.bot.handlers.subscription_handler.generate_message_subscription_change_failed"
        ) as mock_generate_failed:
            handler.services.user_service.get_user_profile.return_value = (
                mock_user_profile
            )
            handler.services.user_service.update_user_subscription.side_effect = (
                UserSubscriptionUpdateError("Update failed")
            )
            mock_generate_failed.return_value = "Failed to update subscription!"
            handler.send_error_message = AsyncMock()

            await handler.handle_subscription_callback(mock_update, mock_context)

            mock_callback_query.answer.assert_called_once()
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
        make_mock_user_profile,
        make_mock_callback_query,
    ) -> None:
        """Test handle_subscription_callback with general exception.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object with callback_query
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :param make_mock_user_profile: Factory for mock user profiles
        :param make_mock_callback_query: Factory for callback queries
        """
        mock_user_profile = make_mock_user_profile(SubscriptionType.BASIC)
        mock_callback_query = make_mock_callback_query("premium")

        with patch(
            "src.bot.handlers.subscription_handler.generate_message_subscription_change_error"
        ) as mock_generate_error:
            handler.services.user_service.get_user_profile.return_value = (
                mock_user_profile
            )
            handler.services.user_service.update_user_subscription.side_effect = (
                Exception("General error")
            )
            mock_generate_error.return_value = "An error occurred!"
            handler.send_error_message = AsyncMock()

            await handler.handle_subscription_callback(mock_update, mock_context)

            mock_callback_query.answer.assert_called_once()
            mock_generate_error.assert_called_once_with(
                user_info=mock_update.effective_user
            )
            handler.send_error_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_subscription_callback_log_execution(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
        make_mock_user_profile,
        make_mock_callback_query,
    ) -> None:
        """Test that callback execution is logged properly.

        :param handler: SubscriptionHandler instance
        :param mock_update: Mock Update object with callback_query
        :param mock_context: Mock ContextTypes object
        :param mock_get_user_language: Mocked get_user_language function
        :param make_mock_user_profile: Factory for mock user profiles
        :param make_mock_callback_query: Factory for callback queries
        """
        mock_user_profile = make_mock_user_profile(SubscriptionType.BASIC)
        mock_callback_query = make_mock_callback_query("basic")

        with patch("src.bot.handlers.subscription_handler.logger") as mock_logger:
            handler.services.user_service.get_user_profile.return_value = (
                mock_user_profile
            )
            handler.edit_message = AsyncMock()

            await handler.handle_subscription_callback(mock_update, mock_context)

            # Verify that callback query was answered
            mock_callback_query.answer.assert_called_once()

            # Verify that the callback execution log message is called
            mock_logger.info.assert_called()
            log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
            assert any(
                "Callback executed: subscription_basic" in log_call
                for log_call in log_calls
            )
