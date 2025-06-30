"""Core functionality for tracking life weeks and statistics."""

import datetime
from typing import Tuple

def get_weeks_lived(birth_date: str) -> int:
    """Calculate the number of weeks lived since birth date.

    :param birth_date: Birth date in YYYY-MM-DD format
    :type birth_date: str
    :returns: The number of complete weeks lived since birth date.
    :rtype: int
    """
    birth_date_obj = datetime.datetime.strptime(birth_date, "%Y-%m-%d").date()
    today = datetime.date.today()
    return (today - birth_date_obj).days // 7

def get_months_lived(birth_date: str) -> int:
    """Calculate the number of months lived since birth date.

    :param birth_date: Birth date in YYYY-MM-DD format
    :type birth_date: str
    :returns: The number of complete months lived since birth date.
    :rtype: int
    """
    weeks_lived = get_weeks_lived(birth_date)
    return weeks_lived // 4

def get_years_lived(birth_date: str) -> Tuple[int, int]:
    """Calculate years and remaining weeks lived.

    :param birth_date: Birth date in YYYY-MM-DD format
    :type birth_date: str
    :returns: Tuple of (years, remaining_weeks)
    :rtype: Tuple[int, int]
    """
    weeks_lived = get_weeks_lived(birth_date)
    years = weeks_lived // 52
    remaining_weeks = weeks_lived % 52
    return years, remaining_weeks
