"""Support tickets with small attachments (spec Story 4, FR-025…FR-029)."""

import logging
from typing import Literal
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import emails, uploads
from app.config import get_settings
from app.db import get_db, new_session
from app.google import GoogleError, get_google
from app.http import ApiError
from app.models import Attachment, Company, Ticket, User
from app.security import current_user

log = logging.getLogger(__name__)
router = APIRouter()


class TicketIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    subject: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    priority: Literal["low", "medium", "high"]
    attachment_ids: list[int] = Field(default_factory=list, max_length=uploads.MAX_PER_TICKET)


def send_ticket_notification(ticket_id: int, google) -> str:
    with new_session() as db:
        t = db.get(Ticket, ticket_id)
        user = db.get(User, t.user_id)
        files = db.scalars(select(Attachment).where(Attachment.ticket_id == t.id)
                           .order_by(Attachment.id)).all()
        subject, text = emails.staff_ticket(
            t.id, db.get(Company, t.company_id).name, user.name, user.email, t.priority,
            t.subject, t.description, [f.filename for f in files])
        try:
            google.send_email(get_settings().staff_email, subject, text, reply_to=user.email,
                              attachments=[(f.filename, f.content_type, f.content) for f in files])
            t.notification_status = "sent"
        except GoogleError:
            log.exception("ticket notification failed", extra={"ticket_id": t.id})
            t.notification_status = "failed"
        db.commit()
        return t.notification_status


@router.post("/attachments", status_code=201)
async def upload_attachment(file: UploadFile, user: User = Depends(current_user),
                            db: Session = Depends(get_db)):
    content = await file.read(uploads.MAX_BYTES + 1)
    if len(content) > uploads.MAX_BYTES:
        raise ApiError(413, "too_large")
    content_type = uploads.sniff(content)
    if content_type is None:
        raise ApiError(415, "unsupported_type")
    att = Attachment(user_id=user.id, filename=uploads.sanitize_filename(file.filename or ""),
                     content_type=content_type, size=len(content), content=content)
    db.add(att)
    db.commit()
    return {"id": att.id, "filename": att.filename, "size": att.size,
            "content_type": att.content_type}


@router.get("/attachments/{attachment_id}")
def download_attachment(attachment_id: int, user: User = Depends(current_user),
                        db: Session = Depends(get_db)):
    att = db.scalar(select(Attachment).join(User, User.id == Attachment.user_id).where(
        Attachment.id == attachment_id, User.company_id == user.company_id))
    if att is None:
        raise ApiError(404, "not_found")  # also for other companies' files (FR-022)
    return Response(att.content, media_type=att.content_type, headers={
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(att.filename)}",
        "X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store"})


@router.post("/tickets", status_code=201)
def create_ticket(body: TicketIn, background: BackgroundTasks,
                  user: User = Depends(current_user), db: Session = Depends(get_db),
                  google=Depends(get_google)):
    ids = set(body.attachment_ids)
    files = db.scalars(select(Attachment).where(
        Attachment.id.in_(ids), Attachment.user_id == user.id,
        Attachment.ticket_id.is_(None))).all() if ids else []
    if len(files) != len(ids):
        raise ApiError(422, "invalid", fields={"attachment_ids": "invalid"})
    t = Ticket(company_id=user.company_id, user_id=user.id, subject=body.subject,
               description=body.description, priority=body.priority)
    db.add(t)
    db.flush()
    for f in files:
        f.ticket_id = t.id
    db.commit()
    background.add_task(send_ticket_notification, t.id, google)
    return {"id": t.id}


def company_tickets(db: Session, company_id: int) -> list[dict]:
    tickets = db.scalars(select(Ticket).where(Ticket.company_id == company_id)
                         .order_by(Ticket.created_at.desc(), Ticket.id.desc())).all()
    files = db.scalars(select(Attachment).where(
        Attachment.ticket_id.in_([t.id for t in tickets])).order_by(Attachment.id)).all()
    by_ticket: dict[int, list] = {}
    for f in files:
        by_ticket.setdefault(f.ticket_id, []).append(
            {"id": f.id, "filename": f.filename, "size": f.size})
    return [{"id": t.id, "subject": t.subject, "priority": t.priority, "status": t.status,
             "created_at": t.created_at.isoformat(), "attachments": by_ticket.get(t.id, [])}
            for t in tickets]
