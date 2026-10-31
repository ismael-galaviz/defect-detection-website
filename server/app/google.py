"""Gmail send + Calendar free/busy and events over plain HTTPS (research R7).

One OAuth refresh token of the owner's Google account covers both APIs. `FakeGoogle` replaces
the real client in tests and when GOOGLE_FAKE=1 (local development): it logs instead of calling.
"""

import base64
import logging
import time
import uuid
from datetime import datetime
from email.message import EmailMessage
from functools import lru_cache

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)

TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105 (URL, not a secret)
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
CALENDAR_URL = "https://www.googleapis.com/calendar/v3"
SCOPES = (
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.freebusy",
)

Attachment = tuple[str, str, bytes]  # filename, content type, content


class GoogleError(RuntimeError):
    """Any failure talking to Google (network, auth, quota, bad response)."""


def _iso(dt: datetime) -> str:
    return dt.isoformat()


class GoogleClient:
    def __init__(self, *, client_id, client_secret, refresh_token, sender, calendar_id,
                 http: httpx.Client | None = None):
        self._creds = {"client_id": client_id, "client_secret": client_secret,
                       "refresh_token": refresh_token, "grant_type": "refresh_token"}
        self.sender = sender
        self.calendar_id = calendar_id
        self._http = http or httpx.Client(timeout=15)
        self._token: str | None = None
        self._token_expires = 0.0

    def _access_token(self) -> str:
        if self._token and time.monotonic() < self._token_expires:
            return self._token
        data = self._call("POST", TOKEN_URL, data=self._creds, auth=False)
        self._token = data["access_token"]
        self._token_expires = time.monotonic() + int(data.get("expires_in", 3600)) - 60
        return self._token

    def _call(self, method, url, *, auth=True, **kwargs) -> dict:
        headers = {"Authorization": f"Bearer {self._access_token()}"} if auth else {}
        try:
            resp = self._http.request(method, url, headers=headers, **kwargs)
        except httpx.HTTPError as e:
            raise GoogleError(f"{method} {url} failed: {e}") from e
        if resp.status_code >= 400:
            raise GoogleError(f"{method} {url} -> {resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def send_email(self, to: str, subject: str, text: str, reply_to: str | None = None,
                   attachments: tuple[Attachment, ...] | list[Attachment] = ()) -> None:
        msg = EmailMessage()
        msg["From"] = self.sender
        msg["To"] = to
        msg["Subject"] = subject
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.set_content(text)
        for filename, content_type, content in attachments:
            maintype, subtype = content_type.split("/", 1)
            msg.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        self._call("POST", GMAIL_SEND_URL, json={"raw": raw})

    def busy_intervals(self, start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
        data = self._call("POST", f"{CALENDAR_URL}/freeBusy", json={
            "timeMin": _iso(start), "timeMax": _iso(end), "items": [{"id": self.calendar_id}]})
        cal = data.get("calendars", {}).get(self.calendar_id, {})
        if cal.get("errors"):
            raise GoogleError(f"freeBusy errors: {cal['errors']}")
        return [(datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"]))
                for b in cal.get("busy", [])]

    def create_event(self, start: datetime, end: datetime, summary: str, description: str,
                     attendee: str) -> str:
        data = self._call(
            "POST", f"{CALENDAR_URL}/calendars/{self.calendar_id}/events",
            params={"conferenceDataVersion": "1", "sendUpdates": "all"},
            json={
                "summary": summary,
                "description": description,
                "start": {"dateTime": _iso(start)},
                "end": {"dateTime": _iso(end)},
                "attendees": [{"email": attendee}],
                "conferenceData": {"createRequest": {
                    "requestId": uuid.uuid4().hex,
                    "conferenceSolutionKey": {"type": "hangoutsMeet"}}},
            })
        return data["id"]


class FakeGoogle:
    """Records calls instead of making them. Set `fail = True` to simulate an outage."""

    def __init__(self):
        self.sent: list[dict] = []
        self.events: list[dict] = []
        self.busy: list[tuple[datetime, datetime]] = []
        self.fail = False

    def _check(self):
        if self.fail:
            raise GoogleError("fake outage")

    def send_email(self, to, subject, text, reply_to=None, attachments=()):
        self._check()
        self.sent.append({"to": to, "subject": subject, "text": text, "reply_to": reply_to,
                          "attachments": list(attachments)})
        # Full text so local developers can follow invite/reset links (GOOGLE_FAKE=1 only).
        log.info("fake email to %s: %s\n%s", to, subject, text)

    def busy_intervals(self, start, end):
        self._check()
        return [b for b in self.busy if b[0] < end and b[1] > start]

    def create_event(self, start, end, summary, description, attendee):
        self._check()
        self.events.append({"start": start, "end": end, "summary": summary,
                            "description": description, "attendee": attendee})
        return f"fake-{len(self.events)}"


@lru_cache
def get_google() -> GoogleClient | FakeGoogle:
    s = get_settings()
    if s.google_fake:
        return FakeGoogle()
    return GoogleClient(client_id=s.google_client_id, client_secret=s.google_client_secret,
                        refresh_token=s.google_refresh_token, sender=s.staff_email,
                        calendar_id=s.google_calendar_id)
