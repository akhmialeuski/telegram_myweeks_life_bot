"""Integration tests package.

This package contains integration tests organized by functionality:
- user_registration: User registration flows (/start, birth date input)
- settings: User settings management
- data_retrieval: Data retrieval commands (/weeks, /visualize, /help)
- subscription: Subscription management
- scheduler: Scheduler functionality
- error_handling: Error scenarios and /cancel flow
- network: Network tests with real Telegram API (via Local Bot API Server)

Running tests:
    # Run all mock-based integration tests (fast)
    pytest tests/integration/ -m "integration and not network" -v

    # Run network tests (requires Local Bot API Server)
    pytest tests/integration/network/ -m network -v
"""

from .conftest import (
    IntegrationTestServiceContainer,
    IntegrationTestServices,
    TelegramEmulator,
    integration_container,
    integration_services,
    mock_telegram_user,
    registered_user,
    telegram_emulator,
)

__all__: list[str] = [
    "IntegrationTestServiceContainer",
    "IntegrationTestServices",
    "TelegramEmulator",
    "integration_container",
    "integration_services",
    "mock_telegram_user",
    "registered_user",
    "telegram_emulator",
]
