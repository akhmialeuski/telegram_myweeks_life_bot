"""Unit tests for StartHandler.

Tests the StartHandler class which handles /start command and user registration.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
        """Create StartHandler instance with fake container."""
        return StartHandler(FakeServiceContainer())

    @pytest.fixture(autouse=True)
    def mock_localization(self):
        """Mock localization to return keys for testing."""

        def mock_pgettext(context, message):
            return f"pgettext_{context}.{message}"

        with patch("src.bot.handlers.start_handler.use_locale") as mock_use_locale:
            mock_use_locale.return_value = (None, None, mock_pgettext)
            yield

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

        # Configure mock profile with valid settings
        mock_profile = MagicMock()
        mock_profile.settings.birth_date = birth_date
        mock_profile.settings.life_expectancy = 80
        mock_profile.settings.language = "en"
        handler.services.user_service.get_user_profile.return_value = mock_profile

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
            or "pgettext_registration.error" in call_args.kwargs["text"]
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
        assert "pgettext_birth_date.future_error" in call_args.kwargs["text"]

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
        assert "pgettext_birth_date.old_error" in call_args.kwargs["text"]

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
        assert "pgettext_birth_date.format_error" in call_args.kwargs["text"]

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
        assert "pgettext_registration.error" in call_args.kwargs["text"]
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
        assert "pgettext_registration.error" in call_args.kwargs["text"]
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

        # Configure mock profile with valid settings
        mock_profile = MagicMock()
        mock_profile.settings.birth_date = birth_date
        mock_profile.settings.life_expectancy = 80
        mock_profile.settings.language = "en"
        handler.services.user_service.get_user_profile.return_value = mock_profile

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

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_unknown_validation_error(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handling of unknown validation error code.

        This test verifies that when validation returns an unknown error code,
        case in _handle_validation_error is executed for unknown error codes.

        :param handler: StartHandler instance from fixture
        :type handler: StartHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        from unittest.mock import patch

        from src.services.validation_service import ValidationResult

        mock_context.user_data["waiting_for"] = "start_birth_date"
        mock_update.message.text = "15.03.1990"

        # Mock validation to return unknown error code
        with patch.object(
            handler._validation_service, "validate_birth_date"
        ) as mock_validate:
            mock_validate.return_value = ValidationResult.failure(
                error_key="UNKNOWN_ERROR_CODE"
            )

            await handler.handle_birth_date_input(mock_update, mock_context)

        # Should send format error message (default case)
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "pgettext_birth_date.format_error" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_send_date_format_error_deprecated(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
    ) -> None:
        """Test deprecated _send_date_format_error method.

        This test verifies that the deprecated _send_date_format_error method
        still functions correctly by sending the expected error message.

        :param handler: StartHandler instance from fixture
        :type handler: StartHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :returns: None
        :rtype: None
        """
        # Call the deprecated method directly
        await handler._send_date_format_error(mock_update, "en")

        # Verify message sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "pgettext_birth_date.format_error" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_registration_success_message_profile_error(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handling of missing profile after registration.

        This test verifies that if the user profile cannot be fetched after
        creation (returning None), a UserServiceError is raised and handled.

        :param handler: StartHandler instance from fixture
        :type handler: StartHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        from src.services.validation_service import ValidationResult

        birth_date = date(1990, 3, 15)
        with patch.object(
            handler._validation_service, "validate_birth_date"
        ) as mock_validate:
            mock_validate.return_value = ValidationResult.success(value=birth_date)
            handler.services.user_service.create_user_profile.return_value = None

            # Mock get_user_profile to return None (simulating fetch failure)
            handler.services.user_service.get_user_profile.return_value = None

            with patch.object(
                handler, "_add_user_to_scheduler", new_callable=AsyncMock
            ):
                with patch.object(handler, "send_error_message") as mock_send_error:
                    # _persistence needs to be mocked because error handler also calls clear_state
                    mock_persistence = AsyncMock()
                    with patch.object(handler, "_persistence", mock_persistence):
                        mock_context.user_data["waiting_for"] = "start_birth_date"
                        mock_update.message.text = "15.03.1990"

                        await handler.handle_birth_date_input(mock_update, mock_context)

                        # Should catch UserServiceError and send error message
                        mock_send_error.assert_called_once()
                        assert (
                            "pgettext_registration.error"
                            in mock_send_error.call_args.kwargs["error_message"]
                        )

    @pytest.mark.asyncio
    async def test_send_registration_success_message(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test sending of registration success message with statistics.

        This test verifies that the success message is correctly formatted
        with life statistics and that the waiting state is cleared.

        :param handler: StartHandler instance from fixture
        :type handler: StartHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        from src.services.validation_service import ValidationResult

        birth_date = date(1990, 3, 15)

        # Mock validation success
        with patch.object(
            handler._validation_service, "validate_birth_date"
        ) as mock_validate:
            mock_validate.return_value = ValidationResult.success(value=birth_date)

            # Mock user creation
            handler.services.user_service.create_user_profile.return_value = None

            # Use a mock profile for get_user_profile so stats can be calculated
            mock_profile = MagicMock()
            mock_profile.settings.birth_date = birth_date
            mock_profile.settings.life_expectancy = 80
            mock_profile.settings.language = "en"
            handler.services.user_service.get_user_profile.return_value = mock_profile

            # Mock persistence using AsyncMock
            mock_persistence = AsyncMock()
            with patch.object(handler, "_persistence", mock_persistence):
                # Mock send_message to inspect arguments (must be AsyncMock)
                with patch.object(
                    handler, "send_message", new_callable=AsyncMock
                ) as mock_send_message:
                    # Mock _add_user_to_scheduler
                    with patch.object(
                        handler, "_add_user_to_scheduler", new_callable=AsyncMock
                    ):

                        mock_context.user_data["waiting_for"] = "start_birth_date"
                        mock_update.message.text = "15.03.1990"

                        await handler.handle_birth_date_input(mock_update, mock_context)

                        # Verify message headers/content
                        mock_send_message.assert_called_once()
                        kwargs = mock_send_message.call_args.kwargs
                        message_text = kwargs["message_text"]

                        assert "pgettext_registration.success" in message_text

                        # Verify clear_state was called
                        mock_persistence.clear_state.assert_called_once_with(
                            user_id=mock_update.effective_user.id, context=mock_context
                        )

    @pytest.mark.asyncio
    async def test_handle_start_existing_user(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test start command for already registered user.

        This test verifies that if a user is already registered,
        they receive a welcome back message instead of registration prompt.

        :param handler: StartHandler instance from fixture
        :type handler: StartHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        # Mock user exists
        handler.services.user_service.is_valid_user_profile.return_value = True

        # Mock user profile
        mock_profile = MagicMock()
        mock_profile.settings.language = "en"
        handler.services.user_service.get_user_profile.return_value = mock_profile

        # Mock persistence
        mock_persistence = AsyncMock()
        with patch.object(handler, "_persistence", mock_persistence):
            await handler.handle(mock_update, mock_context)

            # Verify welcome back message sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "pgettext_start.welcome_existing" in call_args.kwargs["text"]

            # Verify persistence state was NOT set (since no registration needed)
            mock_persistence.set_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_start_new_user(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test start command for new user.

        This test verifies that a new user is prompted to enter their birth date
        and the state is set to AWAITING_START_BIRTH_DATE.

        :param handler: StartHandler instance from fixture
        :type handler: StartHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        from src.bot.conversations.states import ConversationState

        # Mock user does not exist
        handler.services.user_service.is_valid_user_profile.return_value = False

        # Mock persistence
        mock_persistence = AsyncMock()
        with patch.object(handler, "_persistence", mock_persistence):
            await handler.handle(mock_update, mock_context)

            # Verify welcome new message sent
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "pgettext_start.welcome_new" in call_args.kwargs["text"]

            # Verify state set to awaiting birth date
            mock_persistence.set_state.assert_called_once_with(
                user_id=mock_update.effective_user.id,
                state=ConversationState.AWAITING_START_BIRTH_DATE,
                context=mock_context,
            )

    @pytest.mark.asyncio
    async def test_handle_birth_date_input_generic_exception(
        self,
        handler: StartHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test generic exception handling during registration.

        This test verifies that any unexpected exception during registration
        is caught, logged, and results in a generic error message to the user.

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

        # Mock generic exception
        handler.services.user_service.create_user_profile.side_effect = Exception(
            "Unexpected error"
        )

        await handler.handle_birth_date_input(mock_update, mock_context)

        # Verify fallback error handling
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "pgettext_registration.error" in call_args.kwargs["text"]

        # Verify state cleared
        assert "waiting_for" not in mock_context.user_data
