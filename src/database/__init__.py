"""Database package for LifeWeeksBot.

This package provides data models and database abstraction layer
for storing user profiles and settings using SQLAlchemy 2.0.
"""

from .abstract_repository import AbstractUserRepository
from .constants import DEFAULT_DATABASE_PATH
from .models import Base, User, UserSettings
from .sqlite_repository import SQLAlchemyUserRepository

__all__ = [
    "Base",
    "User",
    "UserSettings",
    "AbstractUserRepository",
    "SQLAlchemyUserRepository",
    "DEFAULT_DATABASE_PATH",
]
