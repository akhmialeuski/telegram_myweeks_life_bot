"""Notification gateways for delivering notifications.

This package provides implementations of NotificationGatewayProtocol
for various delivery channels.
"""

from .logging_gateway import LoggingGateway
from .telegram_gateway import TelegramNotificationGateway

__all__: list[str] = [
    "TelegramNotificationGateway",
    "LoggingGateway",
]
