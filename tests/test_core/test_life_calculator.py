"""Unit tests for calculate_life_statistics function.

Tests the pure function calculate_life_statistics and the LifeCalculationResult dataclass.
"""

from datetime import date

from src.core.life_calculator import calculate_life_statistics


class TestLifeCalculator:
    """Test suite for calculate_life_statistics function."""

    def test_calculate_age_exact_birthday(self) -> None:
        """Test age calculation when today is exactly the birthday."""
        birth_date = date(1990, 3, 15)
        reference_date = date(2024, 3, 15)

        stats = calculate_life_statistics(
            birth_date=birth_date,
            life_expectancy=80,
            reference_date=reference_date,
        )

        assert stats.age == 34

    def test_calculate_age_before_birthday(self) -> None:
        """Test age calculation before birthday occurs this year."""
        birth_date = date(1990, 6, 15)
        reference_date = date(2024, 3, 15)

        stats = calculate_life_statistics(
            birth_date=birth_date,
            life_expectancy=80,
            reference_date=reference_date,
        )

        assert stats.age == 33

    def test_calculate_age_after_birthday(self) -> None:
        """Test age calculation after birthday occurred this year."""
        birth_date = date(1990, 1, 15)
        reference_date = date(2024, 3, 15)

        stats = calculate_life_statistics(
            birth_date=birth_date,
            life_expectancy=80,
            reference_date=reference_date,
        )

        assert stats.age == 34

    def test_calculate_days_lived(self) -> None:
        """Test calculation of total days lived."""
        birth_date = date(1990, 3, 15)
        reference_date = date(2024, 3, 15)

        stats = calculate_life_statistics(
            birth_date=birth_date,
            life_expectancy=80,
            reference_date=reference_date,
        )

        # 34 years * 365 + 8 leap days (1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020)
        # Note: 2024 is leap but Feb 29 is passed? 2024-03-15. Yes.
        # Leap years: 1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024.
        # 9 leap years.
        # 34 * 365 + 9 = 12410 + 9 = 12419?
        # Let's just check range or exact logic if needed, but assertion of value is safer if we trust datetime implementation.
        assert stats.days_lived == (reference_date - birth_date).days

    def test_calculate_weeks_lived(self) -> None:
        """Test calculation of total weeks lived."""
        birth_date = date(1990, 3, 15)
        reference_date = date(2024, 3, 15)

        stats = calculate_life_statistics(
            birth_date=birth_date,
            life_expectancy=80,
            reference_date=reference_date,
        )

        assert stats.total_weeks_lived == (reference_date - birth_date).days // 7

    def test_calculate_remaining_weeks(self) -> None:
        """Test calculation of weeks remaining until life expectancy."""
        birth_date = date(1990, 3, 15)
        reference_date = date(2024, 3, 15)
        life_expectancy = 80

        stats = calculate_life_statistics(
            birth_date=birth_date,
            life_expectancy=life_expectancy,
            reference_date=reference_date,
        )

        expected_total_weeks = life_expectancy * 52
        weeks_lived = (reference_date - birth_date).days // 7
        expected_remaining = max(0, expected_total_weeks - weeks_lived)

        assert stats.remaining_weeks == expected_remaining

    def test_calculate_life_percentage(self) -> None:
        """Test calculation of percentage of life lived."""
        birth_date = date(1990, 3, 15)
        reference_date = date(2024, 3, 15)

        stats = calculate_life_statistics(
            birth_date=birth_date,
            life_expectancy=80,
            reference_date=reference_date,
        )

        assert 0.0 <= stats.percentage_lived <= 1.0
        assert 0.4 < stats.percentage_lived < 0.5

    def test_get_next_birthday_same_year(self) -> None:
        """Test getting next birthday when it occurs later this year."""
        birth_date = date(1990, 3, 15)
        reference_date = date(2024, 1, 15)

        stats = calculate_life_statistics(
            birth_date=birth_date,
            life_expectancy=80,
            reference_date=reference_date,
        )

        assert stats.next_birthday == date(2024, 3, 15)

    def test_get_next_birthday_next_year(self) -> None:
        """Test getting next birthday when it will be next year."""
        birth_date = date(1990, 3, 15)
        reference_date = date(2024, 6, 15)

        stats = calculate_life_statistics(
            birth_date=birth_date,
            life_expectancy=80,
            reference_date=reference_date,
        )

        assert stats.next_birthday == date(2025, 3, 15)

    def test_days_until_next_birthday(self) -> None:
        """Test calculation of days until next birthday."""
        birth_date = date(1990, 3, 15)
        reference_date = date(2024, 3, 14)

        stats = calculate_life_statistics(
            birth_date=birth_date,
            life_expectancy=80,
            reference_date=reference_date,
        )

        assert stats.days_until_birthday == 1

    def test_edge_case_newborn(self) -> None:
        """Test edge case for newborn (born today)."""
        birth_date = date(2024, 3, 15)
        reference_date = date(2024, 3, 15)

        stats = calculate_life_statistics(
            birth_date=birth_date,
            life_expectancy=80,
            reference_date=reference_date,
        )

        assert stats.age == 0
        assert stats.days_lived == 0
        assert stats.total_weeks_lived == 0

    def test_edge_case_elderly(self) -> None:
        """Test edge case for elderly person over life expectancy."""
        birth_date = date(1940, 3, 15)
        reference_date = date(2024, 3, 15)

        stats = calculate_life_statistics(
            birth_date=birth_date,
            life_expectancy=80,
            reference_date=reference_date,
        )

        # Remaining weeks should be 0 (not negative)
        assert stats.remaining_weeks == 0

        # Life percentage should be 1.0 (not more than 100%)
        assert stats.percentage_lived == 1.0


class TestLeapYearHandlingV2:
    """Test suite for leap year edge case handling."""

    def test_february_29_birthday_in_leap_year(self) -> None:
        """Test next birthday calculation for February 29 in a leap year."""
        birth_date = date(1996, 2, 29)
        reference_date = date(2024, 1, 15)  # 2024 is leap

        stats = calculate_life_statistics(
            birth_date=birth_date,
            life_expectancy=80,
            reference_date=reference_date,
        )

        assert stats.next_birthday == date(2024, 2, 29)

    def test_february_29_birthday_in_non_leap_year(self) -> None:
        """Test next birthday calculation for February 29 in a non-leap year."""
        birth_date = date(1996, 2, 29)
        reference_date = date(2023, 1, 15)  # 2023 is non-leap

        stats = calculate_life_statistics(
            birth_date=birth_date,
            life_expectancy=80,
            reference_date=reference_date,
        )

        assert stats.next_birthday == date(2023, 2, 28)

    def test_february_29_passed_this_year_leap(self) -> None:
        """Test next birthday calculation when February 29 has passed in leap year."""
        birth_date = date(1996, 2, 29)
        reference_date = date(2024, 3, 15)

        stats = calculate_life_statistics(
            birth_date=birth_date,
            life_expectancy=80,
            reference_date=reference_date,
        )

        # 2025 is non-leap
        assert stats.next_birthday == date(2025, 2, 28)

    def test_february_29_passed_this_year_non_leap(self) -> None:
        """Test next birthday calculation when February 29 has passed in non-leap year."""
        birth_date = date(1996, 2, 29)
        reference_date = date(2023, 3, 15)

        stats = calculate_life_statistics(
            birth_date=birth_date,
            life_expectancy=80,
            reference_date=reference_date,
        )

        # 2024 is leap
        assert stats.next_birthday == date(2024, 2, 29)
