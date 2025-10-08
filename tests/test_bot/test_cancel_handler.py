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
    """Test suite for CancelHandler class.

    This test class contains all tests for CancelHandler functionality,
    including successful cancellation, error handling for deletion failures,
    service errors, and scheduler removal failures.
    """

    @pytest.fixture
    def handler(self) -> CancelHandler:
        """Create CancelHandler instance for testing.

        :returns: Configured CancelHandler instance with fake service container
        :rtype: CancelHandler
        """
        services = FakeServiceContainer()
        return CancelHandler(services)

    @pytest.fixture(autouse=True)
    def mock_use_locale(self, mocker) -> MagicMock:
        """Mock use_locale to control translations.

        This fixture automatically mocks the use_locale function to return
        predictable translation strings for testing purposes.

        :param mocker: pytest-mock fixture for creating mocks
        :type mocker: pytest_mock.MockerFixture
        :returns: Mocked pgettext function
        :rtype: MagicMock
        """
        mock_pgettext = MagicMock(side_effect=lambda c, m: f"pgettext_{c}_{m}")
        mocker.patch(
            "src.bot.handlers.cancel_handler.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return mock_pgettext

    def test_handler_creation(self, handler: CancelHandler) -> None:
        """Test that CancelHandler is created with correct command name.

        This test verifies that the handler is properly initialized with
        the /cancel command name constant.

        :param handler: CancelHandler instance from fixture
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
    ) -> None:
        """Test successful user cancellation and profile deletion.

        This test verifies that when a user cancels their registration,
        the handler correctly removes them from the scheduler, deletes
        their profile, and sends a success message.

        :param handler: CancelHandler instance from fixture
        :type handler: CancelHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
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
        """Test cancellation handling when user deletion fails.

        This test verifies that when the delete_user_profile operation
        raises a UserDeletionError, the handler catches it and sends
        an appropriate error message to the user.

        :param handler: CancelHandler instance from fixture
        :type handler: CancelHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
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
        """Test cancellation handling when user service encounters an error.

        This test verifies that when the user service raises a generic
        UserServiceError during deletion, the handler catches it and
        sends an appropriate error message to the user.

        :param handler: CancelHandler instance from fixture
        :type handler: CancelHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
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
        """Test cancellation handling when scheduler removal fails.

        This test verifies that when removing the user from the scheduler
        fails with a SchedulerOperationError, the handler catches it and
        sends an appropriate error message to the user.

        :param handler: CancelHandler instance from fixture
        :type handler: CancelHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
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
