"""Initial migration - create users and user_settings tables.

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables for users and user settings."""

    # Create users table
    op.create_table('users',
        sa.Column('telegram_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('telegram_id')
    )

    # Create user_settings table
    op.create_table('user_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.Integer(), nullable=False),
        sa.Column('birth_date', sa.Date(), nullable=True),
        sa.Column('notifications_day', sa.String(length=20), nullable=True),
        sa.Column('life_expectancy', sa.Integer(), nullable=True),
        sa.Column('timezone', sa.String(length=100), nullable=True),
        sa.Column('notifications', sa.Boolean(), nullable=True),
        sa.Column('notifications_time', sa.Time(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['telegram_id'], ['users.telegram_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on telegram_id for better performance
    op.create_index(op.f('ix_user_settings_telegram_id'), 'user_settings', ['telegram_id'], unique=False)


def downgrade() -> None:
    """Drop all tables created in this migration."""

    # Drop user_settings table
    op.drop_index(op.f('ix_user_settings_telegram_id'), table_name='user_settings')
    op.drop_table('user_settings')

    # Drop users table
    op.drop_table('users')
    