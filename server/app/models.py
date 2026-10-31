"""Database tables (specs/001-backend/data-model.md)."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Identity, Index, Text, func
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
