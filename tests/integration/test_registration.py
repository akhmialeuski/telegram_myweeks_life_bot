"""Integration tests for user registration flow.

This module tests the complete user registration flow using the real
database and actual handlers. Only Telegram API calls are mocked.

Test Scenarios:
    - New user registration flow (happy path)
    - Invalid birth date handling (format, future date, old date)
    - Existing user welcome back
    - Unsupported date formats (DD-MM-YYYY, ISO)
"""

from datetime import date
from unittest.mock import MagicMock

import pytest

from src.bot.handlers.start_handler import StartHandler
from src.services.container import ServiceContainer
from tests.integration.conftest import (
    TEST_FIRST_NAME,
    TEST_LAST_NAME,
    TEST_USER_ID,
    TEST_USERNAME,
    get_reply_text,
    set_message_text,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserRegistrationFlow:
    """Integration tests for the complete user registration flow.

    These tests verify the end-to-end registration process including:
    - Welcome message delivery for new users
    - Birth date input validation and persistence
    - User profile creation with correct data mapping
    - Response message content verification
    - Error handling for invalid inputs
    """

    async def test_start_command_new_user_receives_welcome_and_birth_date_prompt(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that /start command sends welcome message with birth date prompt.

        Preconditions:
            - User is not registered (no profile in database)
            - User has valid Telegram account with first_name

        Test Steps:
            1. User sends /start command
               Expected: Bot responds with personalized welcome message
               Response: Contains user's first name and birth date input prompt

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        """
        # --- ARRANGE ---
        # Create handler instance with test service container
        handler = StartHandler(services=test_service_container)
        # Configure mock update with /start command
        set_message_text(mock_update=mock_update, text="/start")

        # --- ACT: STEP 1 - User sends /start command ---
        await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT: STEP 1 - Verify welcome message ---
        # Bot should respond exactly once
        mock_update.message.reply_text.assert_called_once()

        # Extract and verify response message content
        reply_text = get_reply_text(mock_message=mock_update.message)
        assert reply_text is not None, "Reply text should not be None"
        assert len(reply_text) > 0, "Reply text should not be empty"

        # Welcome message should contain user's first name (personalization)
        assert (
            TEST_FIRST_NAME in reply_text
        ), f"Welcome message should contain user's first name '{TEST_FIRST_NAME}'"

    async def test_valid_birth_date_creates_profile_and_sends_confirmation(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test complete registration flow with valid birth date.

        Preconditions:
            - User is not registered (no profile in database)
            - User has valid Telegram account

        Test Steps:
            1. User sends /start command
               Expected: Bot responds with welcome message and birth date prompt
               Response: Personalized greeting with date format instructions

            2. User sends valid birth date "15.03.1990" (DD.MM.YYYY format)
               Expected: Bot creates user profile in database
               Expected: Bot responds with registration success confirmation
               Response: Confirmation message with life statistics

        Post-conditions:
            - User profile exists in database with correct data
            - Birth date is stored as 1990-03-15

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        """
        # --- ARRANGE ---
        handler = StartHandler(services=test_service_container)
        birth_date_str = "15.03.1990"
        expected_birth_date = date(1990, 3, 15)

        # --- ACT: STEP 1 - User sends /start command ---
        set_message_text(mock_update=mock_update, text="/start")
        await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT: STEP 1 - Verify welcome message ---
        mock_update.message.reply_text.assert_called_once()
        welcome_text = get_reply_text(mock_message=mock_update.message)
        assert welcome_text is not None, "Welcome message should be sent"

        # Reset mock to track next response separately
        mock_update.message.reply_text.reset_mock()

        # --- ACT: STEP 2 - User sends valid birth date ---
        set_message_text(mock_update=mock_update, text=birth_date_str)
        await handler.handle_birth_date_input(
            update=mock_update,
            context=mock_context,
        )

        # --- ASSERT: STEP 2 - Verify confirmation message ---
        mock_update.message.reply_text.assert_called_once()
        confirmation_text = get_reply_text(mock_message=mock_update.message)
        assert confirmation_text is not None, "Confirmation message should be sent"
        assert len(confirmation_text) > 0, "Confirmation message should not be empty"

        # --- ASSERT: Post-conditions - Verify database state ---
        profile = await test_service_container.user_service.get_user_profile(
            telegram_id=TEST_USER_ID
        )

        # Profile should exist with correct data
        assert profile is not None, "User profile should be created in database"
        assert profile.telegram_id == TEST_USER_ID, "Telegram ID should match"
        assert profile.username == TEST_USERNAME, "Username should match"
        assert profile.first_name == TEST_FIRST_NAME, "First name should match"
        assert profile.last_name == TEST_LAST_NAME, "Last name should match"

        # Settings should contain birth date
        assert profile.settings is not None, "User settings should be created"
        assert (
            profile.settings.birth_date == expected_birth_date
        ), f"Birth date should be {expected_birth_date}"

    async def test_invalid_birth_date_format_shows_error_no_profile_created(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that invalid birth date format shows error and doesn't create profile.

        Preconditions:
            - User is not registered (no profile in database)

        Test Steps:
            1. User sends /start command
               Expected: Bot responds with welcome message
               Response: Birth date input prompt

            2. User sends invalid text "not-a-date" (non-date string)
               Expected: Bot rejects input and shows error message
               Expected: No profile is created in database
               Response: Error message explaining correct date format

        Post-conditions:
            - No user profile in database

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        """
        # --- ARRANGE ---
        handler = StartHandler(services=test_service_container)
        invalid_date = "not-a-date"

        # --- ACT: STEP 1 - User sends /start command ---
        set_message_text(mock_update=mock_update, text="/start")
        await handler.handle(update=mock_update, context=mock_context)
        mock_update.message.reply_text.reset_mock()

        # --- ACT: STEP 2 - User sends invalid birth date ---
        set_message_text(mock_update=mock_update, text=invalid_date)
        await handler.handle_birth_date_input(
            update=mock_update,
            context=mock_context,
        )

        # --- ASSERT: STEP 2 - Verify error message ---
        mock_update.message.reply_text.assert_called_once()
        error_text = get_reply_text(mock_message=mock_update.message)
        assert error_text is not None, "Error message should be sent"
        assert len(error_text) > 0, "Error message should not be empty"

        # --- ASSERT: Post-conditions - No profile created ---
        profile = await test_service_container.user_service.get_user_profile(
            telegram_id=TEST_USER_ID
        )
        assert profile is None, "No profile should be created for invalid input"

    async def test_future_birth_date_shows_error_no_profile_created(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that future birth date is rejected.

        Preconditions:
            - User is not registered (no profile in database)

        Test Steps:
            1. User sends /start command
               Expected: Bot responds with welcome message
               Response: Birth date input prompt

            2. User sends future date "01.01.2100"
               Expected: Bot rejects input (date is in the future)
               Expected: No profile is created
               Response: Error message about invalid date

        Post-conditions:
            - No user profile in database

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        """
        # --- ARRANGE ---
        handler = StartHandler(services=test_service_container)
        future_date = "01.01.2100"

        # --- ACT: STEP 1 - User sends /start command ---
        set_message_text(mock_update=mock_update, text="/start")
        await handler.handle(update=mock_update, context=mock_context)
        mock_update.message.reply_text.reset_mock()

        # --- ACT: STEP 2 - User sends future birth date ---
        set_message_text(mock_update=mock_update, text=future_date)
        await handler.handle_birth_date_input(
            update=mock_update,
            context=mock_context,
        )

        # --- ASSERT: STEP 2 - Verify error message ---
        mock_update.message.reply_text.assert_called_once()
        error_text = get_reply_text(mock_message=mock_update.message)
        assert error_text is not None, "Error message should be sent for future date"

        # --- ASSERT: Post-conditions - No profile created ---
        profile = await test_service_container.user_service.get_user_profile(
            telegram_id=TEST_USER_ID
        )
        assert profile is None, "No profile should be created for future birth date"

    async def test_very_old_birth_date_shows_error_no_profile_created(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that unrealistically old birth date is rejected.

        Preconditions:
            - User is not registered (no profile in database)

        Test Steps:
            1. User sends /start command
               Expected: Bot responds with welcome message
               Response: Birth date input prompt

            2. User sends very old date "01.01.1800" (over 200 years ago)
               Expected: Bot rejects input (unrealistic age)
               Expected: No profile is created
               Response: Error message about invalid date

        Post-conditions:
            - No user profile in database

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        """
        # --- ARRANGE ---
        handler = StartHandler(services=test_service_container)
        very_old_date = "01.01.1800"

        # --- ACT: STEP 1 - User sends /start command ---
        set_message_text(mock_update=mock_update, text="/start")
        await handler.handle(update=mock_update, context=mock_context)
        mock_update.message.reply_text.reset_mock()

        # --- ACT: STEP 2 - User sends very old birth date ---
        set_message_text(mock_update=mock_update, text=very_old_date)
        await handler.handle_birth_date_input(
            update=mock_update,
            context=mock_context,
        )

        # --- ASSERT: STEP 2 - Verify error message ---
        mock_update.message.reply_text.assert_called_once()
        error_text = get_reply_text(mock_message=mock_update.message)
        assert error_text is not None, "Error message should be sent for very old date"

        # --- ASSERT: Post-conditions - No profile created ---
        profile = await test_service_container.user_service.get_user_profile(
            telegram_id=TEST_USER_ID
        )
        assert profile is None, "No profile should be created for unrealistic date"

    async def test_existing_user_receives_welcome_back_message(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
        mock_telegram_user: MagicMock,
    ) -> None:
        """Test that existing registered users receive welcome back message.

        Preconditions:
            - User already has profile in database (registered previously)
            - User has birth date set to 1990-01-01

        Test Steps:
            1. User sends /start command
               Expected: Bot recognizes existing user
               Expected: Bot sends welcome back message (not registration flow)
               Response: Welcome back message (different from new user flow)

        Post-conditions:
            - User profile unchanged (birth date still 1990-01-01)

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :param mock_telegram_user: Mock Telegram User object
        :type mock_telegram_user: MagicMock
        :returns: None
        """
        # --- ARRANGE: Create existing user profile (precondition) ---
        existing_birth_date = date(1990, 1, 1)
        await test_service_container.user_service.create_user_profile(
            user_info=mock_telegram_user,
            birth_date=existing_birth_date,
        )

        # Verify precondition - profile exists
        profile_before = await test_service_container.user_service.get_user_profile(
            telegram_id=TEST_USER_ID
        )
        assert profile_before is not None, "Precondition: Profile should exist"

        handler = StartHandler(services=test_service_container)

        # --- ACT: STEP 1 - Existing user sends /start ---
        set_message_text(mock_update=mock_update, text="/start")
        await handler.handle(update=mock_update, context=mock_context)

        # --- ASSERT: STEP 1 - Verify welcome back message ---
        mock_update.message.reply_text.assert_called_once()
        welcome_back_text = get_reply_text(mock_message=mock_update.message)
        assert welcome_back_text is not None, "Welcome back message should be sent"
        assert len(welcome_back_text) > 0, "Welcome back message should not be empty"

        # --- ASSERT: Post-conditions - Profile unchanged ---
        profile_after = await test_service_container.user_service.get_user_profile(
            telegram_id=TEST_USER_ID
        )
        assert profile_after is not None, "Profile should still exist"
        assert (
            profile_after.settings.birth_date == existing_birth_date
        ), "Birth date should remain unchanged"

    async def test_unsupported_date_format_dashes_shows_error(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that unsupported date format with dashes is rejected.

        NOTE: Bot only supports DD.MM.YYYY format. DD-MM-YYYY is NOT supported.

        Preconditions:
            - User is not registered (no profile in database)

        Test Steps:
            1. User sends /start command
               Expected: Bot responds with welcome message
               Response: Birth date input prompt

            2. User sends date with dashes "25-12-1985" (unsupported format)
               Expected: Bot rejects input (wrong format)
               Expected: No profile is created
               Response: Error message explaining correct format

        Post-conditions:
            - No user profile in database

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        """
        # --- ARRANGE ---
        handler = StartHandler(services=test_service_container)
        unsupported_format_date = "25-12-1985"  # Dashes not supported

        # --- ACT: STEP 1 - /start command ---
        set_message_text(mock_update=mock_update, text="/start")
        await handler.handle(update=mock_update, context=mock_context)
        mock_update.message.reply_text.reset_mock()

        # --- ACT: STEP 2 - Enter date in unsupported format ---
        set_message_text(mock_update=mock_update, text=unsupported_format_date)
        await handler.handle_birth_date_input(
            update=mock_update,
            context=mock_context,
        )

        # --- ASSERT: STEP 2 - Error message sent ---
        mock_update.message.reply_text.assert_called_once()
        error_text = get_reply_text(mock_message=mock_update.message)
        assert error_text is not None, "Error message should be sent"

        # --- ASSERT: Post-conditions - No profile created ---
        profile = await test_service_container.user_service.get_user_profile(
            telegram_id=TEST_USER_ID
        )
        assert profile is None, "No profile should be created for unsupported format"

    async def test_unsupported_iso_date_format_shows_error(
        self,
        test_service_container: ServiceContainer,
        mock_update: MagicMock,
        mock_context: MagicMock,
    ) -> None:
        """Test that ISO date format YYYY-MM-DD is rejected.

        NOTE: Bot only supports DD.MM.YYYY format. ISO format is NOT supported.

        Preconditions:
            - User is not registered (no profile in database)

        Test Steps:
            1. User sends /start command
               Expected: Bot responds with welcome message
               Response: Birth date input prompt

            2. User sends date in ISO format "1985-12-25" (unsupported)
               Expected: Bot rejects input (wrong format)
               Expected: No profile is created
               Response: Error message explaining correct format

        Post-conditions:
            - No user profile in database

        :param test_service_container: ServiceContainer with test database
        :type test_service_container: ServiceContainer
        :param mock_update: Mock Telegram Update object
        :type mock_update: MagicMock
        :param mock_context: Mock Telegram Context object
        :type mock_context: MagicMock
        :returns: None
        """
        # --- ARRANGE ---
        handler = StartHandler(services=test_service_container)
        iso_format_date = "1985-12-25"  # ISO format not supported

        # --- ACT: STEP 1 - /start command ---
        set_message_text(mock_update=mock_update, text="/start")
        await handler.handle(update=mock_update, context=mock_context)
        mock_update.message.reply_text.reset_mock()

        # --- ACT: STEP 2 - Enter date in ISO format ---
        set_message_text(mock_update=mock_update, text=iso_format_date)
        await handler.handle_birth_date_input(
            update=mock_update,
            context=mock_context,
        )

        # --- ASSERT: STEP 2 - Error message sent ---
        mock_update.message.reply_text.assert_called_once()
        error_text = get_reply_text(mock_message=mock_update.message)
        assert error_text is not None, "Error message should be sent"

        # --- ASSERT: Post-conditions - No profile created ---
        profile = await test_service_container.user_service.get_user_profile(
            telegram_id=TEST_USER_ID
        )
        assert profile is None, "No profile should be created for ISO format"
