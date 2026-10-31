"""accounts: companies, users, tokens, sessions, subscriptions, payments, audit_log

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"

ENUMS = ("user_status", "token_kind", "subscription_status", "audit_kind")


def _base():
    return [sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
                      nullable=False)]


def _fk(name, target):
    return sa.Column(name, sa.BigInteger(), sa.ForeignKey(target, ondelete="CASCADE"),
                     nullable=False, index=True)


def upgrade() -> None:
    lang = postgresql.ENUM("es", "en", "fr", name="site_lang", create_type=False)
    op.create_table("companies", *_base(), sa.Column("name", sa.Text(), nullable=False,
                                                     unique=True))
    op.create_table(
        "users", *_base(), _fk("company_id", "companies.id"),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text()),
        sa.Column("status", sa.Enum("invited", "active", "disabled", name="user_status"),
                  nullable=False, server_default="invited"),
        sa.Column("lang", lang, nullable=False, server_default="es"))
    op.create_table(
        "tokens", *_base(), _fk("user_id", "users.id"),
        sa.Column("kind", sa.Enum("invite", "reset", name="token_kind"), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)))
    op.create_table(
        "sessions", *_base(), _fk("user_id", "users.id"),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table(
        "subscriptions", *_base(), _fk("company_id", "companies.id"),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum("active", "paused", "cancelled", name="subscription_status"),
                  nullable=False, server_default="active"))
    op.create_table(
        "payments", *_base(), _fk("company_id", "companies.id"),
        sa.Column("paid_on", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.CHAR(3), nullable=False),
        sa.CheckConstraint("amount > 0", name="payments_amount_positive"))
    op.create_table(
        "audit_log", *_base(),
        sa.Column("kind", sa.Enum("login_ok", "login_failed", "logout", "invite_sent",
                                  "invite_accepted", "reset_requested", "reset_done",
                                  "user_disabled", "user_enabled", name="audit_kind"),
                  nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("ip", postgresql.INET()))
    op.create_index("ix_audit_email_kind_created", "audit_log", ["email", "kind", "created_at"])
    op.create_index("ix_audit_ip_kind_created", "audit_log", ["ip", "kind", "created_at"])


def downgrade() -> None:
    for table in ("audit_log", "payments", "subscriptions", "sessions", "tokens", "users",
                  "companies"):
        op.drop_table(table)
    for enum in ENUMS:
        sa.Enum(name=enum).drop(op.get_bind())
