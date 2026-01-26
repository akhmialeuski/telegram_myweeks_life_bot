"""Unit tests for test fake implementations.

Tests the InMemoryUserRepository, FakeUserService, and FakeNotificationGateway
to ensure they correctly implement the protocol contracts.
"""

from datetime import date

import pytest

from tests.fakes import (
    FakeNotificationGateway,
    FakeUserService,
    InMemoryUserRepository,
)


class TestInMemoryUserRepository:
    """Test suite for InMemoryUserRepository.

    Tests the in-memory implementation of user data storage
    used for testing without database dependencies.
    """

    def test_create_and_get_user(self) -> None:
        """Test creating and retrieving a user.

        This test verifies that users can be created and retrieved
        from the in-memory repository.
        """
        from src.database.models.user import User

        repo = InMemoryUserRepository()
        user = User(
            telegram_id=12345,
            username="testuser",
            first_name="Test",
            last_name="User",
        )

        result = repo.create_user(user=user)
        assert result is True

        retrieved = repo.get_user(telegram_id=12345)
        assert retrieved is not None
        assert retrieved.telegram_id == 12345
        assert retrieved.username == "testuser"

    def test_get_nonexistent_user_returns_none(self) -> None:
        """Test that getting a nonexistent user returns None.

        This test verifies proper handling of missing users.
        """
        repo = InMemoryUserRepository()

        result = repo.get_user(telegram_id=99999)
        assert result is None

    def test_delete_user(self) -> None:
        """Test deleting a user.

        This test verifies that users can be removed from the repository.
        """
        repo = InMemoryUserRepository()
        repo.seed_user(telegram_id=12345)

        result = repo.delete_user(telegram_id=12345)
        assert result is True

        retrieved = repo.get_user(telegram_id=12345)
        assert retrieved is None

    def test_delete_nonexistent_user_returns_false(self) -> None:
        """Test that deleting a nonexistent user returns False.

        This test verifies proper handling of delete operations
        on missing users.
        """
        repo = InMemoryUserRepository()

        result = repo.delete_user(telegram_id=99999)
        assert result is False

    def test_seed_user_creates_user(self) -> None:
        """Test the seed_user convenience method.

        This test verifies that seed_user properly creates
        a test user with default values.
        """
        repo = InMemoryUserRepository()

        user = repo.seed_user(telegram_id=12345)

        assert user is not None
        assert user.telegram_id == 12345
        assert user.username == "testuser"

    def test_clear_removes_all_users(self) -> None:
        """Test that clear removes all stored users.

        This test verifies the clear method for test isolation.
        """
        repo = InMemoryUserRepository()
        repo.seed_user(telegram_id=1)
        repo.seed_user(telegram_id=2)

        repo.clear()

        assert repo.get_user(telegram_id=1) is None
        assert repo.get_user(telegram_id=2) is None


class TestFakeUserService:
    """Test suite for FakeUserService.

    Tests the fake user service implementation to ensure
    it correctly implements UserServiceProtocol.
    """

    @pytest.mark.asyncio
    async def test_create_user_profile(self) -> None:
        """Test creating a user profile.

        This test verifies that user profiles can be created
        with all required data.
        """

        class MockUserInfo:
            id = 12345
            username = "testuser"
            first_name = "Test"
            last_name = "User"

        service = FakeUserService()
        user = await service.create_user_profile(
            user_info=MockUserInfo(),
            birth_date=date(1990, 1, 15),
        )

        assert user is not None
        assert user.telegram_id == 12345
        assert user.settings is not None
        assert user.settings.birth_date == date(1990, 1, 15)

    @pytest.mark.asyncio
    async def test_is_valid_user_profile(self) -> None:
        """Test checking if user profile is valid.

        This test verifies that is_valid_user_profile correctly
        identifies valid and invalid profiles.
        """

        class MockUserInfo:
            id = 12345
            username = "testuser"
            first_name = "Test"
            last_name = "User"

        service = FakeUserService()

        # Before creating profile
        assert await service.is_valid_user_profile(telegram_id=12345) is False

        # After creating profile
        await service.create_user_profile(
            user_info=MockUserInfo(),
            birth_date=date(1990, 1, 15),
        )
        assert await service.is_valid_user_profile(telegram_id=12345) is True

    @pytest.mark.asyncio
    async def test_delete_user_profile(self) -> None:
        """Test deleting a user profile.

        This test verifies that user profiles can be deleted.
        """

        class MockUserInfo:
            id = 12345
            username = "testuser"
            first_name = "Test"
            last_name = "User"

        service = FakeUserService()
        await service.create_user_profile(
            user_info=MockUserInfo(),
            birth_date=date(1990, 1, 15),
        )

        await service.delete_user_profile(telegram_id=12345)

        assert await service.is_valid_user_profile(telegram_id=12345) is False


class TestFakeNotificationGateway:
    """Test suite for FakeNotificationGateway.

    Tests the fake notification gateway to ensure it properly
    records sent messages for test verification.
    """

    @pytest.mark.asyncio
    async def test_send_message_records_message(self) -> None:
        """Test that send_message records the message.

        This test verifies that sent messages are recorded
        for later verification in tests.
        """
        gateway = FakeNotificationGateway()

        result = await gateway.send_message(
            recipient_id=12345,
            message="Hello, World!",
        )

        assert result is True
        assert len(gateway.sent_messages) == 1
        assert gateway.sent_messages[0] == (12345, "Hello, World!")

    @pytest.mark.asyncio
    async def test_send_photo_records_photo(self) -> None:
        """Test that send_photo records the photo.

        This test verifies that sent photos are recorded
        for later verification in tests.
        """
        gateway = FakeNotificationGateway()

        result = await gateway.send_photo(
            recipient_id=12345,
            photo=b"photo_data",
            caption="Test photo",
        )

        assert result is True
        assert len(gateway.sent_photos) == 1
        assert gateway.sent_photos[0] == (12345, b"photo_data", "Test photo")

    @pytest.mark.asyncio
    async def test_set_should_fail_causes_failures(self) -> None:
        """Test that set_should_fail causes send operations to fail.

        This test verifies the failure simulation functionality
        for error handling tests.
        """
        gateway = FakeNotificationGateway()
        gateway.set_should_fail(should_fail=True)

        result = await gateway.send_message(
            recipient_id=12345,
            message="Hello",
        )

        assert result is False
        assert len(gateway.sent_messages) == 0

    def test_get_messages_for_recipient(self) -> None:
        """Test filtering messages by recipient.

        This test verifies that messages can be filtered
        by recipient ID for targeted assertions.
        """
        gateway = FakeNotificationGateway()
        gateway.sent_messages.append((1, "Message to 1"))
        gateway.sent_messages.append((2, "Message to 2"))
        gateway.sent_messages.append((1, "Another to 1"))

        messages = gateway.get_messages_for_recipient(recipient_id=1)

        assert len(messages) == 2
        assert "Message to 1" in messages
        assert "Another to 1" in messages

    def test_clear_removes_all_messages(self) -> None:
        """Test that clear removes all recorded messages.

        This test verifies the clear method for test isolation.
        """
        gateway = FakeNotificationGateway()
        gateway.sent_messages.append((1, "Message"))
        gateway.sent_photos.append((1, b"photo", None))

        gateway.clear()

        assert len(gateway.sent_messages) == 0
        assert len(gateway.sent_photos) == 0
