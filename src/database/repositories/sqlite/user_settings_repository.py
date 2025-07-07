"""SQLite implementation of user settings repository.

Provides SQLite-based implementation of AbstractUserSettingsRepository
for storing user settings in SQLite database.
"""

import logging
from datetime import UTC, date, datetime, time
from typing import Optional

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from ....utils.config import BOT_NAME
from ...models import UserSettings
from ..abstract.user_settings_repository import AbstractUserSettingsRepository
from .base_repository import BaseSQLiteRepository

logger = logging.getLogger(BOT_NAME)


class SQLiteUserSettingsRepository(
    BaseSQLiteRepository, AbstractUserSettingsRepository
):
    """SQLite implementation of user settings repository.

    Handles all database operations for user settings using SQLite as the backend storage.
    """

    def create_user_settings(self, settings: UserSettings) -> bool:
        """Create user settings.

        :param settings: UserSettings object to create
        :returns: True if successful, False otherwise
        """
        try:
            with self.session() as session:
                session.add(settings)
                logger.info(f"Created settings for user {settings.telegram_id}")
                return True

        except IntegrityError:
            logger.warning(f"Settings for user {settings.telegram_id} already exist")
            return False
        except Exception as e:
            logger.error(f"Failed to create user settings: {e}")
            return False

    def get_user_settings(self, telegram_id: int) -> Optional[UserSettings]:
        """Get user settings by Telegram ID.

        :param telegram_id: Telegram user ID
        :returns: UserSettings object if found, None otherwise
        """
        try:
            with self.session() as session:
                stmt = select(UserSettings).where(
                    UserSettings.telegram_id == telegram_id
                )
                result = session.execute(stmt)
                settings = result.scalar_one_or_none()
                if settings:
                    self._detach_instance(session, settings)
                return settings

        except Exception as e:
            logger.error(f"Failed to get user settings {telegram_id}: {e}")
            return None

    def update_user_settings(self, settings: UserSettings) -> bool:
        """Update user settings.

        :param settings: UserSettings object with updated data
        :returns: True if successful, False otherwise
        """
        try:
            with self.session() as session:
                stmt = (
                    update(UserSettings)
                    .where(UserSettings.telegram_id == settings.telegram_id)
                    .values(
                        birth_date=settings.birth_date,
                        notifications_day=settings.notifications_day,
                        life_expectancy=settings.life_expectancy,
                        timezone=settings.timezone,
                        notifications=settings.notifications,
                        notifications_time=settings.notifications_time,
                        updated_at=datetime.now(UTC),
                    )
                )
                result = session.execute(stmt)

                if result.rowcount > 0:
                    logger.info(f"Updated settings for user {settings.telegram_id}")
                    return True
                else:
                    logger.warning(
                        f"Settings for user {settings.telegram_id} not found"
                    )
                    return False

        except Exception as e:
            logger.error(f"Failed to update user settings: {e}")
            return False

    def delete_user_settings(self, telegram_id: int) -> bool:
        """Delete user settings.

        :param telegram_id: Telegram user ID
        :returns: True if successful, False otherwise
        """
        try:
            with self.session() as session:
                stmt = delete(UserSettings).where(
                    UserSettings.telegram_id == telegram_id
                )
                result = session.execute(stmt)

                if result.rowcount > 0:
                    logger.info(f"Deleted settings for user {telegram_id}")
                    return True
                else:
                    logger.warning(f"Settings for user {telegram_id} not found")
                    return False

        except Exception as e:
            logger.error(f"Failed to delete user settings: {e}")
            return False

    def set_birth_date(self, telegram_id: int, birth_date: date) -> bool:
        """Set user birth date.

        :param telegram_id: Telegram user ID
        :param birth_date: Birth date to set
        :returns: True if successful, False otherwise
        """
        try:
            with self.session() as session:
                stmt = select(UserSettings).where(
                    UserSettings.telegram_id == telegram_id
                )
                result = session.execute(stmt)
                settings = result.scalar_one_or_none()

                if settings:
                    settings.birth_date = birth_date
                    settings.updated_at = datetime.now(UTC)
                    return True
                else:
                    # Create new settings with birth date
                    new_settings = UserSettings(
                        telegram_id=telegram_id,
                        birth_date=birth_date,
                        updated_at=datetime.now(UTC),
                    )
                    return self.create_user_settings(new_settings)

        except Exception as e:
            logger.error(f"Failed to set birth date: {e}")
            return False

    def get_birth_date(self, telegram_id: int) -> Optional[date]:
        """Get user birth date.

        :param telegram_id: Telegram user ID
        :returns: Birth date if set, None otherwise
        """
        settings = self.get_user_settings(telegram_id)
        return settings.birth_date if settings else None

    def set_notification_settings(
        self,
        telegram_id: int,
        notifications: bool,
        notifications_day: Optional[str] = None,
        notifications_time: Optional[time] = None,
    ) -> bool:
        """Set notification settings.

        :param telegram_id: Telegram user ID
        :param notifications: Whether notifications are enabled
        :param notifications_day: Day of week for notifications
        :param notifications_time: Time for notifications
        :returns: True if successful, False otherwise
        """
        try:
            with self.session() as session:
                stmt = select(UserSettings).where(
                    UserSettings.telegram_id == telegram_id
                )
                result = session.execute(stmt)
                settings = result.scalar_one_or_none()

                if settings:
                    settings.notifications = notifications
                    settings.notifications_day = notifications_day
                    settings.notifications_time = notifications_time
                    settings.updated_at = datetime.now(UTC)
                    return True
                else:
                    # Create new settings with notification settings
                    new_settings = UserSettings(
                        telegram_id=telegram_id,
                        notifications=notifications,
                        notifications_day=notifications_day,
                        notifications_time=notifications_time,
                        updated_at=datetime.now(UTC),
                    )
                    return self.create_user_settings(new_settings)

        except Exception as e:
            logger.error(f"Failed to set notification settings: {e}")
            return False
