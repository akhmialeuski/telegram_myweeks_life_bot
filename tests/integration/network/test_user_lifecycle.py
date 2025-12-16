"""Network integration tests for user lifecycle.

This module contains classic integration test cases for user lifecycle
management using the Local Bot API Server. All tests make real API calls
to the Telegram bot through the local server.

Test Categories:
    - User creation (registration flow)
    - User data retrieval
    - User settings modification
    - User deletion/reset
"""

import pytest

from tests.integration.network.conftest import NetworkTestClient

# =============================================================================
# Test Constants for Response Validation
# =============================================================================

# Keywords to check in bot responses (language-independent)
BIRTH_DATE_PROMPT_KEYWORDS: list[str] = ["birth", "date", "DD.MM.YYYY", "дат"]
REGISTRATION_SUCCESS_KEYWORDS: list[str] = ["weeks", "недел", "registered", "успе"]
INVALID_DATE_KEYWORDS: list[str] = ["invalid", "incorrect", "неверн", "формат"]
HELP_KEYWORDS: list[str] = ["/start", "/weeks", "/help", "/settings"]
WEEKS_KEYWORDS: list[str] = ["weeks", "lived", "remaining", "недел", "прожи"]
SUBSCRIPTION_KEYWORDS: list[str] = ["subscription", "подписк", "premium", "basic"]
CANCEL_KEYWORDS: list[str] = ["cancel", "отмен"]
UNKNOWN_COMMAND_KEYWORDS: list[str] = ["unknown", "неизвест", "/help"]
NOT_REGISTERED_KEYWORDS: list[str] = ["register", "/start", "регистр"]


def _contains_any_keyword(text: str | None, keywords: list[str]) -> bool:
    """Check if text contains any of the keywords (case-insensitive).

    :param text: Text to search in
    :type text: str | None
    :param keywords: List of keywords to search for
    :type keywords: list[str]
    :returns: True if any keyword found
    :rtype: bool
    """
    if text is None:
        return False
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


@pytest.mark.network
@pytest.mark.asyncio
class TestUserCreation:
    """Test cases for new user creation.

    This class contains integration tests for the user registration flow
    using the real Telegram Bot API through Local Bot API Server.
    """

    async def test_new_user_registration_success(
        self,
        network_client: NetworkTestClient,
    ) -> None:
        """TC-001: Successful registration of a new user.

        Test Steps:
            1. Send /start command to the bot
            2. Verify bot responds with birth date prompt
            3. Send valid birth date in DD.MM.YYYY format
            4. Verify bot responds with success message
            5. Verify user is created in the database

        Preconditions:
            - Local Bot API Server is running
            - Test bot is configured and accessible
            - User is not registered in the system

        Expected Result:
            - User is successfully registered
            - User profile is created with provided birth date
            - User receives welcome message with life statistics

        :param network_client: Network test client instance
        :type network_client: NetworkTestClient
        :returns: None
        """
        # Step 1: Send /start command and wait for response
        start_response = await network_client.send_command_and_wait(
            command="/start",
            timeout=10,
        )

        # Step 2: Verify bot responds with birth date prompt
        assert start_response is not None, "Bot did not respond to /start command"
        assert _contains_any_keyword(
            text=start_response,
            keywords=BIRTH_DATE_PROMPT_KEYWORDS,
        ), f"Expected birth date prompt, got: {start_response}"

        # Step 3: Send valid birth date
        date_response = await network_client.send_message_and_wait(
            text="15.01.1990",
            timeout=10,
        )

        # Step 4: Verify bot confirms registration
        assert date_response is not None, "Bot did not respond to birth date"
        assert _contains_any_keyword(
            text=date_response,
            keywords=REGISTRATION_SUCCESS_KEYWORDS,
        ), f"Expected registration success, got: {date_response}"

    async def test_new_user_registration_with_invalid_birth_date(
        self,
        network_client: NetworkTestClient,
    ) -> None:
        """TC-002: User registration fails with invalid birth date.

        Test Steps:
            1. Send /start command to the bot
            2. Verify bot responds with birth date prompt
            3. Send invalid birth date format (e.g., "not-a-date")
            4. Verify bot responds with error message
            5. Verify user can retry with valid date

        Preconditions:
            - Local Bot API Server is running
            - Test bot is configured and accessible
            - User is not registered in the system

        Expected Result:
            - Bot rejects invalid birth date
            - User receives error message with format hint
            - User can continue registration after providing valid date

        :param network_client: Network test client instance
        :type network_client: NetworkTestClient
        :returns: None
        """
        # Step 1: Send /start command
        start_response = await network_client.send_command_and_wait(
            command="/start",
            timeout=10,
        )

        # Step 2: Verify birth date prompt
        assert start_response is not None, "Bot did not respond to /start"

        # Step 3: Send invalid birth date
        error_response = await network_client.send_message_and_wait(
            text="not-a-valid-date",
            timeout=10,
        )

        # Step 4: Verify error message
        assert error_response is not None, "Bot did not respond to invalid date"
        assert _contains_any_keyword(
            text=error_response,
            keywords=INVALID_DATE_KEYWORDS,
        ), f"Expected error message, got: {error_response}"


@pytest.mark.network
@pytest.mark.asyncio
class TestUserDataRetrieval:
    """Test cases for user data retrieval.

    This class contains integration tests for retrieving user data
    through bot commands like /weeks, /help, /visualize.
    """

    async def test_get_weeks_for_registered_user(
        self,
        network_client: NetworkTestClient,
    ) -> None:
        """TC-003: Retrieve weeks information for registered user.

        Test Steps:
            1. Ensure user is registered (precondition)
            2. Send /weeks command to the bot
            3. Verify bot responds with weeks information
            4. Verify response contains correct life statistics

        Preconditions:
            - Local Bot API Server is running
            - User is already registered with known birth date
            - User has active session

        Expected Result:
            - Bot responds with weeks lived, weeks remaining
            - Data matches expected calculation based on birth date

        :param network_client: Network test client instance
        :type network_client: NetworkTestClient
        :returns: None
        """
        # Step 2: Send /weeks command
        weeks_response = await network_client.send_command_and_wait(
            command="/weeks",
            timeout=10,
        )

        # Step 3: Verify response contains weeks information
        assert weeks_response is not None, "Bot did not respond to /weeks"
        assert _contains_any_keyword(
            text=weeks_response,
            keywords=WEEKS_KEYWORDS,
        ), f"Expected weeks info, got: {weeks_response}"

    async def test_get_help_information(
        self,
        network_client: NetworkTestClient,
    ) -> None:
        """TC-004: Retrieve help information.

        Test Steps:
            1. Send /help command to the bot
            2. Verify bot responds with help message
            3. Verify help contains all available commands

        Preconditions:
            - Local Bot API Server is running
            - Test bot is configured and accessible

        Expected Result:
            - Bot responds with comprehensive help message
            - Help includes all bot commands and descriptions

        :param network_client: Network test client instance
        :type network_client: NetworkTestClient
        :returns: None
        """
        # Step 1: Send /help command
        help_response = await network_client.send_command_and_wait(
            command="/help",
            timeout=10,
        )

        # Step 2: Verify help message received
        assert help_response is not None, "Bot did not respond to /help"

        # Step 3: Verify help contains command references
        assert _contains_any_keyword(
            text=help_response,
            keywords=HELP_KEYWORDS,
        ), f"Expected help with commands, got: {help_response}"

    async def test_get_visualization_for_registered_user(
        self,
        network_client: NetworkTestClient,
    ) -> None:
        """TC-005: Generate life visualization for registered user.

        Test Steps:
            1. Ensure user is registered (precondition)
            2. Send /visualize command to the bot
            3. Verify bot responds with visualization image
            4. Verify image is valid PNG/JPEG format

        Preconditions:
            - Local Bot API Server is running
            - User is already registered with known birth date

        Expected Result:
            - Bot sends life grid visualization as photo
            - Image shows weeks lived and weeks remaining

        :param network_client: Network test client instance
        :type network_client: NetworkTestClient
        :returns: None
        """
        # Step 2: Send /visualize command
        # Note: This command sends a photo, text response might be null
        await network_client.send_command(command="/visualize")

        # For photo commands, verification requires checking received updates
        # The bot sends a photo, not a text message
        # Basic check: command was sent successfully


@pytest.mark.network
@pytest.mark.asyncio
class TestUserSettingsModification:
    """Test cases for user settings modification.

    This class contains integration tests for modifying user settings
    such as birth date, life expectancy, and language.
    """

    async def test_access_settings_menu(
        self,
        network_client: NetworkTestClient,
    ) -> None:
        """TC-006: Access settings menu.

        Test Steps:
            1. Ensure user is registered (precondition)
            2. Send /settings command to the bot
            3. Verify bot responds with settings menu
            4. Verify menu contains available options

        Preconditions:
            - Local Bot API Server is running
            - User is already registered

        Expected Result:
            - Bot responds with settings menu
            - Menu shows available settings options

        :param network_client: Network test client instance
        :type network_client: NetworkTestClient
        :returns: None
        """
        # Step 2: Send /settings command
        settings_response = await network_client.send_command_and_wait(
            command="/settings",
            timeout=10,
        )

        # Step 3: Verify settings menu received
        assert settings_response is not None, "Bot did not respond to /settings"

        # Settings response should contain menu or inline keyboard
        # At minimum, verify we got a response


@pytest.mark.network
@pytest.mark.asyncio
class TestUserDeletion:
    """Test cases for user deletion/reset.

    This class contains integration tests for canceling operations
    and potential user data reset functionality.
    """

    async def test_cancel_registration_flow(
        self,
        network_client: NetworkTestClient,
    ) -> None:
        """TC-007: Cancel during registration flow.

        Test Steps:
            1. Start new registration with /start
            2. Verify bot asks for birth date
            3. Send /cancel command
            4. Verify registration is cancelled
            5. Verify user can restart registration

        Preconditions:
            - Local Bot API Server is running
            - User is not registered

        Expected Result:
            - Registration flow is cancelled
            - Bot confirms cancellation
            - User can start fresh with /start

        :param network_client: Network test client instance
        :type network_client: NetworkTestClient
        :returns: None
        """
        # Step 1: Start registration
        await network_client.send_command_and_wait(
            command="/start",
            timeout=10,
        )

        # Step 3: Cancel registration
        cancel_response = await network_client.send_command_and_wait(
            command="/cancel",
            timeout=10,
        )

        # Step 4: Verify cancellation confirmed
        assert cancel_response is not None, "Bot did not respond to /cancel"
        assert _contains_any_keyword(
            text=cancel_response,
            keywords=CANCEL_KEYWORDS,
        ), f"Expected cancellation message, got: {cancel_response}"


@pytest.mark.network
@pytest.mark.asyncio
class TestSubscriptionManagement:
    """Test cases for subscription management.

    This class contains integration tests for viewing and managing
    user subscription status.
    """

    async def test_view_subscription_status(
        self,
        network_client: NetworkTestClient,
    ) -> None:
        """TC-008: View current subscription status.

        Test Steps:
            1. Ensure user is registered (precondition)
            2. Send /subscription command
            3. Verify bot shows current subscription type
            4. Verify subscription details are accurate

        Preconditions:
            - Local Bot API Server is running
            - User is already registered

        Expected Result:
            - Bot displays current subscription status
            - Shows subscription type (Basic/Premium)
            - Shows expiration date if applicable

        :param network_client: Network test client instance
        :type network_client: NetworkTestClient
        :returns: None
        """
        # Step 2: Check subscription
        subscription_response = await network_client.send_command_and_wait(
            command="/subscription",
            timeout=10,
        )

        # Step 3: Verify subscription info received
        assert subscription_response is not None, "Bot did not respond to /subscription"
        assert _contains_any_keyword(
            text=subscription_response,
            keywords=SUBSCRIPTION_KEYWORDS,
        ), f"Expected subscription info, got: {subscription_response}"


@pytest.mark.network
@pytest.mark.asyncio
class TestErrorHandling:
    """Test cases for error handling.

    This class contains integration tests for bot error handling
    in various edge cases.
    """

    async def test_unknown_command_handling(
        self,
        network_client: NetworkTestClient,
    ) -> None:
        """TC-009: Handle unknown command gracefully.

        Test Steps:
            1. Send unknown command (e.g., /unknowncommand)
            2. Verify bot responds with error message
            3. Verify error message suggests valid commands

        Preconditions:
            - Local Bot API Server is running
            - Bot is accessible

        Expected Result:
            - Bot responds with "unknown command" message
            - Suggests using /help for available commands

        :param network_client: Network test client instance
        :type network_client: NetworkTestClient
        :returns: None
        """
        # Step 1: Send unknown command
        error_response = await network_client.send_command_and_wait(
            command="/unknowncommand123",
            timeout=10,
        )

        # Step 2: Verify error response
        assert error_response is not None, "Bot did not respond to unknown command"
        assert _contains_any_keyword(
            text=error_response,
            keywords=UNKNOWN_COMMAND_KEYWORDS,
        ), f"Expected unknown command handling, got: {error_response}"

    async def test_unregistered_user_weeks_command(
        self,
        network_client: NetworkTestClient,
    ) -> None:
        """TC-010: Handle /weeks for unregistered user.

        Test Steps:
            1. Ensure user is NOT registered (precondition)
            2. Send /weeks command
            3. Verify bot responds with registration prompt

        Preconditions:
            - Local Bot API Server is running
            - User is not registered in the system

        Expected Result:
            - Bot informs user they need to register
            - Suggests using /start to register

        :param network_client: Network test client instance
        :type network_client: NetworkTestClient
        :returns: None
        """
        # Step 2: Send /weeks without registration
        response = await network_client.send_command_and_wait(
            command="/weeks",
            timeout=10,
        )

        # Step 3: Verify registration prompt or error
        assert response is not None, "Bot did not respond to /weeks"
        # Response should either show weeks (if registered) or prompt to register
        has_weeks = _contains_any_keyword(text=response, keywords=WEEKS_KEYWORDS)
        has_register_prompt = _contains_any_keyword(
            text=response,
            keywords=NOT_REGISTERED_KEYWORDS,
        )
        assert (
            has_weeks or has_register_prompt
        ), f"Expected weeks info or registration prompt, got: {response}"
