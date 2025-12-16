"""Life Calculator Engine for computing life statistics.

This module provides a pure function based calculator for life-related metrics
using immutable data structures and cached properties.
"""

from dataclasses import dataclass
from datetime import date
from functools import cached_property
from typing import Optional


@dataclass(frozen=True)
class LifeCalculationResult:
    """Immutable result of life calculation.

    All derived values are cached for performance.

    :ivar birth_date: User's birth date
    :type birth_date: date
    :ivar life_expectancy: Expected life span in years
    :type life_expectancy: int
    :ivar reference_date: Date to calculate from
    :type reference_date: date
    """

    birth_date: date
    life_expectancy: int
    reference_date: date

    @cached_property
    def age(self) -> int:
        """Calculate current age in years.

        :returns: Current age in years
        :rtype: int
        """
        age = self.reference_date.year - self.birth_date.year
        if (self.reference_date.month, self.reference_date.day) < (
            self.birth_date.month,
            self.birth_date.day,
        ):
            age -= 1
        return age

    @cached_property
    def days_lived(self) -> int:
        """Calculate total days lived since birth.

        :returns: Total number of days lived
        :rtype: int
        """
        return (self.reference_date - self.birth_date).days

    @cached_property
    def total_weeks_lived(self) -> int:
        """Calculate weeks from birth to reference date.

        :returns: Total number of complete weeks lived
        :rtype: int
        """
        return self.days_lived // 7

    @cached_property
    def total_weeks_expected(self) -> int:
        """Calculate total weeks in expected lifespan.

        :returns: Total weeks in expected lifespan
        :rtype: int
        """
        return self.life_expectancy * 52

    @cached_property
    def remaining_weeks(self) -> int:
        """Calculate remaining weeks.

        :returns: Estimated remaining weeks
        :rtype: int
        """
        return max(0, self.total_weeks_expected - self.total_weeks_lived)

    @cached_property
    def percentage_lived(self) -> float:
        """Calculate percentage of life lived.

        :returns: Percentage of life lived (0.0 to 1.0)
        :rtype: float
        """
        if self.total_weeks_expected == 0:
            return 0.0
        return min(1.0, self.total_weeks_lived / self.total_weeks_expected)

    @cached_property
    def years_lived(self) -> int:
        """Calculate years component of weeks lived.

        :returns: Years lived based on weeks
        :rtype: int
        """
        return self.total_weeks_lived // 52

    @cached_property
    def weeks_in_current_year(self) -> int:
        """Calculate weeks elapsed in the current year of life.

        :returns: Weeks elapsed in current year
        :rtype: int
        """
        return self.total_weeks_lived % 52

    @cached_property
    def next_birthday(self) -> date:
        """Calculate the next birthday date.

        :returns: Date of the next birthday
        :rtype: date
        """
        year = self.reference_date.year
        # Handle February 29 edge case
        try:
            birthday_this_year = self.birth_date.replace(year=year)
        except ValueError:
            # Must be Feb 29 and current year is not leap
            birthday_this_year = date(year, 2, 28)

        if birthday_this_year < self.reference_date:
            year += 1
            try:
                return self.birth_date.replace(year=year)
            except ValueError:
                return date(year, 2, 28)

        return birthday_this_year

    @cached_property
    def days_until_birthday(self) -> int:
        """Calculate days until next birthday.

        :returns: Number of days until next birthday
        :rtype: int
        """
        return (self.next_birthday - self.reference_date).days


def calculate_life_statistics(
    birth_date: date,
    life_expectancy: int,
    reference_date: Optional[date] = None,
) -> LifeCalculationResult:
    """Pure function for life statistics calculation.

    :param birth_date: User's birth date
    :type birth_date: date
    :param life_expectancy: Expected life span in years
    :type life_expectancy: int
    :param reference_date: Date to calculate from (default: today)
    :type reference_date: Optional[date]
    :returns: Immutable calculation result with cached derived values
    :rtype: LifeCalculationResult
    """
    if reference_date is None:
        reference_date = date.today()

    return LifeCalculationResult(
        birth_date=birth_date,
        life_expectancy=life_expectancy,
        reference_date=reference_date,
    )
