"""Normalize notifications_day values to lowercase.

Existing records may contain uppercase enum member names (MONDAY, TUESDAY, ...)
written before the model adopted values_callable. The ORM now expects lowercase
values (monday, tuesday, ...) matching StrEnum.auto() output.

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-14
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Normalize notifications_day column values to lowercase."""
    op.execute(
        "UPDATE user_settings "
        "SET notifications_day = LOWER(notifications_day) "
        "WHERE notifications_day IS NOT NULL "
        "AND notifications_day != LOWER(notifications_day)"
    )


def downgrade() -> None:
    """No-op: lowercase values are valid for both old and new model variants."""
    pass
