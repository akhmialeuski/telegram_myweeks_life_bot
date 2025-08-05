"""Unit tests for LifeCalculatorEngine class.

Tests all methods of the LifeCalculatorEngine class using pytest
with proper fixtures, mocking, and edge case coverage.
"""

from datetime import date
from unittest.mock import Mock, patch

import pytest

from src.core.life_calculator import LifeCalculatorEngine


class TestLifeCalculatorEngine:
    """Test suite for LifeCalculatorEngine class."""

    @pytest.fixture
    def sample_user_with_settings(self):
        """Create a sample User with settings for testing.

        :returns: Sample User with settings
        :rtype: User
        """
        user = Mock()
        user.settings = Mock()
        user.settings.birth_date = date(1990, 3, 15)
        user.settings.life_expectancy = 80
        return user

    @pytest.fixture
    def calculator(self, sample_user_with_settings):
        """Create LifeCalculatorEngine instance.

        :returns: LifeCalculatorEngine instance
        :rtype: LifeCalculatorEngine
        """
        return LifeCalculatorEngine(sample_user_with_settings)

    def test_calculate_age_exact_birthday(self):
        """Test calculating age on exact birthday.

        :returns: None
        """
        user = Mock()
        user.settings = Mock()
        user.settings.birth_date = date(1990, 3, 15)

        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            calculator = LifeCalculatorEngine(user)
            age = calculator.calculate_age()

            assert age == 34

    def test_calculate_age_before_birthday(self):
        """Test calculating age before birthday this year.

        :returns: None
        """
        user = Mock()
        user.settings = Mock()
        user.settings.birth_date = date(1990, 6, 15)

        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            calculator = LifeCalculatorEngine(user)
            age = calculator.calculate_age()

            assert age == 33

    def test_calculate_age_after_birthday(self):
        """Test calculating age after birthday this year.

        :returns: None
        """
        user = Mock()
        user.settings = Mock()
        user.settings.birth_date = date(1990, 1, 15)

        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            calculator = LifeCalculatorEngine(user)
            age = calculator.calculate_age()

            assert age == 34

    def test_calculate_days_lived(self, calculator):
        """Test calculating total days lived.

        :param calculator: LifeCalculatorEngine instance
        :returns: None
        """
        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            # Birth date is 1990-03-15, today is 2024-03-15
            # So exactly 34 years = 34 * 365 + leap days
            days = calculator.calculate_days_lived()

            assert isinstance(days, int)
            assert days > 12000  # More than 30 years
            assert days < 15000  # Less than 40 years

    def test_calculate_weeks_lived(self, calculator):
        """Test calculating total weeks lived.

        :param calculator: LifeCalculatorEngine instance
        :returns: None
        """
        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            weeks = calculator.calculate_weeks_lived()

            assert isinstance(weeks, int)
            assert weeks > 1700  # More than 30 years worth of weeks
            assert weeks < 2200  # Less than 40 years worth of weeks

    def test_calculate_months_lived(self, calculator):
        """Test calculating total months lived.

        :param calculator: LifeCalculatorEngine instance
        :returns: None
        """
        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            months = calculator.calculate_months_lived()

            assert isinstance(months, int)
            assert months > 400  # More than 30 years worth of months
            assert months < 600  # Less than 40 years worth of months

    def test_calculate_years_and_remaining_weeks(self, calculator):
        """Test calculating years and remaining weeks.

        :param calculator: LifeCalculatorEngine instance
        :returns: None
        """
        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            years, remaining_weeks = calculator.calculate_years_and_remaining_weeks()

            assert isinstance(years, int)
            assert isinstance(remaining_weeks, int)
            assert years > 30
            assert years < 40
            assert 0 <= remaining_weeks < 52

    def test_calculate_remaining_weeks(self, calculator):
        """Test calculating remaining weeks until life expectancy.

        :param calculator: LifeCalculatorEngine instance
        :returns: None
        """
        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            remaining = calculator.calculate_remaining_weeks(80)

            assert isinstance(remaining, int)
            assert remaining > 2000  # More than 40 years left
            assert remaining < 3000  # Less than 60 years left

    def test_calculate_life_percentage(self, calculator):
        """Test calculating percentage of life lived.

        :param calculator: LifeCalculatorEngine instance
        :returns: None
        """
        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            percentage = calculator.calculate_life_percentage(80)

            assert isinstance(percentage, float)
            assert 0.0 <= percentage <= 1.0
            assert 0.4 < percentage < 0.5  # Around 42-45%

    def test_get_next_birthday_same_year(self, calculator):
        """Test getting next birthday when it's later this year.

        :param calculator: LifeCalculatorEngine instance
        :returns: None
        """
        # Manually override the today attribute on the calculator instance
        calculator.today = date(2024, 1, 15)

        next_birthday = calculator.get_next_birthday()

        assert next_birthday == date(2024, 3, 15)

    def test_get_next_birthday_next_year(self, calculator):
        """Test getting next birthday when it's next year.

        :param calculator: LifeCalculatorEngine instance
        :returns: None
        """
        # Manually override the today attribute on the calculator instance
        calculator.today = date(2024, 6, 15)

        next_birthday = calculator.get_next_birthday()

        assert next_birthday == date(2025, 3, 15)

    def test_days_until_next_birthday(self, calculator):
        """Test calculating days until next birthday.

        :param calculator: LifeCalculatorEngine instance
        :returns: None
        """
        # Manually override the today attribute on the calculator instance
        calculator.today = date(2024, 3, 14)

        days = calculator.days_until_next_birthday()

        assert days == 1

    def test_get_life_statistics(self, calculator):
        """Test getting comprehensive life statistics.

        :param calculator: LifeCalculatorEngine instance
        :returns: None
        """
        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            stats = calculator.get_life_statistics(80)

            assert isinstance(stats, dict)
            assert "age" in stats
            assert "days_lived" in stats
            assert "weeks_lived" in stats
            assert "months_lived" in stats
            assert "remaining_weeks" in stats
            assert "life_percentage" in stats
            assert "next_birthday" in stats
            assert "days_until_birthday" in stats

    def test_edge_case_newborn(self):
        """Test edge case for newborn (born today).

        :returns: None
        """
        user = Mock()
        user.settings = Mock()
        user.settings.birth_date = date(2024, 3, 15)

        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            calculator = LifeCalculatorEngine(user)

            assert calculator.calculate_age() == 0
            assert calculator.calculate_days_lived() == 0
            assert calculator.calculate_weeks_lived() == 0

    def test_edge_case_elderly(self):
        """Test edge case for elderly person over life expectancy.

        :returns: None
        """
        user = Mock()
        user.settings = Mock()
        user.settings.birth_date = date(1940, 3, 15)  # 84 years old

        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            calculator = LifeCalculatorEngine(user)

            # Remaining weeks should be 0 (not negative)
            remaining = calculator.calculate_remaining_weeks(80)
            assert remaining == 0

            # Life percentage should be 1.0 (not more than 100%)
            percentage = calculator.calculate_life_percentage(80)
            assert percentage == 1.0

    def test_invalid_user_no_birth_date(self):
        """Test error handling for user without birth date.

        :returns: None
        """
        user = Mock()
        user.settings = None

        with pytest.raises(ValueError, match="User must have a valid birth date"):
            LifeCalculatorEngine(user)

    def test_invalid_user_no_settings(self):
        """Test error handling for user without settings.

        :returns: None
        """
        user = Mock()
        user.settings = Mock()
        user.settings.birth_date = None

        with pytest.raises(ValueError, match="User must have a valid birth date"):
            LifeCalculatorEngine(user)


class TestLeapYearHandling:
    """Test suite for leap year edge case handling in LifeCalculatorEngine."""

    @pytest.fixture
    def february_29_user(self) -> Mock:
        """Create a user with February 29 birth date.

        :returns: User with February 29 birth date
        :rtype: Mock
        """
        user: Mock = Mock()
        user.settings = Mock()
        user.settings.birth_date = date(1996, 2, 29)  # Leap year birth
        return user

    @pytest.fixture
    def february_29_calculator(self, february_29_user: Mock) -> LifeCalculatorEngine:
        """Create LifeCalculatorEngine instance for February 29 birth date.

        :param february_29_user: User with February 29 birth date
        :type february_29_user: Mock
        :returns: LifeCalculatorEngine instance
        :rtype: LifeCalculatorEngine
        """
        return LifeCalculatorEngine(february_29_user)

    def test_is_leap_year_helper_method(
        self, february_29_calculator: LifeCalculatorEngine
    ) -> None:
        """Test the _is_leap_year helper method.

        :param february_29_calculator: LifeCalculatorEngine instance
        :type february_29_calculator: LifeCalculatorEngine
        :returns: None
        """
        # Test leap years
        assert (
            february_29_calculator._is_leap_year(year=2000) is True
        )  # Century leap year
        assert (
            february_29_calculator._is_leap_year(year=2024) is True
        )  # Regular leap year
        assert (
            february_29_calculator._is_leap_year(year=1996) is True
        )  # Regular leap year

        # Test non-leap years
        assert february_29_calculator._is_leap_year(year=2023) is False  # Regular year
        assert february_29_calculator._is_leap_year(year=2025) is False  # Regular year
        assert (
            february_29_calculator._is_leap_year(year=2100) is False
        )  # Century non-leap year
        assert (
            february_29_calculator._is_leap_year(year=1900) is False
        )  # Century non-leap year

    def test_get_next_birthday_february_29_in_leap_year(
        self, february_29_calculator: LifeCalculatorEngine
    ) -> None:
        """Test next birthday calculation for February 29 in a leap year.

        :param february_29_calculator: LifeCalculatorEngine instance
        :type february_29_calculator: LifeCalculatorEngine
        :returns: None
        """
        # Set today to 2024 (leap year) before February 29
        february_29_calculator.today = date(2024, 1, 15)

        next_birthday: date = february_29_calculator.get_next_birthday()

        # Should return February 29, 2024 (leap year)
        assert next_birthday == date(2024, 2, 29)

    def test_get_next_birthday_february_29_in_non_leap_year(
        self, february_29_calculator: LifeCalculatorEngine
    ) -> None:
        """Test next birthday calculation for February 29 in a non-leap year.

        :param february_29_calculator: LifeCalculatorEngine instance
        :type february_29_calculator: LifeCalculatorEngine
        :returns: None
        """
        # Set today to 2023 (non-leap year) before February 28
        february_29_calculator.today = date(2023, 1, 15)

        next_birthday: date = february_29_calculator.get_next_birthday()

        # Should return February 28, 2023 (fallback for non-leap year)
        assert next_birthday == date(2023, 2, 28)

    def test_get_next_birthday_february_29_passed_this_year_leap(
        self, february_29_calculator: LifeCalculatorEngine
    ) -> None:
        """Test next birthday calculation when February 29 has passed in leap year.

        :param february_29_calculator: LifeCalculatorEngine instance
        :type february_29_calculator: LifeCalculatorEngine
        :returns: None
        """
        # Set today to 2024 (leap year) after February 29
        february_29_calculator.today = date(2024, 3, 15)

        next_birthday: date = february_29_calculator.get_next_birthday()

        # Should return February 28, 2025 (next year, not leap year)
        assert next_birthday == date(2025, 2, 28)

    def test_get_next_birthday_february_29_passed_this_year_non_leap(
        self, february_29_calculator: LifeCalculatorEngine
    ) -> None:
        """Test next birthday calculation when February 29 has passed in non-leap year.

        :param february_29_calculator: LifeCalculatorEngine instance
        :type february_29_calculator: LifeCalculatorEngine
        :returns: None
        """
        # Set today to 2023 (non-leap year) after February 28
        february_29_calculator.today = date(2023, 3, 15)

        next_birthday: date = february_29_calculator.get_next_birthday()

        # Should return February 29, 2024 (next leap year)
        assert next_birthday == date(2024, 2, 29)

    def test_get_next_birthday_february_29_on_birthday_leap_year(
        self, february_29_calculator: LifeCalculatorEngine
    ) -> None:
        """Test next birthday calculation on February 29 in leap year.

        :param february_29_calculator: LifeCalculatorEngine instance
        :type february_29_calculator: LifeCalculatorEngine
        :returns: None
        """
        # Set today to February 29, 2024 (leap year)
        february_29_calculator.today = date(2024, 2, 29)

        next_birthday: date = february_29_calculator.get_next_birthday()

        # When today is the birthday, next birthday is today (same day)
        # Should return February 29, 2024 (same day)
        assert next_birthday == date(2024, 2, 29)

    def test_get_next_birthday_february_29_on_birthday_non_leap_year(
        self, february_29_calculator: LifeCalculatorEngine
    ) -> None:
        """Test next birthday calculation on February 28 in non-leap year.

        :param february_29_calculator: LifeCalculatorEngine instance
        :type february_29_calculator: LifeCalculatorEngine
        :returns: None
        """
        # Set today to February 28, 2023 (non-leap year, fallback date)
        february_29_calculator.today = date(2023, 2, 28)

        next_birthday: date = february_29_calculator.get_next_birthday()

        # When today is the birthday, next birthday is today (same day)
        # Should return February 28, 2023 (same day)
        assert next_birthday == date(2023, 2, 28)

    def test_days_until_next_birthday_february_29_edge_case(
        self, february_29_calculator: LifeCalculatorEngine
    ) -> None:
        """Test days until next birthday for February 29 edge case.

        :param february_29_calculator: LifeCalculatorEngine instance
        :type february_29_calculator: LifeCalculatorEngine
        :returns: None
        """
        # Set today to February 27, 2023 (non-leap year)
        february_29_calculator.today = date(2023, 2, 27)

        days: int = february_29_calculator.days_until_next_birthday()

        # Should be 1 day until February 28, 2023
        assert days == 1

    def test_life_statistics_with_february_29_birthday(
        self, february_29_calculator: LifeCalculatorEngine
    ) -> None:
        """Test life statistics calculation with February 29 birthday.

        :param february_29_calculator: LifeCalculatorEngine instance
        :type february_29_calculator: LifeCalculatorEngine
        :returns: None
        """
        # Set today to 2023 (non-leap year)
        february_29_calculator.today = date(2023, 1, 15)

        stats: dict = february_29_calculator.get_life_statistics(80)

        # Verify that next_birthday is properly calculated
        assert "next_birthday" in stats
        assert stats["next_birthday"] == date(2023, 2, 28)  # Fallback to February 28

        # Verify that days_until_birthday is calculated correctly
        assert "days_until_birthday" in stats
        assert isinstance(stats["days_until_birthday"], int)
        assert stats["days_until_birthday"] > 0

    def test_century_leap_year_edge_cases(
        self, february_29_calculator: LifeCalculatorEngine
    ) -> None:
        """Test century leap year edge cases (1900, 2000, 2100).

        :param february_29_calculator: LifeCalculatorEngine instance
        :type february_29_calculator: LifeCalculatorEngine
        :returns: None
        """
        # Test 2000 (century leap year - should be leap year)
        assert february_29_calculator._is_leap_year(year=2000) is True

        # Test 1900 (century non-leap year - should not be leap year)
        assert february_29_calculator._is_leap_year(year=1900) is False

        # Test 2100 (century non-leap year - should not be leap year)
        assert february_29_calculator._is_leap_year(year=2100) is False

    def test_february_29_birthday_in_century_transition(
        self, february_29_calculator: LifeCalculatorEngine
    ) -> None:
        """Test February 29 birthday handling during century transitions.

        :param february_29_calculator: LifeCalculatorEngine instance
        :type february_29_calculator: LifeCalculatorEngine
        :returns: None
        """
        # Test transition from 2000 (leap year) to 2001 (non-leap year)
        february_29_calculator.today = date(2000, 12, 31)
        next_birthday: date = february_29_calculator.get_next_birthday()
        assert next_birthday == date(2001, 2, 28)  # 2001 is not a leap year

        # Test transition from 2099 (non-leap year) to 2100 (non-leap year)
        february_29_calculator.today = date(2099, 12, 31)
        next_birthday = february_29_calculator.get_next_birthday()
        assert next_birthday == date(2100, 2, 28)  # 2100 is not a leap year


class TestImprovedMonthsCalculation:
    """Test suite for improved months calculation accuracy."""

    def test_exact_month_calculation_same_day(self):
        """Test exact month calculation when current day matches birth day.

        :returns: None
        """
        user = Mock()
        user.settings = Mock()
        user.settings.birth_date = date(2023, 1, 15)

        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            calculator = LifeCalculatorEngine(user)
            months = calculator.calculate_months_lived()

            # Exactly 12 months
            assert months == 12

    def test_exact_month_calculation_different_day(self):
        """Test exact month calculation when current day differs from birth day.

        :returns: None
        """
        user = Mock()
        user.settings = Mock()
        user.settings.birth_date = date(2023, 1, 15)

        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 20)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            calculator = LifeCalculatorEngine(user)
            months = calculator.calculate_months_lived()

            # Still 12 months (calendar months, not partial)
            assert months == 12

    def test_exact_month_calculation_partial_month(self):
        """Test exact month calculation for partial month.

        :returns: None
        """
        user = Mock()
        user.settings = Mock()
        user.settings.birth_date = date(2023, 1, 15)

        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2023, 2, 10)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            calculator = LifeCalculatorEngine(user)
            months = calculator.calculate_months_lived()

            # Less than 1 month, should be 0
            assert months == 0

    def test_exact_month_calculation_varying_month_lengths(self):
        """Test exact month calculation with varying month lengths.

        :returns: None
        """
        user = Mock()
        user.settings = Mock()
        user.settings.birth_date = date(2023, 1, 31)  # January 31

        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(
                2023, 2, 28
            )  # February 28 (non-leap year)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            calculator = LifeCalculatorEngine(user)
            months = calculator.calculate_months_lived()

            # Should be 1 month (calendar month difference)
            assert months == 1

    def test_exact_month_calculation_leap_year_february(self):
        """Test exact month calculation with leap year February.

        :returns: None
        """
        user = Mock()
        user.settings = Mock()
        user.settings.birth_date = date(2023, 1, 31)  # January 31

        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 2, 29)  # February 29 (leap year)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            calculator = LifeCalculatorEngine(user)
            months = calculator.calculate_months_lived()

            # Should be 13 months (1 year + 1 month)
            assert months == 13

    def test_exact_month_calculation_multi_year(self):
        """Test exact month calculation over multiple years.

        :returns: None
        """
        user = Mock()
        user.settings = Mock()
        user.settings.birth_date = date(2020, 6, 15)

        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 6, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            calculator = LifeCalculatorEngine(user)
            months = calculator.calculate_months_lived()

            # Exactly 4 years = 48 months
            assert months == 48

    def test_exact_month_calculation_edge_case_month_end(self):
        """Test exact month calculation for month end edge cases.

        :returns: None
        """
        user = Mock()
        user.settings = Mock()
        user.settings.birth_date = date(2023, 3, 31)  # March 31

        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2023, 4, 30)  # April 30
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            calculator = LifeCalculatorEngine(user)
            months = calculator.calculate_months_lived()

            # Should be 1 month (calendar month difference)
            assert months == 1

    def test_exact_month_calculation_compared_to_old_method(self):
        """Test that new method is more accurate than old approximation.

        :returns: None
        """
        user = Mock()
        user.settings = Mock()
        user.settings.birth_date = date(2020, 1, 15)

        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 6, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            calculator = LifeCalculatorEngine(user)
            new_months = calculator.calculate_months_lived()

            # Calculate what old method would have returned
            days_lived = calculator.calculate_days_lived()
            old_months = days_lived // 7 // 4  # Old approximation

            # New method should be more accurate
            assert new_months != old_months
            # New method should be closer to actual calendar months
            assert abs(new_months - 53) <= 1  # Around 4 years + 5 months = 53 months

    def test_exact_month_calculation_newborn(self):
        """Test exact month calculation for newborn.

        :returns: None
        """
        user = Mock()
        user.settings = Mock()
        user.settings.birth_date = date(2024, 6, 15)

        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 6, 20)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            calculator = LifeCalculatorEngine(user)
            months = calculator.calculate_months_lived()

            # Less than 1 month, should be 0
            assert months == 0

    def test_exact_month_calculation_exactly_one_month(self):
        """Test exact month calculation for exactly one month.

        :returns: None
        """
        user = Mock()
        user.settings = Mock()
        user.settings.birth_date = date(2024, 5, 15)

        with patch("src.core.life_calculator.date") as mock_date:
            mock_date.today.return_value = date(2024, 6, 15)
            mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

            calculator = LifeCalculatorEngine(user)
            months = calculator.calculate_months_lived()

            # Exactly 1 month
            assert months == 1
