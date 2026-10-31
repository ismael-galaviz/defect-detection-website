from sqlalchemy import select

from app.db import new_session
from app.models import ContactRequest

CONTACT = {
    "name": "Ana Ruiz", "company": "Textiles Ruiz", "email": "ana@example.com",
    "country": "México", "stage": "Evaluating", "message": "Hola, quiero una demo", "lang": "es",
    "website": "",
}
CALC = {
    "name": "Ana", "email": "ana@example.com", "lang": "en", "currency": "MXN",
    "inputs": {
        "defects": {"rateBefore": 1.2, "rateAfter": 0.2, "volume": 500000, "costPerDefect": 150},
        "laborHours": {"hoursBefore": 12, "hoursAfter": 2, "hourlyCost": 80, "shiftsPerYear": 250},
        "lineSpeed": {"speedBefore": 70, "speedAfter": 100, "hoursPerYear": 4000,
                      "marginPerMeter": 0.5},
    },
    "results": {"defects": 750000, "laborHours": 200000, "lineSpeed": 3600000, "total": 4550000},
    "website": "",
}


def rows():
    with new_session() as db:
        return db.scalars(select(ContactRequest).order_by(ContactRequest.id)).all()


def test_contact_is_stored_and_both_emails_sent(client, google):
    r = client.post("/api/contact", json=CONTACT)
    assert r.status_code == 202
    [row] = rows()
    assert row.kind == "message" and row.lang == "es" and row.email == "ana@example.com"
    assert row.payload["message"] == "Hola, quiero una demo"
    assert row.notification_status == "sent"
    staff, visitor = google.sent
    assert staff["to"] == "staff@example.com" and staff["reply_to"] == "ana@example.com"
    assert "Hola, quiero una demo" in staff["text"] and "Textiles Ruiz" in staff["text"]
    assert visitor["to"] == "ana@example.com"


def test_email_is_trimmed_and_lowercased(client, google):
    client.post("/api/contact", json={**CONTACT, "email": "  Ana@Example.COM "})
    assert rows()[0].email == "ana@example.com"


def test_meeting_preference_reaches_staff(client, google):
    body = {**CONTACT, "preferred_slot": "2026-11-03 10:00", "video_tool": "Zoom"}
    assert client.post("/api/contact", json=body).status_code == 202
    staff = google.sent[0]
    assert "2026-11-03 10:00" in staff["text"] and "Zoom" in staff["text"]


def test_field_errors(client, google):
    r = client.post("/api/contact", json={**CONTACT, "email": "nope", "name": ""})
    assert r.status_code == 422
    assert r.json()["error"] == "invalid"
    assert r.json()["fields"]["email"] == "invalid_email"
    assert r.json()["fields"]["name"] == "required"
    assert rows() == [] and google.sent == []


def test_unknown_language_rejected(client, google):
    assert client.post("/api/contact", json={**CONTACT, "lang": "de"}).status_code == 422


def test_honeypot_is_silently_discarded(client, google):
    r = client.post("/api/contact", json={**CONTACT, "website": "http://spam"})
    assert r.status_code == 202
    assert rows() == [] and google.sent == []


def test_rate_limit_per_ip(client, google):
    headers = {"X-Forwarded-For": "203.0.113.9"}
    for _ in range(5):
        assert client.post("/api/contact", json=CONTACT, headers=headers).status_code == 202
    r = client.post("/api/calculator-results", json=CALC, headers=headers)
    assert r.status_code == 429 and r.json()["error"] == "rate_limited"
    other = client.post("/api/contact", json=CONTACT, headers={"X-Forwarded-For": "203.0.113.10"})
    assert other.status_code == 202


def test_email_failure_keeps_the_request(client, google):
    google.fail = True
    assert client.post("/api/contact", json=CONTACT).status_code == 202
    [row] = rows()
    assert row.notification_status == "failed"


def test_calculator_results_emailed_to_visitor(client, google):
    r = client.post("/api/calculator-results", json=CALC)
    assert r.status_code == 202
    [row] = rows()
    assert row.kind == "calculator" and row.notification_status == "sent"
    visitor = next(m for m in google.sent if m["to"] == "ana@example.com")
    assert "4,550,000 MXN" in visitor["text"]
    assert any(m["to"] == "staff@example.com" for m in google.sent)


def test_calculator_rejects_unknown_keys_and_non_numbers(client, google):
    bad_key = {**CALC, "inputs": {**CALC["inputs"], "spam": {"x": 1}}}
    assert client.post("/api/calculator-results", json=bad_key).status_code == 422
    bad_field = {**CALC, "inputs": {"defects": {"buy now http://x": 1}}}
    assert client.post("/api/calculator-results", json=bad_field).status_code == 422
    text_value = {**CALC, "results": {**CALC["results"], "total": "lots"}}
    assert client.post("/api/calculator-results", json=text_value).status_code == 422
    bad_currency = {**CALC, "currency": "dollars"}
    assert client.post("/api/calculator-results", json=bad_currency).status_code == 422
    assert rows() == []
