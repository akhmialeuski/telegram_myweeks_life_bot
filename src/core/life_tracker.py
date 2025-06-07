"""Core functionality for tracking life weeks and statistics."""

import datetime
from typing import Tuple
from ..utils.config import DATE_OF_BIRTH

def get_weeks_lived() -> int:
    """Calculate the number of weeks lived since birth date.

    :returns: The number of complete weeks lived since birth date.
    :rtype: int
    :note: Uses the DATE_OF_BIRTH environment variable for calculation.
    """
    birth_date = datetime.datetime.strptime(DATE_OF_BIRTH, "%Y-%m-%d").date()
    today = datetime.date.today()
    return (today - birth_date).days // 7

def get_months_lived() -> int:
    """Calculate the number of months lived since birth date.

    :returns: The number of complete months lived since birth date.
    :rtype: int
    """
    weeks_lived = get_weeks_lived()
    return weeks_lived // 4

def get_years_lived() -> Tuple[int, int]:
    """Calculate years and remaining weeks lived.

    :returns: Tuple of (years, remaining_weeks)
    :rtype: Tuple[int, int]
    """
    weeks_lived = get_weeks_lived()
    years = weeks_lived // 52
    remaining_weeks = weeks_lived % 52
    return years, remaining_weeks
