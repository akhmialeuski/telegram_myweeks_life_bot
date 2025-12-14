"""Unit tests for SubscriptionHandler.

Tests the SubscriptionHandler class which handles /subscription command.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot.constants import COMMAND_SUBSCRIPTION
from src.bot.handlers.subscription_handler import SubscriptionHandler
from src.database.service import UserSubscriptionUpdateError
from src.enums import SubscriptionType


class TestSubscriptionHandler:
    """Test suite for SubscriptionHandler class.

    This test class contains all tests for SubscriptionHandler functionality,
    including subscription management, subscription type changes, error
    handling, and callback query processing.
    """

    @pytest.fixture
    def handler(self) -> SubscriptionHandler:
        """Create SubscriptionHandler instance for testing.

        :returns: Configured SubscriptionHandler instance with fake service container
        :rtype: SubscriptionHandler
        """
        from tests.utils.fake_container import FakeServiceContainer

        services = FakeServiceContainer()
        return SubscriptionHandler(services)

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
            "src.bot.handlers.subscription_handler.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return mock_pgettext

    @pytest.fixture
    def make_mock_callback_query(self):
        """Create mock callback query for subscription selection.

        This fixture provides a factory function for creating mock callback
        queries with specific subscription types.

        :returns: Factory function that creates mock callback queries
        :rtype: callable
        """

        def _make(update, subscription_key: str):
            query = MagicMock()
            query.data = f"subscription_{subscription_key}"
            query.answer = AsyncMock()
            query.edit_message_text = AsyncMock()
            update.callback_query = query
            return query

        return _make

    def test_handler_creation(self, handler: SubscriptionHandler) -> None:
        """Test that SubscriptionHandler is created with correct command name.

        This test verifies that the handler is properly initialized with
        the /subscription command name constant.

        :param handler: SubscriptionHandler instance from fixture
        :type handler: SubscriptionHandler
        :returns: None
        :rtype: None
        """
        assert handler.command_name == f"/{COMMAND_SUBSCRIPTION}"

    @pytest.mark.asyncio
    async def test_handle_success(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        make_mock_user_profile,
    ) -> None:
        """Test successful subscription information display.

        This test verifies that when a registered user executes /subscription,
        they receive their current subscription information with management options.

        :param handler: SubscriptionHandler instance from fixture
        :type handler: SubscriptionHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :param make_mock_user_profile: Fixture for creating mock user profiles
        :type make_mock_user_profile: callable
        :returns: None
        :rtype: None
        """
        mock_user_profile = make_mock_user_profile(SubscriptionType.BASIC)
        mock_user_profile.settings = MagicMock()
        mock_user_profile.settings.language = "en"
        mock_user_profile.subscription = MagicMock()
        mock_user_profile.subscription.subscription_type = SubscriptionType.BASIC

        handler.services.user_service.is_valid_user_profile.return_value = True
        handler.services.user_service.get_user_profile.return_value = mock_user_profile

        with patch.object(handler, "send_message") as mock_send_message:
            await handler.handle(mock_update, mock_context)
            mock_send_message.assert_called_once()
            call_kwargs = mock_send_message.call_args.kwargs
            assert "pgettext_subscription.management_" in call_kwargs["message_text"]

    @pytest.mark.asyncio
    async def test_handle_no_profile(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test subscription handler when user profile is not found.

        This test verifies that the handler sends an appropriate error
        message when the user profile doesn't exist in the database.

        :param handler: SubscriptionHandler instance from fixture
        :type handler: SubscriptionHandler
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

    @pytest.mark.asyncio
    async def test_handle_exception(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test subscription handler exception handling.

        This test verifies that exceptions raised in the internal
        handler are caught and handled by the base handler wrapper.

        :param handler: SubscriptionHandler instance from fixture
        :type handler: SubscriptionHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :returns: None
        :rtype: None
        """
        mock_profile = MagicMock()
        mock_profile.settings.language = "en"
        handler.services.user_service.get_user_profile.return_value = mock_profile
        handler.services.user_service.is_valid_user_profile.return_value = True

        with patch.object(
            handler, "_handle_subscription", side_effect=Exception("Test exception")
        ), patch.object(handler, "send_error_message") as mock_send_error:
            await handler.handle(mock_update, mock_context)

            # Assert error handling was invoked
            mock_send_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_subscription_callback_same_subscription(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        make_mock_user_profile,
        make_mock_callback_query,
    ) -> None:
        """Test subscription callback when user selects current subscription.

        This test verifies that when a user tries to switch to their
        currently active subscription type, they receive an appropriate
        message indicating the subscription is already active.

        :param handler: SubscriptionHandler instance from fixture
        :type handler: SubscriptionHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :param make_mock_user_profile: Fixture for creating mock user profiles
        :type make_mock_user_profile: callable
        :param make_mock_callback_query: Fixture for creating mock callback queries
        :type make_mock_callback_query: callable
        :returns: None
        :rtype: None
        """
        mock_user_profile = make_mock_user_profile(SubscriptionType.BASIC)
        mock_callback_query = make_mock_callback_query(
            mock_update, SubscriptionType.BASIC.value
        )
        handler.services.user_service.get_user_profile.return_value = mock_user_profile

        with patch.object(handler, "edit_message") as mock_edit_message:
            await handler.handle_subscription_callback(mock_update, mock_context)

            mock_callback_query.answer.assert_called_once()
            mock_edit_message.assert_called_once()
            assert (
                "pgettext_subscription.already_active_"
                in mock_edit_message.call_args.kwargs["message_text"]
            )

    @pytest.mark.asyncio
    async def test_handle_subscription_callback_successful_change(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        make_mock_user_profile,
        make_mock_callback_query,
    ) -> None:
        """Test successful subscription type change.

        This test verifies that a user can successfully change their
        subscription type and receive a confirmation message.

        :param handler: SubscriptionHandler instance from fixture
        :type handler: SubscriptionHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :param make_mock_user_profile: Fixture for creating mock user profiles
        :type make_mock_user_profile: callable
        :param make_mock_callback_query: Fixture for creating mock callback queries
        :type make_mock_callback_query: callable
        :returns: None
        :rtype: None
        """
        mock_user_profile = make_mock_user_profile(SubscriptionType.BASIC)
        mock_callback_query = make_mock_callback_query(
            mock_update, SubscriptionType.PREMIUM.value
        )
        handler.services.user_service.get_user_profile.return_value = mock_user_profile
        handler.services.user_service.update_user_subscription.return_value = None

        with patch.object(handler, "edit_message") as mock_edit_message:
            await handler.handle_subscription_callback(mock_update, mock_context)

            mock_callback_query.answer.assert_called_once()
            handler.services.user_service.update_user_subscription.assert_called_once_with(
                telegram_id=mock_update.effective_user.id,
                subscription_type=SubscriptionType.PREMIUM,
            )
            mock_edit_message.assert_called_once()
            assert (
                "pgettext_subscription.change_success_"
                in mock_edit_message.call_args.kwargs["message_text"]
            )

    @pytest.mark.asyncio
    async def test_handle_subscription_callback_update_error(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        make_mock_user_profile,
        make_mock_callback_query,
    ) -> None:
        """Test subscription callback handling when update fails.

        This test verifies that when the subscription update operation
        fails with a UserSubscriptionUpdateError, an appropriate error
        message is sent to the user.

        :param handler: SubscriptionHandler instance from fixture
        :type handler: SubscriptionHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :param make_mock_user_profile: Fixture for creating mock user profiles
        :type make_mock_user_profile: callable
        :param make_mock_callback_query: Fixture for creating mock callback queries
        :type make_mock_callback_query: callable
        :returns: None
        :rtype: None
        """
        mock_user_profile = make_mock_user_profile(SubscriptionType.BASIC)
        mock_callback_query = make_mock_callback_query(
            mock_update, SubscriptionType.PREMIUM.value
        )
        handler.services.user_service.get_user_profile.return_value = mock_user_profile
        handler.services.user_service.update_user_subscription.side_effect = (
            UserSubscriptionUpdateError("Update failed")
        )

        with patch.object(handler, "send_error_message") as mock_send_error:
            await handler.handle_subscription_callback(mock_update, mock_context)
            mock_callback_query.answer.assert_called_once()
            mock_send_error.assert_called_once()
            assert (
                "pgettext_subscription.change_failed"
                in mock_send_error.call_args.kwargs["error_message"]
            )

    @pytest.mark.asyncio
    async def test_handle_subscription_callback_general_exception(
        self,
        handler: SubscriptionHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
        make_mock_user_profile,
        make_mock_callback_query,
    ) -> None:
        """Test subscription callback handling with general exception.

        This test verifies that when a general exception occurs during
        subscription update, an appropriate error message is sent.

        :param handler: SubscriptionHandler instance from fixture
        :type handler: SubscriptionHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :param mock_context: Mocked Telegram context object
        :type mock_context: MagicMock
        :param make_mock_user_profile: Fixture for creating mock user profiles
        :type make_mock_user_profile: callable
        :param make_mock_callback_query: Fixture for creating mock callback queries
        :type make_mock_callback_query: callable
        :returns: None
        :rtype: None
        """
        mock_user_profile = make_mock_user_profile(SubscriptionType.BASIC)
        mock_callback_query = make_mock_callback_query(
            mock_update, SubscriptionType.PREMIUM.value
        )
        handler.services.user_service.get_user_profile.return_value = mock_user_profile
        handler.services.user_service.update_user_subscription.side_effect = Exception(
            "General error"
        )

        with patch.object(handler, "send_error_message") as mock_send_error:
            await handler.handle_subscription_callback(mock_update, mock_context)
            mock_callback_query.answer.assert_called_once()
            mock_send_error.assert_called_once()
            assert (
                "pgettext_subscription.change_error"
                in mock_send_error.call_args.kwargs["error_message"]
            )
