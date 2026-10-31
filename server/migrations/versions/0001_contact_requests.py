"""contact_requests

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None


def upgrade() -> None:
    op.create_table(
        "contact_requests",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.Column("kind", sa.Enum("message", "meeting", "calculator", name="contact_kind"),
                  nullable=False),
        sa.Column("lang", sa.Enum("es", "en", "fr", name="site_lang"), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("ip", postgresql.INET(), nullable=False),
        sa.Column("notification_status",
                  sa.Enum("pending", "sent", "failed", name="notification_status"),
                  nullable=False, server_default="pending"),
    )
    op.create_index("ix_contact_requests_ip_created", "contact_requests", ["ip", "created_at"])


def downgrade() -> None:
    op.drop_table("contact_requests")
    for enum in ("contact_kind", "site_lang", "notification_status"):
        sa.Enum(name=enum).drop(op.get_bind())
