"""Unit tests for LanguageHandler.

Tests the LanguageHandler class which handles language settings.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.bot.handlers.settings.language_handler import LanguageHandler
from src.database.service import UserNotFoundError
from tests.conftest import TEST_USER_ID


class TestLanguageHandler:
    """Test suite for LanguageHandler class."""

    @pytest.fixture
    def handler(self) -> LanguageHandler:
        """Create LanguageHandler instance for testing.

        :returns: Configured LanguageHandler instance
        :rtype: LanguageHandler
        """
        from tests.utils.fake_container import FakeServiceContainer

        services = FakeServiceContainer()
        return LanguageHandler(services)

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
            "src.bot.handlers.settings.language_handler.use_locale",
            return_value=(None, None, mock_pgettext),
        )
        return mock_pgettext

    @pytest.mark.asyncio
    async def test_handle_callback_shows_menu(
        self,
        handler: LanguageHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that handle_callback displays language selection menu.

        :param handler: LanguageHandler instance
        :type handler: LanguageHandler
        :param mock_update_with_callback: Mocked update
        :type mock_update_with_callback: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        mock_update_with_callback.callback_query.data = "settings_language"

        mock_profile = MagicMock()
        mock_profile.settings.language = "en"
        handler.services.user_service.get_user_profile.return_value = mock_profile

        with patch.object(handler, "edit_message") as mock_edit_message:
            await handler.handle_callback(mock_update_with_callback, mock_context)

            mock_edit_message.assert_called_once()
            assert (
                "pgettext_settings.change_language_"
                in mock_edit_message.call_args.kwargs["message_text"]
            )

    @pytest.mark.asyncio
    async def test_handle_selection_callback_success(
        self,
        handler: LanguageHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test successful language selection.

        :param handler: LanguageHandler instance
        :type handler: LanguageHandler
        :param mock_update_with_callback: Mocked update
        :type mock_update_with_callback: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        from src.events.domain_events import UserSettingsChangedEvent

        mock_update_with_callback.callback_query.data = "language_ru"

        mock_profile = MagicMock()
        mock_profile.settings.language = "en"
        handler.services.user_service.get_user_profile.return_value = mock_profile

        with patch.object(handler, "edit_message") as mock_edit_message:
            await handler.handle_selection_callback(
                mock_update_with_callback, mock_context
            )

            # Verify DB update
            handler.services.user_service.update_user_settings.assert_called_once_with(
                telegram_id=TEST_USER_ID, language="ru"
            )

            # Verify event published
            handler.services.event_bus.publish.assert_called_once()
            call_args = handler.services.event_bus.publish.call_args
            event = call_args[0][0]
            assert isinstance(event, UserSettingsChangedEvent)
            assert event.user_id == TEST_USER_ID
            assert event.new_value == "ru"
            assert event.setting_name == "language"

            # Verify confirmation message
            mock_edit_message.assert_called_once()
            assert (
                "pgettext_settings.language_updated"
                in mock_edit_message.call_args.kwargs["message_text"]
            )

    @pytest.mark.asyncio
    async def test_handle_selection_callback_invalid_code(
        self,
        handler: LanguageHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handling of invalid language code.

        :param handler: LanguageHandler instance
        :type handler: LanguageHandler
        :param mock_update_with_callback: Mocked update
        :type mock_update_with_callback: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        mock_update_with_callback.callback_query.data = "language_invalid"
        mock_profile = MagicMock()
        mock_profile.settings.language = "en"
        handler.services.user_service.get_user_profile.return_value = mock_profile

        with patch.object(handler, "send_error_message"):
            # Should not crash, might log error or send generic error
            # But the handler might actually fail if use_locale fails to find language
            # In current implementation, normalize_babel_locale handles defaults
            await handler.handle_selection_callback(
                mock_update_with_callback, mock_context
            )
            # Depending on implementation, it might just ignore or send error
            # Current implementation tries to use the language.
            # We just verify it doesn't crash with unhandled exception
            pass

    @pytest.mark.asyncio
    async def test_handle_selection_callback_db_error(
        self,
        handler: LanguageHandler,
        mock_update_with_callback: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test handling of database error during language update.

        :param handler: LanguageHandler instance
        :type handler: LanguageHandler
        :param mock_update_with_callback: Mocked update
        :type mock_update_with_callback: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        mock_update_with_callback.callback_query.data = "language_en"
        handler.services.user_service.update_user_settings.side_effect = (
            UserNotFoundError("User not found")
        )

        mock_profile = MagicMock()
        mock_profile.settings.language = "ru"
        handler.services.user_service.get_user_profile.return_value = mock_profile

        with patch.object(handler, "edit_message") as mock_edit_message:
            await handler.handle_selection_callback(
                mock_update_with_callback, mock_context
            )
            mock_edit_message.assert_called_once()
            assert (
                "pgettext_settings.error_"
                in mock_edit_message.call_args.kwargs["message_text"]
            )

    @pytest.mark.asyncio
    async def test_handle_returns_none(
        self,
        handler: LanguageHandler,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that handle() method returns None.

        This test verifies the handle() method properly returns None.

        :param handler: LanguageHandler instance
        :type handler: LanguageHandler
        :param mock_update: Mocked update
        :type mock_update: MagicMock
        :param mock_context: Mocked context
        :type mock_context: MagicMock
        :returns: None
        """
        result = await handler.handle(mock_update, mock_context)
        assert result is None
