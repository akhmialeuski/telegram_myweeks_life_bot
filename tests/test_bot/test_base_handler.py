"""Unit tests for BaseHandler.

Tests the BaseHandler class which provides common functionality.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import CallbackQuery, InlineKeyboardMarkup
from telegram.constants import ParseMode

from src.bot.constants import COMMAND_HELP, COMMAND_START, COMMAND_WEEKS
from src.bot.handlers.base_handler import BaseHandler, CommandContext
from src.enums import SupportedLanguage
from tests.utils.fake_container import FakeServiceContainer


class TestBaseHandler:
    """Test suite for BaseHandler class.

    This test class contains all tests for BaseHandler functionality,
    including initialization, registration requirements, message editing,
    and command context extraction.
    """

    class ConcreteHandler(BaseHandler):
        """Concrete implementation of BaseHandler for testing.

        This is a minimal concrete subclass used to test the abstract
        BaseHandler class functionality.
        """

        async def handle(self, update, context):
            """Test implementation of handle method.

            Minimal implementation required by BaseHandler abstract class.

            :param update: Telegram update object
            :param context: Telegram context object
            :returns: None
            """
            return None

    @pytest.fixture
    def handler(self) -> ConcreteHandler:
        """Create ConcreteHandler instance.

        :returns: ConcreteHandler instance
        :rtype: ConcreteHandler
        """
        services = FakeServiceContainer()
        return self.ConcreteHandler(services)

    def test_init_default_values(self, handler: ConcreteHandler) -> None:
        """Test BaseHandler initialization with default values.

        :param handler: ConcreteHandler instance
        :type handler: ConcreteHandler
        :returns: None
        :rtype: None
        """
        assert handler.command_name is None
        assert handler.bot_name == "LifeWeeksBot"

    def test_should_require_registration_with_no_command_name(
        self, handler: ConcreteHandler
    ) -> None:
        """Test _should_require_registration when command_name is None.

        :param handler: ConcreteHandler instance
        :type handler: ConcreteHandler
        :returns: None
        :rtype: None
        """
        assert handler.command_name is None
        result = handler._should_require_registration()
        assert result is True

    def test_should_require_registration_with_no_registration_command(
        self, handler: ConcreteHandler
    ) -> None:
        """Test _should_require_registration with command that doesn't require registration.

        :param handler: ConcreteHandler instance
        :type handler: ConcreteHandler
        :returns: None
        :rtype: None
        """
        handler.command_name = f"/{COMMAND_START}"
        result = handler._should_require_registration()
        assert result is False

    def test_should_require_registration_with_protected_command(
        self, handler: ConcreteHandler
    ) -> None:
        """Test _should_require_registration with command that requires registration.

        :param handler: ConcreteHandler instance
        :type handler: ConcreteHandler
        :returns: None
        :rtype: None
        """
        handler.command_name = f"/{COMMAND_WEEKS}"
        result = handler._should_require_registration()
        assert result is True

    def test_wrap_with_registration_no_registration_required(
        self, handler: ConcreteHandler
    ) -> None:
        """Test _wrap_with_registration when registration is not required.

        :param handler: ConcreteHandler instance
        :type handler: ConcreteHandler
        :returns: None
        :rtype: None
        """
        mock_method = MagicMock()
        handler.command_name = f"/{COMMAND_HELP}"
        result = handler._wrap_with_registration(mock_method)
        assert callable(result)  # Should return a callable wrapper

    @pytest.mark.asyncio
    async def test_edit_message(self, handler: ConcreteHandler) -> None:
        """Test edit_message method.

        :param handler: ConcreteHandler instance
        :type handler: ConcreteHandler
        :returns: None
        :rtype: None
        """
        mock_query = MagicMock(spec=CallbackQuery)
        mock_query.edit_message_text = AsyncMock()
        mock_reply_markup = MagicMock(spec=InlineKeyboardMarkup)
        message_text = "Test message"

        await handler.edit_message(
            query=mock_query, message_text=message_text, reply_markup=mock_reply_markup
        )

        mock_query.edit_message_text.assert_called_once_with(
            text=message_text, reply_markup=mock_reply_markup, parse_mode=ParseMode.HTML
        )

    @pytest.mark.asyncio
    async def test_edit_message_without_markup(self, handler: ConcreteHandler) -> None:
        """Test edit_message method without reply markup.

        :param handler: ConcreteHandler instance
        :type handler: ConcreteHandler
        :returns: None
        :rtype: None
        """
        mock_query = MagicMock(spec=CallbackQuery)
        mock_query.edit_message_text = AsyncMock()
        message_text = "Test message"

        await handler.edit_message(query=mock_query, message_text=message_text)

        mock_query.edit_message_text.assert_called_once_with(
            text=message_text, reply_markup=None, parse_mode=ParseMode.HTML
        )

    @pytest.mark.asyncio
    async def test_extract_command_context(
        self,
        handler: ConcreteHandler,
        mock_update: MagicMock,
    ) -> None:
        """Test command context extraction from update object.

        This test verifies that _extract_command_context correctly extracts
        user information, profile, and language from an update object.

        :param handler: ConcreteHandler instance
        :type handler: ConcreteHandler
        :param mock_update: Mocked Telegram update object
        :type mock_update: MagicMock
        :returns: None
        :rtype: None
        """
        mock_user_profile = MagicMock()
        mock_user_profile.settings.language = SupportedLanguage.EN.value
        handler.services.user_service.get_user_profile.return_value = mock_user_profile

        result = await handler._extract_command_context(mock_update)

        assert isinstance(result, CommandContext)
        assert result.user == mock_update.effective_user
        assert result.user_id == mock_update.effective_user.id
        assert result.language == SupportedLanguage.EN.value
        assert result.user_profile == mock_user_profile
        assert result.command_name is None
