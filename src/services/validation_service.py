"""Validation service for centralized user input validation.

This module provides a centralized validation service that handles all user
input validation, returning structured results instead of throwing exceptions.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from src.utils.config import (
    MAX_LIFE_EXPECTANCY,
    MIN_BIRTH_YEAR,
    MIN_LIFE_EXPECTANCY,
)

# Error keys for localization
ERROR_INVALID_DATE_FORMAT = "invalid_date_format"
ERROR_DATE_IN_FUTURE = "date_in_future"
ERROR_DATE_TOO_OLD = "date_too_old"
ERROR_INVALID_NUMBER = "invalid_number"
ERROR_OUT_OF_RANGE = "out_of_range"
ERROR_VALUE_TOO_LOW = "value_too_low"
ERROR_VALUE_TOO_HIGH = "value_too_high"


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationResult:
    """Result of input validation.

    Immutable data structure containing validation result with optional
    parsed value and error key for localization.

    :ivar is_valid: Whether the input passed validation
    :type is_valid: bool
    :ivar value: Parsed value if validation succeeded, None otherwise
    :type value: Any
    :ivar error_key: Error message key for localization if validation failed
    :type error_key: str | None
    """

    is_valid: bool
    value: Any = None
    error_key: str | None = None

    @classmethod
    def success(cls, value: Any) -> "ValidationResult":
        """Create a successful validation result.

        :param value: The validated and parsed value
        :type value: Any
        :returns: Successful validation result
        :rtype: ValidationResult
        """
        return cls(is_valid=True, value=value, error_key=None)

    @classmethod
    def failure(cls, error_key: str) -> "ValidationResult":
        """Create a failed validation result.

        :param error_key: Error message key for localization
        :type error_key: str
        :returns: Failed validation result
        :rtype: ValidationResult
        """
        return cls(is_valid=False, value=None, error_key=error_key)


class ValidationService:
    """Centralized validation for all user inputs.

    Returns structured results instead of throwing exceptions,
    allowing handlers to respond with localized error messages.
    """

    def validate_birth_date(self, input_str: str) -> ValidationResult:
        """Validate birth date input.

        Accepts DD.MM.YYYY format and validates:
        - Date format is correct
        - Date is not in the future
        - Date is not before MIN_BIRTH_YEAR (1900)

        :param input_str: User input string
        :type input_str: str
        :returns: Validation result with parsed date or error key
        :rtype: ValidationResult
        """
        # Parse date from user input (DD.MM.YYYY format)
        try:
            parsed_date = datetime.strptime(input_str.strip(), "%d.%m.%Y").date()
        except ValueError:
            return ValidationResult.failure(error_key=ERROR_INVALID_DATE_FORMAT)

        # Validate that birth date is not in the future
        if parsed_date > date.today():
            return ValidationResult.failure(error_key=ERROR_DATE_IN_FUTURE)

        # Validate that birth date is not unreasonably old
        if parsed_date.year < MIN_BIRTH_YEAR:
            return ValidationResult.failure(error_key=ERROR_DATE_TOO_OLD)

        return ValidationResult.success(value=parsed_date)

    def validate_life_expectancy(self, input_str: str) -> ValidationResult:
        """Validate life expectancy input.

        Validates:
        - Input is a valid integer
        - Value is within MIN_LIFE_EXPECTANCY to MAX_LIFE_EXPECTANCY range

        :param input_str: User input string
        :type input_str: str
        :returns: Validation result with parsed integer or error key
        :rtype: ValidationResult
        """
        try:
            value = int(input_str.strip())
        except ValueError:
            return ValidationResult.failure(error_key=ERROR_INVALID_NUMBER)

        if value < MIN_LIFE_EXPECTANCY:
            return ValidationResult.failure(error_key=ERROR_VALUE_TOO_LOW)

        if value > MAX_LIFE_EXPECTANCY:
            return ValidationResult.failure(error_key=ERROR_VALUE_TOO_HIGH)

        return ValidationResult.success(value=value)
