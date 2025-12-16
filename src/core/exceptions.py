"""Core exceptions for the application.

This module defines the base exception class and specific exceptions
for the application, ensuring consistent error handling.
"""

from typing import Optional


class BotError(Exception):
    """Base class for all bot exceptions.

    :ivar message: Error message for logging
    :type message: str
    :ivar user_message_key: Localized message key for user
    :type user_message_key: Optional[str]
    """

    def __init__(self, message: str, user_message_key: Optional[str] = None) -> None:
        """Initialize exception.

        :param message: Internal error message
        :type message: str
        :param user_message_key: Key for localized user message
        :type user_message_key: Optional[str]
        """
        super().__init__(message)
        self.message = message
        self.user_message_key = user_message_key


class ValidationError(BotError):
    """Exception raised for validation errors.

    :ivar error_key: Validation error key
    :type error_key: str
    """

    def __init__(self, message: str, error_key: str) -> None:
        """Initialize validation error.

        :param message: Internal error message
        :type message: str
        :param error_key: Validation error key
        :type error_key: str
        """
        super().__init__(message, user_message_key=error_key)
        self.error_key = error_key


class ServiceError(BotError):
    """Exception raised for service layer errors."""

    pass
