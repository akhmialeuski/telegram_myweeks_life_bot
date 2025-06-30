#!/usr/bin/env python3
"""Database setup script for LifeWeeksBot.

This script initializes the database and runs all migrations
to ensure the database schema is up to date.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from database.constants import DEFAULT_DATABASE_PATH, DATABASE_DIRECTORY


def run_command(command: list[str], description: str) -> bool:
    """Run a shell command and handle errors.

    :param command: List of command arguments
    :param description: Description of what the command does
    :returns: True if successful, False otherwise
    """
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def setup_database() -> bool:
    """Set up the database with all migrations.

    :returns: True if successful, False otherwise
    """
    print("🚀 Setting up LifeWeeksBot database...")

    # Create database directory if it doesn't exist
    db_dir = Path(DATABASE_DIRECTORY)
    if not db_dir.exists():
        print(f"📁 Creating database directory: {db_dir}")
        db_dir.mkdir(parents=True, exist_ok=True)

    # Check if alembic is installed
    try:
        import alembic
        print(f"✅ Alembic version {alembic.__version__} is available")
    except ImportError:
        print("❌ Alembic is not installed. Please install it with: pip install alembic")
        return False

    # Run alembic upgrade to apply all migrations
    if not run_command(["alembic", "upgrade", "head"], "Applying database migrations"):
        return False

    print(f"🎉 Database setup completed! Database file: {DEFAULT_DATABASE_PATH}")
    return True


def create_initial_data() -> bool:
    """Create initial data in the database (optional).

    :returns: True if successful, False otherwise
    """
    print("📝 Creating initial data...")

    try:
        from database import SQLAlchemyUserRepository

        # Initialize repository
        repo = SQLAlchemyUserRepository()
        repo.initialize()

        # You can add initial data here if needed
        # For example, create a test user or default settings

        repo.close()
        print("✅ Initial data created successfully")
        return True

    except Exception as e:
        print(f"❌ Failed to create initial data: {e}")
        return False


def main():
    """Main function to set up the database."""
    print("=" * 50)
    print("LifeWeeksBot Database Setup")
    print("=" * 50)

    # Set up database
    if not setup_database():
        print("❌ Database setup failed!")
        sys.exit(1)

    # Create initial data (optional)
    create_initial_data()

    print("=" * 50)
    print("✅ Database setup completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()