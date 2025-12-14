"""Tests for message context utilities."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from telegram import User as TelegramUser

from src.core.message_context import _CURRENT_CTX, MessageContext, use_message_context
from src.database.models.user import User
from src.database.models.user_settings import UserSettings


class TestMessageContext:
    """Test class for MessageContext functionality.

    This class contains all tests for the MessageContext class,
    including context creation, language resolution, and profile management.
    """

    def setup_method(self) -> None:
        """Set up test fixtures before each test method.

        Resets the global message context before each test to ensure
        test isolation and prevent context leakage between tests.

        :returns: None
        :rtype: None
        """
        # Reset context before each test
        _CURRENT_CTX.set(None)

    def teardown_method(self) -> None:
        """Clean up after each test method.

        Resets the global message context after each test to ensure
        clean state for subsequent tests.

        :returns: None
        :rtype: None
        """
        # Reset context after each test
        _CURRENT_CTX.set(None)

    def test_message_context_creation(self) -> None:
        """Test MessageContext creation with all fields.

        This test verifies that MessageContext can be created with all
        required fields and stores them correctly.

        :returns: None
        :rtype: None
        """
        # Create mock objects
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = 12345
        telegram_user.language_code = "en"

        user_profile = Mock(spec=User)
        user_profile.id = 1

        # Create MessageContext
        context = MessageContext(
            user_info=telegram_user,
            user_id=12345,
            user_profile=user_profile,
            language="en",
        )

        # Verify all fields are set correctly
        assert context.user_info == telegram_user
        assert context.user_id == 12345
        assert context.user_profile == user_profile
        assert context.language == "en"

    def test_message_context_without_profile(self) -> None:
        """Test MessageContext creation without user profile.

        This test verifies that MessageContext can be created with None
        user_profile and handles it correctly.

        :returns: None
        :rtype: None
        """
        # Create mock objects
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = 12345
        telegram_user.language_code = "ru"

        # Create MessageContext without profile
        context = MessageContext(
            user_info=telegram_user,
            user_id=12345,
            user_profile=None,
            language="ru",
        )

        # Verify fields are set correctly
        assert context.user_info == telegram_user
        assert context.user_id == 12345
        assert context.user_profile is None
        assert context.language == "ru"

    @pytest.mark.asyncio
    @patch("src.services.container.ServiceContainer")
    async def test_from_user_with_fetch_profile_true(
        self, mock_container_class
    ) -> None:
        """Test MessageContext.from_user with fetch_profile=True.

        This test verifies that from_user method fetches user profile
        when fetch_profile is True.

        :param mock_container_class: Mocked ServiceContainer class
        :type mock_container_class: Mock
        :returns: None
        :rtype: None
        """
        # Setup mocks
        mock_container = Mock()
        mock_user_service = Mock()
        mock_container.get_user_service.return_value = mock_user_service
        mock_container_class.return_value = mock_container

        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = 12345
        telegram_user.language_code = "en"

        user_profile = Mock(spec=User)
        user_profile.id = 1
        user_profile.settings = None

        mock_user_service.get_user_profile = AsyncMock(return_value=user_profile)

        # Call from_user with fetch_profile=True
        context = await MessageContext.from_user(
            user_info=telegram_user, fetch_profile=True
        )

        # Verify profile was fetched
        mock_user_service.get_user_profile.assert_called_once_with(telegram_id=12345)
        assert context.user_profile == user_profile
        assert context.user_info == telegram_user
        assert context.user_id == 12345

    @pytest.mark.asyncio
    @patch("src.services.container.ServiceContainer")
    async def test_from_user_with_fetch_profile_false(
        self, mock_container_class
    ) -> None:
        """Test MessageContext.from_user with fetch_profile=False.

        This test verifies that from_user method does not fetch user profile
        when fetch_profile is False.

        :param mock_container_class: Mocked ServiceContainer class
        :type mock_container_class: Mock
        :returns: None
        :rtype: None
        """
        # Setup mocks
        mock_container = Mock()
        mock_container_class.return_value = mock_container

        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = 12345
        telegram_user.language_code = "ru"

        # Call from_user with fetch_profile=False
        context = await MessageContext.from_user(
            user_info=telegram_user, fetch_profile=False
        )

        # Verify profile was not fetched
        mock_container.get_user_service.assert_not_called()
        assert context.user_profile is None
        assert context.user_info == telegram_user
        assert context.user_id == 12345

    def test_resolve_language_from_user_profile(self) -> None:
        """Test language resolution from user profile.

        This test verifies that language is resolved from user profile
        settings when available, taking priority over Telegram language.

        :returns: None
        :rtype: None
        """
        # Create mock objects
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.language_code = "en"

        user_settings = Mock(spec=UserSettings)
        user_settings.language = "ru"

        user_profile = Mock(spec=User)
        user_profile.settings = user_settings

        # Test language resolution
        language = MessageContext._resolve_language(telegram_user, user_profile)

        # Verify language from profile is used
        assert language == "ru"

    def test_resolve_language_from_telegram_user(self) -> None:
        """Test language resolution from Telegram user.

        This test verifies that language is resolved from Telegram user
        when user profile has no language setting.

        :returns: None
        :rtype: None
        """
        # Create mock objects
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.language_code = "uk"

        user_profile = Mock(spec=User)
        user_profile.settings = None

        # Test language resolution
        language = MessageContext._resolve_language(telegram_user, user_profile)

        # Verify language from Telegram user is used
        assert language == "uk"

    def test_resolve_language_with_no_profile(self) -> None:
        """Test language resolution with no user profile.

        This test verifies that language is resolved from Telegram user
        when no user profile is available.

        :returns: None
        :rtype: None
        """
        # Create mock objects
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.language_code = "be"

        # Test language resolution with no profile
        language = MessageContext._resolve_language(telegram_user, None)

        # Verify language from Telegram user is used
        assert language == "be"

    def test_resolve_language_with_no_telegram_language(self) -> None:
        """Test language resolution with no Telegram language code.

        This test verifies that default language is used when neither
        user profile nor Telegram user has language information.

        :returns: None
        :rtype: None
        """
        # Create mock objects
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.language_code = None

        # Test language resolution
        language = MessageContext._resolve_language(telegram_user, None)

        # Verify default language is used (DEFAULT_LANGUAGE from config)
        assert language == "ru"  # DEFAULT_LANGUAGE

    @pytest.mark.asyncio
    @patch("src.services.container.ServiceContainer")
    async def test_ensure_profile_with_existing_profile(
        self, mock_container_class
    ) -> None:
        """Test ensure_profile when profile already exists.

        This test verifies that ensure_profile returns existing profile
        without fetching it again from the database.

        :param mock_container_class: Mocked ServiceContainer class
        :type mock_container_class: Mock
        :returns: None
        :rtype: None
        """
        # Create mock objects
        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = 12345

        user_profile = Mock(spec=User)
        user_profile.id = 1

        context = MessageContext(
            user_info=telegram_user,
            user_id=12345,
            user_profile=user_profile,
            language="en",
        )

        # Test ensure_profile
        result = await context.ensure_profile()

        # Verify existing profile is returned
        assert result == user_profile
        # Verify no service calls were made
        mock_container_class.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.container.ServiceContainer")
    async def test_ensure_profile_with_none_profile_success(
        self, mock_container_class
    ) -> None:
        """Test ensure_profile when profile is None but can be fetched.

        This test verifies that ensure_profile fetches and caches profile
        when it's not present but available in database.

        :param mock_container_class: Mocked ServiceContainer class
        :type mock_container_class: Mock
        :returns: None
        :rtype: None
        """
        # Setup mocks
        mock_container = Mock()
        mock_user_service = Mock()
        mock_container.get_user_service.return_value = mock_user_service
        mock_container_class.return_value = mock_container

        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = 12345

        user_profile = Mock(spec=User)
        user_profile.id = 1

        mock_user_service.get_user_profile = AsyncMock(return_value=user_profile)

        context = MessageContext(
            user_info=telegram_user,
            user_id=12345,
            user_profile=None,
            language="en",
        )

        # Test ensure_profile
        result = await context.ensure_profile()

        # Verify profile was fetched and cached
        mock_user_service.get_user_profile.assert_called_once_with(telegram_id=12345)
        assert result == user_profile
        assert context.user_profile == user_profile

    @pytest.mark.asyncio
    @patch("src.services.container.ServiceContainer")
    async def test_ensure_profile_with_none_profile_not_found(
        self, mock_container_class
    ) -> None:
        """Test ensure_profile when profile is None and cannot be fetched.

        This test verifies that ensure_profile raises ValueError when
        profile is not found in database.

        :param mock_container_class: Mocked ServiceContainer class
        :type mock_container_class: Mock
        :returns: None
        :rtype: None
        """
        # Setup mocks
        mock_container = Mock()
        mock_user_service = Mock()
        mock_container.get_user_service.return_value = mock_user_service
        mock_container_class.return_value = mock_container

        telegram_user = Mock(spec=TelegramUser)
        telegram_user.id = 12345

        mock_user_service.get_user_profile = AsyncMock(return_value=None)

        context = MessageContext(
            user_info=telegram_user,
            user_id=12345,
            user_profile=None,
            language="en",
        )

        # Test ensure_profile should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            await context.ensure_profile()

        # Verify error message
        assert "User profile not found for telegram_id: 12345" in str(exc_info.value)


class TestUseMessageContext:
    """Test class for use_message_context context manager.

    This class contains all tests for the use_message_context context manager,
    including context setup, cleanup, exception handling, and nested contexts.
    """

    def setup_method(self) -> None:
        """Set up test fixtures before each test method.

        Resets the global message context before each test to ensure
        test isolation and prevent context leakage between tests.

        :returns: None
        :rtype: None
        """
        # Reset context before each test
        _CURRENT_CTX.set(None)

    def teardown_method(self) -> None:
        """Clean up after each test method.

        Resets the global message context after each test to ensure
        clean state for subsequent tests.

        :returns: None
        :rtype: None
        """
        # Reset context after each test
        _CURRENT_CTX.set(None)

    @pytest.mark.asyncio
    @patch("src.core.message_context.MessageContext.from_user")
    async def test_use_message_context_success(self, mock_from_user) -> None:
        """Test use_message_context context manager success.

        This test verifies that use_message_context properly sets and
        cleans up the message context.

        :param mock_from_user: Mocked MessageContext.from_user method
        :type mock_from_user: Mock
        :returns: None
        :rtype: None
        """
        # Setup mocks
        telegram_user = Mock(spec=TelegramUser)
        mock_context = Mock(spec=MessageContext)
        mock_from_user.return_value = mock_context

        # Test context manager
        async with use_message_context(telegram_user, fetch_profile=True) as ctx:
            # Verify context is set
            assert _CURRENT_CTX.get() == mock_context
            assert ctx == mock_context

            # Verify from_user was called correctly
            mock_from_user.assert_called_once_with(
                user_info=telegram_user, fetch_profile=True
            )

        # Verify context is cleaned up
        assert _CURRENT_CTX.get() is None

    @pytest.mark.asyncio
    @patch("src.core.message_context.MessageContext.from_user")
    async def test_use_message_context_with_exception(self, mock_from_user) -> None:
        """Test use_message_context context manager with exception.

        This test verifies that use_message_context properly cleans up
        context even when an exception occurs inside the context.

        :param mock_from_user: Mocked MessageContext.from_user method
        :type mock_from_user: Mock
        :returns: None
        :rtype: None
        """
        # Setup mocks
        telegram_user = Mock(spec=TelegramUser)
        mock_context = Mock(spec=MessageContext)
        mock_from_user.return_value = mock_context

        # Test context manager with exception
        with pytest.raises(ValueError):
            async with use_message_context(telegram_user, fetch_profile=False):
                # Verify context is set
                assert _CURRENT_CTX.get() == mock_context

                # Raise exception
                raise ValueError("Test exception")

        # Verify context is cleaned up even after exception
        assert _CURRENT_CTX.get() is None

    @pytest.mark.asyncio
    @patch("src.core.message_context.MessageContext.from_user")
    async def test_use_message_context_nested_contexts(self, mock_from_user) -> None:
        """Test use_message_context with nested contexts.

        This test verifies that use_message_context properly handles
        nested context usage and restores the outer context correctly.

        :param mock_from_user: Mocked MessageContext.from_user method
        :type mock_from_user: Mock
        :returns: None
        :rtype: None
        """
        # Setup mocks
        telegram_user1 = Mock(spec=TelegramUser)
        telegram_user2 = Mock(spec=TelegramUser)

        mock_context1 = Mock(spec=MessageContext)
        mock_context2 = Mock(spec=MessageContext)

        mock_from_user.side_effect = [mock_context1, mock_context2]

        # Test nested context managers
        async with use_message_context(telegram_user1, fetch_profile=True) as ctx1:
            assert _CURRENT_CTX.get() == mock_context1
            assert ctx1 == mock_context1

            async with use_message_context(telegram_user2, fetch_profile=False) as ctx2:
                assert _CURRENT_CTX.get() == mock_context2
                assert ctx2 == mock_context2

            # Verify inner context is restored
            assert _CURRENT_CTX.get() == mock_context1

        # Verify outer context is cleaned up
        assert _CURRENT_CTX.get() is None
