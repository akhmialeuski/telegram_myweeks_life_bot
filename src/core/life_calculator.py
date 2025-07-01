"""Life Calculator Engine for computing life statistics.

This module provides a comprehensive calculator for life-related metrics
including age, weeks lived, months lived, and remaining time calculations.
"""

from datetime import date, datetime
from typing import Tuple

from ..database.models import User


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

        This is an approximation based on weeks lived.

        :returns: Approximate number of months lived
        :rtype: int

        Example:
            >>> calculator = LifeCalculatorEngine(user_profile)
            >>> calculator.calculate_months_lived()
            444
        """
        return self.calculate_weeks_lived() // 4

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

        :returns: Date of the next birthday
        :rtype: date

        Example:
            >>> calculator = LifeCalculatorEngine(user_profile)
            >>> calculator.get_next_birthday()
            datetime.date(2025, 3, 15)
        """
        next_birthday = date(
            self.today.year, self.birth_date.month, self.birth_date.day
        )

        # If birthday has passed this year, next birthday is next year
        if next_birthday < self.today:
            next_birthday = date(
                self.today.year + 1, self.birth_date.month, self.birth_date.day
            )

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

    @classmethod
    def from_birth_date(cls, birth_date: date) -> "LifeCalculatorEngine":
        """Create calculator from birth date (for backward compatibility).

        :param birth_date: Birth date
        :type birth_date: date
        :returns: LifeCalculatorEngine instance
        :rtype: LifeCalculatorEngine
        :raises ValueError: If birth date is invalid

        Example:
            >>> calculator = LifeCalculatorEngine.from_birth_date(date(1990, 3, 15))
            >>> calculator.calculate_age()
            34
        """
        if not birth_date:
            raise ValueError("Birth date cannot be None")

        # Create a mock user object for backward compatibility
        from ..database.models import User, UserSettings

        mock_user = User(telegram_id=0, first_name="Mock", created_at=datetime.utcnow())
        mock_user.settings = UserSettings(
            telegram_id=0,
            birth_date=birth_date,
            notifications=True,
            timezone="UTC",
            notifications_day="monday",
            notifications_time=datetime.strptime("09:00:00", "%H:%M:%S").time(),
            updated_at=datetime.utcnow(),
        )
        return cls(mock_user)

    @classmethod
    def from_string(cls, birth_date_str: str) -> "LifeCalculatorEngine":
        """Create calculator from birth date string.

        :param birth_date_str: Birth date in YYYY-MM-DD format
        :type birth_date_str: str
        :returns: LifeCalculatorEngine instance
        :rtype: LifeCalculatorEngine
        :raises ValueError: If date string is invalid

        Example:
            >>> calculator = LifeCalculatorEngine.from_string("1990-03-15")
            >>> calculator.calculate_age()
            34
        """
        try:
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            return cls.from_birth_date(birth_date)
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {e}")

    @classmethod
    def from_datetime(cls, birth_datetime: datetime) -> "LifeCalculatorEngine":
        """Create calculator from datetime object.

        :param birth_datetime: Birth datetime object
        :type birth_datetime: datetime
        :returns: LifeCalculatorEngine instance
        :rtype: LifeCalculatorEngine

        Example:
            >>> from datetime import datetime
            >>> dt = datetime(1990, 3, 15)
            >>> calculator = LifeCalculatorEngine.from_datetime(dt)
            >>> calculator.calculate_age()
            34
        """
        return cls.from_birth_date(birth_datetime.date())
