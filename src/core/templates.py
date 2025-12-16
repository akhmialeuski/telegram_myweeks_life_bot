"""Message templates and keys.

This module contains keys and default messages for the application's
internationalization system.
"""

from typing import Final

# Start / Registration
START_WELCOME_EXISTING_KEY: Final[str] = "start.welcome_existing"
START_WELCOME_EXISTING_DEFAULT: Final[str] = (
    "👋 Hello, %(first_name)s! Welcome back to LifeWeeksBot!\n\n"
    "You are already registered and ready to track your life weeks.\n\n"
    "Use /weeks to view your life weeks.\n"
    "Use /help for help."
)

START_WELCOME_NEW_KEY: Final[str] = "start.welcome_new"
START_WELCOME_NEW_DEFAULT: Final[str] = (
    "👋 Hello, %(first_name)s! Welcome to LifeWeeksBot!\n\n"
    "This bot will help you track the weeks of your life.\n\n"
    "📅 Please enter your birth date in DD.MM.YYYY format\n"
    "For example: 15.03.1990"
)

REGISTRATION_SUCCESS_KEY: Final[str] = "registration.success"
REGISTRATION_SUCCESS_DEFAULT: Final[str] = (
    "✅ Great! You have successfully registered!\n\n"
    "📅 Birth date: %(birth_date)s\n"
    "🎂 Age: %(age)s years\n"
    "📊 Weeks lived: %(weeks_lived)s\n"
    "⏳ Remaining weeks: %(remaining_weeks)s\n"
    "📈 Life progress: %(life_percentage)s\n\n"
    "Now you can use commands:\n"
    "• /weeks - show life weeks\n"
    "• /visualize - visualize weeks\n"
    "• /help - help"
)

REGISTRATION_ERROR_KEY: Final[str] = "registration.error"
REGISTRATION_ERROR_DEFAULT: Final[str] = (
    "❌ An error occurred during registration.\n"
    "Try again or contact the administrator."
)

# Validation Error Messages
BIRTH_DATE_FUTURE_KEY: Final[str] = "birth_date.future_error"
BIRTH_DATE_FUTURE_DEFAULT: Final[str] = (
    "❌ Birth date cannot be in the future!\n"
    "Please enter a valid date in DD.MM.YYYY format"
)

BIRTH_DATE_TOO_OLD_KEY: Final[str] = "birth_date.old_error"
BIRTH_DATE_TOO_OLD_DEFAULT: Final[str] = (
    "❌ Birth date is too old!\n" "Please enter a valid date in DD.MM.YYYY format"
)

BIRTH_DATE_FORMAT_KEY: Final[str] = "birth_date.format_error"
BIRTH_DATE_FORMAT_DEFAULT: Final[str] = (
    "❌ Invalid date format!\n"
    "Please enter date in DD.MM.YYYY format\n"
    "For example: 15.03.1990"
)

# Common
COMMON_NOT_REGISTERED_KEY: Final[str] = "common.not_registered"
COMMON_NOT_REGISTERED_DEFAULT: Final[str] = (
    "You are not registered. Use /start to register."
)


# Help
HELP_MAIN_KEY: Final[str] = "help.text"
HELP_MAIN_DEFAULT: Final[str] = (
    "🤖 LifeWeeksBot - Helps you track the weeks of your life\n\n"
    "📋 Available commands:\n"
    "• /start - Registration and settings\n"
    "• /weeks - Show life weeks\n"
    "• /visualize - Visualize life weeks\n"
    "• /settings - Settings\n"
    "• /subscription - Subscription\n"
    "• /help - This help\n\n"
    "💡 Fun facts:\n"
    "• There are 52 weeks in a year\n"
    "• Average life expectancy: 80 years\n"
    "• That's about 4,160 weeks\n\n"
    "🎯 The goal of the bot is to help you realize the value of time!"
)


# Subscription
SUBSCRIPTION_STATUS_ACTIVE_KEY: Final[str] = "subscription.status_active"
SUBSCRIPTION_STATUS_ACTIVE_DEFAULT: Final[str] = (
    "✅ *Premium Subscription Active*\n\n"
    "Expires on: %(expiry_date)s\n"
    "Plan: %(plan_name)s"
)

SUBSCRIPTION_STATUS_INACTIVE_KEY: Final[str] = "subscription.status_inactive"
SUBSCRIPTION_STATUS_INACTIVE_DEFAULT: Final[str] = (
    "❌ *No Active Subscription*\n\n"
    "Upgrade to Premium to unlock:\n"
    "• High-resolution visualizations\n"
    "• PDF exports\n"
    "• Dark mode themes\n"
    "• Cloud backup"
)

SUBSCRIPTION_BASIC_INFO_KEY: Final[str] = "subscription.basic_info"
SUBSCRIPTION_BASIC_INFO_DEFAULT: Final[str] = (
    "💡 <b>Basic Subscription</b>\n\n"
    "You are using the basic version of the bot with core functionality.\n\n"
    "🔗 <b>Support the project:</b>\n"
    "• GitHub: https://github.com/your-project/lifeweeks-bot\n"
    "• Donate: {buymeacoffee_url}\n\n"
    "Your support helps develop the bot! 🙏"
)

SUBSCRIPTION_PREMIUM_CONTENT_KEY: Final[str] = "subscription.premium_content"
SUBSCRIPTION_PREMIUM_CONTENT_DEFAULT: Final[str] = (
    "✨ <b>Premium Content</b>\n\n"
    "🧠 <b>Psychology of Time:</b>\n"
    "Research shows that time visualization helps make more conscious decisions. When we see the limitation of our weeks, we begin to value each one.\n\n"
    "📊 <b>Interesting Facts:</b>\n"
    "• Average person spends 26 years sleeping (about 1,352 weeks)\n"
    "• 11 years working (572 weeks)\n"
    "• 5 years eating and cooking (260 weeks)\n"
    "• 4 years commuting (208 weeks)\n\n"
    "🎯 <b>Daily Tip:</b> Try doing something new every week - it will help make life more fulfilling and memorable!"
)

SUBSCRIPTION_MANAGEMENT_KEY: Final[str] = "subscription.management"
SUBSCRIPTION_MANAGEMENT_DEFAULT: Final[str] = (
    "🔐 <b>Subscription Management</b>\n\n"
    "Current subscription: <b>{subscription_type}</b>\n"
    "{subscription_description}\n\n"
    "Select new subscription type:"
)

SUBSCRIPTION_ALREADY_ACTIVE_KEY: Final[str] = "subscription.already_active"
SUBSCRIPTION_ALREADY_ACTIVE_DEFAULT: Final[str] = (
    "ℹ️ You already have an active <b>{subscription_type}</b> subscription"
)

SUBSCRIPTION_CHANGE_SUCCESS_KEY: Final[str] = "subscription.change_success"
SUBSCRIPTION_CHANGE_SUCCESS_DEFAULT: Final[str] = (
    "✅ <b>Subscription successfully changed!</b>\n\n"
    "New subscription: <b>{subscription_type}</b>\n"
    "{subscription_description}\n\n"
    "Changes took effect immediately."
)

SUBSCRIPTION_CHANGE_FAILED_KEY: Final[str] = "subscription.change_failed"
SUBSCRIPTION_CHANGE_FAILED_DEFAULT: Final[str] = (
    "❌ Failed to change subscription. Please try again later."
)

SUBSCRIPTION_CHANGE_ERROR_KEY: Final[str] = "subscription.change_error"
SUBSCRIPTION_CHANGE_ERROR_DEFAULT: Final[str] = (
    "❌ An error occurred while changing subscription"
)
