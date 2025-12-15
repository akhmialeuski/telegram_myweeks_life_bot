"""Abstract base handler for settings-related operations.

This module provides the AbstractSettingsHandler class which contains common
functionality for all settings handlers, including state management and validation.
"""

from abc import abstractmethod
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from src.bot.conversations.persistence import TelegramContextPersistence
from src.bot.conversations.states import ConversationState
from src.bot.handlers.base_handler import BaseHandler
from src.services.container import ServiceContainer


class AbstractSettingsHandler(BaseHandler):
    """Abstract base class for settings handlers.

    This class extends BaseHandler with common functionality needed for
    settings management, particularly FSM state handling.

    :ivar _persistence: Persistence handler for FSM states
    :type _persistence: TelegramContextPersistence
    """

    def __init__(self, services: ServiceContainer) -> None:
        """Initialize the abstract settings handler.

        :param services: Service container with dependencies
        :type services: ServiceContainer
        """
        super().__init__(services)
        self._persistence = TelegramContextPersistence()

    @abstractmethod
    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle the initial request for this setting.

        :param update: The update object
        :type update: Update
        :param context: The context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: Optional state or None
        :rtype: Optional[int]
        """
        pass

    @abstractmethod
    async def handle_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle callback query for this setting.

        :param update: The update object
        :type update: Update
        :param context: The context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        pass

    async def _set_waiting_state(
        self,
        user_id: int,
        state: ConversationState,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Set the user's waiting state.

        :param user_id: Telegram user ID
        :type user_id: int
        :param state: The state to set
        :type state: ConversationState
        :param context: The context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        await self._persistence.set_state(
            user_id=user_id,
            state=state,
            context=context,
        )

    async def _is_valid_waiting_state(
        self,
        user_id: int,
        expected_state: ConversationState,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> bool:
        """Check if the user is in the expected waiting state.

        :param user_id: Telegram user ID
        :type user_id: int
        :param expected_state: The expected state
        :type expected_state: ConversationState
        :param context: The context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: True if state is valid, False otherwise
        :rtype: bool
        """
        return await self._persistence.is_state_valid(
            user_id=user_id,
            expected_state=expected_state,
            context=context,
        )

    async def _clear_waiting_state(
        self,
        user_id: int,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """Clear the user's waiting state.

        :param user_id: Telegram user ID
        :type user_id: int
        :param context: The context object
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        await self._persistence.clear_state(
            user_id=user_id,
            context=context,
        )
