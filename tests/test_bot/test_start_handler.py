"""Unit tests for StartHandler.

Tests the StartHandler class which handles /start command and user registration.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest

from src.bot.constants import COMMAND_START
from src.bot.handlers.start_handler import StartHandler
from src.database.service import UserRegistrationError, UserServiceError
from src.events.domain_events import UserSettingsChangedEvent
from tests.utils.fake_container import FakeServiceContainer


class TestStartHandler:
    """Test suite for StartHandler class.

    This test class contains all tests for StartHandler functionality,
    including user registration flow, birth date validation, existing
    user handling, and error scenarios during registration.
    """

    @pytest.fixture
    def handler(self) -> StartHandler:
        """Create StartHandler instance for testing.

        :returns: Configured StartHandler instance with fake service container
        :rtype: StartHandler
        """
        services = FakeServiceContainer()
        return StartHandler(services)

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
            "src.bot.handlers.start_handler.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return mock_pgettext

    def test_handler_creation(self, handler: StartHandler) -> None:
        """Test that StartHandler is created with correct command name.

        This test verifies that the handler is properly initialized with
        the /start command name constant.

        :param handler: StartHandler instance from fixture
        :type handler: StartHandler
        :returns: None
        :rtype: None
        """
        assert handler.command_name == f"/{COMMAND_START}"

    @pytest.mark.asyncio
    async def test_handle_existing_user(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test start handler response for existing user.

        This test verifies that when an existing user executes /start,
        they receive a welcome back message without registration flow.

        :param handler: StartHandler instance from fixture
        :type handler: StartHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        handler.services.user_service.is_valid_user_profile.return_value = True

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "pgettext_start.welcome_existing_" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_new_user(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test start handler initiation of registration for new user.

        This test verifies that when a new user executes /start, they
        receive a welcome message and are prompted for their birth date.

        :param handler: StartHandler instance from fixture
        :type handler: StartHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        handler.services.user_service.is_valid_user_profile.return_value = False

        await handler.handle(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "pgettext_start.welcome_new_" in call_args.kwargs["text"]
        assert mock_context.user_data["waiting_for"] == "start_birth_date"

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_success(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test successful user registration with valid birth date.

        This test verifies that a valid birth date successfully registers
        the user, publishes a registration event, and sends a success message.

        :param handler: StartHandler instance from fixture
        :type handler: StartHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        mock_context.user_data["waiting_for"] = "start_birth_date"
        mock_update.message.text = "15.03.1990"
        birth_date = date(1990, 3, 15)

        await handler.handle_birth_date_input(mock_update, mock_context)

        # Verify event published
        handler.services.event_bus.publish.assert_called_once()
        call_args = handler.services.event_bus.publish.call_args
        event = call_args[0][0]
        assert isinstance(event, UserSettingsChangedEvent)
        assert event.user_id == mock_update.effective_user.id
        assert event.setting_name == "registration"
        assert event.new_value is True

        handler.services.user_service.create_user_profile.assert_called_once_with(
            user_info=mock_update.effective_user, birth_date=birth_date
        )
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert (
            "pgettext_registration.success" in call_args.kwargs["text"]
            or "pgettext_registration.error_" in call_args.kwargs["text"]
        )
        assert "waiting_for" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_future_date(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test registration rejection with future birth date.

        This test verifies that birth dates in the future are rejected
        during registration with an appropriate error message.

        :param handler: StartHandler instance from fixture
        :type handler: StartHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        mock_context.user_data["waiting_for"] = "start_birth_date"
        mock_update.message.text = "15.03.2030"

        await handler.handle_birth_date_input(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "pgettext_birth_date.future_error_" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_old_date(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test registration rejection with unrealistically old birth date.

        This test verifies that birth dates before 1900 are rejected
        during registration with an appropriate error message.

        :param handler: StartHandler instance from fixture
        :type handler: StartHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        mock_context.user_data["waiting_for"] = "start_birth_date"
        mock_update.message.text = "15.03.1800"

        await handler.handle_birth_date_input(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "pgettext_birth_date.old_error_" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_invalid_format(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test registration rejection with invalid date format.

        This test verifies that invalid date formats are rejected during
        registration with a format error message.

        :param handler: StartHandler instance from fixture
        :type handler: StartHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        mock_context.user_data["waiting_for"] = "start_birth_date"
        mock_update.message.text = "invalid-date"

        await handler.handle_birth_date_input(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "pgettext_birth_date.format_error_" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_registration_error(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test registration handling when user creation fails.

        This test verifies that when the user profile creation fails
        with a UserRegistrationError, an appropriate error message is
        sent and the waiting state is cleared.

        :param handler: StartHandler instance from fixture
        :type handler: StartHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        mock_context.user_data["waiting_for"] = "start_birth_date"
        mock_update.message.text = "15.03.1990"
        handler.services.user_service.create_user_profile.side_effect = (
            UserRegistrationError("Registration failed")
        )

        await handler.handle_birth_date_input(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "pgettext_registration.error_" in call_args.kwargs["text"]
        handler.services.user_service.create_user_profile.assert_called_once()
        assert "waiting_for" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_service_error(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test registration handling when service encounters an error.

        This test verifies that when a generic UserServiceError occurs
        during registration, an appropriate error message is sent and
        the waiting state is cleared.

        :param handler: StartHandler instance from fixture
        :type handler: StartHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        mock_context.user_data["waiting_for"] = "start_birth_date"
        mock_update.message.text = "15.03.1990"
        handler.services.user_service.create_user_profile.side_effect = (
            UserServiceError("Service error")
        )

        await handler.handle_birth_date_input(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "pgettext_registration.error_" in call_args.kwargs["text"]
        handler.services.user_service.create_user_profile.assert_called_once()
        assert "waiting_for" not in mock_context.user_data

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_event_bus_error(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test registration handling when event publication fails.

        This test verifies that even when publishing the registration event
        fails, the user profile is still created and a response is sent.

        :param handler: StartHandler instance from fixture
        :type handler: StartHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        mock_context.user_data["waiting_for"] = "start_birth_date"
        mock_update.message.text = "15.03.1990"
        birth_date = date(1990, 3, 15)

        # Mock event bus failure
        handler.services.event_bus.publish.side_effect = Exception("Event Bus Error")

        await handler.handle_birth_date_input(mock_update, mock_context)

        handler.services.event_bus.publish.assert_called_once()
        handler.services.user_service.create_user_profile.assert_called_once_with(
            user_info=mock_update.effective_user, birth_date=birth_date
        )
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "pgettext_registration" in call_args.kwargs["text"]
        assert "waiting_for" not in mock_context.user_data
