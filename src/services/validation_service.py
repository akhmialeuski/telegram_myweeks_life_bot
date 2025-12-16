"""Validation service for centralized user input validation.

This module provides a centralized validation service that handles all user
input validation using Pydantic models from the core logic.
"""

from datetime import date

from pydantic import ValidationError

from src.core.exceptions import ValidationError as CoreValidationError
from src.core.validation import (
    ERROR_DATE_IN_FUTURE,
    ERROR_DATE_TOO_OLD,
    ERROR_INVALID_DATE_FORMAT,
    ERROR_INVALID_NUMBER,
    ERROR_VALUE_TOO_HIGH,
    ERROR_VALUE_TOO_LOW,
    BirthDateInput,
    LifeExpectancyInput,
)


class ValidationService:
    """Centralized validation for all user inputs.

    Raises CoreValidationError with specific error keys for localization.
    """

    def validate_birth_date(self, input_str: str) -> date:
        """Validate birth date input.

        Uses Pydantic model to validate format and logical constraints.

        :param input_str: User input string (expected DD.MM.YYYY)
        :type input_str: str
        :returns: Validated birth date object
        :rtype: date
        :raises CoreValidationError: If validation fails
        """
        try:
            # Pydantic model handles parsing and validation
            model = BirthDateInput(birth_date=input_str)
            return model.birth_date

        except ValidationError as error:
            # Map Pydantic errors to our error keys
            for err in error.errors():
                msg = err.get("msg", "")
                if ERROR_DATE_IN_FUTURE in msg:
                    raise CoreValidationError(
                        message="Birth date is in the future",
                        error_key=ERROR_DATE_IN_FUTURE,
                    ) from error
                if ERROR_DATE_TOO_OLD in msg:
                    raise CoreValidationError(
                        message="Birth date is too old",
                        error_key=ERROR_DATE_TOO_OLD,
                    ) from error
                if ERROR_INVALID_DATE_FORMAT in msg:
                    raise CoreValidationError(
                        message="Invalid date format",
                        error_key=ERROR_INVALID_DATE_FORMAT,
                    ) from error

            # Default fallback
            raise CoreValidationError(
                message="Invalid birth date", error_key=ERROR_INVALID_DATE_FORMAT
            ) from error

        except ValueError as error:
            # Should be caught by Pydantic, but just in case
            raise CoreValidationError(
                message="Invalid date format", error_key=ERROR_INVALID_DATE_FORMAT
            ) from error

    def validate_life_expectancy(self, input_str: str) -> int:
        """Validate life expectancy input.

        Uses Pydantic model to validate type and range constraints.

        :param input_str: User input string
        :type input_str: str
        :returns: Validated life expectancy integer
        :rtype: int
        :raises CoreValidationError: If validation fails
        """
        try:
            # Pydantic handles type coercion (str -> int) and validation
            model = LifeExpectancyInput(life_expectancy=input_str)
            return model.life_expectancy

        except ValidationError as error:
            # Map Pydantic errors to our error keys
            for err in error.errors():
                msg = err.get("msg", "")
                if ERROR_VALUE_TOO_LOW in msg:
                    raise CoreValidationError(
                        message="Life expectancy input too low",
                        error_key=ERROR_VALUE_TOO_LOW,
                    ) from error
                if ERROR_VALUE_TOO_HIGH in msg:
                    raise CoreValidationError(
                        message="Life expectancy input too high",
                        error_key=ERROR_VALUE_TOO_HIGH,
                    ) from error

            # If it's a type error (not a number), return invalid number
            raise CoreValidationError(
                message="Invalid life expectancy number", error_key=ERROR_INVALID_NUMBER
            ) from error

        except ValueError as error:
            raise CoreValidationError(
                message="Invalid life expectancy number", error_key=ERROR_INVALID_NUMBER
            ) from error
