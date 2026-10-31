"""Live meeting booking against the VeritX Google Calendar (spec Story 2, FR-007…FR-010)."""

import logging
from datetime import date, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from pydantic import AwareDatetime, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import booking as slots
from app import emails
from app.db import get_db
from app.google import GoogleError, get_google
from app.http import client_ip, error
from app.models import Booking, ContactRequest
from app.routes.forms import _Form, rate_limited, send_notifications

log = logging.getLogger(__name__)
router = APIRouter()
MAX_RANGE_DAYS = 62


class BookingIn(_Form):
    slot_start: AwareDatetime
    name: str = Field(min_length=1, max_length=200)
    company: str = Field(min_length=1, max_length=200)
    country: str | None = Field(None, max_length=100)
    stage: str | None = Field(None, max_length=200)
    message: str | None = Field(None, max_length=5000)
    video_tool: str | None = Field(None, max_length=100)


def _day_start(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=slots.CDMX)


@router.get("/availability")
def availability(first: date = Query(alias="from"), last: date = Query(alias="to"),
                 db: Session = Depends(get_db), google=Depends(get_google)):
    if last < first or (last - first).days > MAX_RANGE_DAYS:
        return error(422, "invalid", fields={"to": "invalid_range"})
    start, end = _day_start(first), _day_start(last) + timedelta(days=1)
    try:
        busy = google.busy_intervals(start, end)
    except GoogleError:
        log.exception("freeBusy failed")
        return error(503, "calendar_unavailable")
    booked = set(db.scalars(select(Booking.slot_start).where(
        Booking.slot_start >= start, Booking.slot_start < end)))
    free = slots.free_slots(first, last, busy=busy, booked=booked,
                            now=datetime.now(slots.CDMX))
    return {"timezone": "America/Mexico_City", "slots": [s.isoformat() for s in free]}


@router.post("/bookings", status_code=201)
def create_booking(body: BookingIn, request: Request, background: BackgroundTasks,
                   db: Session = Depends(get_db), google=Depends(get_google)):
    slot = body.slot_start.astimezone(slots.CDMX)
    if body.website:
        log.info("honeypot hit", extra={"kind": "meeting"})
        return {"slot_start": slot.isoformat()}
    if not slots.is_bookable(slot, datetime.now(slots.CDMX)):
        return error(422, "invalid", fields={"slot_start": "invalid_slot"})
    ip = client_ip(request)
    if rate_limited(db, ip):
        return error(429, "rate_limited")
    try:
        busy = google.busy_intervals(slot, slot + slots.SLOT_LENGTH)
    except GoogleError:
        log.exception("freeBusy failed")
        return error(503, "calendar_unavailable")
    if slots.overlaps(slot, busy):
        return error(409, "slot_unavailable")

    payload = body.model_dump(exclude={"website", "slot_start"}, exclude_none=True)
    payload["slot_start"] = slot.isoformat()
    row = ContactRequest(kind="meeting", lang=body.lang, email=body.email, ip=ip, payload=payload)
    db.add(row)
    db.flush()
    reservation = Booking(contact_request_id=row.id, slot_start=slot)
    db.add(reservation)
    try:
        db.commit()  # the unique slot_start decides concurrent requests (FR-009)
    except IntegrityError:
        db.rollback()
        return error(409, "slot_unavailable")

    summary, description = emails.EVENT_COPY[body.lang]
    try:
        reservation.calendar_event_id = google.create_event(
            slot, slot + slots.SLOT_LENGTH, summary, description, body.email)
    except GoogleError:
        log.exception("event creation failed", extra={"booking_id": reservation.id})
        db.delete(row)  # cascades to the booking
        db.commit()
        return error(503, "calendar_unavailable")
    db.commit()
    background.add_task(send_notifications, row.id, google)
    return {"slot_start": slot.isoformat()}
