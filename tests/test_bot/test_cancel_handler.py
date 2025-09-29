"""Unit tests for CancelHandler.

Tests the CancelHandler class which handles /cancel command.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.bot.constants import COMMAND_CANCEL
from src.bot.handlers.cancel_handler import CancelHandler
from src.database.service import UserDeletionError, UserServiceError
from tests.conftest import TEST_USER_ID
from tests.utils.fake_container import FakeServiceContainer


class TestCancelHandler:
    """Test suite for CancelHandler class."""

    @pytest.fixture
    def handler(self) -> CancelHandler:
        """Create CancelHandler instance."""
        services = FakeServiceContainer()
        return CancelHandler(services)

    @pytest.fixture(autouse=True)
    def mock_use_locale(self, mocker):
        """Mock use_locale to control translations."""
        mock_pgettext = MagicMock(side_effect=lambda c, m: f"pgettext_{c}_{m}")
        mocker.patch(
            "src.bot.handlers.cancel_handler.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return mock_pgettext

    def test_handler_creation(self, handler: CancelHandler) -> None:
        """Test CancelHandler creation."""
        assert handler.command_name == f"/{COMMAND_CANCEL}"

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: CancelHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handle method with successful cancellation."""
        mock_user_profile = MagicMock()
        handler.services.user_service.is_valid_user_profile.return_value = True
        handler.services.user_service.get_user_profile.return_value = mock_user_profile

        with patch(
            "src.bot.handlers.cancel_handler.remove_user_from_scheduler"
        ) as mock_remove_scheduler:
            mock_scheduler = MagicMock()
            mock_context.bot_data.get.return_value = mock_scheduler

            await handler.handle(mock_update, mock_context)

            mock_remove_scheduler.assert_called_once_with(
                mock_scheduler, mock_update.effective_user.id
            )
            handler.services.user_service.delete_user_profile.assert_called_once_with(
                telegram_id=mock_update.effective_user.id
            )
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "pgettext_cancel.success_" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_deletion_error(
        self,
        handler: CancelHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handle method with user deletion error."""
        handler.services.user_service.is_valid_user_profile.return_value = True
        handler.services.user_service.delete_user_profile.side_effect = (
            UserDeletionError("Delete failed")
        )

        with patch("src.bot.handlers.cancel_handler.remove_user_from_scheduler"):
            await handler.handle(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "pgettext_cancel.error_" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_service_error(
        self,
        handler: CancelHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handle method with user service error."""
        handler.services.user_service.is_valid_user_profile.return_value = True
        handler.services.user_service.delete_user_profile.side_effect = (
            UserServiceError("Service error")
        )

        with patch("src.bot.handlers.cancel_handler.remove_user_from_scheduler"):
            await handler.handle(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "pgettext_cancel.error_" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_scheduler_removal_failure(
        self,
        handler: CancelHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handle method with scheduler removal failure."""
        handler.services.user_service.is_valid_user_profile.return_value = True
        from src.bot.scheduler import SchedulerOperationError

        with patch(
            "src.bot.handlers.cancel_handler.remove_user_from_scheduler"
        ) as mock_remove_scheduler:
            mock_remove_scheduler.side_effect = SchedulerOperationError(
                message="Scheduler not initialized",
                user_id=TEST_USER_ID,
                operation="remove_user",
            )
            await handler.handle(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "pgettext_cancel.error_" in call_args.kwargs["text"]
