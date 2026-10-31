"""Public forms: contact message and calculator results (spec Story 1, FR-001…FR-006)."""

import logging
import re
from datetime import timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import emails
from app.config import get_settings
from app.db import get_db, new_session
from app.google import GoogleError, get_google
from app.http import client_ip, error
from app.models import ContactRequest

log = logging.getLogger(__name__)
router = APIRouter()

RATE_LIMIT = 5
RATE_WINDOW = timedelta(minutes=10)
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

Lang = Literal["es", "en", "fr"]
Number = Annotated[float, Field(allow_inf_nan=False)]


def _email(value: str) -> str:
    value = value.strip().lower()
    if len(value) > 254 or not EMAIL_RE.match(value):
        raise PydanticCustomError("invalid_email", "invalid email")
    return value


class _Form(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    email: str
    lang: Lang
    website: str = Field("", max_length=500)  # honeypot: humans never fill it

    _check_email = field_validator("email")(_email)


class ContactIn(_Form):
    name: str = Field(min_length=1, max_length=200)
    company: str = Field(min_length=1, max_length=200)
    country: str | None = Field(None, max_length=100)
    stage: str | None = Field(None, max_length=200)
    message: str | None = Field(None, max_length=5000)
    # Until live booking (Story 2) ships, a meeting request is a contact message with these.
    preferred_slot: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
    video_tool: str | None = Field(None, max_length=100)


class CalculatorIn(_Form):
    name: str | None = Field(None, max_length=200)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    inputs: dict[str, dict[str, Number]]
    results: dict[str, Number]

    @model_validator(mode="after")
    def known_keys_only(self):
        for section, fields in self.inputs.items():
            allowed = emails.CALC_SECTIONS.get(section)
            if allowed is None or not set(fields) <= set(allowed):
                raise ValueError("unknown calculator field")
        if not set(self.results) <= set(emails.CALC_SECTIONS) | {"total"}:
            raise ValueError("unknown calculator result")
        return self


def rate_limited(db: Session, ip: str) -> bool:
    since = func.now() - RATE_WINDOW
    count = db.scalar(select(func.count()).select_from(ContactRequest).where(
        ContactRequest.ip == ip, ContactRequest.created_at > since))
    return count >= RATE_LIMIT


def _messages(row: ContactRequest) -> list[tuple[str, str, str, str | None]]:
    """(to, subject, text, reply_to) for each email a stored request triggers."""
    staff = get_settings().staff_email
    p = row.payload
    if row.kind == "meeting":
        staff_mail = emails.staff_booking(p)
        visitor_mail = emails.visitor_booking(row.lang, p["slot_start"])
    elif row.kind == "calculator":
        staff_mail = emails.staff_calculator(p)
        visitor_mail = emails.visitor_calculator(row.lang, p["currency"], p["inputs"],
                                                 p["results"])
    else:
        staff_mail = emails.staff_contact(p)
        visitor_mail = emails.visitor_contact(row.lang, meeting=bool(p.get("preferred_slot")))
    return [(staff, *staff_mail, row.email), (row.email, *visitor_mail, None)]


def send_notifications(request_id: int, google) -> str:
    """Send a stored request's emails and record the outcome (FR-006). Returns the status."""
    with new_session() as db:
        row = db.get(ContactRequest, request_id)
        try:
            for to, subject, text, reply_to in _messages(row):
                google.send_email(to, subject, text, reply_to=reply_to)
            row.notification_status = "sent"
        except GoogleError:
            log.exception("notification failed", extra={"contact_request_id": request_id})
            row.notification_status = "failed"
        db.commit()
        return row.notification_status


def _accept(kind: str, body: _Form, request: Request, background: BackgroundTasks,
            db: Session, google):
    if body.website:
        log.info("honeypot hit", extra={"kind": kind})
        return {"ok": True}
    ip = client_ip(request)
    if rate_limited(db, ip):
        return error(429, "rate_limited")
    row = ContactRequest(kind=kind, lang=body.lang, email=body.email, ip=ip,
                         payload=body.model_dump(exclude={"website"}, exclude_none=True))
    db.add(row)
    db.commit()
    background.add_task(send_notifications, row.id, google)
    return {"ok": True}


@router.post("/contact", status_code=202)
def contact(body: ContactIn, request: Request, background: BackgroundTasks,
            db: Session = Depends(get_db), google=Depends(get_google)):
    return _accept("message", body, request, background, db, google)


@router.post("/calculator-results", status_code=202)
def calculator_results(body: CalculatorIn, request: Request, background: BackgroundTasks,
                       db: Session = Depends(get_db), google=Depends(get_google)):
    return _accept("calculator", body, request, background, db, google)
