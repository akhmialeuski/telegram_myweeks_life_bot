"""Core functionality for the LifeWeeksBot application.

This package contains the core business logic for life tracking,
statistics calculation, and data processing.
"""

from .life_calculator import LifeCalculationResult, calculate_life_statistics

__all__ = [
    "LifeCalculationResult",
    "calculate_life_statistics",
]
