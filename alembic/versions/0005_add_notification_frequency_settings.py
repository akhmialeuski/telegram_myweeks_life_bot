"""add_notification_frequency_settings

Revision ID: 0005
Revises: 0004
Create Date: 2026-02-14
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


NOTIFICATION_FREQUENCY_ENUM = sa.Enum(
    "daily",
    "weekly",
    "monthly",
    name="notificationfrequency",
)


def upgrade() -> None:
    """Add notification frequency fields to user_settings."""
    op.add_column(
        "user_settings",
        sa.Column(
            "notification_frequency",
            NOTIFICATION_FREQUENCY_ENUM,
            nullable=False,
            server_default="weekly",
        ),
    )
    op.add_column(
        "user_settings",
        sa.Column("notifications_month_day", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Remove notification frequency fields from user_settings."""
    op.drop_column("user_settings", "notifications_month_day")
    op.drop_column("user_settings", "notification_frequency")
