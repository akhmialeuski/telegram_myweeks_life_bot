"""add_user_subscriptions_table

Revision ID: 0002
Revises: 0001
Create Date: 2025-07-07 18:45:39.811786

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create user_subscriptions table."""

    # Create user_subscriptions table
    op.create_table(
        "user_subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["telegram_id"], ["users.telegram_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id", name="uq_user_subscriptions_telegram_id"),
    )


def downgrade() -> None:
    """Drop user_subscriptions table."""

    # Drop user_subscriptions table
    op.drop_table("user_subscriptions")
