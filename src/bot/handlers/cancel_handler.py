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

from ...core.messages import (
    generate_message_cancel_error,
    generate_message_cancel_success,
)
from ...database.service import user_service
from ...utils.config import BOT_NAME
from ...utils.logger import get_logger
from ..constants import COMMAND_CANCEL
from ..scheduler import remove_user_from_scheduler
from .base_handler import BaseHandler

# Initialize logger for this module
logger = get_logger(BOT_NAME)


class CancelHandler(BaseHandler):
    """Handler for /cancel command - delete user profile and data.

    This handler allows users to completely remove their profile and all
    associated data from the system. It's useful for users who want to
    start over or completely opt out of the service.

    Attributes:
        command_name: Name of the command this handler processes
    """

    def __init__(self) -> None:
        """Initialize the cancel handler.

        Sets up the command name and initializes the base handler.
        """
        super().__init__()
        self.command_name = f"/{COMMAND_CANCEL}"

    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle /cancel command - delete user profile and data.

        This command allows users to completely remove their profile and all
        associated data from the system. It's useful for users who want to
        start over or completely opt out of the service.

        The deletion process:
        1. Validates that user is registered (via decorator)
        2. Attempts to delete user profile and settings from database
        3. Provides feedback on success or failure
        4. Logs the operation for audit purposes

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
            User sends /cancel → Bot deletes profile → Shows confirmation message
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
        cmd_context = self._extract_command_context(update=update)
        user = cmd_context.user
        user_id = cmd_context.user_id
        user_lang = cmd_context.language

        logger.info(f"{self.command_name}: [{user_id}]: Handling command")

        try:
            # First remove user from notification scheduler
            scheduler = context.bot_data.get("scheduler")
            if scheduler:
                remove_user_from_scheduler(scheduler, user_id)
                logger.info(
                    f"{self.command_name}: [{user_id}]: User removed from notification scheduler"
                )
            else:
                logger.warning(
                    f"{self.command_name}: [{user_id}]: No scheduler available"
                )

            # Then attempt to delete user profile and all associated data
            logger.info(
                f"{self.command_name}: [{user_id}]: Deleting user profile and all associated data"
            )
            user_service.delete_user_profile(telegram_id=user_id)
            logger.info(
                f"{self.command_name}: [{user_id}]: User data deleted successfully"
            )

            # Send success confirmation message
            await self.send_message(
                update=update,
                message_text=generate_message_cancel_success(
                    user_info=user, language=user_lang
                ),
            )

        except Exception as error:
            # Handle all errors with a single error message
            await self.send_error_message(
                update=update,
                cmd_context=cmd_context,
                error_message=generate_message_cancel_error(
                    user_info=user,
                    error_message=str(error),
                ),
            )

        finally:
            # Always end conversation after cancel attempt, regardless of success or failure
            return ConversationHandler.END
