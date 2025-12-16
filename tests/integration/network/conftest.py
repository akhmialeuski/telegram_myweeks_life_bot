"""Network integration test fixtures.

This module provides fixtures for network-based integration tests
that interact with the actual Telegram API via Local Bot API Server.
These tests are marked with @pytest.mark.network and are run separately.
"""

import asyncio
import os
from collections.abc import AsyncIterator
from typing import Any

import pytest
from telegram import Bot, Update
from telegram.ext import Application

# =============================================================================
# Configuration Constants
# =============================================================================

# Rate limiting configuration
RATE_LIMIT_DELAY: float = float(os.getenv("TEST_RATE_LIMIT_DELAY", "0.5"))
MAX_RETRIES: int = int(os.getenv("TEST_RETRY_COUNT", "3"))
RETRY_BACKOFF: float = 2.0
DEFAULT_TIMEOUT: int = int(os.getenv("TEST_TIMEOUT_SECONDS", "30"))

# Message prefix for test isolation
TEST_MESSAGE_PREFIX: str = os.getenv("TEST_MESSAGE_PREFIX", "[TEST]")


# =============================================================================
# Network Test Client
# =============================================================================


class NetworkTestClient:
    """Client for network-based integration tests.

    This client communicates with the Telegram API through a Local Bot API
    Server for controlled testing. It includes rate limiting, retry logic,
    and backoff handling.

    Attributes:
        bot: Telegram Bot instance configured for local API
        chat_id: Test chat ID for sending messages
        rate_limit_delay: Delay between requests (seconds)
        max_retries: Maximum retry attempts
        retry_backoff: Exponential backoff multiplier

    Example:
        >>> client = NetworkTestClient(bot=test_bot, chat_id=123456)
        >>> await client.send_message("Hello from test!")
        >>> reply = await client.wait_for_reply(timeout=30)
    """

    def __init__(
        self,
        bot: Bot,
        chat_id: int,
        rate_limit_delay: float = RATE_LIMIT_DELAY,
        max_retries: int = MAX_RETRIES,
        retry_backoff: float = RETRY_BACKOFF,
    ) -> None:
        """Initialize the network test client.

        :param bot: Telegram Bot instance
        :type bot: Bot
        :param chat_id: Test chat ID
        :type chat_id: int
        :param rate_limit_delay: Delay between requests
        :type rate_limit_delay: float
        :param max_retries: Maximum retry attempts
        :type max_retries: int
        :param retry_backoff: Exponential backoff multiplier
        :type retry_backoff: float
        :returns: None
        """
        self.bot = bot
        self.chat_id = chat_id
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self._last_request_time: float = 0

    async def _rate_limit(self) -> None:
        """Apply rate limiting between requests.

        :returns: None
        """
        import time

        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    async def _retry_with_backoff(
        self,
        func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute function with retry and exponential backoff.

        :param func: Async function to execute
        :type func: Any
        :param args: Positional arguments for function
        :type args: Any
        :param kwargs: Keyword arguments for function
        :type kwargs: Any
        :returns: Function result
        :rtype: Any
        :raises Exception: If all retries exhausted
        """
        last_exception: Exception | None = None
        delay = self.rate_limit_delay

        for attempt in range(self.max_retries):
            try:
                await self._rate_limit()
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(delay)
                    delay *= self.retry_backoff

        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected error in retry logic")

    async def send_message(
        self,
        text: str,
        prefix: bool = True,
    ) -> Any:
        """Send a message to the test chat.

        :param text: Message text to send
        :type text: str
        :param prefix: Whether to add test prefix
        :type prefix: bool
        :returns: Sent message object
        :rtype: Any
        """
        message_text = f"{TEST_MESSAGE_PREFIX} {text}" if prefix else text
        return await self._retry_with_backoff(
            self.bot.send_message,
            chat_id=self.chat_id,
            text=message_text,
        )

    async def send_command(
        self,
        command: str,
    ) -> Any:
        """Send a command to the test chat.

        :param command: Command to send (e.g., "/start")
        :type command: str
        :returns: Sent message object
        :rtype: Any
        """
        # Commands don't need prefix
        return await self._retry_with_backoff(
            self.bot.send_message,
            chat_id=self.chat_id,
            text=command,
        )

    async def get_updates(
        self,
        offset: int | None = None,
        limit: int = 100,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> list[Update]:
        """Get updates from the bot.

        :param offset: Update offset
        :type offset: int | None
        :param limit: Maximum updates to retrieve
        :type limit: int
        :param timeout: Timeout in seconds
        :type timeout: int
        :returns: List of updates
        :rtype: list[Update]
        """
        return await self._retry_with_backoff(
            self.bot.get_updates,
            offset=offset,
            limit=limit,
            timeout=timeout,
        )

    async def wait_for_reply(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        poll_interval: float = 0.5,
    ) -> str | None:
        """Wait for bot reply message.

        Polls for new messages from the bot until a reply is received
        or timeout expires.

        :param timeout: Maximum time to wait for reply (seconds)
        :type timeout: float
        :param poll_interval: Time between poll attempts (seconds)
        :type poll_interval: float
        :returns: Bot reply text or None if timeout
        :rtype: str | None
        """
        import time

        start_time = time.time()
        last_update_id: int | None = None

        while (time.time() - start_time) < timeout:
            try:
                updates = await self.get_updates(
                    offset=last_update_id,
                    timeout=1,
                )

                for update in updates:
                    last_update_id = update.update_id + 1

                    # Check for message from bot (not our own message)
                    if update.message and update.message.from_user:
                        if update.message.from_user.is_bot:
                            return update.message.text

            except Exception:
                pass

            await asyncio.sleep(poll_interval)

        return None

    async def send_command_and_wait(
        self,
        command: str,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> str | None:
        """Send command and wait for bot reply.

        Combines sending a command with waiting for the bot's response.

        :param command: Command to send (e.g., "/start")
        :type command: str
        :param timeout: Maximum time to wait for reply (seconds)
        :type timeout: float
        :returns: Bot reply text or None if timeout
        :rtype: str | None
        """
        await self.send_command(command=command)
        return await self.wait_for_reply(timeout=timeout)

    async def send_message_and_wait(
        self,
        text: str,
        timeout: float = DEFAULT_TIMEOUT,
        prefix: bool = False,
    ) -> str | None:
        """Send message and wait for bot reply.

        Combines sending a message with waiting for the bot's response.

        :param text: Message text to send
        :type text: str
        :param timeout: Maximum time to wait for reply (seconds)
        :type timeout: float
        :param prefix: Whether to add test prefix
        :type prefix: bool
        :returns: Bot reply text or None if timeout
        :rtype: str | None
        """
        await self.send_message(text=text, prefix=prefix)
        return await self.wait_for_reply(timeout=timeout)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def local_bot_api_url() -> str:
    """Get Local Bot API Server URL.

    :returns: Local Bot API Server URL
    :rtype: str
    """
    return os.getenv("LOCAL_BOT_API_URL", "http://localhost:8081")


@pytest.fixture(scope="session")
def test_bot_token() -> str:
    """Get test bot token (not production!).

    :returns: Test bot token
    :rtype: str
    :raises pytest.skip: If TEST_BOT_TOKEN not configured
    """
    token = os.getenv("TEST_BOT_TOKEN")
    if not token:
        pytest.skip("TEST_BOT_TOKEN not configured - skipping network tests")
    return token


@pytest.fixture(scope="session")
def test_chat_id() -> int:
    """Get test chat ID.

    :returns: Test chat ID
    :rtype: int
    :raises pytest.skip: If TEST_CHAT_ID not configured
    """
    chat_id = os.getenv("TEST_CHAT_ID")
    if not chat_id:
        pytest.skip("TEST_CHAT_ID not configured - skipping network tests")
    return int(chat_id)


@pytest.fixture(scope="session")
async def test_bot(
    test_bot_token: str,
    local_bot_api_url: str,
) -> AsyncIterator[Bot]:
    """Create bot configured for Local Bot API Server.

    :param test_bot_token: Test bot token
    :type test_bot_token: str
    :param local_bot_api_url: Local Bot API Server URL
    :type local_bot_api_url: str
    :returns: Configured Bot instance
    :rtype: AsyncIterator[Bot]
    """
    app = (
        Application.builder()
        .token(test_bot_token)
        .base_url(f"{local_bot_api_url}/bot")
        .base_file_url(f"{local_bot_api_url}/file/bot")
        .local_mode(True)
        .build()
    )
    yield app.bot


@pytest.fixture(scope="session")
async def network_client(
    test_bot: Bot,
    test_chat_id: int,
) -> AsyncIterator[NetworkTestClient]:
    """Create network test client.

    :param test_bot: Configured Bot instance
    :type test_bot: Bot
    :param test_chat_id: Test chat ID
    :type test_chat_id: int
    :returns: NetworkTestClient instance
    :rtype: AsyncIterator[NetworkTestClient]
    """
    client = NetworkTestClient(
        bot=test_bot,
        chat_id=test_chat_id,
    )
    yield client
