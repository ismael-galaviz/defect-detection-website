"""tickets and attachments

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"


def _base():
    return [sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                      nullable=False)]


def upgrade() -> None:
    notification = postgresql.ENUM("pending", "sent", "failed", name="notification_status",
                                   create_type=False)
    op.create_table(
        "tickets", *_base(),
        sa.Column("company_id", sa.BigInteger(),
                  sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.Enum("low", "medium", "high", name="ticket_priority"),
                  nullable=False),
        sa.Column("status", sa.Enum("open", "in_progress", "resolved", "closed",
                                    name="ticket_status"), nullable=False,
                  server_default="open"),
        sa.Column("notification_status", notification, nullable=False, server_default="pending"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False))
    op.create_table(
        "attachments", *_base(),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("ticket_id", sa.BigInteger(), sa.ForeignKey("tickets.id", ondelete="CASCADE"),
                  index=True),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("content_type", sa.Enum("image/png", "image/jpeg", "application/pdf",
                                          name="attachment_type"), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False))


def downgrade() -> None:
    op.drop_table("attachments")
    op.drop_table("tickets")
    for enum in ("ticket_priority", "ticket_status", "attachment_type"):
        sa.Enum(name=enum).drop(op.get_bind())
