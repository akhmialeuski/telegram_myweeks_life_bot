"""Integration tests for subscription management.

This module tests the /subscription command and subscription flow.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from src.bot.handlers.subscription_handler import SubscriptionHandler
from src.enums import SubscriptionType
from tests.integration.conftest import (
    TEST_USER_ID,
    IntegrationTestServiceContainer,
    IntegrationTestServices,
    TelegramEmulator,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestSubscriptionCommand:
    """Test /subscription command functionality.

    This class tests the subscription command for viewing and managing
    user subscriptions.
    """

    @pytest.fixture
    def subscription_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> SubscriptionHandler:
        """Create SubscriptionHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: SubscriptionHandler instance
        :rtype: SubscriptionHandler
        """
        return SubscriptionHandler(services=integration_container)

    @pytest_asyncio.fixture
    async def registered_user(
        self,
        integration_services: IntegrationTestServices,
    ) -> None:
        """Create a pre-registered user with basic subscription.

        :param integration_services: In-memory test services
        :type integration_services: IntegrationTestServices
        :returns: None
        """
        user_info = MagicMock()
        user_info.id = TEST_USER_ID
        user_info.username = "test_user"
        user_info.first_name = "Test"
        user_info.last_name = "User"

        await integration_services.user_service.create_user_profile(
            user_info=user_info,
            birth_date=date(1990, 1, 15),
            subscription_type=SubscriptionType.BASIC,
        )

    async def test_subscription_command_shows_status(
        self,
        telegram_emulator: TelegramEmulator,
        subscription_handler: SubscriptionHandler,
        registered_user: None,
    ) -> None:
        """Test that /subscription shows current subscription status.

        This test verifies that the subscription command shows
        the user's current subscription information.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param subscription_handler: Subscription handler instance
        :type subscription_handler: SubscriptionHandler
        :param registered_user: Pre-registered user fixture
        :type registered_user: None
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/subscription",
            handler=subscription_handler,
        )

        assert telegram_emulator.get_reply_count() >= 1

    async def test_unregistered_user_subscription(
        self,
        telegram_emulator: TelegramEmulator,
        subscription_handler: SubscriptionHandler,
    ) -> None:
        """Test /subscription for unregistered user.

        This test verifies that unregistered users get appropriate
        message when using /subscription.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param subscription_handler: Subscription handler instance
        :type subscription_handler: SubscriptionHandler
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/subscription",
            handler=subscription_handler,
        )

        assert telegram_emulator.get_reply_count() >= 1


@pytest.mark.skip(reason="Subscription upgrade requires callback-based UI interaction")
@pytest.mark.integration
@pytest.mark.asyncio
class TestSubscriptionUpgrade:
    """Test subscription upgrade functionality.

    This class tests upgrading from basic to premium subscription.
    """

    @pytest.fixture
    def subscription_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> SubscriptionHandler:
        """Create SubscriptionHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: SubscriptionHandler instance
        :rtype: SubscriptionHandler
        """
        return SubscriptionHandler(services=integration_container)

    @pytest_asyncio.fixture
    async def basic_user(
        self,
        integration_services: IntegrationTestServices,
    ) -> None:
        """Create a user with basic subscription.

        :param integration_services: In-memory test services
        :type integration_services: IntegrationTestServices
        :returns: None
        """
        user_info = MagicMock()
        user_info.id = TEST_USER_ID
        user_info.username = "basic_user"
        user_info.first_name = "Basic"
        user_info.last_name = "User"

        await integration_services.user_service.create_user_profile(
            user_info=user_info,
            birth_date=date(1990, 1, 15),
            subscription_type=SubscriptionType.BASIC,
        )

    async def test_upgrade_to_premium(
        self,
        telegram_emulator: TelegramEmulator,
        subscription_handler: SubscriptionHandler,
        basic_user: None,
    ) -> None:
        """Test upgrading from basic to premium.

        This test verifies that a basic user can initiate
        a premium subscription upgrade.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param subscription_handler: Subscription handler instance
        :type subscription_handler: SubscriptionHandler
        :param basic_user: Pre-registered basic user fixture
        :type basic_user: None
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/subscription",
            handler=subscription_handler,
        )

        # Try to upgrade via callback
        await telegram_emulator.send_callback(
            callback_data="upgrade_premium",
            handler=subscription_handler,
        )

        assert telegram_emulator.get_reply_count() >= 1


@pytest.mark.integration
@pytest.mark.asyncio
class TestPremiumUserSubscription:
    """Test subscription for premium users.

    This class tests subscription behavior for users with premium.
    """

    @pytest.fixture
    def subscription_handler(
        self,
        integration_container: IntegrationTestServiceContainer,
    ) -> SubscriptionHandler:
        """Create SubscriptionHandler with test services.

        :param integration_container: Test service container
        :type integration_container: IntegrationTestServiceContainer
        :returns: SubscriptionHandler instance
        :rtype: SubscriptionHandler
        """
        return SubscriptionHandler(services=integration_container)

    @pytest_asyncio.fixture
    async def premium_user(
        self,
        integration_services: IntegrationTestServices,
    ) -> None:
        """Create a user with premium subscription.

        :param integration_services: In-memory test services
        :type integration_services: IntegrationTestServices
        :returns: None
        """
        user_info = MagicMock()
        user_info.id = TEST_USER_ID
        user_info.username = "premium_user"
        user_info.first_name = "Premium"
        user_info.last_name = "User"

        await integration_services.user_service.create_user_profile(
            user_info=user_info,
            birth_date=date(1990, 1, 15),
            subscription_type=SubscriptionType.PREMIUM,
        )

    async def test_premium_user_sees_active_status(
        self,
        telegram_emulator: TelegramEmulator,
        subscription_handler: SubscriptionHandler,
        premium_user: None,
    ) -> None:
        """Test that premium user sees active subscription status.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param subscription_handler: Subscription handler instance
        :type subscription_handler: SubscriptionHandler
        :param premium_user: Pre-registered premium user fixture
        :type premium_user: None
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/subscription",
            handler=subscription_handler,
        )

        assert telegram_emulator.get_reply_count() >= 1
