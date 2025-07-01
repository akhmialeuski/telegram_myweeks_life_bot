#!/usr/bin/env python3
"""Script to check database schema and constraints."""

import sqlite3
from pathlib import Path


def check_schema():
    """Check database schema and constraints."""
    db_path = Path("lifeweeks.db")

    if not db_path.exists():
        print("❌ Database file not found!")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("==========================================")
        print("Database Schema Check")
        print("==========================================")

        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 Tables found: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")

        print("\n📊 Table Schemas:")

        # Check users table
        cursor.execute("PRAGMA table_info(users);")
        users_columns = cursor.fetchall()
        print("\n👥 Users table:")
        for col in users_columns:
            print(
                f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'PRIMARY KEY' if col[5] else ''}"
            )

        # Check user_settings table
        cursor.execute("PRAGMA table_info(user_settings);")
        settings_columns = cursor.fetchall()
        print("\n⚙️ User Settings table:")
        for col in settings_columns:
            print(
                f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'PRIMARY KEY' if col[5] else ''}"
            )

        # Check indexes
        cursor.execute("PRAGMA index_list(user_settings);")
        indexes = cursor.fetchall()
        print("\n🔍 Indexes on user_settings:")
        for idx in indexes:
            print(f"  - {idx[1]} (unique: {idx[2]})")

        # Check foreign keys
        cursor.execute("PRAGMA foreign_key_list(user_settings);")
        foreign_keys = cursor.fetchall()
        print("\n🔗 Foreign Keys on user_settings:")
        for fk in foreign_keys:
            print(f"  - {fk[3]} -> {fk[4]}.{fk[5]}")

        # Check unique constraints
        cursor.execute("PRAGMA index_list(user_settings);")
        indexes = cursor.fetchall()
        unique_constraints = [idx for idx in indexes if idx[2] == 1]
        print("\n🔒 Unique Constraints on user_settings:")
        for constraint in unique_constraints:
            print(f"  - {constraint[1]}")

        conn.close()
        print("\n✅ Schema check completed!")

    except Exception as e:
        print(f"❌ Error checking schema: {e}")


if __name__ == "__main__":
    check_schema()
