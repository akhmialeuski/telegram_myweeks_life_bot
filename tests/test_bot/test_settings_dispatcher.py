"""Unit tests for SettingsDispatcher.

Tests the SettingsDispatcher class which handles the main settings menu.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot.handlers.settings.dispatcher import SettingsDispatcher
from src.enums import SubscriptionType
from tests.utils.fake_container import FakeServiceContainer


class TestSettingsDispatcher:
    """Test suite for SettingsDispatcher class."""

    @pytest.fixture
    def handler(self) -> SettingsDispatcher:
        """Create SettingsDispatcher instance for testing.

        :returns: Configured SettingsDispatcher instance
        :rtype: SettingsDispatcher
        """
        services = FakeServiceContainer()
        services.user_service = MagicMock()
        return SettingsDispatcher(services)

    @pytest.fixture(autouse=True)
    def mock_use_locale(self, mocker) -> MagicMock:
        """Mock use_locale to control translations.

        :param mocker: pytest-mock fixture
        :type mocker: pytest_mock.MockerFixture
        :returns: Mocked pgettext function
        :rtype: MagicMock
        """
        mock_pgettext = MagicMock(side_effect=lambda c, m: f"pgettext_{c}_{m}")
        mocker.patch(
            "src.bot.handlers.settings.dispatcher.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return mock_pgettext

    @pytest.mark.asyncio
    async def test_handle_shows_menu_basic(
        self,
        handler: SettingsDispatcher,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that handle method shows settings menu for basic user.

        :param handler: SettingsDispatcher instance
        :type handler: SettingsDispatcher
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        # Setup basic user profile
        from src.bot.handlers.base_handler import CommandContext

        mock_profile = MagicMock()
        mock_profile.subscription.subscription_type = SubscriptionType.BASIC
        mock_profile.settings.language = "en"
        mock_profile.settings.life_expectancy = 80
        mock_profile.birth_date = None  # Add birth_date attribute

        # Mock _extract_command_context to return proper CommandContext
        mock_cmd_context = CommandContext(
            user=mock_update.effective_user,
            user_id=mock_update.effective_user.id,
            language="en",
            user_profile=mock_profile,
        )

        with patch.object(
            handler, "_extract_command_context", new_callable=AsyncMock
        ) as mock_extract:
            mock_extract.return_value = mock_cmd_context

            with patch.object(
                handler, "send_message", new_callable=AsyncMock
            ) as mock_send_message:
                # Call _handle_settings directly to avoid registration decorator complexity
                await handler._handle_settings(mock_update, mock_context)

            mock_send_message.assert_called_once()
            args = mock_send_message.call_args.kwargs

            assert "pgettext_settings.basic" in args["message_text"]
            assert args["reply_markup"] is not None

    @pytest.mark.asyncio
    async def test_handle_shows_menu_premium(
        self,
        handler: SettingsDispatcher,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that handle method shows settings menu for premium user.

        :param handler: SettingsDispatcher instance
        :type handler: SettingsDispatcher
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        # Setup premium user profile
        from src.bot.handlers.base_handler import CommandContext

        mock_profile = MagicMock()
        mock_profile.subscription.subscription_type = SubscriptionType.PREMIUM
        mock_profile.settings.language = "en"
        mock_profile.settings.life_expectancy = 80
        mock_profile.birth_date = None  # Add birth_date attribute

        # Mock _extract_command_context to return proper CommandContext
        mock_cmd_context = CommandContext(
            user=mock_update.effective_user,
            user_id=mock_update.effective_user.id,
            language="en",
            user_profile=mock_profile,
        )

        with patch.object(
            handler, "_extract_command_context", new_callable=AsyncMock
        ) as mock_extract:
            mock_extract.return_value = mock_cmd_context

            with patch.object(
                handler, "send_message", new_callable=AsyncMock
            ) as mock_send_message:
                # Call _handle_settings directly to avoid registration decorator complexity
                await handler._handle_settings(mock_update, mock_context)

            mock_send_message.assert_called_once()
            args = mock_send_message.call_args.kwargs

            assert "pgettext_settings.premium" in args["message_text"]

            assert "pgettext_settings.premium" in args["message_text"]

    @pytest.mark.asyncio
    async def test_handle_wrapper_call(
        self,
        handler: SettingsDispatcher,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handle method calls wrapper.

        :param handler: SettingsDispatcher instance
        :type handler: SettingsDispatcher
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        # Mock _wrap_with_registration to verify it's called
        wrapper_mock = AsyncMock()
        mock_wrap = MagicMock(return_value=wrapper_mock)

        with patch.object(handler, "_wrap_with_registration", mock_wrap):
            await handler.handle(mock_update, mock_context)

            mock_wrap.assert_called_once_with(handler_method=handler._handle_settings)
            wrapper_mock.assert_called_once_with(
                update=mock_update, context=mock_context
            )

    @pytest.mark.asyncio
    async def test_handle_error(
        self,
        handler: SettingsDispatcher,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test error handling in dispatcher.

        :param handler: SettingsDispatcher instance
        :type handler: SettingsDispatcher
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        # Mock send_message to raise exception to trigger error handling in _handle_settings
        with patch.object(
            handler, "send_message", side_effect=Exception("Render error")
        ):
            # Also mock _extract_command_context to succeed
            # We need to bypass the _wrap_with_registration failure if we want to test _handle_settings error handling
            # BUT _wrap_with_registration calls _extract_command_context.
            # If we want exception INSIDE _handle_settings, we must let extraction succeed.

            # Setup successful profile retrieval
            mock_profile = MagicMock()
            mock_profile.subscription.subscription_type = SubscriptionType.BASIC
            mock_profile.settings.language = "en"

            with patch.object(
                handler.services.user_service,
                "get_user_profile",
                new_callable=AsyncMock,
            ) as mock_get_profile:
                mock_get_profile.return_value = mock_profile

                with patch.object(handler, "send_error_message") as mock_send_error:
                    await handler.handle(mock_update, mock_context)

                    mock_send_error.assert_called_once()

                mock_send_error.assert_called_once()
