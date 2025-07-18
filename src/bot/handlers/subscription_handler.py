"""Subscription command handler for user subscription management.

This module contains the SubscriptionHandler class which handles the /subscription command
and related callbacks. It allows users to view their subscription status and manage
subscription features.

The subscription management includes:
- Display current subscription status
- Show subscription benefits and features
- Manage subscription upgrades
- Handle subscription-related callbacks
"""

from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from ...core.messages import (
    generate_message_subscription_already_active,
    generate_message_subscription_change_error,
    generate_message_subscription_change_failed,
    generate_message_subscription_change_success,
    generate_message_subscription_current,
    generate_message_subscription_invalid_type,
    generate_message_subscription_profile_error,
    get_user_language,
)
from ...database.models import SubscriptionType
from ...database.service import user_service
from ...utils.localization import get_message
from ..constants import COMMAND_SUBSCRIPTION
from .base_handler import BaseHandler


class SubscriptionHandler(BaseHandler):
    """Handler for /subscription command and related callbacks.

    This handler manages user subscription information and provides
    subscription-related functionality including status display,
    upgrade options, and feature explanations.

    Attributes:
        command_name: Name of the command this handler processes
    """

    def __init__(self) -> None:
        """Initialize the subscription handler.

        Sets up the command name and initializes the base handler.
        """
        super().__init__()
        self.command_name = f"/{COMMAND_SUBSCRIPTION}"

    async def handle(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Handle /subscription command - show user subscription.

        This command allows users to view and manage their subscription.
        It provides a list of available subscriptions and allows users to change them.

        :param update: The update object containing the subscription command
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        return await self._wrap_with_registration(self._handle_subscription)(
            update, context
        )

    async def _handle_subscription(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Optional[int]:
        """Internal method to handle /subscription command with registration check.

        :param update: The update object containing the subscription command
        :type update: Update
        :param context: The context object for the command execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        # Extract user information
        user = update.effective_user
        self.log_command(user.id, self.command_name)
        self.logger.info(f"Handling /subscription command from user {user.id}")

        language = None

        try:
            # Get user profile with current subscription
            user_profile = user_service.get_user_profile(user.id)

            # Get user's language preference
            language = get_user_language(user, user_profile)

            if not user_profile or not user_profile.subscription:
                await update.message.reply_text(
                    get_message(
                        message_key="common",
                        sub_key="error",
                        language=language,
                    )
                )
                return

            current_subscription = user_profile.subscription.subscription_type

            # Create subscription selection keyboard
            keyboard = []
            for subscription_type in SubscriptionType:
                # Add checkmark for current subscription
                text = (
                    f"{'✅ ' if subscription_type == current_subscription else ''}"
                    f"{subscription_type.value.title()}"
                )
                callback_data = f"subscription_{subscription_type.value}"
                keyboard.append(
                    [InlineKeyboardButton(text, callback_data=callback_data)]
                )

            reply_markup = InlineKeyboardMarkup(keyboard)

            # Generate message using messages module
            message_text = generate_message_subscription_current(user_info=user)

            await update.message.reply_text(
                text=message_text, reply_markup=reply_markup, parse_mode="HTML"
            )

        except Exception as error:
            self.logger.error(f"Error in subscription command: {error}")
            # Use default language if language is not set
            fallback_language = language or get_user_language(user, None)
            await update.message.reply_text(
                get_message(
                    message_key="common",
                    sub_key="error",
                    language=fallback_language,
                )
            )

    async def handle_subscription_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle subscription selection callback from inline keyboard.

        This function processes the user's subscription selection and updates
        the database accordingly. It provides feedback about the change.

        :param update: The update object containing the callback
        :type update: Update
        :param context: The context object for the callback execution
        :type context: ContextTypes.DEFAULT_TYPE
        :returns: None
        """
        query = update.callback_query
        user = update.effective_user
        self.log_callback(user.id, query.data)

        try:
            # Answer the callback query to remove loading state
            await query.answer()

            # Extract subscription type from callback data
            callback_data = query.data
            if not callback_data.startswith("subscription_"):
                return

            subscription_value = callback_data.replace("subscription_", "")

            # Validate subscription type
            try:
                new_subscription_type = SubscriptionType(subscription_value)
            except ValueError:
                await query.edit_message_text(
                    text=generate_message_subscription_invalid_type(user_info=user),
                    parse_mode="HTML",
                )
                return

            # Get current user profile
            user_profile = user_service.get_user_profile(user.id)
            if not user_profile or not user_profile.subscription:
                await query.edit_message_text(
                    text=generate_message_subscription_profile_error(user_info=user),
                    parse_mode="HTML",
                )
                return

            current_subscription = user_profile.subscription.subscription_type

            # Check if subscription actually changed
            if current_subscription == new_subscription_type:
                await query.edit_message_text(
                    text=generate_message_subscription_already_active(
                        user_info=user, subscription_type=new_subscription_type.value
                    ),
                    parse_mode="HTML",
                )
                return

            # Update subscription in database
            success = user_service.update_user_subscription(
                user.id, new_subscription_type
            )

            if success:
                success_message = generate_message_subscription_change_success(
                    user_info=user, subscription_type=new_subscription_type.value
                )

                await query.edit_message_text(text=success_message, parse_mode="HTML")

                self.logger.info(
                    f"User {user.id} changed subscription from {current_subscription} to {new_subscription_type}"
                )
            else:
                await query.edit_message_text(
                    text=generate_message_subscription_change_failed(user_info=user),
                    parse_mode="HTML",
                )

        except Exception as error:
            self.logger.error(f"Error in subscription callback handler: {error}")
            await query.edit_message_text(
                text=generate_message_subscription_change_error(user_info=user),
                parse_mode="HTML",
            )
