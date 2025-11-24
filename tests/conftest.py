"""Common test fixtures and configuration for all tests."""

# Ensure compatibility alias for legacy import paths in some modules
import sys
import types
from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update
from telegram.ext import Application, ContextTypes

import src.core.life_calculator as _lc
from src.bot.application import LifeWeeksBot
from src.constants import (
    DEFAULT_LIFE_EXPECTANCY,
    DEFAULT_NOTIFICATIONS_DAY,
    DEFAULT_NOTIFICATIONS_ENABLED,
    DEFAULT_NOTIFICATIONS_TIME,
    DEFAULT_TIMEZONE,
    DEFAULT_USER_FIRST_NAME,
)
from src.core.enums import SubscriptionType, SupportedLanguage, WeekDay

sys.modules.setdefault("core", types.ModuleType("core"))
sys.modules["core.life_calculator"] = _lc
# Alias missing class name used by some modules
setattr(_lc, "LifeCalculator", _lc.LifeCalculatorEngine)


class MockerFixture:
    """Lightweight substitute for the pytest-mock fixture."""

    MagicMock = MagicMock
    AsyncMock = AsyncMock

    def __init__(self) -> None:
        """Initialize patch tracking list."""
        self._patches: list[Any] = []

    def patch(self, target: str, *args, **kwargs):
        """Patch target and register cleanup."""
        p = patch(target, *args, **kwargs)
        mocked = p.start()
        self._patches.append(p)
        return mocked


@pytest.fixture
def mocker() -> Iterator[MockerFixture]:
    """Provide a minimal mocker fixture compatible with pytest-mock."""
    fixture = MockerFixture()
    yield fixture
    for p in fixture._patches:
        p.stop()


# --- Test Constants ---

# Re-export production defaults for use in tests
__all__ = [
    "DEFAULT_LIFE_EXPECTANCY",
    "DEFAULT_NOTIFICATIONS_DAY",
    "DEFAULT_NOTIFICATIONS_ENABLED",
    "DEFAULT_NOTIFICATIONS_TIME",
    "DEFAULT_TIMEZONE",
    "DEFAULT_USER_FIRST_NAME",
    "WeekDay",
    "SubscriptionType",
    "SupportedLanguage",
]

# Test user IDs
TEST_USER_ID = 123456789
TEST_USER_ID_ALT = 987654321
TEST_USER_ID_NONEXISTENT = 999999

# Test numeric values
TEST_LIFE_EXPECTANCY_ALT = 85
TEST_BIRTH_YEAR = 1990
TEST_BIRTH_MONTH = 3
TEST_BIRTH_DAY = 15

# Test string values
TEST_USERNAME = "testuser"
TEST_USERNAME_ALT = "testuser2"
TEST_FIRST_NAME = "Test"
TEST_FIRST_NAME_ALT = "Test2"
TEST_LAST_NAME = "User"
TEST_LAST_NAME_ALT = "User2"
TEST_TIMEZONE_EST = "EST"

# Test scheduler and message values
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
    """Mocks the global scheduler instance and returns it.

    This fixture is used for testing scheduler management functions that rely on
    global _global_scheduler_instance variable.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: A dictionary containing the mocked scheduler components
    :rtype: dict[str, MagicMock]
    """
    # Create mock for the APScheduler inside NotificationScheduler
    mock_apscheduler = MagicMock()

    # Create mock for NotificationScheduler instance
    mock_scheduler_instance = MagicMock()
    mock_scheduler_instance.scheduler = mock_apscheduler

    mocker.patch(
        "src.bot.scheduler._global_scheduler_instance", mock_scheduler_instance
    )
    return {"scheduler": mock_apscheduler, "instance": mock_scheduler_instance}


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


# These fixtures are no longer needed as we use FakeServiceContainer
# @pytest.fixture
# def mock_start_handler_user_service(mocker: MockerFixture) -> MagicMock:
#     """Provides a mocked user_service for start handler testing.

#     :param mocker: Pytest mocker fixture
#     :type mocker: MockerFixture
#     :returns: Mocked user_service instance for start handler
#     :rtype: MagicMock
#     """
#     return mocker.patch("src.bot.handlers.start_handler.user_service")


# @pytest.fixture
# def mock_base_handler_user_service(mocker: MockerFixture) -> MagicMock:
#     """Provides a mocked user_service for base handler testing.

#     :param mocker: Pytest mocker fixture
#     :type mocker: MockerFixture
#     :returns: Mocked user_service instance for base handler
#     :rtype: MagicMock
#     """
#     return mocker.patch("src.bot.handlers.base_handler.user_service")


@pytest.fixture
def mock_generate_message(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked WeeksMessages.generate function for scheduler tests."""
    return mocker.patch(
        "src.bot.scheduler.WeeksMessages.generate", return_value=TEST_MESSAGE
    )


@pytest.fixture
def bot() -> LifeWeeksBot:
    """Provides a fresh LifeWeeksBot instance for each test.

    :returns: LifeWeeksBot instance for testing
    :rtype: LifeWeeksBot
    """
    return LifeWeeksBot()


@pytest.fixture
def mock_application_builder(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked Application.builder() chain for testing bot setup.

    The builder chain supports post_init() method for registering callbacks.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :returns: Mocked Application.builder() chain
    :rtype: MagicMock
    """
    mock_app_class = mocker.patch("src.bot.application.Application")
    mock_app = MagicMock(spec=Application)
    mock_builder_chain = MagicMock()
    mock_builder_chain.token.return_value = mock_builder_chain
    mock_builder_chain.post_init.return_value = mock_builder_chain
    mock_builder_chain.build.return_value = mock_app
    mock_app_class.builder.return_value = mock_builder_chain
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
            "class": lambda services=None: handler_instance,
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
    update.effective_user.language_code = SupportedLanguage.EN.value
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
def make_mock_user_profile():
    """Provides a factory for creating mock user profiles.

    :returns: Factory function for creating mock user profiles
    :rtype: function
    """

    def _make(subscription_type: SubscriptionType):
        """Create a mock user profile with the given subscription type.

        :param subscription_type: Subscription type
        :type subscription_type: SubscriptionType
        :returns: Mock user profile with the given subscription type
        :rtype: MagicMock
        """
        mock_user = MagicMock()
        mock_user.subscription.subscription_type = subscription_type.value
        return mock_user

    return _make


@pytest.fixture
def mock_user_profile() -> MagicMock:
    """Provides a mock user profile for testing.

    :returns: Mock user profile with basic attributes
    :rtype: MagicMock
    """
    user = MagicMock()
    user.telegram_id = TEST_USER_ID
    user.birth_date = "15.03.1990"
    user.language = SupportedLanguage.EN.value
    user.life_expectancy = DEFAULT_LIFE_EXPECTANCY
    user.subscription_type = SubscriptionType.BASIC
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
    user.language = SupportedLanguage.EN.value
    user.life_expectancy = DEFAULT_LIFE_EXPECTANCY
    user.subscription_type = SubscriptionType.PREMIUM
    return user


@pytest.fixture
def mock_update_with_callback() -> MagicMock:
    """Create mock Update object with callback query for testing.

    :returns: Mock Update object with callback query
    :rtype: MagicMock
    """
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = TEST_USER_ID
    update.effective_user.username = "testuser"
    update.effective_user.first_name = "Test"
    update.effective_user.language_code = SupportedLanguage.EN.value
    update.callback_query = MagicMock()
    update.callback_query.data = "settings_birth_date"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    return update
