"""Integration tests for /cancel command.

This module tests the /cancel command functionality for aborting
ongoing operations and clearing conversation state.
"""

import pytest

from src.bot.handlers.cancel_handler import CancelHandler
from src.bot.handlers.start_handler import StartHandler
from tests.integration.conftest import (
    IntegrationTestServiceContainer,
    TelegramEmulator,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestCancelDuringRegistration:
    """Test /cancel command during registration flow.

    This class tests that users can cancel the registration process
    at any point using the /cancel command.
    """

    @pytest.fixture
    def start_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> StartHandler:
        """Create StartHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: StartHandler instance
        :rtype: StartHandler
        """
        return StartHandler(services=integration_container)

    @pytest.fixture
    def cancel_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> CancelHandler:
        """Create CancelHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: CancelHandler instance
        :rtype: CancelHandler
        """
        return CancelHandler(services=integration_container)

    async def test_cancel_during_birth_date_input(
        self,
        telegram_emulator: TelegramEmulator,
        start_handler: StartHandler,
        cancel_handler: CancelHandler,
    ) -> None:
        """Test canceling registration during birth date input.

        This test verifies that a user can cancel the registration
        process while being asked for their birth date.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param start_handler: Start handler instance
        :type start_handler: StartHandler
        :param cancel_handler: Cancel handler instance
        :type cancel_handler: CancelHandler
        :returns: None
        """
        # Start registration flow
        await telegram_emulator.send_command(
            command="/start",
            handler=start_handler,
        )

        # Now cancel
        await telegram_emulator.send_command(
            command="/cancel",
            handler=cancel_handler,
        )

        # Should receive cancel confirmation
        assert telegram_emulator.get_reply_count() >= 2


@pytest.mark.integration
@pytest.mark.asyncio
class TestCancelWithNoActiveOperation:
    """Test /cancel command when no operation is active.

    This class tests the behavior when a user sends /cancel
    but there's no active operation to cancel.
    """

    @pytest.fixture
    def cancel_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> CancelHandler:
        """Create CancelHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: CancelHandler instance
        :rtype: CancelHandler
        """
        return CancelHandler(services=integration_container)

    async def test_cancel_with_no_active_operation(
        self,
        telegram_emulator: TelegramEmulator,
        cancel_handler: CancelHandler,
    ) -> None:
        """Test /cancel when there's no active operation.

        This test verifies that the bot handles /cancel gracefully
        even when there's nothing to cancel.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param cancel_handler: Cancel handler instance
        :type cancel_handler: CancelHandler
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/cancel",
            handler=cancel_handler,
        )

        # Should still get a response
        assert telegram_emulator.get_reply_count() >= 1
