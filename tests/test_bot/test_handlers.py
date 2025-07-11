"""Unit tests for bot handlers.

Tests all handler functions in the bot handlers module
with proper mocking, edge cases, and error handling coverage.
"""

# from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.handlers import (
    WAITING_USER_INPUT,
    command_cancel,
    command_help,
    command_start,
    command_start_handle_birth_date,
    command_subscription,
    command_subscription_callback,
    command_visualize,
    command_weeks,
    require_registration,
)
from src.database.models import SubscriptionType
from src.database.service import (
    UserAlreadyExistsError,
    UserDeletionError,
    UserRegistrationError,
    UserServiceError,
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
                    "common", "not_registered", "en"
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
                    "common", "not_registered", "ru"
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
                "src.bot.handlers.generate_message_registration_success"
            ) as mock_generate_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.create_user_profile.return_value = True
                    mock_generate_message.return_value = "Registration successful!"

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
                    mock_logger.info.assert_called_once()

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
                "src.bot.handlers.generate_message_start_welcome_existing"
            ) as mock_generate_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.create_user_profile.side_effect = (
                        UserAlreadyExistsError("User exists")
                    )
                    mock_generate_message.return_value = "Welcome back!"

                    # Execute
                    result = await command_start_handle_birth_date(
                        mock_update, mock_context
                    )

                    # Assert
                    assert result == ConversationHandler.END
                    mock_update.message.reply_text.assert_called_once_with(
                        text="Welcome back!", parse_mode="HTML"
                    )
                    mock_logger.info.assert_called_once()

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
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_cancel_success"
            ) as mock_generate_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.is_valid_user_profile.return_value = True
                    mock_user_service.delete_user_profile.return_value = None
                    mock_generate_message.return_value = "User deleted successfully"

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
                    mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_command_cancel_deletion_error(self, mock_update, mock_context):
        """Test user cancellation with deletion error.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_cancel_error"
            ) as mock_generate_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.is_valid_user_profile.return_value = True
                    mock_user_service.delete_user_profile.side_effect = (
                        UserDeletionError("Deletion failed")
                    )
                    mock_generate_message.return_value = "Deletion error"

                    # Execute
                    result = await command_cancel(mock_update, mock_context)

                    # Assert
                    assert result == ConversationHandler.END
                    mock_update.message.reply_text.assert_called_once_with(
                        text="Deletion error", parse_mode="HTML"
                    )
                    mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_command_cancel_service_error(self, mock_update, mock_context):
        """Test user cancellation with service error.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.user_service") as mock_user_service:
            with patch(
                "src.bot.handlers.generate_message_cancel_error"
            ) as mock_generate_message:
                with patch("src.bot.handlers.logger") as mock_logger:
                    mock_user_service.is_valid_user_profile.return_value = True
                    mock_user_service.delete_user_profile.side_effect = (
                        UserServiceError("Service error")
                    )
                    mock_generate_message.return_value = "Deletion error"

                    # Execute
                    result = await command_cancel(mock_update, mock_context)

                    # Assert
                    assert result == ConversationHandler.END
                    mock_update.message.reply_text.assert_called_once_with(
                        text="Deletion error", parse_mode="HTML"
                    )
                    mock_logger.error.assert_called_once()


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
        """Test successful help command.

        :param mock_update: Mock Update object
        :param mock_context: Mock ContextTypes object
        :returns: None
        """
        # Setup
        with patch("src.bot.handlers.generate_message_help") as mock_generate_message:
            with patch("src.bot.handlers.logger") as mock_logger:
                mock_generate_message.return_value = "Help message"

                # Execute
                await command_help(mock_update, mock_context)

                # Assert
                mock_update.message.reply_text.assert_called_once_with(
                    text="Help message", parse_mode="HTML"
                )
                mock_generate_message.assert_called_once_with(
                    user_info=mock_update.effective_user
                )
                mock_logger.info.assert_called_once()
