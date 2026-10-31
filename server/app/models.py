"""Database tables (specs/001-backend/data-model.md)."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CHAR,
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Identity,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class _Row:
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


LANGS = ("es", "en", "fr")
NOTIFICATION_STATUSES = ("pending", "sent", "failed")


class ContactRequest(_Row, Base):
    """A public form submission: contact message, meeting request or calculator results."""

    __tablename__ = "contact_requests"
    __table_args__ = (Index("ix_contact_requests_ip_created", "ip", "created_at"),)

    kind: Mapped[str] = mapped_column(
        Enum("message", "meeting", "calculator", name="contact_kind"), nullable=False)
    lang: Mapped[str] = mapped_column(Enum(*LANGS, name="site_lang"), nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    ip: Mapped[str] = mapped_column(INET, nullable=False)
    notification_status: Mapped[str] = mapped_column(
        Enum(*NOTIFICATION_STATUSES, name="notification_status"), nullable=False,
        server_default="pending")


class Booking(_Row, Base):
    """A reserved meeting slot; at most one per slot_start (FR-009)."""

    __tablename__ = "bookings"

    contact_request_id: Mapped[int] = mapped_column(
        ForeignKey("contact_requests.id", ondelete="CASCADE"), nullable=False)
    slot_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                 unique=True)
    calendar_event_id: Mapped[str | None] = mapped_column(Text)


def _fk(target: str, **kw):
    return mapped_column(ForeignKey(target, ondelete="CASCADE"), nullable=False, **kw)


class Company(_Row, Base):
    __tablename__ = "companies"
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class User(_Row, Base):
    __tablename__ = "users"
    company_id: Mapped[int] = _fk("companies.id", index=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)  # lower-case
    name: Mapped[str] = mapped_column(Text, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        Enum("invited", "active", "disabled", name="user_status"), nullable=False,
        server_default="invited")
    lang: Mapped[str] = mapped_column(Enum(*LANGS, name="site_lang"), nullable=False,
                                      server_default="es")


class Token(_Row, Base):
    """Invite / password-reset link. Only the SHA-256 of the link secret is stored."""

    __tablename__ = "tokens"
    user_id: Mapped[int] = _fk("users.id", index=True)
    kind: Mapped[str] = mapped_column(Enum("invite", "reset", name="token_kind"), nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserSession(_Row, Base):
    __tablename__ = "sessions"
    user_id: Mapped[int] = _fk("users.id", index=True)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Subscription(_Row, Base):
    __tablename__ = "subscriptions"
    company_id: Mapped[int] = _fk("companies.id", index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("active", "paused", "cancelled", name="subscription_status"), nullable=False,
        server_default="active")


class Payment(_Row, Base):
    __tablename__ = "payments"
    __table_args__ = (CheckConstraint("amount > 0", name="payments_amount_positive"),)
    company_id: Mapped[int] = _fk("companies.id", index=True)
    paid_on: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False)


AUDIT_KINDS = ("login_ok", "login_failed", "logout", "invite_sent", "invite_accepted",
               "reset_requested", "reset_done", "user_disabled", "user_enabled")


class AuditLog(_Row, Base):
    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_email_kind_created", "email", "kind", "created_at"),
                      Index("ix_audit_ip_kind_created", "ip", "kind", "created_at"))
    kind: Mapped[str] = mapped_column(Enum(*AUDIT_KINDS, name="audit_kind"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    email: Mapped[str] = mapped_column(Text, nullable=False)
    ip: Mapped[str | None] = mapped_column(INET)


class Ticket(_Row, Base):
    __tablename__ = "tickets"
    company_id: Mapped[int] = _fk("companies.id", index=True)
    user_id: Mapped[int] = _fk("users.id")
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", name="ticket_priority"), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("open", "in_progress", "resolved", "closed", name="ticket_status"), nullable=False,
        server_default="open")
    notification_status: Mapped[str] = mapped_column(
        Enum(*NOTIFICATION_STATUSES, name="notification_status"), nullable=False,
        server_default="pending")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Attachment(_Row, Base):
    __tablename__ = "attachments"
    user_id: Mapped[int] = _fk("users.id", index=True)
    ticket_id: Mapped[int | None] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(
        Enum("image/png", "image/jpeg", "application/pdf", name="attachment_type"),
        nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
