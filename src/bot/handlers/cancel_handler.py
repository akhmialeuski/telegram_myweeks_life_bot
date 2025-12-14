"""Cancel command handler for operation cancellation.

This module contains the CancelHandler class which handles the /cancel command
and allows users to cancel ongoing operations and conversations.

The cancel functionality includes:
- Cancel current conversation state
- Clear user input context
- Return to main menu
- Reset bot state
"""

from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.events.domain_events import UserDeletedEvent
from src.i18n import use_locale

from ...services.container import ServiceContainer
from ...utils.config import BOT_NAME
from ...utils.logger import get_logger
from ..constants import COMMAND_CANCEL
from .base_handler import BaseHandler

# Initialize logger for this module
logger = get_logger(BOT_NAME)


class CancelHandler(BaseHandler):
    """Handler for /cancel command - cancel conversation and delete user data.

    This handler allows users to cancel the current conversation state, clear
    user input context, return to the main menu, reset the bot state, and
    completely remove their profile and all associated data from the system.
    It's useful for users who want to start over or completely opt out of
    the service.

    The cancel functionality includes:
    - Cancel current conversation state
    - Clear user input context
    - Return to main menu
    - Reset bot state
    - Remove user from notification scheduler
    - Delete user profile and all associated data

    Attributes:
        command_name: Name of the command this handler processes
    """

    def __init__(self, services: ServiceContainer) -> None:
        """Initialize the cancel handler.

        Sets up the command name and initializes the base handler.

        :param services: Service container with all dependencies
        :type services: ServiceContainer
        """
        super().__init__(services)
        self.command_name = f"/{COMMAND_CANCEL}"

    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle /cancel command - cancel conversation and delete user data.

        This command allows users to cancel the current conversation state,
        clear user input context, return to the main menu, reset the bot state,
        and completely remove their profile and all associated data from the system.
        It's useful for users who want to start over or completely opt out of
        the service.

        The cancellation process:
        1. Validates that user is registered (via decorator)
        2. Removes user from notification scheduler
        3. Attempts to delete user profile and settings from database
        4. Provides feedback on success or failure
        5. Logs the operation for audit purposes
        6. Ends conversation state

        Error handling:
        - UserDeletionError: Specific deletion failures
        - UserServiceError: General service errors
        - SchedulerOperationError: Scheduler operation failures
        - All cases: Show error message to user

        :param update: The update object containing the cancel command
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: Conversation state (always END)
        :rtype: Optional[int]

        Example:
            User sends /cancel → Bot cancels conversation and deletes profile → Shows confirmation message
        """
        return await self._wrap_with_registration(self._handle_cancel)(
            update=update,
            context=context,
        )

    async def _handle_cancel(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Internal method to handle /cancel command with registration check.

        :param update: The update object containing the cancel command
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: Conversation state (always END)
        :rtype: Optional[int]
        """
        cmd_context = await self._extract_command_context(update=update)
        user = cmd_context.user
        user_id = cmd_context.user_id

        logger.info(f"{self.command_name}: [{user_id}]: Handling command")

        # Resolve language from DB profile or Telegram fallback
        profile = await self.services.user_service.get_user_profile(telegram_id=user_id)
        lang = (
            profile.settings.language
            if profile and profile.settings and profile.settings.language
            else (user.language_code or "en")
        )
        _, _, pgettext = use_locale(lang=lang)

        try:
            # Attempt to delete user profile and all associated data
            # Notification cleanup will be handled via domain event
            logger.info(
                f"{self.command_name}: [{user_id}]: Deleting user profile and all associated data"
            )
            await self.services.user_service.delete_user_profile(telegram_id=user_id)
            logger.info(
                f"{self.command_name}: [{user_id}]: User data deleted successfully"
            )

            # Publish event to trigger cleanup in other services (scheduler, etc.)
            await self.services.event_bus.publish(UserDeletedEvent(user_id=user_id))
            logger.info(f"{self.command_name}: [{user_id}]: Published UserDeletedEvent")

            # Send success confirmation message
            await self.send_message(
                update=update,
                message_text=pgettext(
                    "cancel.success",
                    "✅ %(first_name)s, all your data has been successfully deleted.\n"
                    "Use /start for re-registration.",
                )
                % {"first_name": user.first_name},
            )

        except Exception:
            # Handle all errors with a single error message
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=pgettext(
                    "cancel.error",
                    "❌ An error occurred while deleting your data.\n"
                    "Please try again or contact the administrator.",
                ),
            )

        finally:
            # Always end conversation after cancel attempt, regardless of success or failure
            return ConversationHandler.END
