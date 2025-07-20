"""Common test fixtures and configuration for all tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from telegram import Update
from telegram.ext import Application, ContextTypes

from src.bot.application import LifeWeeksBot
from src.core.enums import WeekDay
from src.utils.localization import SupportedLanguage

# --- Test Constants ---
TEST_USER_ID = 123456789
TEST_JOB_ID = f"weekly_notification_user_{TEST_USER_ID}"
TEST_MESSAGE = "Test weekly message"
DB_ERROR = "Database error"
SCHEDULER_ERROR = "Scheduler error"


# --- Common Fixtures ---


@pytest.fixture
def mock_app() -> MagicMock:
    """Provides a mocked instance of telegram.ext.Application.

    :returns: Mocked Application instance with AsyncMock bot
    :rtype: MagicMock
    """
    app = MagicMock(spec=Application)
    app.bot = AsyncMock()
    return app


@pytest.fixture
def mock_user_with_settings() -> MagicMock:
    """Provides a mocked user object with complete notification settings.

    :returns: Mocked user with valid notification settings
    :rtype: MagicMock
    """
    user = MagicMock()
    user.telegram_id = TEST_USER_ID
    user.settings = MagicMock()
    user.settings.notifications = True
    user.settings.notifications_day = WeekDay.MONDAY
    user.settings.notifications_time = MagicMock(hour=10, minute=30)
    user.first_name = "Test"
    user.username = "testuser"
    user.settings.language = SupportedLanguage.EN
    return user


@pytest.fixture
def mock_user_without_settings() -> MagicMock:
    """Provides a mocked user object without settings.

    :returns: Mocked user without settings
    :rtype: MagicMock
    """
    user = MagicMock()
    user.telegram_id = TEST_USER_ID
    user.settings = None
    return user


@pytest.fixture
def mock_scheduler() -> MagicMock:
    """Provides a mocked instance of the scheduler.

    :returns: Mocked scheduler instance
    :rtype: MagicMock
    """
    return MagicMock()


@pytest.fixture
def mock_globals(mocker: MockerFixture) -> dict[str, MagicMock]:
    """Mocks the global scheduler and application instances and returns them.

    This fixture is used for testing scheduler management functions that rely on
    global _scheduler_instance and _application_instance variables.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: A dictionary containing the mocked scheduler and application
    :rtype: dict[str, MagicMock]
    """
    mock_scheduler = MagicMock()
    mock_app = MagicMock()
    mocker.patch("src.bot.scheduler._scheduler_instance", mock_scheduler)
    mocker.patch("src.bot.scheduler._application_instance", mock_app)
    return {"scheduler": mock_scheduler, "app": mock_app}


@pytest.fixture
def mock_application_logger(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked logger for testing application logging functionality.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked logger instance for application module
    :rtype: MagicMock
    """
    return mocker.patch("src.bot.application.logger")


@pytest.fixture
def mock_scheduler_logger(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked logger for testing scheduler logging functionality.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked logger instance for scheduler module
    :rtype: MagicMock
    """
    return mocker.patch("src.bot.scheduler.logger")


@pytest.fixture
def mock_user_service(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked user_service for testing database operations.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked user_service instance
    :rtype: MagicMock
    """
    return mocker.patch("src.bot.scheduler.user_service")


@pytest.fixture
def mock_start_handler_user_service(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked user_service for start handler testing.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked user_service instance for start handler
    :rtype: MagicMock
    """
    return mocker.patch("src.bot.handlers.start_handler.user_service")


@pytest.fixture
def mock_base_handler_user_service(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked user_service for base handler testing.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked user_service instance for base handler
    :rtype: MagicMock
    """
    return mocker.patch("src.bot.handlers.base_handler.user_service")


@pytest.fixture
def mock_generate_message(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked generate_message_week function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked generate_message_week function
    :rtype: MagicMock
    """
    return mocker.patch(
        "src.bot.scheduler.generate_message_week", return_value=TEST_MESSAGE
    )


@pytest.fixture
def bot() -> "LifeWeeksBot":
    """Provides a fresh LifeWeeksBot instance for each test.

    :returns: LifeWeeksBot instance for testing
    :rtype: LifeWeeksBot
    """
    from src.bot.application import LifeWeeksBot

    return LifeWeeksBot()


@pytest.fixture
def mock_application_builder(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked Application.builder() chain for testing bot setup.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked Application.builder() chain
    :rtype: MagicMock
    """
    mock_app_class = mocker.patch("src.bot.application.Application")
    mock_app = MagicMock(spec=Application)
    mock_app_class.builder.return_value.token.return_value.build.return_value = mock_app
    return mock_app


@pytest.fixture
def mock_handlers(mocker: MockerFixture) -> dict:
    """Provides test handlers configuration for testing handler registration.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Test handlers configuration
    :rtype: dict
    """
    handler_instance = MagicMock(handle=MagicMock())
    return {
        "test_cmd": {
            "class": lambda: handler_instance,
            "callbacks": [],
            "message_handler": True,
        }
    }


@pytest.fixture
def mock_scheduler_setup_error(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked scheduler setup that raises SchedulerSetupError.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked scheduler setup function that raises error
    :rtype: MagicMock
    """
    from src.bot.scheduler import SchedulerSetupError

    return mocker.patch(
        "src.bot.application.setup_user_notification_schedules",
        side_effect=SchedulerSetupError("Test error"),
    )


@pytest.fixture
def mock_start_scheduler(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked start_scheduler function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked start_scheduler function
    :rtype: MagicMock
    """
    return mocker.patch("src.bot.application.start_scheduler")


@pytest.fixture
def mock_stop_scheduler(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked stop_scheduler function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked stop_scheduler function
    :rtype: MagicMock
    """
    return mocker.patch("src.bot.application.stop_scheduler")


@pytest.fixture
def mock_setup_user_notification_schedules(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked setup_user_notification_schedules function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked setup_user_notification_schedules function
    :rtype: MagicMock
    """
    return mocker.patch("src.bot.application.setup_user_notification_schedules")


@pytest.fixture
def mock_update() -> MagicMock:
    """Create mock Update object for testing handlers.

    :returns: Mock Update object with required attributes
    :rtype: MagicMock
    """
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock()
    update.effective_user.id = TEST_USER_ID
    update.effective_user.username = "testuser"
    update.effective_user.first_name = "Test"
    update.effective_user.last_name = "User"
    update.effective_user.language_code = "en"
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.message.reply_photo = AsyncMock()
    return update


@pytest.fixture
def mock_context() -> MagicMock:
    """Create mock ContextTypes object for testing handlers.

    :returns: Mock ContextTypes object with user_data
    :rtype: MagicMock
    """
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    return context


@pytest.fixture
def mock_generate_message_help(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked generate_message_help function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked generate_message_help function
    :rtype: MagicMock
    """
    return mocker.patch("src.core.messages.generate_message_help")


@pytest.fixture
def mock_generate_message_cancel_success(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked generate_message_cancel_success function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked generate_message_cancel_success function
    :rtype: MagicMock
    """
    return mocker.patch("src.core.messages.generate_message_cancel_success")


@pytest.fixture
def mock_generate_message_cancel_error(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked generate_message_cancel_error function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked generate_message_cancel_error function
    :rtype: MagicMock
    """
    return mocker.patch("src.core.messages.generate_message_cancel_error")


@pytest.fixture
def mock_remove_user_from_scheduler(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked remove_user_from_scheduler function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked remove_user_from_scheduler function
    :rtype: MagicMock
    """
    return mocker.patch("src.bot.scheduler.remove_user_from_scheduler")


@pytest.fixture
def mock_get_user_language(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked get_user_language function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked get_user_language function
    :rtype: MagicMock
    """
    return mocker.patch("src.bot.handlers.base_handler.get_user_language")


@pytest.fixture
def mock_get_message(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked get_message function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked get_message function
    :rtype: MagicMock
    """
    return mocker.patch("src.bot.handlers.base_handler.get_message")


@pytest.fixture
def mock_user_profile() -> MagicMock:
    """Provides a mock user profile for testing.

    :returns: Mock user profile with basic attributes
    :rtype: MagicMock
    """
    user = MagicMock()
    user.telegram_id = TEST_USER_ID
    user.birth_date = "15.03.1990"
    user.language = "en"
    user.life_expectancy = 80
    user.subscription_type = "basic"
    return user


@pytest.fixture
def mock_premium_user_profile() -> MagicMock:
    """Provides a mock premium user profile for testing.

    :returns: Mock premium user profile with premium attributes
    :rtype: MagicMock
    """
    user = MagicMock()
    user.telegram_id = TEST_USER_ID
    user.birth_date = "15.03.1990"
    user.language = "en"
    user.life_expectancy = 80
    user.subscription_type = "premium"
    return user


@pytest.fixture
def mock_generate_message_unknown_command(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked generate_message_unknown_command function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked generate_message_unknown_command function
    :rtype: MagicMock
    """
    return mocker.patch(
        "src.bot.handlers.unknown_handler.generate_message_unknown_command"
    )


# --- Start Handler Fixtures ---


@pytest.fixture
def mock_generate_message_start_welcome_existing(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked generate_message_start_welcome_existing function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked generate_message_start_welcome_existing function
    :rtype: MagicMock
    """
    return mocker.patch(
        "src.bot.handlers.start_handler.generate_message_start_welcome_existing"
    )


@pytest.fixture
def mock_generate_message_start_welcome_new(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked generate_message_start_welcome_new function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked generate_message_start_welcome_new function
    :rtype: MagicMock
    """
    return mocker.patch(
        "src.bot.handlers.start_handler.generate_message_start_welcome_new"
    )


@pytest.fixture
def mock_generate_message_birth_date_future_error(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked generate_message_birth_date_future_error function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked generate_message_birth_date_future_error function
    :rtype: MagicMock
    """
    return mocker.patch(
        "src.bot.handlers.start_handler.generate_message_birth_date_future_error"
    )


@pytest.fixture
def mock_generate_message_birth_date_old_error(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked generate_message_birth_date_old_error function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked generate_message_birth_date_old_error function
    :rtype: MagicMock
    """
    return mocker.patch(
        "src.bot.handlers.start_handler.generate_message_birth_date_old_error"
    )


@pytest.fixture
def mock_generate_message_birth_date_format_error(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked generate_message_birth_date_format_error function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked generate_message_birth_date_format_error function
    :rtype: MagicMock
    """
    return mocker.patch(
        "src.bot.handlers.start_handler.generate_message_birth_date_format_error"
    )


@pytest.fixture
def mock_generate_message_registration_error(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked generate_message_registration_error function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked generate_message_registration_error function
    :rtype: MagicMock
    """
    return mocker.patch(
        "src.bot.handlers.start_handler.generate_message_registration_error"
    )


@pytest.fixture
def mock_add_user_to_scheduler(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked add_user_to_scheduler function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked add_user_to_scheduler function
    :rtype: MagicMock
    """
    return mocker.patch("src.bot.handlers.start_handler.add_user_to_scheduler")


# --- Weeks Handler Fixtures ---


@pytest.fixture
def mock_generate_message_week(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked generate_message_week function.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked generate_message_week function
    :rtype: MagicMock
    """
    return mocker.patch("src.bot.handlers.weeks_handler.generate_message_week")
