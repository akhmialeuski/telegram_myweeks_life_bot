"""Unit tests for StartHandler.

Tests the StartHandler class which handles /start command and user registration.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from telegram.constants import ParseMode

from src.bot.constants import COMMAND_START
from src.bot.handlers.start_handler import StartHandler
from src.database.service import (
    UserRegistrationError,
    UserServiceError,
)


class TestStartHandler:
    """Test suite for StartHandler class."""

    @pytest.fixture
    def handler(self) -> StartHandler:
        """Create StartHandler instance.

        :returns: StartHandler instance
        :rtype: StartHandler
        """
        return StartHandler()

    def test_handler_creation(self, handler: StartHandler) -> None:
        """Test StartHandler creation.

        :param handler: StartHandler instance
        :returns: None
        """
        assert handler.command_name == f"/{COMMAND_START}"

    @pytest.mark.asyncio
    async def test_handle_existing_user(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_start_handler_user_service: MagicMock,
        mock_generate_message_start_welcome_existing: MagicMock,
    ) -> None:
        """Test handle method with existing user.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_start_handler_user_service: Mocked user_service for start handler
        :param mock_generate_message_start_welcome_existing: Mocked generate_message_start_welcome_existing function
        :returns: None
        """
        # Setup
        mock_start_handler_user_service.is_valid_user_profile.return_value = True
        mock_generate_message_start_welcome_existing.return_value = "Welcome back!"

        # Execute
        await handler.handle(mock_update, mock_context)

        # Assert
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Welcome back!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_new_user(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_start_handler_user_service: MagicMock,
        mock_generate_message_start_welcome_new: MagicMock,
    ) -> None:
        """Test handle method with new user.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_start_handler_user_service: Mocked user_service for start handler
        :param mock_generate_message_start_welcome_new: Mocked generate_message_start_welcome_new function
        :returns: None
        """
        # Setup
        mock_start_handler_user_service.is_valid_user_profile.return_value = False
        mock_generate_message_start_welcome_new.return_value = (
            "Welcome! Please register."
        )

        # Execute
        await handler.handle(mock_update, mock_context)

        # Assert
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Welcome! Please register."
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML
        assert mock_context.user_data["waiting_for"] == "start_birth_date"

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_success(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_start_handler_user_service: MagicMock,
        mock_generate_message_start_welcome_existing: MagicMock,
        mock_add_user_to_scheduler: MagicMock,
    ) -> None:
        """Test handle_birth_date_input with valid birth date.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_start_handler_user_service: Mocked user_service for start handler
        :param mock_generate_message_start_welcome_existing: Mocked generate_message_start_welcome_existing function
        :param mock_add_user_to_scheduler: Mocked add_user_to_scheduler function
        :returns: None
        """
        # Setup
        mock_context.user_data["waiting_for"] = "start_birth_date"
        mock_update.message.text = "15.03.1990"
        birth_date = datetime.strptime("15.03.1990", "%d.%m.%Y").date()

        mock_generate_message_start_welcome_existing.return_value = (
            "Registration successful!"
        )
        mock_add_user_to_scheduler.return_value = True

        # Execute
        await handler.handle_birth_date_input(mock_update, mock_context)

        # Assert
        mock_start_handler_user_service.create_user_profile.assert_called_once_with(
            user_info=mock_update.effective_user, birth_date=birth_date
        )
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Registration successful!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML
        assert "waiting_for" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_future_date(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_generate_message_birth_date_future_error: MagicMock,
    ) -> None:
        """Test handle_birth_date_input with future date.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_generate_message_birth_date_future_error: Mocked generate_message_birth_date_future_error function
        :returns: None
        """
        # Setup
        mock_context.user_data["waiting_for"] = "start_birth_date"
        mock_update.message.text = "15.03.2030"
        mock_generate_message_birth_date_future_error.return_value = (
            "Future date not allowed!"
        )

        # Execute
        await handler.handle_birth_date_input(mock_update, mock_context)

        # Assert
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Future date not allowed!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_old_date(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_generate_message_birth_date_old_error: MagicMock,
    ) -> None:
        """Test handle_birth_date_input with too old date.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_generate_message_birth_date_old_error: Mocked generate_message_birth_date_old_error function
        :returns: None
        """
        # Setup
        mock_context.user_data["waiting_for"] = "start_birth_date"
        mock_update.message.text = "15.03.1800"
        mock_generate_message_birth_date_old_error.return_value = "Date too old!"

        # Execute
        await handler.handle_birth_date_input(mock_update, mock_context)

        # Assert
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Date too old!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_invalid_format(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_generate_message_birth_date_format_error: MagicMock,
    ) -> None:
        """Test handle_birth_date_input with invalid format.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_generate_message_birth_date_format_error: Mocked generate_message_birth_date_format_error function
        :returns: None
        """
        # Setup
        mock_context.user_data["waiting_for"] = "start_birth_date"
        mock_update.message.text = "invalid-date"
        mock_generate_message_birth_date_format_error.return_value = "Invalid format!"

        # Execute
        await handler.handle_birth_date_input(mock_update, mock_context)

        # Assert
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Invalid format!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_registration_error(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_start_handler_user_service: MagicMock,
        mock_generate_message_registration_error: MagicMock,
    ) -> None:
        """Test handle_birth_date_input with registration error.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_start_handler_user_service: Mocked user_service for start handler
        :param mock_generate_message_registration_error: Mocked generate_message_registration_error function
        :returns: None
        """
        # Setup
        mock_context.user_data["waiting_for"] = "start_birth_date"
        mock_update.message.text = "15.03.1990"
        mock_start_handler_user_service.create_user_profile.side_effect = (
            UserRegistrationError("Registration failed")
        )
        mock_generate_message_registration_error.return_value = "Registration failed!"

        # Execute
        await handler.handle_birth_date_input(mock_update, mock_context)

        # Assert
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Registration failed!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML
        mock_start_handler_user_service.create_user_profile.assert_called_once()
        assert "waiting_for" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_service_error(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_start_handler_user_service: MagicMock,
        mock_generate_message_registration_error: MagicMock,
    ) -> None:
        """Test handle_birth_date_input with service error.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_start_handler_user_service: Mocked user_service for start handler
        :param mock_generate_message_registration_error: Mocked generate_message_registration_error function
        :returns: None
        """
        # Setup
        mock_context.user_data["waiting_for"] = "start_birth_date"
        mock_update.message.text = "15.03.1990"
        mock_start_handler_user_service.create_user_profile.side_effect = (
            UserServiceError("Service error")
        )
        mock_generate_message_registration_error.return_value = "Service error!"

        # Execute
        await handler.handle_birth_date_input(mock_update, mock_context)

        # Assert
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Service error!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML
        mock_start_handler_user_service.create_user_profile.assert_called_once()
        assert "waiting_for" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_scheduler_failure(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_start_handler_user_service: MagicMock,
        mock_generate_message_start_welcome_existing: MagicMock,
        mock_add_user_to_scheduler: MagicMock,
    ) -> None:
        """Test handle_birth_date_input with scheduler failure.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_start_handler_user_service: Mocked user_service for start handler
        :param mock_generate_message_start_welcome_existing: Mocked generate_message_start_welcome_existing function
        :param mock_add_user_to_scheduler: Mocked add_user_to_scheduler function
        :returns: None
        """
        # Setup
        mock_context.user_data["waiting_for"] = "start_birth_date"
        mock_update.message.text = "15.03.1990"
        birth_date = datetime.strptime("15.03.1990", "%d.%m.%Y").date()

        mock_generate_message_start_welcome_existing.return_value = (
            "Registration successful!"
        )
        mock_add_user_to_scheduler.return_value = False

        # Execute
        await handler.handle_birth_date_input(mock_update, mock_context)

        # Assert
        mock_start_handler_user_service.create_user_profile.assert_called_once_with(
            user_info=mock_update.effective_user, birth_date=birth_date
        )
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert call_args.kwargs["text"] == "Registration successful!"
        assert call_args.kwargs["parse_mode"] == ParseMode.HTML
        assert "waiting_for" not in mock_context.user_data
