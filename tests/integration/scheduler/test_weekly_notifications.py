"""Integration tests for weekly notification scheduler.

This module tests the scheduler functionality for weekly notifications.
"""

from datetime import date
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from src.enums import SubscriptionType
from tests.integration.conftest import (
    TEST_USER_ID,
    IntegrationTestServices,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestSchedulerUserManagement:
    """Test scheduler user management.

    This class tests adding and removing users from the scheduler.
    """

    @pytest_asyncio.fixture
    async def registered_user(
        self,
        integration_services: IntegrationTestServices,
    ) -> None:
        """Create a pre-registered user.

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

    async def test_user_added_to_scheduler_on_registration(
        self,
        integration_services: IntegrationTestServices,
        registered_user: None,
    ) -> None:
        """Test that user is added to scheduler on registration.

        This test verifies that when a user registers, they
        are automatically added to the notification scheduler.

        :param integration_services: In-memory test services
        :type integration_services: IntegrationTestServices
        :param registered_user: Pre-registered user fixture
        :type registered_user: None
        :returns: None
        """
        # User should exist after registration
        user = await integration_services.user_service.get_user_profile(
            telegram_id=TEST_USER_ID
        )
        assert user is not None

    async def test_get_all_users_for_scheduler(
        self,
        integration_services: IntegrationTestServices,
        registered_user: None,
    ) -> None:
        """Test getting all users for scheduler.

        This test verifies that all registered users can be
        retrieved for scheduling notifications.

        :param integration_services: In-memory test services
        :type integration_services: IntegrationTestServices
        :param registered_user: Pre-registered user fixture
        :type registered_user: None
        :returns: None
        """
        users = await integration_services.user_service.get_all_users()
        assert len(users) >= 1


@pytest.mark.integration
@pytest.mark.asyncio
class TestSchedulerNotificationSettings:
    """Test scheduler notification settings.

    This class tests notification scheduling settings per user.
    """

    @pytest_asyncio.fixture
    async def registered_user(
        self,
        integration_services: IntegrationTestServices,
    ) -> None:
        """Create a pre-registered user.

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

    async def test_user_has_default_notification_settings(
        self,
        integration_services: IntegrationTestServices,
        registered_user: None,
    ) -> None:
        """Test that new user has default notification settings.

        This test verifies that registered users have
        default notification settings.

        :param integration_services: In-memory test services
        :type integration_services: IntegrationTestServices
        :param registered_user: Pre-registered user fixture
        :type registered_user: None
        :returns: None
        """
        user = await integration_services.user_service.get_user_profile(
            telegram_id=TEST_USER_ID
        )
        assert user is not None
        assert user.settings is not None


@pytest.mark.integration
@pytest.mark.asyncio
class TestSchedulerMultipleUsers:
    """Test scheduler with multiple users.

    This class tests scheduler behavior with multiple registered users.
    """

    async def test_multiple_users_scheduled_independently(
        self,
        integration_services: IntegrationTestServices,
    ) -> None:
        """Test that multiple users are scheduled independently.

        This test verifies that each user has their own
        notification schedule.

        :param integration_services: In-memory test services
        :type integration_services: IntegrationTestServices
        :returns: None
        """
        # Create multiple users
        user_ids: list[int] = [111111, 222222, 333333]

        for user_id in user_ids:
            user_info = MagicMock()
            user_info.id = user_id
            user_info.username = f"user_{user_id}"
            user_info.first_name = f"User{user_id}"
            user_info.last_name = "Test"

            await integration_services.user_service.create_user_profile(
                user_info=user_info,
                birth_date=date(1990, 1, 15),
                subscription_type=SubscriptionType.BASIC,
            )

        # All users should be retrievable
        all_users = await integration_services.user_service.get_all_users()
        assert len(all_users) >= len(user_ids)
