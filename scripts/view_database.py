#!/usr/bin/env python3
"""Script to view database contents.

This script allows viewing all records from the database tables
without requiring sqlite3 CLI tool.
"""

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.constants import DEFAULT_DATABASE_PATH  # noqa: E402
from src.database.models import User, UserSettings, UserSubscription  # noqa: E402


def print_table_header(table_name: str) -> None:
    """Print table header.

    :param table_name: Name of the table
    :type table_name: str
    :returns: None
    """
    print(f"\n{'=' * 80}")
    print(f"Table: {table_name}")
    print(f"{'=' * 80}")


def print_user(user: User) -> None:
    """Print user information.

    :param user: User object
    :type user: User
    :returns: None
    """
    print(f"Telegram ID: {user.telegram_id}")
    print(f"  Username: {user.username or 'N/A'}")
    print(f"  First Name: {user.first_name or 'N/A'}")
    print(f"  Last Name: {user.last_name or 'N/A'}")
    print(f"  Created At: {user.created_at}")
    print()


def print_user_settings(settings: UserSettings) -> None:
    """Print user settings information.

    :param settings: UserSettings object
    :type settings: UserSettings
    :returns: None
    """
    print(f"Telegram ID: {settings.telegram_id}")
    print(f"  Birth Date: {settings.birth_date or 'N/A'}")
    print(f"  Language: {settings.language or 'N/A'}")
    print(f"  Life Expectancy: {settings.life_expectancy or 'N/A'} years")
    print(f"  Timezone: {settings.timezone or 'N/A'}")
    print(f"  Notifications Enabled: {settings.notifications}")
    print(f"  Notifications Day: {settings.notifications_day or 'N/A'}")
    print(f"  Notifications Time: {settings.notifications_time or 'N/A'}")
    print(f"  Updated At: {settings.updated_at}")
    print()


def print_user_subscription(subscription: UserSubscription) -> None:
    """Print user subscription information.

    :param subscription: UserSubscription object
    :type subscription: UserSubscription
    :returns: None
    """
    print(f"Telegram ID: {subscription.telegram_id}")
    print(f"  Subscription Type: {subscription.subscription_type.value}")
    print(f"  Is Active: {subscription.is_active}")
    print(f"  Created At: {subscription.created_at}")
    print(f"  Expires At: {subscription.expires_at or 'Never'}")
    print()


def main() -> None:
    """Main function to view database contents.

    :returns: None
    """
    # Get database path from environment or use default
    database_path = os.getenv("DATABASE_PATH", DEFAULT_DATABASE_PATH)
    database_url = f"sqlite:///{database_path}"
    engine = create_engine(database_url, echo=False)

    # Check if database exists
    if not Path(database_path).exists():
        print(f"Error: Database file '{database_path}' not found!")
        sys.exit(1)

    with Session(engine) as session:
        # Get all users
        print_table_header("users")
        users = session.scalars(select(User)).all()
        if not users:
            print("No users found.")
        else:
            print(f"Total users: {len(users)}\n")
            for user in users:
                print_user(user)

        # Get all user settings
        print_table_header("user_settings")
        settings_list = session.scalars(select(UserSettings)).all()
        if not settings_list:
            print("No user settings found.")
        else:
            print(f"Total user settings: {len(settings_list)}\n")
            for settings in settings_list:
                print_user_settings(settings)

        # Get all user subscriptions
        print_table_header("user_subscriptions")
        subscriptions = session.scalars(select(UserSubscription)).all()
        if not subscriptions:
            print("No user subscriptions found.")
        else:
            print(f"Total user subscriptions: {len(subscriptions)}\n")
            for subscription in subscriptions:
                print_user_subscription(subscription)

        # Summary
        print(f"\n{'=' * 80}")
        print("Summary:")
        print(f"  Users: {len(users)}")
        print(f"  User Settings: {len(settings_list)}")
        print(f"  User Subscriptions: {len(subscriptions)}")
        print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
