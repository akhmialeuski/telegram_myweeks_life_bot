"""add_language_column_to_user_settings

Revision ID: 5f8c88736433
Revises: 0003
Create Date: 2025-07-16 21:20:25.194246

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5f8c88736433"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add language column to user_settings table.

    This migration adds a language preference column to store user's
    language choice (e.g., "ru", "en", "ua", "by").
    """
    # Add language column to user_settings table
    op.add_column("user_settings", sa.Column("language", sa.String(5), nullable=True))


def downgrade() -> None:
    """Remove language column from user_settings table.

    This migration removes the language preference column.
    """
    # Remove language column from user_settings table
    op.drop_column("user_settings", "language")
