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
    get_user_language,
)
from ...database.service import (
    UserDeletionError,
    UserServiceError,
    user_service,
)
from ..constants import COMMAND_CANCEL
from ..scheduler import remove_user_from_scheduler
from .base_handler import BaseHandler


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
        - Both cases: Show error message to user

        :param update: The update object containing the cancel command
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: Conversation state (always END)
        :rtype: Optional[int]

        Example:
            User sends /cancel → Bot deletes profile → Shows confirmation message
        """
        return await self._wrap_with_registration(self._handle_cancel)(update, context)

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
        # Extract user information
        user = update.effective_user
        user_id = user.id
        self.log_command(user_id, self.command_name)
        self.logger.info(f"Handling /cancel command from user {user_id}")

        try:
            # First remove user from notification scheduler
            scheduler_success = remove_user_from_scheduler(user_id)
            if scheduler_success:
                self.logger.info(f"User {user_id} removed from notification scheduler")
            else:
                self.logger.warning(
                    f"Failed to remove user {user_id} from notification scheduler"
                )

            # Then attempt to delete user profile and all associated data
            user_lang = get_user_language(user)
            user_service.delete_user_profile(user_id)

            # Send success confirmation message
            await update.message.reply_text(
                text=generate_message_cancel_success(
                    user_info=user, language=user_lang
                ),
                parse_mode="HTML",
            )
            self.logger.info(f"User {user_id} data deleted via /cancel command")

        except UserDeletionError as error:
            # Handle specific deletion failures
            await update.message.reply_text(
                text=generate_message_cancel_error(user_info=user),
                parse_mode="HTML",
            )
            self.logger.error(
                f"Failed to delete user {user_id} data via /cancel command: {error}"
            )

        except UserServiceError as error:
            # Handle general service errors
            await update.message.reply_text(
                text=generate_message_cancel_error(user_info=user),
                parse_mode="HTML",
            )
            self.logger.error(
                f"Service error during user {user_id} deletion via /cancel command: {error}"
            )

        # Always end conversation after cancel attempt
        return ConversationHandler.END
