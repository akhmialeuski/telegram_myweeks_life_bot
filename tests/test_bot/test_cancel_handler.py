"""Unit tests for CancelHandler.

Tests the CancelHandler class which handles /cancel command.
"""

from unittest.mock import MagicMock, patch

import pytest
from telegram.constants import ParseMode

from src.bot.constants import COMMAND_CANCEL
from src.bot.handlers.cancel_handler import CancelHandler
from src.database.service import UserDeletionError, UserServiceError
from src.utils.localization import SupportedLanguage
from tests.conftest import TEST_USER_ID


class TestCancelHandler:
    """Test suite for CancelHandler class."""

    @pytest.fixture
    def handler(self) -> CancelHandler:
        """Create CancelHandler instance.

        :returns: CancelHandler instance
        :rtype: CancelHandler
        """
        return CancelHandler()

    def test_handler_creation(self, handler: CancelHandler) -> None:
        """Test CancelHandler creation.

        :param handler: CancelHandler instance
        :type handler: CancelHandler
        :returns: None
        :rtype: None
        """
        assert handler.command_name == f"/{COMMAND_CANCEL}"

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: CancelHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle method with successful cancellation.

        :param handler: CancelHandler instance
        :type handler: CancelHandler
        :param mock_update: Mock Update object
        :type mock_update: MagicMock
        :param mock_context: Mock ContextTypes object
        :type mock_context: MagicMock
        :param mock_get_user_language: Mocked get_user_language function
        :type mock_get_user_language: MagicMock
        :returns: None
        :rtype: None
        """
        mock_get_user_language.return_value = SupportedLanguage.EN.value

        with patch(
            "src.bot.handlers.cancel_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.base_handler.user_service"
        ) as mock_base_user_service, patch(
            "src.bot.handlers.cancel_handler.remove_user_from_scheduler"
        ) as mock_remove_scheduler, patch(
            "src.bot.handlers.cancel_handler.generate_message_cancel_success"
        ) as mock_generate_success:
            # Create mock user profile
            mock_user_profile = MagicMock()
            mock_user_profile.user = mock_update.effective_user
            mock_user_profile.settings = MagicMock()
            mock_user_profile.settings.birth_date = MagicMock()

            mock_user_service.is_valid_user_profile.return_value = True
            mock_user_service.get_user_profile.return_value = mock_user_profile
            mock_base_user_service.is_valid_user_profile.return_value = True
            mock_user_service.delete_user_profile.return_value = None
            mock_remove_scheduler.return_value = None
            mock_generate_success.return_value = "Account deleted successfully!"

            # Configure mock_context.bot_data.get to return a scheduler mock
            mock_scheduler = MagicMock()
            mock_context.bot_data.get.return_value = mock_scheduler

            await handler.handle(mock_update, mock_context)

            # Verify that remove_user_from_scheduler was called with scheduler and user_id
            # Note: remove_user_from_scheduler is only called if scheduler exists in bot_data
            mock_remove_scheduler.assert_called_once_with(
                mock_context.bot_data.get.return_value, mock_update.effective_user.id
            )
            mock_generate_success.assert_called_once()
            mock_user_service.delete_user_profile.assert_called_once_with(
                telegram_id=mock_update.effective_user.id
            )
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert call_args.kwargs["text"] == "Account deleted successfully!"
            assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_deletion_error(
        self,
        handler: CancelHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle method with user deletion error.

        :param handler: CancelHandler instance
        :type handler: CancelHandler
        :param mock_update: Mock Update object
        :type mock_update: MagicMock
        :param mock_context: Mock ContextTypes object
        :type mock_context: MagicMock
        :param mock_get_user_language: Mocked get_user_language function
        :type mock_get_user_language: MagicMock
        :returns: None
        :rtype: None
        """
        mock_get_user_language.return_value = SupportedLanguage.EN.value

        with patch(
            "src.bot.handlers.cancel_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.base_handler.user_service"
        ) as mock_base_user_service, patch(
            "src.bot.handlers.cancel_handler.remove_user_from_scheduler"
        ) as mock_remove_scheduler, patch(
            "src.bot.handlers.cancel_handler.generate_message_cancel_error"
        ) as mock_generate_error:
            # Create mock user profile
            mock_user_profile = MagicMock()
            mock_user_profile.user = mock_update.effective_user
            mock_user_profile.settings = MagicMock()
            mock_user_profile.settings.birth_date = MagicMock()

            mock_user_service.is_valid_user_profile.return_value = True
            mock_user_service.get_user_profile.return_value = mock_user_profile
            mock_base_user_service.is_valid_user_profile.return_value = True
            mock_user_service.delete_user_profile.side_effect = UserDeletionError(
                "Delete failed"
            )
            mock_remove_scheduler.return_value = None
            mock_generate_error.return_value = "Error deleting account!"

            # Configure mock_context.bot_data.get to return a scheduler mock
            mock_scheduler = MagicMock()
            mock_context.bot_data.get.return_value = mock_scheduler

            await handler.handle(mock_update, mock_context)

            mock_generate_error.assert_called_once()
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert call_args.kwargs["text"] == "Error deleting account!"
            assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_service_error(
        self,
        handler: CancelHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle method with user service error.

        :param handler: CancelHandler instance
        :type handler: CancelHandler
        :param mock_update: Mock Update object
        :type mock_update: MagicMock
        :param mock_context: Mock ContextTypes object
        :type mock_context: MagicMock
        :param mock_get_user_language: Mocked get_user_language function
        :type mock_get_user_language: MagicMock
        :returns: None
        :rtype: None
        """
        mock_get_user_language.return_value = SupportedLanguage.EN.value

        with patch(
            "src.bot.handlers.cancel_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.base_handler.user_service"
        ) as mock_base_user_service, patch(
            "src.bot.handlers.cancel_handler.remove_user_from_scheduler"
        ) as mock_remove_scheduler, patch(
            "src.bot.handlers.cancel_handler.generate_message_cancel_error"
        ) as mock_generate_error:
            # Create mock user profile
            mock_user_profile = MagicMock()
            mock_user_profile.user = mock_update.effective_user
            mock_user_profile.settings = MagicMock()
            mock_user_profile.settings.birth_date = MagicMock()

            mock_user_service.is_valid_user_profile.return_value = True
            mock_user_service.get_user_profile.return_value = mock_user_profile
            mock_base_user_service.is_valid_user_profile.return_value = True
            mock_user_service.delete_user_profile.side_effect = UserServiceError(
                "Service error"
            )
            mock_remove_scheduler.return_value = None
            mock_generate_error.return_value = "Service error occurred!"

            # Configure mock_context.bot_data.get to return a scheduler mock
            mock_scheduler = MagicMock()
            mock_context.bot_data.get.return_value = mock_scheduler

            await handler.handle(mock_update, mock_context)

            mock_generate_error.assert_called_once()
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert call_args.kwargs["text"] == "Service error occurred!"
            assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_scheduler_removal_failure(
        self,
        handler: CancelHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_get_user_language: MagicMock,
    ) -> None:
        """Test handle method with scheduler removal failure.

        :param handler: CancelHandler instance
        :type handler: CancelHandler
        :param mock_update: Mock Update object
        :type mock_update: MagicMock
        :param mock_context: Mock ContextTypes object
        :type mock_context: MagicMock
        :param mock_get_user_language: Mocked get_user_language function
        :type mock_get_user_language: MagicMock
        :returns: None
        :rtype: None
        """
        mock_get_user_language.return_value = SupportedLanguage.EN.value

        with patch(
            "src.bot.handlers.cancel_handler.user_service"
        ) as mock_user_service, patch(
            "src.bot.handlers.base_handler.user_service"
        ) as mock_base_user_service, patch(
            "src.bot.handlers.cancel_handler.remove_user_from_scheduler"
        ) as mock_remove_scheduler, patch(
            "src.bot.handlers.cancel_handler.generate_message_cancel_error"
        ) as mock_generate_error:
            # Create mock user profile
            mock_user_profile = MagicMock()
            mock_user_profile.user = mock_update.effective_user
            mock_user_profile.settings = MagicMock()
            mock_user_profile.settings.birth_date = MagicMock()

            mock_user_service.is_valid_user_profile.return_value = True
            mock_user_service.get_user_profile.return_value = mock_user_profile
            mock_base_user_service.is_valid_user_profile.return_value = True
            mock_user_service.delete_user_profile.return_value = None
            mock_generate_error.return_value = "Scheduler error occurred!"
            from src.bot.scheduler import SchedulerOperationError

            mock_remove_scheduler.side_effect = SchedulerOperationError(
                message="Scheduler not initialized",
                user_id=TEST_USER_ID,
                operation="remove_user",
            )

            # Configure mock_context.bot_data.get to return a scheduler mock
            mock_scheduler = MagicMock()
            mock_context.bot_data.get.return_value = mock_scheduler

            await handler.handle(mock_update, mock_context)

            mock_generate_error.assert_called_once()
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert call_args.kwargs["text"] == "Scheduler error occurred!"
            assert call_args.kwargs["parse_mode"] == ParseMode.HTML
