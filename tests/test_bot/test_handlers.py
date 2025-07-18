"""Unit tests for bot handlers.

Tests all handler functions in the bot handlers module
with proper mocking, edge cases, and error handling coverage.
"""

# from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch, call

import pytest
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.handlers import (
    WAITING_USER_INPUT,
    command_cancel,
    command_help,
    command_language_callback,
    command_settings,
    command_settings_callback,
    command_start,
    command_start_handle_birth_date,
    command_subscription,
    command_subscription_callback,
    command_visualize,
    command_weeks,
    handle_birth_date_input,
    handle_life_expectancy_input,
    handle_settings_input,
    handle_unknown_message,
    require_registration,
)
from src.database.models import SubscriptionType
from src.database.service import (
    UserAlreadyExistsError,
    UserDeletionError,
    UserNotFoundError,
    UserRegistrationError,
    UserServiceError,
    UserSettingsUpdateError,
)
from src.bot.scheduler import (
    add_user_to_scheduler,
    remove_user_from_scheduler,
    setup_user_notification_schedules,
    start_scheduler,
    stop_scheduler,
    send_weekly_message_to_user,
    update_user_schedule,
)


class TestRequireRegistrationDecorator:
    """Test suite for require_registration decorator."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update object.

        :returns: Mock Update object
        :rtype: Mock
        """
        update = Mock(spec=Update)
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.language_code = "en"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock ContextTypes object.

        :returns: Mock ContextTypes object
        :rtype: Mock
        """
        return Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.mark.asyncio
    async def test_require_registration_with_valid_user(
        self, mock_update, mock_context
    ):
        """Test decorator with valid registered user.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_handler = AsyncMock(return_value="success")
        decorated_handler = require_registration()(mock_handler)

        with patch("src.bot.handlers.user_service") as mock_user_service:
            mock_user_service.is_valid_user_profile.return_value = True

            # Execute
            result = await decorated_handler(mock_update, mock_context)

            # Assert
            assert result == "success"
            mock_handler.assert_called_once_with(mock_update, mock_context)
            mock_user_service.is_valid_user_profile.assert_called_once_with(123456789)

    @pytest.mark.asyncio
    async def test_require_registration_with_invalid_user(
        self, mock_update, mock_context
    ):
        """Test decorator with unregistered user.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_handler = AsyncMock()
        decorated_handler = require_registration()(mock_handler)

        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch("src.bot.handlers.get_message") as mock_get_message:
                mock_user_service.is_valid_user_profile.return_value = False
                mock_get_message.return_value = "Not registered"

                # Execute
                result = await decorated_handler(mock_update, mock_context)

                # Assert
                assert result is None
                mock_handler.assert_not_called()
                mock_update.message.reply_text.assert_called_once_with("Not registered")
                mock_get_message.assert_called_once_with(
                    message_key="common", sub_key="not_registered", language="en"
                )

    @pytest.mark.asyncio
    async def test_require_registration_with_exception(self, mock_update, mock_context):
        """Test decorator with exception in handler.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_handler = AsyncMock(side_effect=Exception("Test error"))
        decorated_handler = require_registration()(mock_handler)

        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch("src.bot.handlers.get_message") as mock_get_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.is_valid_user_profile.return_value = True
                    mock_get_message.return_value = "Error occurred"

                    # Execute
                    result = await decorated_handler(mock_update, mock_context)

                    # Assert
                    assert result is None
                    mock_handler.assert_called_once_with(mock_update, mock_context)
                    mock_update.message.reply_text.assert_called_once_with(
                        "Error occurred"
                    )
                    mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_require_registration_with_no_language_code(
        self, mock_update, mock_context
    ):
        """Test decorator with user having no language code.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_update.effective_user.language_code = None
        mock_handler = AsyncMock()
        decorated_handler = require_registration()(mock_handler)

        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch("src.bot.handlers.get_message") as mock_get_message:
                mock_user_service.is_valid_user_profile.return_value = False
                mock_get_message.return_value = "Not registered"

                # Execute
                await decorated_handler(mock_update, mock_context)

                # Assert
                mock_get_message.assert_called_once_with(
                    message_key="common", sub_key="not_registered", language="ru"
                )  # Should use DEFAULT_LANGUAGE


class TestCommandStart:
    """Test suite for command_start handler."""

    @pytest.fixture
    def mock_update(self):
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
    def mock_context(self):
        """Create mock ContextTypes object.

        :returns: Mock ContextTypes object
        :rtype: Mock
        """
        return Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.mark.asyncio
    async def test_command_start_existing_user(self, mock_update, mock_context):
        """Test /start command with existing user.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_start_welcome_existing"
            ) as mock_generate_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.is_valid_user_profile.return_value = True
                    mock_generate_message.return_value = "Welcome back!"

                    # Execute
                    result = await command_start(mock_update, mock_context)

                    # Assert
                    assert result == ConversationHandler.END
                    mock_update.message.reply_text.assert_called_once_with(
                        text="Welcome back!", parse_mode="HTML"
                    )
                    mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_command_start_new_user(self, mock_update, mock_context):
        """Test /start command with new user.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_start_welcome_new"
            ) as mock_generate_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.is_valid_user_profile.return_value = False
                    mock_generate_message.return_value = "Welcome! Please register."

                    # Execute
                    result = await command_start(mock_update, mock_context)

                    # Assert
                    assert result == WAITING_USER_INPUT
                    mock_update.message.reply_text.assert_called_once_with(
                        text="Welcome! Please register.", parse_mode="HTML"
                    )
                    mock_logger.info.assert_called_once()


class TestCommandStartHandleBirthDate:
    """Test suite for command_start_handle_birth_date handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update object.

        :returns: Mock Update object
        :rtype: Mock
        """
        update = Mock(spec=Update)
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.username = "testuser"
        update.message = Mock()
        update.message.text = "15.03.1990"
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock ContextTypes object.

        :returns: Mock ContextTypes object
        :rtype: Mock
        """
        return Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.mark.asyncio
    async def test_handle_birth_date_success(self, mock_update, mock_context):
        """Test successful birth date handling.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_start_welcome_existing"
            ) as mock_generate_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    with patch("src.bot.handlers.add_user_to_scheduler") as mock_add_scheduler:
                        # Create a mock user profile that will be returned by get_user_profile
                        from datetime import date
                        mock_user_profile = Mock()
                        mock_user_profile.settings = Mock()
                        mock_user_profile.settings.birth_date = date(1990, 3, 15)
                        mock_user_profile.subscription = Mock()

                        mock_user_service.create_user_profile.return_value = None
                        mock_user_service.get_user_profile.return_value = mock_user_profile
                        mock_generate_message.return_value = "Registration successful!"

                        # Mock add_user_to_scheduler to return True and call logger.info
                        def mock_add_scheduler_side_effect(user_id):
                            mock_logger.info(f"User {user_id} added to notification scheduler")
                            return True

                        mock_add_scheduler.side_effect = mock_add_scheduler_side_effect

                        # Execute
                        result = await command_start_handle_birth_date(
                            mock_update, mock_context
                        )

                        # Assert
                        assert result == ConversationHandler.END
                        mock_update.message.reply_text.assert_called_once_with(
                            text="Registration successful!", parse_mode="HTML"
                        )
                        mock_user_service.create_user_profile.assert_called_once()
                        # Check that logger.info was called with the expected message
                        mock_logger.info.assert_any_call("User 123456789 added to notification scheduler")

    @pytest.mark.asyncio
    async def test_handle_birth_date_future_date(self, mock_update, mock_context):
        """Test birth date handling with future date.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        future_date = "15.03.2030"
        mock_update.message.text = future_date

        with patch(
            "src.bot.handlers.generate_message_birth_date_future_error"
        ) as mock_generate_message:
            mock_generate_message.return_value = "Future date error"

            # Execute
            result = await command_start_handle_birth_date(mock_update, mock_context)

            # Assert
            assert result == WAITING_USER_INPUT
            mock_update.message.reply_text.assert_called_once_with(
                text="Future date error", parse_mode="HTML"
            )

    @pytest.mark.asyncio
    async def test_handle_birth_date_old_date(self, mock_update, mock_context):
        """Test birth date handling with very old date.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        old_date = "15.03.1850"
        mock_update.message.text = old_date

        with patch(
            "src.bot.handlers.generate_message_birth_date_old_error"
        ) as mock_generate_message:
            mock_generate_message.return_value = "Old date error"

            # Execute
            result = await command_start_handle_birth_date(mock_update, mock_context)

            # Assert
            assert result == WAITING_USER_INPUT
            mock_update.message.reply_text.assert_called_once_with(
                text="Old date error", parse_mode="HTML"
            )

    @pytest.mark.asyncio
    async def test_handle_birth_date_invalid_format(self, mock_update, mock_context):
        """Test birth date handling with invalid format.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        invalid_date = "invalid-date"
        mock_update.message.text = invalid_date

        with patch(
            "src.bot.handlers.generate_message_birth_date_format_error"
        ) as mock_generate_message:
            mock_generate_message.return_value = "Format error"

            # Execute
            result = await command_start_handle_birth_date(mock_update, mock_context)

            # Assert
            assert result == WAITING_USER_INPUT
            mock_update.message.reply_text.assert_called_once_with(
                text="Format error", parse_mode="HTML"
            )

    @pytest.mark.asyncio
    async def test_handle_birth_date_user_already_exists(
        self, mock_update, mock_context
    ):
        """Test birth date handling when user already exists.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_registration_error"
            ) as mock_generate_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.create_user_profile.side_effect = (
                        UserRegistrationError("User already exists")
                    )
                    mock_generate_message.return_value = "Registration error"

                    # Execute
                    result = await command_start_handle_birth_date(
                        mock_update, mock_context
                    )

                    # Assert
                    assert result == ConversationHandler.END
                    mock_update.message.reply_text.assert_called_once_with(
                        text="Registration error", parse_mode="HTML"
                    )
                    mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_birth_date_registration_error(
        self, mock_update, mock_context
    ):
        """Test birth date handling with registration error.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_registration_error"
            ) as mock_generate_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.create_user_profile.side_effect = (
                        UserRegistrationError("Registration failed")
                    )
                    mock_generate_message.return_value = "Registration error"

                    # Execute
                    result = await command_start_handle_birth_date(
                        mock_update, mock_context
                    )

                    # Assert
                    assert result == ConversationHandler.END
                    mock_update.message.reply_text.assert_called_once_with(
                        text="Registration error", parse_mode="HTML"
                    )
                    mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_birth_date_service_error(self, mock_update, mock_context):
        """Test birth date handling with service error.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_registration_error"
            ) as mock_generate_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.create_user_profile.side_effect = (
                        UserServiceError("Service error")
                    )
                    mock_generate_message.return_value = "Registration error"

                    # Execute
                    result = await command_start_handle_birth_date(
                        mock_update, mock_context
                    )

                    # Assert
                    assert result == ConversationHandler.END
                    mock_update.message.reply_text.assert_called_once_with(
                        text="Registration error", parse_mode="HTML"
                    )
                    mock_logger.error.assert_called_once()

    @patch("src.bot.handlers.add_user_to_scheduler")
    @patch("src.bot.handlers.user_service")
    @patch("src.bot.handlers.logger")
    @pytest.mark.asyncio
    async def test_handle_birth_date_scheduler_failure(
        self, mock_logger, mock_user_service, mock_add_user_to_scheduler, mock_update
    ):
        """Test birth date handling when scheduler addition fails.

        :param mock_add_user_to_scheduler: Mock add_user_to_scheduler function
        :param mock_logger: Mock logger
        :param mock_user_service: Mock user_service
        :param mock_update: Mock update object
        :returns: None
        """
        # Setup
        mock_update.message.text = "15.03.1990"
        mock_user_service.create_user_profile.return_value = None
        mock_add_user_to_scheduler.return_value = False

        # Execute
        result = await command_start_handle_birth_date(mock_update, None)

        # Assert
        assert result == ConversationHandler.END
        mock_user_service.create_user_profile.assert_called_once()
        mock_add_user_to_scheduler.assert_called_once_with(mock_update.effective_user.id)
        warning_calls = [
            call
            for call in mock_logger.warning.call_args_list
            if "Failed to add user" in str(call) and "notification scheduler" in str(call)
        ]
        assert len(warning_calls) > 0


class TestCommandCancel:
    """Test suite for command_cancel handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update object.

        :returns: Mock Update object
        :rtype: Mock
        """
        update = Mock(spec=Update)
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.language_code = "en"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock ContextTypes object.

        :returns: Mock ContextTypes object
        :rtype: Mock
        """
        return Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.mark.asyncio
    async def test_command_cancel_success(self, mock_update, mock_context):
        """Test successful user cancellation.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_user_service = Mock()
        mock_user_service.is_valid_user_profile.return_value = True
        mock_user_service.delete_user_profile.return_value = None
        mock_generate_message = Mock()
        mock_generate_message.return_value = "User deleted successfully"
        mock_get_language = Mock()
        mock_get_language.return_value = "en"
        mock_remove_scheduler = Mock()
        mock_remove_scheduler.return_value = True

        # Execute
        result = await command_cancel(mock_update, mock_context)

        # Assert
        assert result == ConversationHandler.END
        mock_update.message.reply_text.assert_called_once_with(
            text="User deleted successfully", parse_mode="HTML"
        )
        mock_user_service.delete_user_profile.assert_called_once_with(
            123456789
        )
        # Check that logger.info was called three times: once for handling command, once for scheduler removal, once for successful deletion
        assert mock_logger.info.call_count == 3

    @patch("src.bot.handlers.generate_message_settings_error")
    @patch("src.bot.handlers.user_service")
    @patch("src.bot.handlers.logger")
    @pytest.mark.asyncio
    async def test_command_cancel_deletion_error(self, mock_logger, mock_user_service, mock_generate_message, mock_update, mock_context):
        """Test user cancellation with deletion error.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_logger: Mock logger
        :param mock_user_service: Mock user_service
        :param mock_generate_message: Mock generate_message_settings_error function
        :returns: None
        """
        # Setup
        mock_user_service.is_valid_user_profile.return_value = True
        mock_user_service.delete_user_profile.side_effect = (
            UserDeletionError("Deletion failed")
        )
        mock_generate_message.return_value = "Deletion error"

        # Execute
        result = await command_cancel(mock_update, mock_context)

        # Assert
        assert result == ConversationHandler.END
        mock_update.message.reply_text.assert_called_once()
        mock_logger.error.assert_called_once()

    @patch("src.bot.handlers.generate_message_settings_error")
    @patch("src.bot.handlers.user_service")
    @patch("src.bot.handlers.logger")
    @pytest.mark.asyncio
    async def test_command_cancel_service_error(self, mock_logger, mock_user_service, mock_generate_message, mock_update, mock_context):
        """Test user cancellation with service error.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_logger: Mock logger
        :param mock_user_service: Mock user_service
        :param mock_generate_message: Mock generate_message_settings_error function
        :returns: None
        """
        # Setup
        mock_user_service.is_valid_user_profile.return_value = True
        mock_user_service.delete_user_profile.side_effect = (
            UserServiceError("Service error")
        )
        mock_generate_message.return_value = "Deletion error"

        # Execute
        result = await command_cancel(mock_update, mock_context)

        # Assert
        assert result == ConversationHandler.END
        mock_update.message.reply_text.assert_called_once()
        mock_logger.error.assert_called_once()

    @patch("src.bot.handlers.remove_user_from_scheduler")
    @patch("src.bot.handlers.generate_message_cancel_success")
    @patch("src.bot.handlers.get_user_language")
    @patch("src.bot.handlers.user_service")
    @pytest.mark.asyncio
    async def test_command_cancel_success(self, mock_user_service, mock_get_language, mock_generate_message, mock_remove_scheduler, mock_update):
        """Test successful user cancellation.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_user_service.is_valid_user_profile.return_value = True
        mock_user_service.delete_user_profile.return_value = None
        mock_generate_message.return_value = "User deleted successfully"
        mock_get_language.return_value = "en"
        mock_remove_scheduler.return_value = True

        # Execute
        result = await command_cancel(mock_update, None)

        # Assert
        assert result == ConversationHandler.END
        mock_update.message.reply_text.assert_called_once_with(
            text="User deleted successfully", parse_mode="HTML"
        )
        mock_user_service.delete_user_profile.assert_called_once_with(
            123456789
        )

    @patch("src.bot.handlers.remove_user_from_scheduler")
    @patch("src.bot.handlers.user_service")
    @patch("src.bot.handlers.logger")
    @pytest.mark.asyncio
    async def test_command_cancel_scheduler_removal_failure(
        self, mock_logger, mock_user_service, mock_remove_user_from_scheduler, mock_update
    ):
        """Test cancel command when scheduler removal fails.

        :param mock_remove_user_from_scheduler: Mock remove_user_from_scheduler function
        :param mock_logger: Mock logger
        :param mock_user_service: Mock user_service
        :param mock_update: Mock update object
        :returns: None
        """
        # Setup
        mock_remove_user_from_scheduler.return_value = False
        mock_user_service.delete_user_profile.return_value = None

        # Execute
        result = await command_cancel(mock_update, None)

        # Assert
        assert result == ConversationHandler.END
        mock_remove_user_from_scheduler.assert_called_once_with(mock_update.effective_user.id)
        mock_user_service.delete_user_profile.assert_called_once_with(mock_update.effective_user.id)
        warning_calls = [
            call
            for call in mock_logger.warning.call_args_list
            if "Failed to remove user" in str(call) and "notification scheduler" in str(call)
        ]
        assert len(warning_calls) > 0


class TestCommandWeeks:
    """Test suite for command_weeks handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update object.

        :returns: Mock Update object
        :rtype: Mock
        """
        update = Mock(spec=Update)
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.language_code = "en"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock ContextTypes object.

        :returns: Mock ContextTypes object
        :rtype: Mock
        """
        return Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.mark.asyncio
    async def test_command_weeks_success(self, mock_update, mock_context):
        """Test successful weeks command.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_week"
            ) as mock_generate_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.is_valid_user_profile.return_value = True
                    mock_generate_message.return_value = "Week statistics"

                    # Execute
                    await command_weeks(mock_update, mock_context)

                    # Assert
                    mock_update.message.reply_text.assert_called_once_with(
                        text="Week statistics", parse_mode="HTML"
                    )
                    mock_generate_message.assert_called_once_with(
                        user_info=mock_update.effective_user
                    )
                    mock_logger.info.assert_called_once()


class TestCommandVisualize:
    """Test suite for command_visualize handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update object.

        :returns: Mock Update object
        :rtype: Mock
        """
        update = Mock(spec=Update)
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.language_code = "en"
        update.message = Mock()
        update.message.reply_photo = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock ContextTypes object.

        :returns: Mock ContextTypes object
        :rtype: Mock
        """
        return Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.mark.asyncio
    async def test_command_visualize_success(self, mock_update, mock_context):
        """Test successful visualize command.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_visualization"
            ) as mock_generate_visualization:
                with patch(
                    "src.bot.handlers.generate_message_visualize"
                ) as mock_generate_message:
                    with patch("src.bot.handlers.logger") as mock_logger:
                        mock_user_service.is_valid_user_profile.return_value = True
                        mock_generate_visualization.return_value = b"fake_image_data"
                        mock_generate_message.return_value = "Visualization caption"

                        # Execute
                        await command_visualize(mock_update, mock_context)

                        # Assert
                        mock_update.message.reply_photo.assert_called_once_with(
                            photo=b"fake_image_data",
                            caption="Visualization caption",
                            parse_mode="HTML",
                        )
                        mock_generate_visualization.assert_called_once_with(
                            user_info=mock_update.effective_user
                        )
                        mock_generate_message.assert_called_once_with(
                            user_info=mock_update.effective_user
                        )
                        mock_logger.info.assert_called_once()


class TestCommandSubscription:
    """Test suite for command_subscription handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update object.

        :returns: Mock Update object
        :rtype: Mock
        """
        update = Mock(spec=Update)
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.language_code = "en"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock ContextTypes object.

        :returns: Mock ContextTypes object
        :rtype: Mock
        """
        return Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.fixture
    def mock_user_profile(self):
        """Create mock user profile with subscription.

        :returns: Mock user profile
        :rtype: Mock
        """
        profile = Mock()
        profile.subscription = Mock()
        profile.subscription.subscription_type = SubscriptionType.BASIC
        return profile

    @pytest.mark.asyncio
    async def test_command_subscription_success(
        self, mock_update, mock_context, mock_user_profile
    ):
        """Test successful subscription command.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_user_profile: Mock user profile
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_subscription_current"
            ) as mock_generate_message:
                mock_user_service.is_valid_user_profile.return_value = True
                mock_user_service.get_user_profile.return_value = mock_user_profile
                mock_generate_message.return_value = "Current subscription info"

                # Execute
                await command_subscription(mock_update, mock_context)

                # Assert
                mock_update.message.reply_text.assert_called_once()
                call_args = mock_update.message.reply_text.call_args
                assert call_args[1]["text"] == "Current subscription info"
                assert call_args[1]["parse_mode"] == "HTML"
                assert "reply_markup" in call_args[1]
                assert isinstance(call_args[1]["reply_markup"], InlineKeyboardMarkup)

    @pytest.mark.asyncio
    async def test_command_subscription_no_profile(self, mock_update, mock_context):
        """Test subscription command with no user profile.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch("src.bot.handlers.get_message") as mock_get_message:
                mock_user_service.is_valid_user_profile.return_value = True
                mock_user_service.get_user_profile.return_value = None
                mock_get_message.return_value = "Error occurred"

                # Execute
                await command_subscription(mock_update, mock_context)

                # Assert
                mock_update.message.reply_text.assert_called_once_with("Error occurred")

    @pytest.mark.asyncio
    async def test_command_subscription_no_subscription(
        self, mock_update, mock_context
    ):
        """Test subscription command with profile but no subscription.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_profile = Mock()
        mock_profile.subscription = None

        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch("src.bot.handlers.get_message") as mock_get_message:
                mock_user_service.is_valid_user_profile.return_value = True
                mock_user_service.get_user_profile.return_value = mock_profile
                mock_get_message.return_value = "Error occurred"

                # Execute
                await command_subscription(mock_update, mock_context)

                # Assert
                mock_update.message.reply_text.assert_called_once_with("Error occurred")

    @pytest.mark.asyncio
    async def test_command_subscription_exception(self, mock_update, mock_context):
        """Test subscription command with exception.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch("src.bot.handlers.get_message") as mock_get_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.is_valid_user_profile.return_value = True
                    mock_user_service.get_user_profile.side_effect = Exception(
                        "Test error"
                    )
                    mock_get_message.return_value = "Error occurred"

                    # Execute
                    await command_subscription(mock_update, mock_context)

                    # Assert
                    mock_update.message.reply_text.assert_called_once_with(
                        "Error occurred"
                    )
                    mock_logger.error.assert_called_once()


class TestCommandSubscriptionCallback:
    """Test suite for command_subscription_callback handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update object with callback query.

        :returns: Mock Update object
        :rtype: Mock
        """
        update = Mock(spec=Update)
        update.callback_query = Mock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "subscription_premium"
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.language_code = "en"
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock ContextTypes object.

        :returns: Mock ContextTypes object
        :rtype: Mock
        """
        return Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.fixture
    def mock_user_profile(self):
        """Create mock user profile with subscription.

        :returns: Mock user profile
        :rtype: Mock
        """
        profile = Mock()
        profile.subscription = Mock()
        profile.subscription.subscription_type = SubscriptionType.BASIC
        return profile

    @pytest.mark.asyncio
    async def test_subscription_callback_success(
        self, mock_update, mock_context, mock_user_profile
    ):
        """Test successful subscription change callback.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_user_profile: Mock user profile
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_subscription_change_success"
            ) as mock_generate_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.get_user_profile.return_value = mock_user_profile
                    mock_user_service.update_user_subscription.return_value = True
                    mock_generate_message.return_value = "Subscription changed"

                    # Execute
                    await command_subscription_callback(mock_update, mock_context)

                    # Assert
                    mock_update.callback_query.answer.assert_called_once()
                    mock_update.callback_query.edit_message_text.assert_called_once_with(
                        text="Subscription changed", parse_mode="HTML"
                    )
                    mock_user_service.update_user_subscription.assert_called_once_with(
                        123456789, SubscriptionType.PREMIUM
                    )
                    mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscription_callback_invalid_data(self, mock_update, mock_context):
        """Test subscription callback with invalid data.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_update.callback_query.data = "invalid_data"

        # Execute
        await command_subscription_callback(mock_update, mock_context)

        # Assert
        mock_update.callback_query.answer.assert_called_once()
        # Should not call edit_message_text since data is invalid

    @pytest.mark.asyncio
    async def test_subscription_callback_invalid_subscription_type(
        self, mock_update, mock_context
    ):
        """Test subscription callback with invalid subscription type.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_update.callback_query.data = "subscription_invalid"

        with patch(
            "src.bot.handlers.generate_message_subscription_invalid_type"
        ) as mock_generate_message:
            mock_generate_message.return_value = "Invalid subscription type"

            # Execute
            await command_subscription_callback(mock_update, mock_context)

            # Assert
            mock_update.callback_query.answer.assert_called_once()
            mock_update.callback_query.edit_message_text.assert_called_once_with(
                text="Invalid subscription type", parse_mode="HTML"
            )

    @pytest.mark.asyncio
    async def test_subscription_callback_no_profile(self, mock_update, mock_context):
        """Test subscription callback with no user profile.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_subscription_profile_error"
            ) as mock_generate_message:
                mock_user_service.get_user_profile.return_value = None
                mock_generate_message.return_value = "Profile error"

                # Execute
                await command_subscription_callback(mock_update, mock_context)

                # Assert
                mock_update.callback_query.answer.assert_called_once()
                mock_update.callback_query.edit_message_text.assert_called_once_with(
                    text="Profile error", parse_mode="HTML"
                )

    @pytest.mark.asyncio
    async def test_subscription_callback_same_subscription(
        self, mock_update, mock_context, mock_user_profile
    ):
        """Test subscription callback with same subscription type.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_user_profile: Mock user profile
        :returns: None
        """
        # Setup
        mock_update.callback_query.data = "subscription_basic"  # Same as current

        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_subscription_already_active"
            ) as mock_generate_message:
                mock_user_service.get_user_profile.return_value = mock_user_profile
                mock_generate_message.return_value = "Already active"

                # Execute
                await command_subscription_callback(mock_update, mock_context)

                # Assert
                mock_update.callback_query.answer.assert_called_once()
                mock_update.callback_query.edit_message_text.assert_called_once_with(
                    text="Already active", parse_mode="HTML"
                )

    @pytest.mark.asyncio
    async def test_subscription_callback_update_failed(
        self, mock_update, mock_context, mock_user_profile
    ):
        """Test subscription callback with update failure.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :param mock_user_profile: Mock user profile
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_subscription_change_failed"
            ) as mock_generate_message:
                mock_user_service.get_user_profile.return_value = mock_user_profile
                mock_user_service.update_user_subscription.return_value = False
                mock_generate_message.return_value = "Update failed"

                # Execute
                await command_subscription_callback(mock_update, mock_context)

                # Assert
                mock_update.callback_query.answer.assert_called_once()
                mock_update.callback_query.edit_message_text.assert_called_once_with(
                    text="Update failed", parse_mode="HTML"
                )

    @pytest.mark.asyncio
    async def test_subscription_callback_exception(self, mock_update, mock_context):
        """Test subscription callback with exception.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_subscription_change_error"
            ) as mock_generate_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.get_user_profile.side_effect = Exception(
                        "Test error"
                    )
                    mock_generate_message.return_value = "Error occurred"

                    # Execute
                    await command_subscription_callback(mock_update, mock_context)

                    # Assert
                    mock_update.callback_query.answer.assert_called_once()
                    mock_update.callback_query.edit_message_text.assert_called_once_with(
                        text="Error occurred", parse_mode="HTML"
                    )
                    mock_logger.error.assert_called_once()


class TestCommandHelp:
    """Test suite for command_help handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update object.

        :returns: Mock Update object
        :rtype: Mock
        """
        update = Mock(spec=Update)
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.language_code = "en"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock ContextTypes object.

        :returns: Mock ContextTypes object
        :rtype: Mock
        """
        return Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.mark.asyncio
    async def test_command_help_success(self, mock_update, mock_context):
        """Test /help command success.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.generate_message_help") as mock_generate:
            mock_generate.return_value = "Help message"

            # Execute
            await command_help(mock_update, mock_context)

            # Assert
            mock_generate.assert_called_once_with(user_info=mock_update.effective_user)
            mock_update.message.reply_text.assert_called_once_with(
                text="Help message", parse_mode="HTML"
            )


class TestHandleUnknownMessage:
    """Test suite for handle_unknown_message handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update object.

        :returns: Mock Update object
        :rtype: Mock
        """
        update = Mock(spec=Update)
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.language_code = "en"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock ContextTypes object.

        :returns: Mock ContextTypes object
        :rtype: Mock
        """
        return Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.mark.asyncio
    async def test_handle_unknown_message_success(self, mock_update, mock_context):
        """Test handle_unknown_message success.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch(
            "src.bot.handlers.generate_message_unknown_command"
        ) as mock_generate:
            mock_generate.return_value = "Unknown command error message"

            # Execute
            await handle_unknown_message(mock_update, mock_context)

            # Assert
            mock_generate.assert_called_once_with(mock_update.effective_user)
            mock_update.message.reply_text.assert_called_once_with(
                "Unknown command error message"
            )

    @pytest.mark.asyncio
    async def test_handle_unknown_message_with_russian_user(
        self, mock_update, mock_context
    ):
        """Test handle_unknown_message with Russian language user.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_update.effective_user.language_code = "ru"
        with patch(
            "src.bot.handlers.generate_message_unknown_command"
        ) as mock_generate:
            mock_generate.return_value = "Ошибка: Неизвестная команда"

            # Execute
            await handle_unknown_message(mock_update, mock_context)

            # Assert
            mock_generate.assert_called_once_with(mock_update.effective_user)
            mock_update.message.reply_text.assert_called_once_with(
                "Ошибка: Неизвестная команда"
            )

    @pytest.mark.asyncio
    async def test_handle_unknown_message_with_no_language_code(
        self, mock_update, mock_context
    ):
        """Test handle_unknown_message with user having no language code.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_update.effective_user.language_code = None
        with patch(
            "src.bot.handlers.generate_message_unknown_command"
        ) as mock_generate:
            mock_generate.return_value = "Error: Unknown command"

            # Execute
            await handle_unknown_message(mock_update, mock_context)

            # Assert
            mock_generate.assert_called_once_with(mock_update.effective_user)
            mock_update.message.reply_text.assert_called_once_with(
                "Error: Unknown command"
            )

    @pytest.mark.asyncio
    async def test_handle_unknown_message_with_ukrainian_user(
        self, mock_update, mock_context
    ):
        """Test handle_unknown_message with Ukrainian language user.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_update.effective_user.language_code = "ua"
        with patch(
            "src.bot.handlers.generate_message_unknown_command"
        ) as mock_generate:
            mock_generate.return_value = "Помилка: Невідома команда"

            # Execute
            await handle_unknown_message(mock_update, mock_context)

            # Assert
            mock_generate.assert_called_once_with(mock_update.effective_user)
            mock_update.message.reply_text.assert_called_once_with(
                "Помилка: Невідома команда"
            )

    @pytest.mark.asyncio
    async def test_handle_unknown_message_with_belarusian_user(
        self, mock_update, mock_context
    ):
        """Test handle_unknown_message with Belarusian language user.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_update.effective_user.language_code = "by"
        with patch(
            "src.bot.handlers.generate_message_unknown_command"
        ) as mock_generate:
            mock_generate.return_value = "Памылка: Невядомая каманда"

            # Execute
            await handle_unknown_message(mock_update, mock_context)

            # Assert
            mock_generate.assert_called_once_with(mock_update.effective_user)
            mock_update.message.reply_text.assert_called_once_with(
                "Памылка: Невядомая каманда"
            )

    @pytest.mark.asyncio
    async def test_handle_unknown_message_function_signature(self):
        """Test handle_unknown_message function signature and docstring.

        :returns: None
        """
        # Assert function exists and is callable
        assert callable(handle_unknown_message)

        # Assert function has correct docstring
        assert handle_unknown_message.__doc__ is not None
        assert "Handle unknown messages and commands" in handle_unknown_message.__doc__
        assert "update" in handle_unknown_message.__doc__
        assert "context" in handle_unknown_message.__doc__

    @pytest.mark.asyncio
    async def test_handle_unknown_message_async_function(self):
        """Test that handle_unknown_message is an async function.

        :returns: None
        """
        import inspect

        # Assert function is async
        assert inspect.iscoroutinefunction(handle_unknown_message)

    @pytest.mark.asyncio
    async def test_handle_unknown_message_parameter_types(
        self, mock_update, mock_context
    ):
        """Test handle_unknown_message parameter types.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch(
            "src.bot.handlers.generate_message_unknown_command"
        ) as mock_generate:
            mock_generate.return_value = "Test message"

            # Execute - should not raise any type errors
            await handle_unknown_message(mock_update, mock_context)

            # Assert
            mock_generate.assert_called_once()
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_unknown_message_integration_with_messages_module(
        self, mock_update, mock_context
    ):
        """Test handle_unknown_message integration with messages module.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch(
            "src.bot.handlers.generate_message_unknown_command"
        ) as mock_generate:
            mock_generate.return_value = "Integration test message"

            # Execute
            await handle_unknown_message(mock_update, mock_context)

            # Assert
            mock_generate.assert_called_once_with(mock_update.effective_user)
            mock_update.message.reply_text.assert_called_once_with(
                "Integration test message"
            )

    @pytest.mark.asyncio
    async def test_handle_unknown_message_error_handling(
        self, mock_update, mock_context
    ):
        """Test handle_unknown_message error handling.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup - simulate an error in generate_message_unknown_command
        with patch(
            "src.bot.handlers.generate_message_unknown_command"
        ) as mock_generate:
            mock_generate.side_effect = Exception("Test error")

            # Execute and assert that exception is raised
            with pytest.raises(Exception, match="Test error"):
                await handle_unknown_message(mock_update, mock_context)

            # Assert
            mock_generate.assert_called_once_with(mock_update.effective_user)
            mock_update.message.reply_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_unknown_message_reply_text_error(
        self, mock_update, mock_context
    ):
        """Test handle_unknown_message when reply_text fails.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        mock_update.message.reply_text.side_effect = Exception("Reply error")
        with patch(
            "src.bot.handlers.generate_message_unknown_command"
        ) as mock_generate:
            mock_generate.return_value = "Test message"

            # Execute and assert that exception is raised
            with pytest.raises(Exception, match="Reply error"):
                await handle_unknown_message(mock_update, mock_context)

            # Assert
            mock_generate.assert_called_once_with(mock_update.effective_user)
            mock_update.message.reply_text.assert_called_once_with("Test message")


class TestCommandSettings:
    """Test suite for command_settings handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update object."""
        update = Mock(spec=Update)
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.effective_user.username = "testuser"
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock ContextTypes object."""
        return Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.fixture
    def mock_user_profile(self):
        """Create mock user profile."""
        profile = Mock()
        profile.subscription = Mock()
        profile.subscription.subscription_type = SubscriptionType.PREMIUM
        return profile

    @pytest.mark.asyncio
    async def test_command_settings_premium_success(
        self, mock_update, mock_context, mock_user_profile
    ):
        """Test /settings command with premium subscription."""
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_settings_premium"
            ) as mock_generate_message:
                with patch(
                    "src.bot.handlers.generate_settings_buttons"
                ) as mock_generate_buttons:
                    with patch("src.bot.handlers.logger") as mock_logger:
                        mock_user_service.get_user_profile.return_value = (
                            mock_user_profile
                        )
                        mock_generate_message.return_value = "Premium settings"
                        mock_generate_buttons.return_value = [
                            [{"text": "Test", "callback_data": "test"}]
                        ]

                        result = await command_settings(mock_update, mock_context)

                        assert result is None
                        mock_update.message.reply_text.assert_called_once()
                        mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_command_settings_basic_success(self, mock_update, mock_context):
        """Test /settings command with basic subscription."""
        profile = Mock()
        profile.subscription = Mock()
        profile.subscription.subscription_type = SubscriptionType.BASIC

        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_settings_basic"
            ) as mock_generate_message:
                with patch(
                    "src.bot.handlers.generate_settings_buttons"
                ) as mock_generate_buttons:
                    mock_user_service.get_user_profile.return_value = profile
                    mock_generate_message.return_value = "Basic settings"
                    mock_generate_buttons.return_value = [
                        [{"text": "Test", "callback_data": "test"}]
                    ]

                    await command_settings(mock_update, mock_context)

                    mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_command_settings_no_profile(self, mock_update, mock_context):
        """Test /settings command with no user profile."""
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch("src.bot.handlers.get_message") as mock_get_message:
                mock_user_service.get_user_profile.return_value = None
                mock_get_message.return_value = "Error"

                await command_settings(mock_update, mock_context)

                mock_update.message.reply_text.assert_called_once_with("Error")

    @pytest.mark.asyncio
    async def test_command_settings_exception(self, mock_update, mock_context):
        """Test /settings command with exception."""
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch("src.bot.handlers.get_message") as mock_get_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.get_user_profile.side_effect = Exception(
                        "Test error"
                    )
                    mock_get_message.return_value = "Error"

                    await command_settings(mock_update, mock_context)

                    assert mock_logger.error.call_count >= 1
                    mock_update.message.reply_text.assert_called_once_with("Error")


class TestCommandSettingsCallback:
    """Test suite for command_settings_callback handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update object."""
        update = Mock(spec=Update)
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.callback_query = Mock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock ContextTypes object."""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        return context

    @pytest.mark.asyncio
    async def test_settings_callback_birth_date(self, mock_update, mock_context):
        """Test settings callback for birth date."""
        mock_update.callback_query.data = "settings_birth_date"

        with patch(
            "src.bot.handlers.generate_message_change_birth_date"
        ) as mock_generate_message:
            mock_generate_message.return_value = "Change birth date"

            await command_settings_callback(mock_update, mock_context)

            mock_update.callback_query.answer.assert_called_once()
            mock_update.callback_query.edit_message_text.assert_called_once()
            assert mock_context.user_data["waiting_for"] == "birth_date"

    @pytest.mark.asyncio
    async def test_settings_callback_language(self, mock_update, mock_context):
        """Test settings callback for language."""
        mock_update.callback_query.data = "settings_language"

        with patch(
            "src.bot.handlers.generate_message_change_language"
        ) as mock_generate_message:
            mock_generate_message.return_value = "Change language"

            await command_settings_callback(mock_update, mock_context)

            mock_update.callback_query.answer.assert_called_once()
            mock_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_settings_callback_life_expectancy(self, mock_update, mock_context):
        """Test settings callback for life expectancy."""
        mock_update.callback_query.data = "settings_life_expectancy"

        with patch(
            "src.bot.handlers.generate_message_change_life_expectancy"
        ) as mock_generate_message:
            mock_generate_message.return_value = "Change life expectancy"

            await command_settings_callback(mock_update, mock_context)

            mock_update.callback_query.answer.assert_called_once()
            mock_update.callback_query.edit_message_text.assert_called_once()
            assert mock_context.user_data["waiting_for"] == "life_expectancy"

    @pytest.mark.asyncio
    async def test_settings_callback_invalid_data(self, mock_update, mock_context):
        """Test settings callback with invalid data."""
        mock_update.callback_query.data = "invalid_data"

        await command_settings_callback(mock_update, mock_context)

        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_settings_callback_exception(self, mock_update, mock_context):
        """Test settings callback with exception."""
        mock_update.callback_query.data = "settings_birth_date"

        with patch(
            "src.bot.handlers.generate_message_change_birth_date",
            side_effect=Exception("Test error"),
        ):
            with patch(
                "src.bot.handlers.generate_message_settings_error"
            ) as mock_error_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_error_message.return_value = "Settings error"

                    await command_settings_callback(mock_update, mock_context)

                    mock_logger.error.assert_called_once()
                    mock_update.callback_query.edit_message_text.assert_called_once()


class TestCommandLanguageCallback:
    """Test suite for command_language_callback handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update object."""
        update = Mock(spec=Update)
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.callback_query = Mock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock ContextTypes object."""
        return Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.mark.asyncio
    async def test_language_callback_success(self, mock_update, mock_context):
        """Test language callback with success."""
        mock_update.callback_query.data = "language_en"

        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_language_updated"
            ) as mock_generate_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.update_user_settings.return_value = None
                    mock_generate_message.return_value = "Language updated"

                    await command_language_callback(mock_update, mock_context)

                    mock_update.callback_query.answer.assert_called_once()
                    mock_update.callback_query.edit_message_text.assert_called_once()
                    mock_user_service.update_user_settings.assert_called_once_with(
                        telegram_id=123456789, language="en"
                    )
                    mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_language_callback_invalid_language(self, mock_update, mock_context):
        """Test language callback with invalid language."""
        mock_update.callback_query.data = "language_invalid"

        with patch(
            "src.bot.handlers.generate_message_settings_error"
        ) as mock_error_message:
            mock_error_message.return_value = "Settings error"

            await command_language_callback(mock_update, mock_context)

            mock_update.callback_query.answer.assert_called_once()
            mock_update.callback_query.edit_message_text.assert_called_once_with(
                text="Settings error", parse_mode="HTML"
            )

    @pytest.mark.asyncio
    async def test_language_callback_update_failed(self, mock_update, mock_context):
        """Test language callback when update fails."""
        mock_update.callback_query.data = "language_ru"

        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_settings_error"
            ) as mock_error_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    from src.database.service import UserSettingsUpdateError
                    mock_user_service.update_user_settings.side_effect = UserSettingsUpdateError("Update failed")
                    mock_error_message.return_value = "Settings error"

                    await command_language_callback(mock_update, mock_context)

                    mock_update.callback_query.edit_message_text.assert_called_once_with(
                        text="Settings error", parse_mode="HTML"
                    )
                    mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_language_callback_exception(self, mock_update, mock_context):
        """Test language callback with exception."""
        mock_update.callback_query.data = "language_en"

        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_settings_error"
            ) as mock_error_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.update_user_settings.side_effect = Exception(
                        "Test error"
                    )
                    mock_error_message.return_value = "Settings error"

                    await command_language_callback(mock_update, mock_context)

                    assert mock_logger.error.call_count >= 1
                    mock_update.callback_query.edit_message_text.assert_called_once()

    @patch("src.bot.handlers.update_user_schedule")
    @patch("src.bot.handlers.user_service")
    @patch("src.bot.handlers.logger")
    @pytest.mark.asyncio
    async def test_language_callback_scheduler_update_failure(
        self, mock_logger, mock_user_service, mock_update_schedule, mock_update
    ):
        """Test language callback when scheduler update fails.

        :param mock_update_schedule: Mock update_user_schedule function
        :param mock_logger: Mock logger
        :param mock_user_service: Mock user_service
        :param mock_update: Mock update object
        :returns: None
        """
        # Setup
        mock_update.callback_query.data = "language_en"
        mock_user_service.update_user_settings.return_value = None
        mock_update_schedule.return_value = False

        # Execute
        await command_language_callback(mock_update, None)

        # Assert
        mock_update_schedule.assert_called_once_with(mock_update.effective_user.id)
        warning_calls = [
            call
            for call in mock_logger.warning.call_args_list
            if "Failed to update notification schedule" in str(call)
        ]
        assert len(warning_calls) > 0

    @patch("src.bot.handlers.update_user_schedule")
    @patch("src.bot.handlers.user_service")
    @patch("src.bot.handlers.logger")
    @patch("src.bot.handlers.LifeCalculatorEngine", create=True)
    @pytest.mark.asyncio
    async def test_birth_date_input_scheduler_update_failure(
        self, mock_calculator, mock_logger, mock_user_service, mock_update_schedule, mock_update
    ):
        """Test birth date input when scheduler update fails.

        :param mock_calculator: Mock LifeCalculatorEngine
        :param mock_update_schedule: Mock update_user_schedule function
        :param mock_logger: Mock logger
        :param mock_user_service: Mock user_service
        :param mock_update: Mock update object
        :returns: None
        """
        # Setup
        from datetime import date
        mock_context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        mock_context.user_data = {"waiting_for": "birth_date"}
        mock_update.message.text = "15.03.1990"
        mock_update.message.reply_text = AsyncMock()
        mock_user_service.update_user_settings.return_value = None

        mock_user_profile = Mock()
        mock_user_profile.settings = Mock()
        mock_user_profile.settings.birth_date = date(1990, 3, 15)
        mock_user_service.get_user_profile.return_value = mock_user_profile

        mock_calculator_instance = Mock()
        mock_calculator_instance.calculate_age.return_value = 25
        mock_calculator.return_value = mock_calculator_instance

        mock_update_schedule.return_value = False

        # Execute
        await handle_birth_date_input(mock_update, mock_context, "15.03.1990")

        # Assert
        mock_update_schedule.assert_called_once_with(mock_update.effective_user.id)
        warning_calls = [
            call
            for call in mock_logger.warning.call_args_list
            if "Failed to update notification schedule" in str(call)
        ]
        assert len(warning_calls) > 0

    @patch("src.bot.handlers.generate_message_help")
    @patch("src.bot.handlers.logger")
    @pytest.mark.asyncio
    async def test_command_help_success(self, mock_logger, mock_generate_message, mock_update):
        """Test /help command success.

        :param mock_update: Mock Update object
        :param mock_logger: Mock logger
        :param mock_generate_message: Mock generate_message_help function
        :returns: None
        """
        # Setup
        mock_context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        mock_generate_message.return_value = "Help message"
        mock_update.message.reply_text = AsyncMock()

        # Execute
        await command_help(mock_update, mock_context)

        # Assert
        mock_generate_message.assert_called_once_with(user_info=mock_update.effective_user)
        mock_update.message.reply_text.assert_called_once_with(
            text="Help message", parse_mode="HTML"
        )


class TestHandleSettingsInput:
    """Test suite for handle_settings_input handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update object."""
        update = Mock(spec=Update)
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.message = Mock()
        update.message.text = "test input"
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock ContextTypes object."""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        return context

    @pytest.mark.asyncio
    async def test_handle_settings_input_birth_date(self, mock_update, mock_context):
        """Test settings input for birth date."""
        mock_context.user_data["waiting_for"] = "birth_date"

        with patch(
            "src.bot.handlers.handle_birth_date_input"
        ) as mock_handle_birth_date:
            await handle_settings_input(mock_update, mock_context)

            mock_handle_birth_date.assert_called_once_with(
                mock_update, mock_context, "test input"
            )

    @pytest.mark.asyncio
    async def test_handle_settings_input_life_expectancy(
        self, mock_update, mock_context
    ):
        """Test settings input for life expectancy."""
        mock_context.user_data["waiting_for"] = "life_expectancy"

        with patch(
            "src.bot.handlers.handle_life_expectancy_input"
        ) as mock_handle_life_expectancy:
            await handle_settings_input(mock_update, mock_context)

            mock_handle_life_expectancy.assert_called_once_with(
                mock_update, mock_context, "test input"
            )

    @pytest.mark.asyncio
    async def test_handle_settings_input_unknown(self, mock_update, mock_context):
        """Test settings input for unknown waiting state."""
        mock_context.user_data["waiting_for"] = "unknown"

        with patch("src.bot.handlers.handle_unknown_message") as mock_handle_unknown:
            await handle_settings_input(mock_update, mock_context)

            mock_handle_unknown.assert_called_once_with(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_handle_settings_input_exception(self, mock_update, mock_context):
        """Test settings input with exception."""
        mock_context.user_data["waiting_for"] = "birth_date"

        with patch(
            "src.bot.handlers.handle_birth_date_input",
            side_effect=Exception("Test error"),
        ):
            with patch(
                "src.bot.handlers.generate_message_settings_error"
            ) as mock_error_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_error_message.return_value = "Settings error"

                    await handle_settings_input(mock_update, mock_context)

                    mock_logger.error.assert_called_once()
                    mock_update.message.reply_text.assert_called_once_with(
                        text="Settings error", parse_mode="HTML"
                    )


class TestHandleBirthDateInput:
    """Test suite for handle_birth_date_input handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update object."""
        update = Mock(spec=Update)
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock ContextTypes object."""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {"waiting_for": "birth_date"}
        return context

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_success(self, mock_update, mock_context):
        """Test birth date input with success."""
        from datetime import date

        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_birth_date_updated"
            ) as mock_success_message:
                with patch(
                    "src.bot.handlers.LifeCalculatorEngine", create=True
                ) as mock_calculator:
                    with patch("src.bot.handlers.logger") as mock_logger:
                        mock_user_service.update_user_settings.return_value = None

                        mock_user_profile = Mock()
                        mock_user_profile.settings = Mock()
                        mock_user_profile.settings.birth_date = date(1990, 3, 15)
                        mock_user_service.get_user_profile.return_value = (
                            mock_user_profile
                        )

                        mock_calculator_instance = Mock()
                        mock_calculator_instance.calculate_age.return_value = 25
                        mock_calculator.return_value = mock_calculator_instance
                        mock_success_message.return_value = "Birth date updated"

                        await handle_birth_date_input(
                            mock_update, mock_context, "15.03.1990"
                        )

                        mock_user_service.update_user_settings.assert_called_once_with(
                            telegram_id=123456789, birth_date=date(1990, 3, 15)
                        )
                        mock_update.message.reply_text.assert_called_once_with(
                            text="Birth date updated", parse_mode="HTML"
                        )
                        assert "waiting_for" not in mock_context.user_data
                        mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_future_date(self, mock_update, mock_context):
        """Test birth date input with future date."""
        with patch(
            "src.bot.handlers.generate_message_birth_date_future_error"
        ) as mock_error_message:
            mock_error_message.return_value = "Future date error"

            await handle_birth_date_input(mock_update, mock_context, "15.03.2030")

            mock_update.message.reply_text.assert_called_once_with(
                text="Future date error", parse_mode="HTML"
            )

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_old_date(self, mock_update, mock_context):
        """Test birth date input with old date."""
        with patch(
            "src.bot.handlers.generate_message_birth_date_old_error"
        ) as mock_error_message:
            mock_error_message.return_value = "Old date error"

            await handle_birth_date_input(mock_update, mock_context, "15.03.1800")

            mock_update.message.reply_text.assert_called_once_with(
                text="Old date error", parse_mode="HTML"
            )

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_invalid_format(
        self, mock_update, mock_context
    ):
        """Test birth date input with invalid format."""
        with patch(
            "src.bot.handlers.generate_message_birth_date_format_error"
        ) as mock_error_message:
            mock_error_message.return_value = "Format error"

            await handle_birth_date_input(mock_update, mock_context, "invalid_date")

            mock_update.message.reply_text.assert_called_once_with(
                text="Format error", parse_mode="HTML"
            )

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_update_failed(
        self, mock_update, mock_context
    ):
        """Test birth date input when update fails."""
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_settings_error"
            ) as mock_error_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    from src.database.service import UserSettingsUpdateError
                    mock_user_service.update_user_settings.side_effect = UserSettingsUpdateError("Update failed")
                    mock_error_message.return_value = "Settings error"

                    await handle_birth_date_input(mock_update, mock_context, "15.03.1990")

                    mock_update.message.reply_text.assert_called_once_with(
                        text="Settings error", parse_mode="HTML"
                    )
                    mock_logger.error.assert_called_once()


class TestHandleLifeExpectancyInput:
    """Test suite for handle_life_expectancy_input handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update object."""
        update = Mock(spec=Update)
        update.effective_user = Mock()
        update.effective_user.id = 123456789
        update.message = Mock()
        update.message.reply_text = AsyncMock()
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock ContextTypes object."""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {"waiting_for": "life_expectancy"}
        return context

    @pytest.mark.asyncio
    async def test_handle_life_expectancy_input_success(
        self, mock_update, mock_context
    ):
        """Test life expectancy input with success."""
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_life_expectancy_updated"
            ) as mock_success_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.update_user_settings.return_value = None
                    mock_success_message.return_value = "Life expectancy updated"

                    await handle_life_expectancy_input(mock_update, mock_context, "80")

                    mock_user_service.update_user_settings.assert_called_once_with(
                        telegram_id=123456789, life_expectancy=80
                    )
                    mock_update.message.reply_text.assert_called_once_with(
                        text="Life expectancy updated", parse_mode="HTML"
                    )
                    assert "waiting_for" not in mock_context.user_data
                    mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_life_expectancy_input_too_low(
        self, mock_update, mock_context
    ):
        """Test life expectancy input with too low value."""
        with patch(
            "src.bot.handlers.generate_message_invalid_life_expectancy"
        ) as mock_error_message:
            mock_error_message.return_value = "Invalid life expectancy"

            await handle_life_expectancy_input(mock_update, mock_context, "30")

            mock_update.message.reply_text.assert_called_once_with(
                text="Invalid life expectancy", parse_mode="HTML"
            )

    @pytest.mark.asyncio
    async def test_handle_life_expectancy_input_too_high(
        self, mock_update, mock_context
    ):
        """Test life expectancy input with too high value."""
        with patch(
            "src.bot.handlers.generate_message_invalid_life_expectancy"
        ) as mock_error_message:
            mock_error_message.return_value = "Invalid life expectancy"

            await handle_life_expectancy_input(mock_update, mock_context, "150")

            mock_update.message.reply_text.assert_called_once_with(
                text="Invalid life expectancy", parse_mode="HTML"
            )

    @pytest.mark.asyncio
    async def test_handle_life_expectancy_input_invalid_format(
        self, mock_update, mock_context
    ):
        """Test life expectancy input with invalid format."""
        with patch(
            "src.bot.handlers.generate_message_invalid_life_expectancy"
        ) as mock_error_message:
            mock_error_message.return_value = "Invalid life expectancy"

            await handle_life_expectancy_input(mock_update, mock_context, "invalid")

            mock_update.message.reply_text.assert_called_once_with(
                text="Invalid life expectancy", parse_mode="HTML"
            )

    @pytest.mark.asyncio
    async def test_handle_life_expectancy_input_update_failed(
        self, mock_update, mock_context
    ):
        """Test life expectancy input when update fails."""
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_settings_error"
            ) as mock_error_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    from src.database.service import UserSettingsUpdateError
                    mock_user_service.update_user_settings.side_effect = UserSettingsUpdateError("Update failed")
                    mock_error_message.return_value = "Settings error"

                    await handle_life_expectancy_input(mock_update, mock_context, "80")

                    mock_update.message.reply_text.assert_called_once_with(
                        text="Settings error", parse_mode="HTML"
                    )
                    mock_logger.error.assert_called_once()

    @patch("src.bot.handlers.update_user_schedule")
    @patch("src.bot.handlers.user_service")
    @patch("src.bot.handlers.logger")
    @pytest.mark.asyncio
    async def test_life_expectancy_input_scheduler_update_failure(
        self, mock_logger, mock_user_service, mock_update_schedule, mock_update
    ):
        """Test life expectancy input when scheduler update fails.

        :param mock_update_schedule: Mock update_user_schedule function
        :param mock_logger: Mock logger
        :param mock_user_service: Mock user_service
        :param mock_update: Mock update object
        :returns: None
        """
        # Setup
        mock_context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        mock_context.user_data = {"waiting_for": "life_expectancy"}
        mock_update.message.text = "80"
        mock_user_service.update_user_settings.return_value = None
        mock_update_schedule.return_value = False

        # Execute
        await handle_life_expectancy_input(mock_update, mock_context, "80")

        # Assert
        mock_update_schedule.assert_called_once_with(mock_update.effective_user.id)
        warning_calls = [
            call
            for call in mock_logger.warning.call_args_list
            if "Failed to update notification schedule" in str(call)
        ]
        assert len(warning_calls) > 0

    @patch("src.bot.handlers.generate_message_unknown_command")
    @patch("src.bot.handlers.logger")
    @pytest.mark.asyncio
    async def test_handle_unknown_message_success(self, mock_logger, mock_generate_message, mock_update):
        """Test handle unknown message success.

        :param mock_logger: Mock logger
        :param mock_generate_message: Mock generate_message_unknown_command function
        :param mock_update: Mock update object
        :returns: None
        """
        # Setup
        mock_context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        mock_generate_message.return_value = "Unknown command message"

        # Execute
        await handle_unknown_message(mock_update, mock_context)

        # Assert
        mock_generate_message.assert_called_once_with(mock_update.effective_user)
        mock_update.message.reply_text.assert_called_once_with(
            "Unknown command message"
        )



@pytest.mark.asyncio
async def test_command_language_callback_invalid_callback(monkeypatch):
    """Test command_language_callback with invalid callback data.

    :param monkeypatch: Pytest monkeypatch fixture
    :returns: None
    """
    update = Mock()
    update.callback_query = Mock()
    update.callback_query.data = "invalid_data"
    update.callback_query.answer = AsyncMock()
    update.effective_user = Mock()
    update.effective_user.id = 123456789
    context = Mock()
    update.callback_query.edit_message_text = AsyncMock()
    result = await command_language_callback(update, context)
    assert result is None
    update.callback_query.edit_message_text.assert_not_called()



@pytest.mark.asyncio
async def test_command_settings_callback_invalid_callback(monkeypatch):
    """Test command_settings_callback with invalid callback data.

    :param monkeypatch: Pytest monkeypatch fixture
    :returns: None
    """
    update = Mock()
    update.callback_query = Mock()
    update.callback_query.data = "invalid_data"
    update.callback_query.answer = AsyncMock()
    update.effective_user = Mock()
    update.effective_user.id = 123456789
    context = Mock()
    update.callback_query.edit_message_text = AsyncMock()
    result = await command_settings_callback(update, context)
    assert result is None
    update.callback_query.edit_message_text.assert_not_called()



@pytest.mark.asyncio
async def test_handle_settings_input_exception(monkeypatch):
    """Test handle_settings_input with exception in handler.

    :param monkeypatch: Pytest monkeypatch fixture
    :returns: None
    """
    update = Mock()
    update.effective_user = Mock()
    update.effective_user.id = 123456789
    update.message = Mock()
    update.message.text = "test"
    update.message.reply_text = AsyncMock()
    context = Mock()
    context.user_data = {"waiting_for": "birth_date"}
    # Мокаем handle_birth_date_input чтобы выбрасывал исключение
    monkeypatch.setattr("src.bot.handlers.handle_birth_date_input", AsyncMock(side_effect=Exception("fail")))
    with patch("src.bot.handlers.logger") as mock_logger:
        with patch("src.bot.handlers.generate_message_settings_error") as mock_generate:
            mock_generate.return_value = "Error message"
        # Проверяем, что reply_text вызван с ошибкой
            result = await handle_settings_input(update, context)
            assert result is None
        mock_logger.error.assert_called()
            update.message.reply_text.assert_called_once_with(
                text="Error message",
                parse_mode="HTML"
            )



@pytest.mark.asyncio
async def test_handle_birth_date_input_value_error(monkeypatch):
    """Test handle_birth_date_input with invalid date format.

    :param monkeypatch: Pytest monkeypatch fixture
    :returns: None
    """
    update = Mock()
    update.effective_user = Mock()
    update.effective_user.id = 123456789
    update.message = Mock()
    update.message.reply_text = AsyncMock()
    context = Mock()
    # Некорректная дата
    result = await handle_birth_date_input(update, context, "not_a_date")
    assert result is None
    update.message.reply_text.assert_called()



@pytest.mark.asyncio
async def test_handle_life_expectancy_input_value_error(monkeypatch):
    """Test handle_life_expectancy_input with invalid number format.

    :param monkeypatch: Pytest monkeypatch fixture
    :returns: None
    """
    update = Mock()
    update.effective_user = Mock()
    update.effective_user.id = 123456789
    update.message = Mock()
    update.message.reply_text = AsyncMock()
    context = Mock()
    # Некорректное число
    result = await handle_life_expectancy_input(update, context, "not_a_number")
    assert result is None
    update.message.reply_text.assert_called()



@pytest.mark.asyncio
async def test_command_language_callback_exception(monkeypatch):
    """Test command_language_callback with exception in user service.

    :param monkeypatch: Pytest monkeypatch fixture
    :returns: None
    """
    update = Mock()
    update.callback_query = Mock()
    update.callback_query.data = "language_en"
    update.callback_query.answer = AsyncMock()
    update.effective_user = Mock()
    update.effective_user.id = 123456789
    context = Mock()
    update.callback_query.edit_message_text = AsyncMock()
    # Мокаем user_service чтобы выбрасывал Exception
    monkeypatch.setattr("src.bot.handlers.user_service.update_user_settings", Mock(side_effect=Exception("fail")))
    with patch("src.bot.handlers.logger") as mock_logger:
        with patch("src.bot.handlers.generate_message_settings_error") as mock_generate:
            mock_generate.return_value = "Error message"
            result = await command_language_callback(update, context)
            assert result is None
        mock_logger.error.assert_called()
        update.callback_query.edit_message_text.assert_called()



@pytest.mark.asyncio
async def test_command_settings_callback_exception(monkeypatch):
    """Test command_settings_callback with exception in message generation.

    :param monkeypatch: Pytest monkeypatch fixture
    :returns: None
    """
    update = Mock()
    update.callback_query = Mock()
    update.callback_query.data = "settings_birth_date"
    update.callback_query.answer = AsyncMock()
    update.effective_user = Mock()
    update.effective_user.id = 123456789
    context = Mock()
    context.user_data = {}
    update.callback_query.edit_message_text = AsyncMock()
    # Мокаем generate_message_change_birth_date чтобы выбрасывал Exception
    monkeypatch.setattr("src.bot.handlers.generate_message_change_birth_date", Mock(side_effect=Exception("fail")))
    with patch("src.bot.handlers.logger") as mock_logger:
        with patch("src.bot.handlers.generate_message_settings_error") as mock_generate:
            mock_generate.return_value = "Error message"
            result = await command_settings_callback(update, context)
            assert result is None
        mock_logger.error.assert_called()
        update.callback_query.edit_message_text.assert_called()



@pytest.mark.asyncio
async def test_handle_birth_date_input_user_error(monkeypatch):
    """Test handle_birth_date_input with UserNotFoundError.

    :param monkeypatch: Pytest monkeypatch fixture
    :returns: None
    """
    update = Mock()
    update.effective_user = Mock()
    update.effective_user.id = 123456789
    update.message = Mock()
    update.message.reply_text = AsyncMock()
    context = Mock()
    # Мокаем user_service чтобы выбрасывал UserNotFoundError
    monkeypatch.setattr("src.bot.handlers.user_service.update_user_settings", Mock(side_effect=UserNotFoundError("fail")))
    with patch("src.bot.handlers.generate_message_settings_error") as mock_generate:
        mock_generate.return_value = "Error message"
        result = await handle_birth_date_input(update, context, "01.01.2000")
        assert result is None
    update.message.reply_text.assert_called()



@pytest.mark.asyncio
async def test_handle_life_expectancy_input_user_error(monkeypatch):
    """Test handle_life_expectancy_input with UserSettingsUpdateError.

    :param monkeypatch: Pytest monkeypatch fixture
    :returns: None
    """
    update = Mock()
    update.effective_user = Mock()
    update.effective_user.id = 123456789
    update.message = Mock()
    update.message.reply_text = AsyncMock()
    context = Mock()
    # Мокаем user_service чтобы выбрасывал UserSettingsUpdateError
    monkeypatch.setattr("src.bot.handlers.user_service.update_user_settings", Mock(side_effect=UserSettingsUpdateError("fail")))
    with patch("src.bot.handlers.generate_message_settings_error") as mock_generate:
        mock_generate.return_value = "Error message"
        result = await handle_life_expectancy_input(update, context, "80")
        assert result is None
    update.message.reply_text.assert_called()



@pytest.mark.asyncio
async def test_handle_settings_input_unknown(monkeypatch):
    """Test handle_settings_input with unknown waiting_for value.

    :param monkeypatch: Pytest monkeypatch fixture
    :returns: None
    """
    update = Mock()
    update.effective_user = Mock()
    update.effective_user.id = 123456789
    update.message = Mock()
    update.message.reply_text = AsyncMock()
    context = Mock()
    context.user_data = {"waiting_for": "unknown"}
    # Мокаем handle_unknown_message
    mock_handle_unknown = AsyncMock()
    monkeypatch.setattr("src.bot.handlers.handle_unknown_message", mock_handle_unknown)
    result = await handle_settings_input(update, context)
    assert result is None
    # Проверяем, что handle_unknown_message был вызван
    mock_handle_unknown.assert_called_once_with(update, context)
