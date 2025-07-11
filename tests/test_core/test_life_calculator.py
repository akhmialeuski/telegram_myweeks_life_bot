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

    def test_from_birth_date_classmethod(self):
        """Test creating calculator from birth date.

        :returns: None
        """
        birth_date = date(1990, 3, 15)
        calculator = LifeCalculatorEngine.from_birth_date(birth_date)

        assert isinstance(calculator, LifeCalculatorEngine)
        assert calculator.birth_date == birth_date

    def test_from_string_classmethod(self):
        """Test creating calculator from date string.

        :returns: None
        """
        date_string = "1990-03-15"
        calculator = LifeCalculatorEngine.from_string(date_string)

        assert isinstance(calculator, LifeCalculatorEngine)
        assert calculator.birth_date == date(1990, 3, 15)

    def test_from_datetime_classmethod(self):
        """Test creating calculator from datetime.

        :returns: None
        """
        from datetime import datetime

        birth_datetime = datetime(1990, 3, 15, 10, 30, 0)
        calculator = LifeCalculatorEngine.from_datetime(birth_datetime)

        assert isinstance(calculator, LifeCalculatorEngine)
        assert calculator.birth_date == date(1990, 3, 15)
