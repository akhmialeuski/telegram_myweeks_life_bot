"""Life Calculator Protocol for life statistics computation.

This module defines the contract for life statistics calculation.
The LifeCalculatorEngine implementation provides methods to calculate
age, weeks lived, remaining weeks, and other life metrics.
"""

from datetime import date
from typing import Protocol, runtime_checkable


@runtime_checkable
class LifeCalculatorProtocol(Protocol):
    """Calculator contract for life statistics computation.

    This protocol defines the interface for computing various life-related
    metrics including age, weeks lived, remaining weeks, and life percentage.
    Implementations are decoupled from data source and receive user data
    through the constructor.

    Implementations:
        - LifeCalculatorEngine: Production implementation
    """

    def calculate_age(self) -> int:
        """Calculate current age in years.

        Calculates the exact age based on birth date and current date.
        Handles leap years and month/day differences correctly.

        :returns: Current age in years
        :rtype: int
        """
        ...

    def calculate_days_lived(self) -> int:
        """Calculate total days lived since birth.

        :returns: Total number of days lived
        :rtype: int
        """
        ...

    def calculate_weeks_lived(self) -> int:
        """Calculate total weeks lived since birth.

        :returns: Total number of complete weeks lived
        :rtype: int
        """
        ...

    def calculate_months_lived(self) -> int:
        """Calculate total months lived since birth.

        :returns: Exact number of calendar months lived
        :rtype: int
        """
        ...

    def calculate_years_and_remaining_weeks(self) -> tuple[int, int]:
        """Calculate years lived and remaining weeks in current year.

        :returns: Tuple of (years_lived, remaining_weeks)
        :rtype: tuple[int, int]
        """
        ...

    def calculate_remaining_weeks(self, life_expectancy: int = 80) -> int:
        """Calculate remaining weeks based on life expectancy.

        :param life_expectancy: Expected life span in years (default: 80)
        :type life_expectancy: int
        :returns: Estimated remaining weeks
        :rtype: int
        """
        ...

    def calculate_life_percentage(self, life_expectancy: int = 80) -> float:
        """Calculate percentage of life lived based on expectancy.

        :param life_expectancy: Expected life span in years (default: 80)
        :type life_expectancy: int
        :returns: Percentage of life lived (0.0 to 1.0)
        :rtype: float
        """
        ...

    def get_next_birthday(self) -> date:
        """Calculate the next birthday date.

        Handles leap year edge case for February 29 birthdays.

        :returns: Date of the next birthday
        :rtype: date
        """
        ...

    def days_until_next_birthday(self) -> int:
        """Calculate days until next birthday.

        :returns: Number of days until next birthday
        :rtype: int
        """
        ...

    def get_life_statistics(self, life_expectancy: int = 80) -> dict:
        """Get comprehensive life statistics.

        :param life_expectancy: Expected life span in years (default: 80)
        :type life_expectancy: int
        :returns: Dictionary with all life statistics including age,
            days_lived, weeks_lived, months_lived, remaining_weeks,
            life_percentage, next_birthday, and days_until_birthday
        :rtype: dict
        """
        ...
