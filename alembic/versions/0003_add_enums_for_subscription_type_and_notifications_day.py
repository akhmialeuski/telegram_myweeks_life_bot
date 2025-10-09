"""Add enums for subscription_type and notifications_day

Revision ID: 0003
Revises: 0002
Create Date: 2025-01-27 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add subscription_type column to user_subscriptions and change notifications_day to enum."""

    # Check if subscription_type column already exists, if not add it
    conn = op.get_bind()
    result = conn.execute(sa.text("PRAGMA table_info(user_subscriptions)"))
    columns = [row[1] for row in result.fetchall()]

    if "subscription_type" not in columns:
        with op.batch_alter_table("user_subscriptions") as batch_op:
            batch_op.add_column(
                sa.Column(
                    "subscription_type",
                    sa.Enum("basic", "premium", "trial", name="subscriptiontype"),
                    nullable=False,
                    server_default="basic",
                )
            )

    # For user_subscriptions table, recreate it to change subscription_type to enum
    op.create_table(
        "user_subscriptions_temp",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column(
            "subscription_type",
            sa.Enum("basic", "premium", "trial", name="subscriptiontype"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["telegram_id"], ["users.telegram_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )

    # Copy data from old table to new table with default value
    op.execute(
        """
        INSERT INTO user_subscriptions_temp
        (id, telegram_id, subscription_type, is_active, created_at, expires_at)
        SELECT id, telegram_id,
               CASE
                   WHEN subscription_type = 'basic' THEN 'basic'
                   WHEN subscription_type = 'premium' THEN 'premium'
                   WHEN subscription_type = 'trial' THEN 'trial'
                   ELSE 'basic'
               END as subscription_type,
               is_active, created_at, expires_at
        FROM user_subscriptions
    """
    )

    # Drop old table and rename new one
    op.drop_table("user_subscriptions")
    op.rename_table("user_subscriptions_temp", "user_subscriptions")

    # For notifications_day in user_settings, recreate the table
    op.create_table(
        "user_settings_temp",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column(
            "notifications_day",
            sa.Enum(
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
                name="weekday",
            ),
            nullable=True,
        ),
        sa.Column("life_expectancy", sa.Integer(), nullable=True),
        sa.Column("timezone", sa.String(length=100), nullable=True),
        sa.Column("notifications", sa.Boolean(), nullable=True),
        sa.Column("notifications_time", sa.Time(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["telegram_id"], ["users.telegram_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )

    # Copy data with case conversion
    op.execute(
        """
        INSERT INTO user_settings_temp
        (id, telegram_id, birth_date, notifications_day, life_expectancy, timezone, notifications, notifications_time, updated_at)
        SELECT id, telegram_id, birth_date,
               CASE
                   WHEN LOWER(notifications_day) = 'monday' THEN 'monday'
                   WHEN LOWER(notifications_day) = 'tuesday' THEN 'tuesday'
                   WHEN LOWER(notifications_day) = 'wednesday' THEN 'wednesday'
                   WHEN LOWER(notifications_day) = 'thursday' THEN 'thursday'
                   WHEN LOWER(notifications_day) = 'friday' THEN 'friday'
                   WHEN LOWER(notifications_day) = 'saturday' THEN 'saturday'
                   WHEN LOWER(notifications_day) = 'sunday' THEN 'sunday'
                   ELSE 'monday'
               END as notifications_day,
               life_expectancy, timezone, notifications, notifications_time, updated_at
        FROM user_settings
    """
    )

    # Drop old table and rename new one
    op.drop_table("user_settings")
    op.rename_table("user_settings_temp", "user_settings")


def downgrade() -> None:
    """Remove enums and revert to string columns."""

    # Recreate user_subscriptions table with string subscription_type
    op.create_table(
        "user_subscriptions_temp",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["telegram_id"], ["users.telegram_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )

    # Copy data back (without subscription_type)
    op.execute(
        """
        INSERT INTO user_subscriptions_temp
        (id, telegram_id, is_active, created_at, expires_at)
        SELECT id, telegram_id, is_active, created_at, expires_at
        FROM user_subscriptions
    """
    )

    # Drop current table and rename temp back
    op.drop_table("user_subscriptions")
    op.rename_table("user_subscriptions_temp", "user_subscriptions")

    # Recreate user_settings table with string column for notifications_day
    op.create_table(
        "user_settings_temp",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("notifications_day", sa.String(length=20), nullable=True),
        sa.Column("life_expectancy", sa.Integer(), nullable=True),
        sa.Column("timezone", sa.String(length=100), nullable=True),
        sa.Column("notifications", sa.Boolean(), nullable=True),
        sa.Column("notifications_time", sa.Time(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["telegram_id"], ["users.telegram_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )

    # Copy data back
    op.execute(
        """
        INSERT INTO user_settings_temp
        (id, telegram_id, birth_date, notifications_day, life_expectancy, timezone, notifications, notifications_time, updated_at)
        SELECT id, telegram_id, birth_date, notifications_day, life_expectancy, timezone, notifications, notifications_time, updated_at
        FROM user_settings
    """
    )

    # Drop current table and rename temp back
    op.drop_table("user_settings")
    op.rename_table("user_settings_temp", "user_settings")
