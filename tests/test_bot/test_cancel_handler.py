"""Unit tests for CancelHandler.

Tests the CancelHandler class which handles /cancel command.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from telegram import Update
from telegram.ext import ContextTypes

from src.bot.handlers.cancel_handler import CancelHandler
from src.database.service import (
    UserDeletionError,
    UserServiceError,
)


class TestCancelHandler:
    """Test suite for CancelHandler class."""

    @pytest.fixture
    def handler(self) -> CancelHandler:
        """Create CancelHandler instance.

        :returns: CancelHandler instance
        :rtype: CancelHandler
        """
        return CancelHandler()

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

    def test_handler_creation(self, handler: CancelHandler) -> None:
        """Test CancelHandler creation.

        :param handler: CancelHandler instance
        :returns: None
        """
        assert handler.command_name == "/cancel"

    @pytest.mark.asyncio
    async def test_handle_success(
        self, handler: CancelHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with successful cancellation.

        :param handler: CancelHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch(
            "src.bot.handlers.cancel_handler.remove_user_from_scheduler"
        ) as mock_remove_scheduler:
            with patch(
                "src.bot.handlers.cancel_handler.generate_message_cancel_success"
            ) as mock_generate_message:
                with patch(
                    "src.bot.handlers.cancel_handler.get_user_language"
                ) as mock_get_language:
                    with patch(
                        "src.bot.handlers.cancel_handler.user_service"
                    ) as mock_user_service:
                        with patch(
                            "src.bot.handlers.base_handler.user_service"
                        ) as mock_base_user_service:
                            mock_base_user_service.is_valid_user_profile.return_value = (
                                True
                            )
                            mock_user_service.delete_user_profile.return_value = None
                            mock_generate_message.return_value = (
                                "Account deleted successfully!"
                            )
                            mock_remove_scheduler.return_value = True
                            mock_get_language.return_value = "en"

                            # Execute
                            await handler.handle(mock_update, mock_context)

                            # Assert
                            mock_user_service.delete_user_profile.assert_called_once_with(
                                mock_update.effective_user.id
                            )
                            mock_update.message.reply_text.assert_called_once_with(
                                text="Account deleted successfully!", parse_mode="HTML"
                            )

    @pytest.mark.asyncio
    async def test_handle_deletion_error(
        self, handler: CancelHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with deletion error.

        :param handler: CancelHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch(
            "src.bot.handlers.cancel_handler.generate_message_cancel_error"
        ) as mock_generate_message:
            with patch(
                "src.bot.handlers.base_handler.user_service"
            ) as mock_user_service:
                mock_user_service.delete_user_profile.side_effect = UserDeletionError(
                    "Deletion failed"
                )
                mock_generate_message.return_value = "Deletion failed!"

                # Execute
                await handler.handle(mock_update, mock_context)

                # Assert
                mock_update.message.reply_text.assert_called_once_with(
                    text="Deletion failed!", parse_mode="HTML"
                )

    @pytest.mark.asyncio
    async def test_handle_service_error(
        self, handler: CancelHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with service error.

        :param handler: CancelHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch(
            "src.bot.handlers.cancel_handler.generate_message_cancel_error"
        ) as mock_generate_message:
            with patch(
                "src.bot.handlers.base_handler.user_service"
            ) as mock_user_service:
                mock_user_service.delete_user_profile.side_effect = UserServiceError(
                    "Service error"
                )
                mock_generate_message.return_value = "Service error!"

                # Execute
                await handler.handle(mock_update, mock_context)

                # Assert
                mock_update.message.reply_text.assert_called_once_with(
                    text="Service error!", parse_mode="HTML"
                )

    @pytest.mark.asyncio
    async def test_handle_scheduler_removal_failure(
        self, handler: CancelHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with scheduler removal failure.

        :param handler: CancelHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch(
            "src.bot.handlers.cancel_handler.remove_user_from_scheduler"
        ) as mock_remove_scheduler:
            with patch(
                "src.bot.handlers.cancel_handler.generate_message_cancel_success"
            ) as mock_generate_message:
                with patch(
                    "src.bot.handlers.cancel_handler.get_user_language"
                ) as mock_get_language:
                    with patch(
                        "src.bot.handlers.cancel_handler.user_service"
                    ) as mock_user_service:
                        with patch(
                            "src.bot.handlers.base_handler.user_service"
                        ) as mock_base_user_service:
                            mock_base_user_service.is_valid_user_profile.return_value = (
                                True
                            )
                            mock_user_service.delete_user_profile.return_value = None
                            mock_generate_message.return_value = (
                                "Account deleted successfully!"
                            )
                            mock_remove_scheduler.return_value = False
                            mock_get_language.return_value = "en"

                            # Execute
                            await handler.handle(mock_update, mock_context)

                            # Assert
                            mock_user_service.delete_user_profile.assert_called_once_with(
                                mock_update.effective_user.id
                            )
                            mock_update.message.reply_text.assert_called_once_with(
                                text="Account deleted successfully!", parse_mode="HTML"
                            )
