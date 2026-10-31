"""bookings

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade() -> None:
    op.create_table(
        "bookings",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.Column("contact_request_id", sa.BigInteger(),
                  sa.ForeignKey("contact_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("slot_start", sa.DateTime(timezone=True), nullable=False, unique=True),
        sa.Column("calendar_event_id", sa.Text()),
    )


def downgrade() -> None:
    op.drop_table("bookings")
