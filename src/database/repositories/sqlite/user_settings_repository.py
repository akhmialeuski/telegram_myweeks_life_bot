"""SQLite implementation of user settings repository.

Provides SQLite-based implementation of AbstractUserSettingsRepository
for storing user settings in SQLite database.
"""

import logging
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import update

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
        return self._create_entity(
            settings, f"settings for user {settings.telegram_id}"
        )

    def get_user_settings(self, telegram_id: int) -> Optional[UserSettings]:
        """Get user settings by Telegram ID.

        :param telegram_id: Telegram user ID
        :returns: UserSettings object if found, None otherwise
        """
        return self._get_entity_by_telegram_id(
            UserSettings, telegram_id, "user settings"
        )

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
        return self._delete_entity_by_telegram_id(UserSettings, telegram_id, "settings")
