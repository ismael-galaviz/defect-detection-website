from datetime import date, datetime, timedelta

from sqlalchemy import select

from app.booking import CDMX
from app.db import new_session
from app.models import Booking, ContactRequest


def next_weekday_slot(hour=10, days_ahead=3):
    d = datetime.now(CDMX).date() + timedelta(days=days_ahead)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return datetime(d.year, d.month, d.day, hour, tzinfo=CDMX)


def booking_body(slot, **kw):
    return {"slot_start": slot.isoformat(), "name": "Ana Ruiz", "company": "Textiles Ruiz",
            "email": "ana@example.com", "video_tool": "Zoom", "message": "Demo please",
            "lang": "en", "website": "", **kw}


def test_availability_returns_free_slots(client, google):
    slot = next_weekday_slot(10)
    google.busy = [(slot, slot + timedelta(hours=1))]
    day = slot.date().isoformat()
    r = client.get(f"/api/availability?from={day}&to={day}")
    assert r.status_code == 200
    body = r.json()
    assert body["timezone"] == "America/Mexico_City"
    assert slot.isoformat() not in body["slots"]
    assert next_weekday_slot(9).isoformat() in body["slots"]


def test_availability_range_validation(client, google):
    today = date.today()
    far = today + timedelta(days=63)
    assert client.get(f"/api/availability?from={today}&to={far}").status_code == 422
    assert client.get(f"/api/availability?from={far}&to={today}").status_code == 422


def test_availability_calendar_down(client, google):
    google.fail = True
    day = next_weekday_slot().date().isoformat()
    r = client.get(f"/api/availability?from={day}&to={day}")
    assert r.status_code == 503 and r.json()["error"] == "calendar_unavailable"


def test_booking_creates_event_and_emails(client, google):
    slot = next_weekday_slot(11)
    r = client.post("/api/bookings", json=booking_body(slot))
    assert r.status_code == 201
    [event] = google.events
    assert event["attendee"] == "ana@example.com"
    assert event["start"] == slot and event["end"] == slot + timedelta(hours=1)
    # The invite reaches the visitor-typed address: no echoed free text in it.
    for text in ("Ana Ruiz", "Textiles Ruiz", "Demo please", "Zoom"):
        assert text not in event["summary"] and text not in event["description"]
    staff = next(m for m in google.sent if m["to"] == "staff@example.com")
    assert "Zoom" in staff["text"] and "Demo please" in staff["text"]
    visitor = next(m for m in google.sent if m["to"] == "ana@example.com")
    assert "Ana Ruiz" not in visitor["text"]
    with new_session() as db:
        booking = db.scalars(select(Booking)).one()
        assert booking.calendar_event_id == "fake-1"
        assert db.get(ContactRequest, booking.contact_request_id).kind == "meeting"


def test_same_slot_twice_conflicts(client, google):
    slot = next_weekday_slot(12)
    assert client.post("/api/bookings", json=booking_body(slot)).status_code == 201
    r = client.post("/api/bookings", json=booking_body(slot, email="b@example.com"))
    assert r.status_code == 409 and r.json()["error"] == "slot_unavailable"
    assert len(google.events) == 1


def test_slot_busy_in_calendar_conflicts(client, google):
    slot = next_weekday_slot(13)
    google.busy = [(slot, slot + timedelta(minutes=30))]
    r = client.post("/api/bookings", json=booking_body(slot))
    assert r.status_code == 409


def test_slot_not_on_grid_rejected(client, google):
    slot = next_weekday_slot(14)
    r = client.post("/api/bookings", json=booking_body(slot))
    assert r.status_code == 422 and r.json()["fields"]["slot_start"] == "invalid_slot"


def test_event_failure_leaves_no_booking(client, google):
    slot = next_weekday_slot(16)
    real_create = google.create_event

    def boom(*a, **kw):
        from app.google import GoogleError
        raise GoogleError("down")

    google.create_event = boom
    r = client.post("/api/bookings", json=booking_body(slot))
    assert r.status_code == 503 and r.json()["error"] == "calendar_unavailable"
    with new_session() as db:
        assert db.scalars(select(Booking)).all() == []
        assert db.scalars(select(ContactRequest)).all() == []
    google.create_event = real_create
    assert client.post("/api/bookings", json=booking_body(slot)).status_code == 201


def test_booking_honeypot(client, google):
    r = client.post("/api/bookings", json=booking_body(next_weekday_slot(17), website="x"))
    assert r.status_code == 201 and google.events == []
