#!/usr/bin/env python3
"""Database viewer script for LifeWeeksBot.

This script allows you to view the contents of the database
including users and their settings.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from database import SQLAlchemyUserRepository, User, UserSettings
from database.constants import DEFAULT_DATABASE_PATH


def view_database():
    """View all data in the database."""
    print("=" * 60)
    print("LifeWeeksBot Database Viewer")
    print("=" * 60)

    # Initialize repository
    repo = SQLAlchemyUserRepository()
    repo.initialize()

    try:
        # Get all users
        users = repo.get_all_users()

        if not users:
            print("📭 База данных пуста - пользователей не найдено")
            return

        print(f"👥 Найдено пользователей: {len(users)}")
        print()

        for i, user in enumerate(users, 1):
            print(f"🔹 Пользователь #{i}")
            print(f"   ID: {user.telegram_id}")
            print(f"   Username: {user.username or 'Не указан'}")
            print(f"   Имя: {user.first_name or 'Не указано'}")
            print(f"   Фамилия: {user.last_name or 'Не указана'}")
            print(f"   Дата регистрации: {user.created_at}")

            # Get user settings
            settings = repo.get_user_settings(user.telegram_id)
            if settings:
                print(f"   📅 Дата рождения: {settings.birth_date or 'Не указана'}")
                print(f"   🔔 Уведомления: {'Включены' if settings.notifications else 'Отключены'}")
                print(f"   🌍 Часовой пояс: {settings.timezone or 'Не указан'}")
                print(f"   📅 День уведомлений: {settings.notifications_day or 'Не указан'}")
                print(f"   ⏰ Время уведомлений: {settings.notifications_time or 'Не указано'}")
                print(f"   📊 Ожидаемая продолжительность жизни: {settings.life_expectancy or 'Не указана'} лет")
                print(f"   🔄 Последнее обновление: {settings.updated_at}")
            else:
                print(f"   ⚠️  Настройки не найдены")

            print()

    except Exception as e:
        print(f"❌ Ошибка при чтении базы данных: {e}")

    finally:
        repo.close()


def view_specific_user(telegram_id: int):
    """View specific user by Telegram ID.

    :param telegram_id: Telegram user ID
    """
    print(f"=" * 60)
    print(f"Просмотр пользователя {telegram_id}")
    print(f"=" * 60)

    # Initialize repository
    repo = SQLAlchemyUserRepository()
    repo.initialize()

    try:
        # Get user profile
        user_profile = repo.get_user_profile(telegram_id)

        if not user_profile:
            print(f"❌ Пользователь с ID {telegram_id} не найден")
            return

        user = user_profile.user
        settings = user_profile.settings

        print(f"👤 Пользователь:")
        print(f"   ID: {user.telegram_id}")
        print(f"   Username: {user.username or 'Не указан'}")
        print(f"   Имя: {user.first_name or 'Не указано'}")
        print(f"   Фамилия: {user.last_name or 'Не указана'}")
        print(f"   Дата регистрации: {user.created_at}")
        print()

        print(f"⚙️  Настройки:")
        print(f"   Дата рождения: {settings.birth_date or 'Не указана'}")
        print(f"   Уведомления: {'Включены' if settings.notifications else 'Отключены'}")
        print(f"   Часовой пояс: {settings.timezone or 'Не указан'}")
        print(f"   День уведомлений: {settings.notifications_day or 'Не указан'}")
        print(f"   Время уведомлений: {settings.notifications_time or 'Не указано'}")
        print(f"   Ожидаемая продолжительность жизни: {settings.life_expectancy or 'Не указана'} лет")
        print(f"   Последнее обновление: {settings.updated_at}")

        if settings.birth_date:
            from datetime import date
            today = date.today()
            days_lived = (today - settings.birth_date).days
            weeks_lived = days_lived // 7
            age = today.year - settings.birth_date.year
            if today.month < settings.birth_date.month or (today.month == settings.birth_date.month and today.day < settings.birth_date.day):
                age -= 1

            print()
            print(f"📊 Статистика:")
            print(f"   Возраст: {age} лет")
            print(f"   Дней прожито: {days_lived:,}")
            print(f"   Недель прожито: {weeks_lived:,}")

    except Exception as e:
        print(f"❌ Ошибка при чтении пользователя: {e}")

    finally:
        repo.close()


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="LifeWeeksBot Database Viewer")
    parser.add_argument("--user", "-u", type=int, help="Telegram ID пользователя для просмотра")
    parser.add_argument("--file", "-f", help="Путь к файлу базы данных (по умолчанию: lifeweeks.db)")

    args = parser.parse_args()

    if args.file:
        # Override default database path
        import os
        os.environ["DATABASE_PATH"] = args.file

    if args.user:
        view_specific_user(args.user)
    else:
        view_database()


if __name__ == "__main__":
    main()