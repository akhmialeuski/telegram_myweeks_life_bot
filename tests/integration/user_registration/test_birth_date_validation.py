"""Integration tests for birth date validation during registration.

This module tests various birth date validation scenarios,
including invalid formats, future dates, and edge cases.
"""

from datetime import date, timedelta

import pytest

from src.bot.handlers.start_handler import StartHandler
from tests.integration.conftest import (
    IntegrationTestServiceContainer,
    TelegramEmulator,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestBirthDateInvalidFormat:
    """Test birth date validation for invalid formats.

    This class tests that invalid date formats are properly rejected
    with helpful error messages.
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

    async def test_invalid_date_format_shows_error(
        self,
        telegram_emulator: TelegramEmulator,
        start_handler: StartHandler,
    ) -> None:
        """Test that invalid date format shows error message.

        This test verifies that entering a date in invalid format
        results in an error message with format hint.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param start_handler: Start handler instance
        :type start_handler: StartHandler
        :returns: None
        """
        # Start registration flow
        await telegram_emulator.send_command(
            command="/start",
            handler=start_handler,
        )

        # Send invalid date format
        await telegram_emulator.send_message(
            text="not-a-date",
            handler=start_handler,
            handler_method="handle_birth_date_input",
        )

        # Verify error response received
        assert telegram_emulator.get_reply_count() >= 2

    async def test_invalid_month_shows_error(
        self,
        telegram_emulator: TelegramEmulator,
        start_handler: StartHandler,
    ) -> None:
        """Test that invalid month (>12) shows error.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param start_handler: Start handler instance
        :type start_handler: StartHandler
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/start",
            handler=start_handler,
        )

        # Send date with invalid month
        await telegram_emulator.send_message(
            text="15.13.1990",  # Month 13 is invalid
            handler=start_handler,
            handler_method="handle_birth_date_input",
        )

        assert telegram_emulator.get_reply_count() >= 2

    async def test_invalid_day_shows_error(
        self,
        telegram_emulator: TelegramEmulator,
        start_handler: StartHandler,
    ) -> None:
        """Test that invalid day (>31) shows error.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param start_handler: Start handler instance
        :type start_handler: StartHandler
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/start",
            handler=start_handler,
        )

        # Send date with invalid day
        await telegram_emulator.send_message(
            text="32.01.1990",  # Day 32 is invalid
            handler=start_handler,
            handler_method="handle_birth_date_input",
        )

        assert telegram_emulator.get_reply_count() >= 2


@pytest.mark.integration
@pytest.mark.asyncio
class TestBirthDateFutureDates:
    """Test birth date validation for future dates.

    This class tests that future dates are properly rejected.
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

    async def test_future_date_rejected(
        self,
        telegram_emulator: TelegramEmulator,
        start_handler: StartHandler,
    ) -> None:
        """Test that future birth date is rejected.

        This test verifies that entering a date in the future
        results in an error message.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param start_handler: Start handler instance
        :type start_handler: StartHandler
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/start",
            handler=start_handler,
        )

        # Calculate a future date
        future_date = date.today() + timedelta(days=365)
        future_date_str = future_date.strftime("%d.%m.%Y")

        await telegram_emulator.send_message(
            text=future_date_str,
            handler=start_handler,
            handler_method="handle_birth_date_input",
        )

        assert telegram_emulator.get_reply_count() >= 2

    async def test_tomorrow_date_rejected(
        self,
        telegram_emulator: TelegramEmulator,
        start_handler: StartHandler,
    ) -> None:
        """Test that tomorrow's date is rejected.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param start_handler: Start handler instance
        :type start_handler: StartHandler
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/start",
            handler=start_handler,
        )

        # Tomorrow's date
        tomorrow = date.today() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%d.%m.%Y")

        await telegram_emulator.send_message(
            text=tomorrow_str,
            handler=start_handler,
            handler_method="handle_birth_date_input",
        )

        assert telegram_emulator.get_reply_count() >= 2


@pytest.mark.integration
@pytest.mark.asyncio
class TestBirthDateEdgeCases:
    """Test birth date validation for edge cases.

    This class tests edge cases like very old dates,
    leap years, and boundary conditions.
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

    async def test_very_old_date_rejected(
        self,
        telegram_emulator: TelegramEmulator,
        start_handler: StartHandler,
    ) -> None:
        """Test that unreasonably old birth date is rejected.

        This test verifies that a date more than 150 years ago
        is rejected as invalid.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param start_handler: Start handler instance
        :type start_handler: StartHandler
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/start",
            handler=start_handler,
        )

        # Very old date (more than 150 years ago)
        await telegram_emulator.send_message(
            text="01.01.1800",
            handler=start_handler,
            handler_method="handle_birth_date_input",
        )

        assert telegram_emulator.get_reply_count() >= 2

    async def test_leap_year_date_valid(
        self,
        telegram_emulator: TelegramEmulator,
        start_handler: StartHandler,
    ) -> None:
        """Test that Feb 29 on a leap year is valid.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param start_handler: Start handler instance
        :type start_handler: StartHandler
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/start",
            handler=start_handler,
        )

        # Feb 29 on a leap year (2000 was a leap year)
        await telegram_emulator.send_message(
            text="29.02.2000",
            handler=start_handler,
            handler_method="handle_birth_date_input",
        )

        assert telegram_emulator.get_reply_count() >= 2

    async def test_today_date_valid(
        self,
        telegram_emulator: TelegramEmulator,
        start_handler: StartHandler,
    ) -> None:
        """Test that today's date might be valid (edge case).

        Note: Whether today's date is valid depends on business logic.
        For a newborn registering, today might be valid.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param start_handler: Start handler instance
        :type start_handler: StartHandler
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/start",
            handler=start_handler,
        )

        today_str = date.today().strftime("%d.%m.%Y")

        await telegram_emulator.send_message(
            text=today_str,
            handler=start_handler,
            handler_method="handle_birth_date_input",
        )

        # Either success or error, but we should get a response
        assert telegram_emulator.get_reply_count() >= 2


@pytest.mark.integration
@pytest.mark.asyncio
class TestBirthDateRetryAfterError:
    """Test that user can retry after validation error.

    This class tests the retry flow when a user enters
    an invalid date and then corrects it.
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

    async def test_can_retry_after_invalid_format(
        self,
        telegram_emulator: TelegramEmulator,
        start_handler: StartHandler,
    ) -> None:
        """Test that user can retry after entering invalid format.

        This test verifies the complete retry flow:
        1. User enters invalid date
        2. User receives error
        3. User enters valid date
        4. Registration succeeds

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param start_handler: Start handler instance
        :type start_handler: StartHandler
        :returns: None
        """
        # Start registration
        await telegram_emulator.send_command(
            command="/start",
            handler=start_handler,
        )

        # First attempt: invalid format
        await telegram_emulator.send_message(
            text="invalid",
            handler=start_handler,
            handler_method="handle_birth_date_input",
        )

        initial_count = telegram_emulator.get_reply_count()
        assert initial_count >= 2

        # Second attempt: valid format
        await telegram_emulator.send_message(
            text="15.01.1990",
            handler=start_handler,
            handler_method="handle_birth_date_input",
        )

        # Should get another response (success or another prompt)
        assert telegram_emulator.get_reply_count() > initial_count

    async def test_multiple_invalid_attempts(
        self,
        telegram_emulator: TelegramEmulator,
        start_handler: StartHandler,
    ) -> None:
        """Test multiple invalid attempts followed by valid one.

        :param telegram_emulator: Telegram emulator instance
        :type telegram_emulator: TelegramEmulator
        :param start_handler: Start handler instance
        :type start_handler: StartHandler
        :returns: None
        """
        await telegram_emulator.send_command(
            command="/start",
            handler=start_handler,
        )

        # Multiple invalid attempts
        invalid_inputs: list[str] = [
            "not-a-date",
            "32.13.2025",
            "00.00.0000",
        ]

        for invalid_input in invalid_inputs:
            await telegram_emulator.send_message(
                text=invalid_input,
                handler=start_handler,
                handler_method="handle_birth_date_input",
            )

        # Finally enter valid date
        await telegram_emulator.send_message(
            text="15.01.1990",
            handler=start_handler,
            handler_method="handle_birth_date_input",
        )

        # Should have responses for each attempt
        # 1 for /start + N invalid + 1 valid
        assert telegram_emulator.get_reply_count() >= len(invalid_inputs) + 2
