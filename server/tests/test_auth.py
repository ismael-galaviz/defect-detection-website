from sqlalchemy import select

from app import security
from app.models import AuditLog, User

PW = "a-long-password-1"


def kinds(db):
    db.expire_all()
    return [a.kind for a in db.scalars(select(AuditLog).order_by(AuditLog.id))]


def login(client, email="ana@example.com", password=PW):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_invite_accept_signs_in(client, google, db, make_user):
    user = make_user(status="invited")
    secret = security.issue_token(db, user, "invite")
    info = client.get(f"/api/auth/invite/{secret}")
    assert info.status_code == 200
    assert info.json() == {"email": "ana@example.com", "name": "Ana Ruiz",
                           "company": "Textiles Ruiz"}
    r = client.post("/api/auth/accept-invite", json={"token": secret, "password": PW})
    assert r.status_code == 204
    me = client.get("/api/me")
    assert me.status_code == 200 and me.json()["company"]["name"] == "Textiles Ruiz"
    assert client.get(f"/api/auth/invite/{secret}").status_code == 410
    assert "invite_accepted" in kinds(db)


def test_accept_invite_rejects_weak_password_without_using_link(client, google, db, make_user):
    user = make_user(status="invited")
    secret = security.issue_token(db, user, "invite")
    r = client.post("/api/auth/accept-invite", json={"token": secret, "password": "short"})
    assert r.status_code == 422 and r.json()["fields"]["password"] == "password_weak"
    assert client.get(f"/api/auth/invite/{secret}").status_code == 200


def test_bad_invite_link(client, google):
    r = client.post("/api/auth/accept-invite", json={"token": "nope", "password": PW})
    assert r.status_code == 410 and r.json()["error"] == "link_expired"


def test_cookie_flags(client, google, make_user):
    make_user()
    cookie = login(client).headers["set-cookie"]
    for flag in ("vx_session=", "HttpOnly", "Secure", "SameSite=lax", "Path=/api"):
        assert flag.lower() in cookie.lower()


def test_wrong_password_and_unknown_email_look_the_same(client, google, db, make_user):
    make_user()
    wrong = login(client, password="wrong-password-xx")
    unknown = login(client, email="nobody@example.com")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"error": "invalid_credentials"}
    assert kinds(db) == ["login_failed", "login_failed"]


def test_invited_user_cannot_log_in(client, google, make_user):
    make_user(status="invited")
    assert login(client).status_code == 401


def test_lockout_after_five_failures(client, google, make_user):
    make_user()
    for _ in range(5):
        assert login(client, password="wrong-password-xx").status_code == 401
    r = login(client)
    assert r.status_code == 429 and r.json()["error"] == "locked"
    assert r.json()["retry_after"] > 0


def test_email_is_case_insensitive(client, google, make_user):
    make_user()
    assert login(client, email="  ANA@example.com ").status_code == 204


def test_logout_ends_session(client, google, db, make_user):
    make_user()
    login(client)
    assert client.get("/api/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/me").status_code == 401
    assert kinds(db) == ["login_ok", "logout"]


def test_forgot_password_never_reveals_accounts(client, google, db, make_user):
    make_user()
    known = client.post("/api/auth/forgot", json={"email": "ana@example.com", "lang": "en"})
    unknown = client.post("/api/auth/forgot", json={"email": "x@example.com", "lang": "en"})
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert [m["to"] for m in google.sent] == ["ana@example.com"]
    assert "#/forgot-password?token=" in google.sent[0]["text"]


def test_reset_password_ends_all_sessions(client, google, db, make_user):
    from fastapi.testclient import TestClient

    from app.main import app
    from tests.conftest import SITE_ORIGIN

    make_user()
    other = TestClient(app, base_url="https://testserver", headers={"Origin": SITE_ORIGIN})
    assert login(other).status_code == 204
    client.post("/api/auth/forgot", json={"email": "ana@example.com", "lang": "es"})
    token = google.sent[0]["text"].split("token=")[1].split()[0]
    r = client.post("/api/auth/reset", json={"token": token, "password": "a-new-password-22"})
    assert r.status_code == 204
    assert other.get("/api/me").status_code == 401
    assert login(client, password="a-new-password-22").status_code == 204
    assert client.post("/api/auth/reset", json={"token": token, "password": "another-one-333"}
                       ).status_code == 410
    assert {"reset_requested", "reset_done"} <= set(kinds(db))


def test_reset_requests_are_rate_limited(client, google, make_user):
    make_user()
    for _ in range(3):
        client.post("/api/auth/forgot", json={"email": "ana@example.com", "lang": "es"})
    r = client.post("/api/auth/forgot", json={"email": "ana@example.com", "lang": "es"})
    assert r.status_code == 429
    assert len(google.sent) == 3


def test_disabled_user_is_signed_out(client, google, db, make_user):
    user = make_user()
    login(client)
    db.get(User, user.id).status = "disabled"
    db.commit()
    assert client.get("/api/me").status_code == 401
    assert login(client).status_code == 401


def test_me_requires_session(client, google):
    r = client.get("/api/me")
    assert r.status_code == 401 and r.json() == {"error": "unauthenticated"}
