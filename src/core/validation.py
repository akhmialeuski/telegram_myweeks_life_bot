"""Validation logic using Pydantic.

This module provides Pydantic models for user input validation, replacing
ad-hoc validation logic in handlers.
"""

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, field_validator

from src.utils.config import (
    MAX_LIFE_EXPECTANCY,
    MIN_BIRTH_YEAR,
    MIN_LIFE_EXPECTANCY,
)

# Error keys mapping
ERROR_INVALID_DATE_FORMAT = "invalid_date_format"
ERROR_DATE_IN_FUTURE = "date_in_future"
ERROR_DATE_TOO_OLD = "date_too_old"
ERROR_INVALID_NUMBER = "invalid_number"
ERROR_VALUE_TOO_LOW = "value_too_low"
ERROR_VALUE_TOO_HIGH = "value_too_high"


def parse_dd_mm_yyyy_date(v: str | date) -> date:
    """Parse date from DD.MM.YYYY string.

    :param v: Input value (string or date)
    :type v: str | date
    :returns: Parsed date object
    :rtype: date
    :raises ValueError: If date format is invalid
    """
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        try:
            return datetime.strptime(v.strip(), "%d.%m.%Y").date()
        except ValueError:
            raise ValueError(ERROR_INVALID_DATE_FORMAT)
    raise ValueError(ERROR_INVALID_DATE_FORMAT)


# Type alias for date field with parsing
CustomDate = Annotated[date, BeforeValidator(parse_dd_mm_yyyy_date)]


class BirthDateInput(BaseModel):
    """Pydantic model for birth date validation.

    :ivar birth_date: The birth date input
    :type birth_date: CustomDate
    """

    birth_date: CustomDate

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, v: date) -> date:
        """Validate birth date logic.

        :param v: parsed date
        :type v: date
        :returns: validated date
        :rtype: date
        :raises ValueError: if date is invalid
        """
        if v > date.today():
            raise ValueError(ERROR_DATE_IN_FUTURE)
        if v.year < MIN_BIRTH_YEAR:
            raise ValueError(ERROR_DATE_TOO_OLD)
        return v


class LifeExpectancyInput(BaseModel):
    """Pydantic model for life expectancy validation.

    :ivar life_expectancy: The life expectancy input
    :type life_expectancy: int
    """

    life_expectancy: int

    @field_validator("life_expectancy")
    @classmethod
    def validate_range(cls, v: int) -> int:
        """Validate life expectancy range.

        :param v: input value
        :type v: int
        :returns: validated value
        :rtype: int
        :raises ValueError: if value is out of range
        """
        if v < MIN_LIFE_EXPECTANCY:
            raise ValueError(ERROR_VALUE_TOO_LOW)
        if v > MAX_LIFE_EXPECTANCY:
            raise ValueError(ERROR_VALUE_TOO_HIGH)
        return v
