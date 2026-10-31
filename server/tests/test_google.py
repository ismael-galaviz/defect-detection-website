import base64
import email
import json
from datetime import UTC, datetime

import httpx
import pytest

from app.google import GoogleClient, GoogleError


class Recorder:
    def __init__(self, responses):
        self.requests = []
        self.responses = responses

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        for prefix, response in self.responses.items():
            if str(request.url).startswith(prefix):
                return response
        return httpx.Response(404)


TOKEN = {"https://oauth2.googleapis.com/token": httpx.Response(
    200, json={"access_token": "at-1", "expires_in": 3600})}


def make(responses):
    rec = Recorder({**TOKEN, **responses})
    client = GoogleClient(
        client_id="cid", client_secret="secret", refresh_token="rt",
        sender="staff@example.com", calendar_id="primary",
        http=httpx.Client(transport=httpx.MockTransport(rec)),
    )
    return client, rec


def test_token_refresh_is_cached_and_sent_as_form():
    client, rec = make({"https://gmail.googleapis.com/": httpx.Response(200, json={"id": "m"})})
    client.send_email("a@example.com", "s", "t")
    client.send_email("b@example.com", "s", "t")
    token_calls = [r for r in rec.requests if "oauth2" in str(r.url)]
    assert len(token_calls) == 1
    body = token_calls[0].content.decode()
    assert "grant_type=refresh_token" in body and "refresh_token=rt" in body
    gmail = [r for r in rec.requests if "gmail" in str(r.url)]
    assert gmail[0].headers["Authorization"] == "Bearer at-1"


def test_send_email_builds_raw_mime_with_reply_to_and_attachment():
    client, rec = make({"https://gmail.googleapis.com/": httpx.Response(200, json={"id": "m"})})
    client.send_email(
        "visitor@example.com", "Asunto ñ", "Hola", reply_to="r@example.com",
        attachments=[("shot.png", "image/png", b"\x89PNGdata")],
    )
    req = rec.requests[-1]
    assert str(req.url).endswith("/gmail/v1/users/me/messages/send")
    raw = json.loads(req.content)["raw"]
    msg = email.message_from_bytes(base64.urlsafe_b64decode(raw))
    assert msg["To"] == "visitor@example.com"
    assert msg["From"] == "staff@example.com"
    assert msg["Reply-To"] == "r@example.com"
    parts = [p for p in msg.walk() if p.get_filename()]
    assert parts[0].get_filename() == "shot.png"
    assert parts[0].get_payload(decode=True) == b"\x89PNGdata"


def test_busy_intervals_parses_freebusy():
    busy = {"calendars": {"primary": {"busy": [
        {"start": "2026-11-03T16:00:00Z", "end": "2026-11-03T17:00:00Z"}]}}}
    client, rec = make({"https://www.googleapis.com/calendar/v3/freeBusy": httpx.Response(
        200, json=busy)})
    start = datetime(2026, 11, 3, tzinfo=UTC)
    busy = client.busy_intervals(start, datetime(2026, 11, 4, tzinfo=UTC))
    assert busy == [(datetime(2026, 11, 3, 16, tzinfo=UTC), datetime(2026, 11, 3, 17, tzinfo=UTC))]
    body = json.loads(rec.requests[-1].content)
    assert body["items"] == [{"id": "primary"}]


def test_create_event_requests_meet_link_and_invites_attendee():
    client, rec = make({"https://www.googleapis.com/calendar/v3/calendars/": httpx.Response(
        200, json={"id": "ev-1"})})
    start = datetime(2026, 11, 3, 16, tzinfo=UTC)
    event_id = client.create_event(
        start, datetime(2026, 11, 3, 17, tzinfo=UTC), "Demo", "desc", "v@example.com")
    assert event_id == "ev-1"
    req = rec.requests[-1]
    assert req.url.params["conferenceDataVersion"] == "1"
    assert req.url.params["sendUpdates"] == "all"
    body = json.loads(req.content)
    assert body["attendees"] == [{"email": "v@example.com"}]
    key = body["conferenceData"]["createRequest"]["conferenceSolutionKey"]
    assert key == {"type": "hangoutsMeet"}


def test_http_errors_raise_google_error():
    client, _ = make({"https://gmail.googleapis.com/": httpx.Response(500, text="boom")})
    with pytest.raises(GoogleError):
        client.send_email("a@example.com", "s", "t")
