"""Unit tests for StartHandler.

Tests the StartHandler class which handles /start command and user registration.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from telegram import Update
from telegram.ext import ContextTypes

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

    def test_handler_creation(self, handler: StartHandler) -> None:
        """Test StartHandler creation.

        :param handler: StartHandler instance
        :returns: None
        """
        assert handler.command_name == "/start"

    @pytest.mark.asyncio
    async def test_handle_existing_user(
        self, handler: StartHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with existing user.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.start_handler.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.start_handler.generate_message_start_welcome_existing"
            ) as mock_generate_message:
                mock_user_service.is_valid_user_profile.return_value = True
                mock_generate_message.return_value = "Welcome back!"

                # Execute
                await handler.handle(mock_update, mock_context)

                # Assert
                mock_update.message.reply_text.assert_called_once_with(
                    text="Welcome back!", parse_mode="HTML"
                )

    @pytest.mark.asyncio
    async def test_handle_new_user(
        self, handler: StartHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle method with new user.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.start_handler.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.start_handler.generate_message_start_welcome_new"
            ) as mock_generate_message:
                mock_user_service.is_valid_user_profile.return_value = False
                mock_generate_message.return_value = "Welcome! Please register."

                # Execute
                await handler.handle(mock_update, mock_context)

                # Assert
                mock_update.message.reply_text.assert_called_once_with(
                    text="Welcome! Please register.", parse_mode="HTML"
                )
                assert mock_context.user_data["waiting_for"] == "birth_date"

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_success(
        self, handler: StartHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle_birth_date_input with valid birth date.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_context.user_data["waiting_for"] = "birth_date"
        mock_update.message.text = "15.03.1990"
        birth_date = datetime.strptime("15.03.1990", "%d.%m.%Y").date()

        with patch("src.bot.handlers.start_handler.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.start_handler.generate_message_start_welcome_existing"
            ) as mock_generate_message:
                with patch(
                    "src.bot.handlers.start_handler.add_user_to_scheduler"
                ) as mock_add_scheduler:
                    mock_generate_message.return_value = "Registration successful!"
                    mock_add_scheduler.return_value = True

                    # Execute
                    await handler.handle_birth_date_input(mock_update, mock_context)

                    # Assert
                    mock_user_service.create_user_profile.assert_called_once_with(
                        user_info=mock_update.effective_user, birth_date=birth_date
                    )
                    mock_update.message.reply_text.assert_called_once_with(
                        text="Registration successful!", parse_mode="HTML"
                    )
                    assert "waiting_for" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_future_date(
        self, handler: StartHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle_birth_date_input with future date.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_context.user_data["waiting_for"] = "birth_date"
        mock_update.message.text = "15.03.2030"

        with patch(
            "src.bot.handlers.start_handler.generate_message_birth_date_future_error"
        ) as mock_generate_message:
            mock_generate_message.return_value = "Future date not allowed!"

            # Execute
            await handler.handle_birth_date_input(mock_update, mock_context)

            # Assert
            mock_update.message.reply_text.assert_called_once_with(
                text="Future date not allowed!", parse_mode="HTML"
            )

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_old_date(
        self, handler: StartHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle_birth_date_input with too old date.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_context.user_data["waiting_for"] = "birth_date"
        mock_update.message.text = "15.03.1800"

        with patch(
            "src.bot.handlers.start_handler.generate_message_birth_date_old_error"
        ) as mock_generate_message:
            mock_generate_message.return_value = "Date too old!"

            # Execute
            await handler.handle_birth_date_input(mock_update, mock_context)

            # Assert
            mock_update.message.reply_text.assert_called_once_with(
                text="Date too old!", parse_mode="HTML"
            )

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_invalid_format(
        self, handler: StartHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle_birth_date_input with invalid format.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_context.user_data["waiting_for"] = "birth_date"
        mock_update.message.text = "invalid-date"

        with patch(
            "src.bot.handlers.start_handler.generate_message_birth_date_format_error"
        ) as mock_generate_message:
            mock_generate_message.return_value = "Invalid format!"

            # Execute
            await handler.handle_birth_date_input(mock_update, mock_context)

            # Assert
            mock_update.message.reply_text.assert_called_once_with(
                text="Invalid format!", parse_mode="HTML"
            )

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_registration_error(
        self, handler: StartHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle_birth_date_input with registration error.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_context.user_data["waiting_for"] = "birth_date"
        mock_update.message.text = "15.03.1990"

        with patch("src.bot.handlers.start_handler.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.start_handler.generate_message_registration_error"
            ) as mock_generate_message:
                mock_user_service.create_user_profile.side_effect = (
                    UserRegistrationError("Registration failed")
                )
                mock_generate_message.return_value = "Registration failed!"

                # Execute
                await handler.handle_birth_date_input(mock_update, mock_context)

                # Assert
                mock_update.message.reply_text.assert_called_once_with(
                    text="Registration failed!", parse_mode="HTML"
                )
                mock_user_service.create_user_profile.assert_called_once()
                assert "waiting_for" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_service_error(
        self, handler: StartHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle_birth_date_input with service error.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_context.user_data["waiting_for"] = "birth_date"
        mock_update.message.text = "15.03.1990"

        with patch("src.bot.handlers.start_handler.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.start_handler.generate_message_registration_error"
            ) as mock_generate_message:
                mock_user_service.create_user_profile.side_effect = UserServiceError(
                    "Service error"
                )
                mock_generate_message.return_value = "Service error!"

                # Execute
                await handler.handle_birth_date_input(mock_update, mock_context)

                # Assert
                mock_update.message.reply_text.assert_called_once_with(
                    text="Service error!", parse_mode="HTML"
                )
                mock_user_service.create_user_profile.assert_called_once()
                assert "waiting_for" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_scheduler_failure(
        self, handler: StartHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle_birth_date_input with scheduler failure.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_context.user_data["waiting_for"] = "birth_date"
        mock_update.message.text = "15.03.1990"

        with patch("src.bot.handlers.start_handler.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.start_handler.generate_message_start_welcome_existing"
            ) as mock_generate_message:
                with patch(
                    "src.bot.handlers.start_handler.add_user_to_scheduler"
                ) as mock_add_scheduler:
                    mock_generate_message.return_value = "Registration successful!"
                    mock_add_scheduler.return_value = False

                    # Execute
                    await handler.handle_birth_date_input(mock_update, mock_context)

                    # Assert
                    mock_update.message.reply_text.assert_called_once_with(
                        text="Registration successful!", parse_mode="HTML"
                    )
                    mock_user_service.create_user_profile.assert_called_once()
                    assert "waiting_for" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_not_waiting(
        self, handler: StartHandler, mock_update: Mock, mock_context: Mock
    ) -> None:
        """Test handle_birth_date_input when not waiting for birth date.

        :param handler: StartHandler instance
        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_context.user_data["waiting_for"] = "something_else"
        mock_update.message.text = "15.03.1990"

        with patch(
            "src.bot.handlers.unknown_handler.UnknownHandler"
        ) as mock_unknown_handler:
            mock_unknown_instance = Mock()
            mock_unknown_instance.handle = AsyncMock()
            mock_unknown_handler.return_value = mock_unknown_instance

            # Execute
            await handler.handle_birth_date_input(mock_update, mock_context)

            # Assert
            mock_unknown_instance.handle.assert_called_once_with(
                mock_update, mock_context
            )
