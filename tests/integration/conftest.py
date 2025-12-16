"""Integration test fixtures and TelegramEmulator for mock-based testing.

This module provides shared fixtures and utilities for integration tests.
It includes the TelegramEmulator class for simulating Telegram interactions
without network access, using in-memory services for speed and isolation.
"""

from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from datetime import date
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import CallbackQuery, Chat, Message, Update, User
from telegram.ext import ContextTypes

from src.bot.handlers.base_handler import BaseHandler
from src.enums import SubscriptionType, SupportedLanguage
from tests.fakes import FakeNotificationGateway, FakeUserService

# =============================================================================
# Test Constants
# =============================================================================

TEST_USER_ID: int = 123456789
TEST_CHAT_ID: int = 123456789
TEST_USERNAME: str = "test_integration_user"
TEST_FIRST_NAME: str = "Integration"
TEST_LAST_NAME: str = "Tester"
TEST_LANGUAGE_CODE: str = SupportedLanguage.EN.value


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class BotReply:
    """Represents a reply sent by the bot.

    Attributes:
        text: Reply text content
        parse_mode: Parse mode used (HTML, Markdown, etc.)
        reply_markup: Keyboard markup if present
        photo: Photo data if reply is a photo
        caption: Photo caption if present
    """

    text: str | None = None
    parse_mode: str | None = None
    reply_markup: Any = None
    photo: bytes | None = None
    caption: str | None = None


@dataclass
class IntegrationTestServices:
    """Container for in-memory test services.

    Provides fake implementations of all services needed for integration
    testing without database or network dependencies.

    Attributes:
        user_service: In-memory user service
        notification_gateway: Fake notification gateway for tracking messages
        event_bus: Mock event bus
    """

    user_service: FakeUserService = field(default_factory=FakeUserService)
    notification_gateway: FakeNotificationGateway = field(
        default_factory=FakeNotificationGateway
    )
    event_bus: MagicMock = field(default_factory=MagicMock)

    def clear(self) -> None:
        """Clear all service state for test isolation.

        :returns: None
        """
        self.user_service.clear()
        self.notification_gateway.clear()
        self.event_bus.reset_mock()


# =============================================================================
# TelegramEmulator
# =============================================================================


class TelegramEmulator:
    """Emulator for simulating Telegram bot interactions.

    This class provides methods to simulate user interactions with the bot
    without actual network calls. It tracks all replies sent by handlers
    for assertion in tests.

    Attributes:
        services: In-memory test services container
        user_id: Telegram user ID for simulated user
        chat_id: Chat ID for simulated conversation
        username: Username for simulated user
        first_name: First name for simulated user
        last_name: Last name for simulated user
        language_code: Language code for simulated user
        replies: List of bot replies collected during test
        context_user_data: Simulated context.user_data storage

    Example:
        >>> emulator = TelegramEmulator(services)
        >>> await emulator.send_command("/start")
        >>> reply = emulator.get_last_reply()
        >>> assert "birth date" in reply.text.lower()
    """

    def __init__(
        self,
        services: IntegrationTestServices,
        user_id: int = TEST_USER_ID,
        chat_id: int = TEST_CHAT_ID,
        username: str = TEST_USERNAME,
        first_name: str = TEST_FIRST_NAME,
        last_name: str = TEST_LAST_NAME,
        language_code: str = TEST_LANGUAGE_CODE,
    ) -> None:
        """Initialize the Telegram emulator.

        :param services: In-memory test services container
        :type services: IntegrationTestServices
        :param user_id: Telegram user ID
        :type user_id: int
        :param chat_id: Chat ID
        :type chat_id: int
        :param username: Username
        :type username: str
        :param first_name: First name
        :type first_name: str
        :param last_name: Last name
        :type last_name: str
        :param language_code: Language code
        :type language_code: str
        :returns: None
        """
        self.services = services
        self.user_id = user_id
        self.chat_id = chat_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.language_code = language_code
        self.replies: list[BotReply] = []
        self.context_user_data: dict[str, Any] = {}

    def _create_mock_user(self) -> MagicMock:
        """Create a mock Telegram User object.

        :returns: Mock User object with test user attributes
        :rtype: MagicMock
        """
        user = MagicMock(spec=User)
        user.id = self.user_id
        user.username = self.username
        user.first_name = self.first_name
        user.last_name = self.last_name
        user.language_code = self.language_code
        user.is_bot = False
        return user

    def _create_mock_chat(self) -> MagicMock:
        """Create a mock Telegram Chat object.

        :returns: Mock Chat object
        :rtype: MagicMock
        """
        chat = MagicMock(spec=Chat)
        chat.id = self.chat_id
        chat.type = "private"
        return chat

    def _create_mock_message(
        self,
        text: str,
        is_command: bool = False,
    ) -> MagicMock:
        """Create a mock Telegram Message object.

        :param text: Message text content
        :type text: str
        :param is_command: Whether message is a command
        :type is_command: bool
        :returns: Mock Message object
        :rtype: MagicMock
        """
        message = MagicMock(spec=Message)
        message.text = text
        message.from_user = self._create_mock_user()
        message.chat = self._create_mock_chat()
        message.message_id = len(self.replies) + 1

        # Set up reply methods to capture responses
        async def capture_reply_text(
            text: str,
            parse_mode: str | None = None,
            reply_markup: Any = None,
            **kwargs: Any,
        ) -> MagicMock:
            """Capture text reply from handler."""
            self.replies.append(
                BotReply(
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
            )
            return MagicMock()

        async def capture_reply_photo(
            photo: Any,
            caption: str | None = None,
            parse_mode: str | None = None,
            reply_markup: Any = None,
            **kwargs: Any,
        ) -> MagicMock:
            """Capture photo reply from handler."""
            self.replies.append(
                BotReply(
                    photo=photo,
                    caption=caption,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
            )
            return MagicMock()

        message.reply_text = AsyncMock(side_effect=capture_reply_text)
        message.reply_photo = AsyncMock(side_effect=capture_reply_photo)

        return message

    def _create_mock_update(
        self,
        message: MagicMock | None = None,
        callback_query: MagicMock | None = None,
    ) -> MagicMock:
        """Create a mock Telegram Update object.

        :param message: Mock message object
        :type message: MagicMock | None
        :param callback_query: Mock callback query object
        :type callback_query: MagicMock | None
        :returns: Mock Update object
        :rtype: MagicMock
        """
        update = MagicMock(spec=Update)
        update.update_id = len(self.replies) + 1000
        update.message = message
        update.callback_query = callback_query
        update.effective_user = self._create_mock_user()
        update.effective_chat = self._create_mock_chat()
        return update

    def _create_mock_context(self) -> MagicMock:
        """Create a mock Telegram Context object.

        :returns: Mock Context object with user_data storage
        :rtype: MagicMock
        """
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = self.context_user_data
        context.bot = MagicMock()
        context.bot.send_message = AsyncMock()
        return context

    async def send_command(
        self,
        command: str,
        handler: BaseHandler,
    ) -> None:
        """Simulate sending a command to the bot.

        :param command: Command to send (e.g., "/start")
        :type command: str
        :param handler: Handler instance to process the command
        :type handler: BaseHandler
        :returns: None
        """
        message = self._create_mock_message(
            text=command,
            is_command=True,
        )
        update = self._create_mock_update(message=message)
        context = self._create_mock_context()

        await handler.handle(update=update, context=context)

    async def send_message(
        self,
        text: str,
        handler: BaseHandler,
        handler_method: str = "handle",
    ) -> None:
        """Simulate sending a text message to the bot.

        :param text: Text message to send
        :type text: str
        :param handler: Handler instance to process the message
        :type handler: BaseHandler
        :param handler_method: Method name to call on handler
        :type handler_method: str
        :returns: None
        """
        message = self._create_mock_message(text=text)
        update = self._create_mock_update(message=message)
        context = self._create_mock_context()

        method = getattr(handler, handler_method)
        await method(update, context)

    async def click_button(
        self,
        callback_data: str,
        handler: BaseHandler,
        handler_method: str = "handle_callback",
    ) -> None:
        """Simulate clicking an inline button.

        :param callback_data: Callback data for the button
        :type callback_data: str
        :param handler: Handler instance to process the callback
        :type handler: BaseHandler
        :param handler_method: Method name to call on handler
        :type handler_method: str
        :returns: None
        """
        callback_query = MagicMock(spec=CallbackQuery)
        callback_query.data = callback_data
        callback_query.from_user = self._create_mock_user()
        callback_query.message = self._create_mock_message(text="")
        callback_query.answer = AsyncMock()
        callback_query.edit_message_text = AsyncMock()

        update = self._create_mock_update(callback_query=callback_query)
        context = self._create_mock_context()

        method = getattr(handler, handler_method)
        await method(update, context)

    def get_last_reply(self) -> BotReply | None:
        """Get the most recent bot reply.

        :returns: Last bot reply or None if no replies
        :rtype: BotReply | None
        """
        if self.replies:
            return self.replies[-1]
        return None

    def get_all_replies(self) -> list[BotReply]:
        """Get all bot replies.

        :returns: List of all bot replies
        :rtype: list[BotReply]
        """
        return self.replies.copy()

    def clear_replies(self) -> None:
        """Clear all collected replies.

        :returns: None
        """
        self.replies.clear()

    def get_reply_count(self) -> int:
        """Get the number of replies collected.

        :returns: Number of replies
        :rtype: int
        """
        return len(self.replies)

    async def send_callback(
        self,
        callback_data: str,
        handler: BaseHandler,
        handler_method: str = "handle_callback",
    ) -> None:
        """Alias for click_button method.

        :param callback_data: Callback data for the button
        :type callback_data: str
        :param handler: Handler instance to process the callback
        :type handler: BaseHandler
        :param handler_method: Method name to call on handler
        :type handler_method: str
        :returns: None
        """
        await self.click_button(
            callback_data=callback_data,
            handler=handler,
            handler_method=handler_method,
        )


# =============================================================================
# IntegrationTestServiceContainer
# =============================================================================


class IntegrationTestServiceContainer:
    """Service container configured for integration testing.

    This container provides the same interface as ServiceContainer
    but uses in-memory implementations for all services.

    Attributes:
        user_service: In-memory user service
        event_bus: Mock event bus
        notification_gateway: Fake notification gateway
        localization_service: Mock localization service
        notification_service: Mock notification service
    """

    def __init__(self, services: IntegrationTestServices) -> None:
        """Initialize the test service container.

        :param services: In-memory test services
        :type services: IntegrationTestServices
        :returns: None
        """
        self._services = services

        # Set up service properties
        self.user_service = services.user_service
        self.event_bus = services.event_bus
        self.notification_gateway = services.notification_gateway

        # Mock localization service
        self.localization_service = MagicMock()
        self.localization_service.translate = MagicMock(
            return_value="Translated message"
        )

        # Mock notification service
        self.notification_service = MagicMock()

        # Set up event bus mock
        self.event_bus.publish = AsyncMock()

    def get_user_service(self) -> FakeUserService:
        """Get the user service.

        :returns: Fake user service
        :rtype: FakeUserService
        """
        return self.user_service

    def get_event_bus(self) -> MagicMock:
        """Get the event bus.

        :returns: Mock event bus
        :rtype: MagicMock
        """
        return self.event_bus

    def get_notification_gateway(self) -> FakeNotificationGateway:
        """Get the notification gateway.

        :returns: Fake notification gateway
        :rtype: FakeNotificationGateway
        """
        return self.notification_gateway


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def integration_services() -> Iterator[IntegrationTestServices]:
    """Provide fresh in-memory test services for each test.

    :returns: IntegrationTestServices instance
    :rtype: Iterator[IntegrationTestServices]
    """
    services = IntegrationTestServices()
    yield services
    services.clear()


@pytest.fixture
def integration_container(
    integration_services: IntegrationTestServices,
) -> IntegrationTestServiceContainer:
    """Provide service container configured for integration testing.

    :param integration_services: In-memory test services
    :type integration_services: IntegrationTestServices
    :returns: Integration test service container
    :rtype: IntegrationTestServiceContainer
    """
    return IntegrationTestServiceContainer(services=integration_services)


@pytest.fixture
def telegram_emulator(
    integration_services: IntegrationTestServices,
) -> TelegramEmulator:
    """Provide TelegramEmulator instance for each test.

    :param integration_services: In-memory test services
    :type integration_services: IntegrationTestServices
    :returns: TelegramEmulator instance
    :rtype: TelegramEmulator
    """
    return TelegramEmulator(services=integration_services)


@pytest.fixture
def mock_telegram_user() -> MagicMock:
    """Provide a mock Telegram User object.

    :returns: Mock User object with test user attributes
    :rtype: MagicMock
    """
    user = MagicMock(spec=User)
    user.id = TEST_USER_ID
    user.username = TEST_USERNAME
    user.first_name = TEST_FIRST_NAME
    user.last_name = TEST_LAST_NAME
    user.language_code = TEST_LANGUAGE_CODE
    user.is_bot = False
    return user


@pytest.fixture
async def registered_user(
    integration_services: IntegrationTestServices,
    mock_telegram_user: MagicMock,
) -> AsyncIterator[MagicMock]:
    """Provide a pre-registered user for tests requiring existing user.

    Creates a user with default settings in the fake user service.

    :param integration_services: In-memory test services
    :type integration_services: IntegrationTestServices
    :param mock_telegram_user: Mock Telegram user
    :type mock_telegram_user: MagicMock
    :returns: Mock user profile
    :rtype: AsyncIterator[MagicMock]
    """
    birth_date = date(1990, 1, 15)
    profile = await integration_services.user_service.create_user_profile(
        user_info=mock_telegram_user,
        birth_date=birth_date,
        subscription_type=SubscriptionType.BASIC,
    )
    yield profile
