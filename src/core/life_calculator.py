"""Life Calculator Engine for computing life statistics.

This module provides a comprehensive calculator for life-related metrics
including age, weeks lived, months lived, and remaining time calculations.
"""

from datetime import date
from typing import Tuple

from dateutil.relativedelta import relativedelta

from ..database.models.user import User


class LifeCalculatorEngine:
    """Engine for calculating life-related statistics and metrics.

    This class provides methods to calculate various life statistics
    including age, weeks lived, months lived, and remaining time.
    All calculations are based on a given user profile.
    """

    def __init__(self, user: User):
        """Initialize the calculator with a user profile.

        :param user: The user profile containing birth date and settings
        :type user: User
        :raises ValueError: If user has no birth date
        """
        if not user or not user.settings or not user.settings.birth_date:
            raise ValueError("User must have a valid birth date")

        self.user = user
        self.birth_date = user.settings.birth_date
        self.today = date.today()

    def calculate_age(self) -> int:
        """Calculate current age in years.

        Calculates the exact age based on birth date and current date.
        Handles leap years and month/day differences correctly.

        :returns: Current age in years
        :rtype: int

        Example:
            >>> calculator = LifeCalculatorEngine(user_profile)
            >>> calculator.calculate_age()
            34
        """
        age = self.today.year - self.birth_date.year

        # Adjust age if birthday hasn't occurred this year
        if (self.today.month, self.today.day) < (
            self.birth_date.month,
            self.birth_date.day,
        ):
            age -= 1

        return age

    def calculate_days_lived(self) -> int:
        """Calculate total days lived since birth.

        :returns: Total number of days lived
        :rtype: int

        Example:
            >>> calculator = LifeCalculatorEngine(user_profile)
            >>> calculator.calculate_days_lived()
            12450
        """
        return (self.today - self.birth_date).days

    def calculate_weeks_lived(self) -> int:
        """Calculate total weeks lived since birth.

        :returns: Total number of complete weeks lived
        :rtype: int

        Example:
            >>> calculator = LifeCalculatorEngine(user_profile)
            >>> calculator.calculate_weeks_lived()
            1778
        """
        return self.calculate_days_lived() // 7

    def calculate_months_lived(self) -> int:
        """Calculate total months lived since birth.

        Calculates the exact number of calendar months between birth date
        and current date, considering varying month lengths for precision.

        :returns: Exact number of months lived
        :rtype: int

        Example:
            >>> calculator = LifeCalculatorEngine(user_profile)
            >>> calculator.calculate_months_lived()
            444
        """
        delta = relativedelta(self.today, self.birth_date)
        return delta.years * 12 + delta.months

    def calculate_years_and_remaining_weeks(self) -> Tuple[int, int]:
        """Calculate years lived and remaining weeks in current year.

        :returns: Tuple of (years_lived, remaining_weeks)
        :rtype: Tuple[int, int]

        Example:
            >>> calculator = LifeCalculatorEngine(user_profile)
            >>> calculator.calculate_years_and_remaining_weeks()
            (34, 12)
        """
        weeks_lived = self.calculate_weeks_lived()
        years = weeks_lived // 52
        remaining_weeks = weeks_lived % 52
        return years, remaining_weeks

    def calculate_remaining_weeks(self, life_expectancy: int = 80) -> int:
        """Calculate remaining weeks based on life expectancy.

        :param life_expectancy: Expected life span in years (default: 80)
        :type life_expectancy: int
        :returns: Estimated remaining weeks
        :rtype: int

        Example:
            >>> calculator = LifeCalculatorEngine(user_profile)
            >>> calculator.calculate_remaining_weeks(80)
            2392
        """
        total_expected_weeks = life_expectancy * 52
        weeks_lived = self.calculate_weeks_lived()
        remaining = total_expected_weeks - weeks_lived
        return max(0, remaining)

    def calculate_life_percentage(self, life_expectancy: int = 80) -> float:
        """Calculate percentage of life lived based on expectancy.

        :param life_expectancy: Expected life span in years (default: 80)
        :type life_expectancy: int
        :returns: Percentage of life lived (0.0 to 1.0)
        :rtype: float

        Example:
            >>> calculator = LifeCalculatorEngine(user_profile)
            >>> calculator.calculate_life_percentage(80)
            0.425
        """
        total_expected_weeks = life_expectancy * 52
        weeks_lived = self.calculate_weeks_lived()
        return min(1.0, weeks_lived / total_expected_weeks)

    def get_next_birthday(self) -> date:
        """Calculate the next birthday date.

        Handles leap year edge case for February 29 birthdays by using
        February 28 in non-leap years.

        :returns: Date of the next birthday
        :rtype: date

        Example:
            >>> calculator = LifeCalculatorEngine(user_profile)
            >>> calculator.get_next_birthday()
            datetime.date(2025, 3, 15)
        """
        # Handle February 29 edge case for non-leap years
        target_day = self.birth_date.day
        if self.birth_date.month == 2 and self.birth_date.day == 29:
            # Check if target year is a leap year, if not use February 28
            if not self._is_leap_year(self.today.year):
                target_day = 28

        next_birthday = date(self.today.year, self.birth_date.month, target_day)

        # If birthday has passed this year, next birthday is next year
        if next_birthday < self.today:
            # Check leap year for next year as well
            next_year = self.today.year + 1
            target_day = self.birth_date.day
            if self.birth_date.month == 2 and self.birth_date.day == 29:
                if not self._is_leap_year(next_year):
                    target_day = 28

            next_birthday = date(next_year, self.birth_date.month, target_day)

        return next_birthday

    def days_until_next_birthday(self) -> int:
        """Calculate days until next birthday.

        :returns: Number of days until next birthday
        :rtype: int

        Example:
            >>> calculator = LifeCalculatorEngine(user_profile)
            >>> calculator.days_until_next_birthday()
            257
        """
        next_birthday = self.get_next_birthday()
        return (next_birthday - self.today).days

    def get_life_statistics(self, life_expectancy: int = 80) -> dict:
        """Get comprehensive life statistics.

        :param life_expectancy: Expected life span in years (default: 80)
        :type life_expectancy: int
        :returns: Dictionary with all life statistics
        :rtype: dict

        Example:
            >>> calculator = LifeCalculatorEngine(user_profile)
            >>> stats = calculator.get_life_statistics(80)
            >>> stats['age']
            34
        """
        return {
            "age": self.calculate_age(),
            "days_lived": self.calculate_days_lived(),
            "weeks_lived": self.calculate_weeks_lived(),
            "months_lived": self.calculate_months_lived(),
            "years_and_remaining_weeks": self.calculate_years_and_remaining_weeks(),
            "remaining_weeks": self.calculate_remaining_weeks(life_expectancy),
            "life_percentage": self.calculate_life_percentage(life_expectancy),
            "next_birthday": self.get_next_birthday(),
            "days_until_birthday": self.days_until_next_birthday(),
            "life_expectancy": life_expectancy,
        }

    def _is_leap_year(self, year: int) -> bool:
        """Check if a given year is a leap year.

        :param year: Year to check
        :type year: int
        :returns: True if the year is a leap year, False otherwise
        :rtype: bool

        Example:
            >>> calculator = LifeCalculatorEngine(user_profile)
            >>> calculator._is_leap_year(year=2024)
            True
            >>> calculator._is_leap_year(year=2023)
            False
        """
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
