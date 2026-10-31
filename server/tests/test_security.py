from datetime import UTC, datetime, timedelta

from app import security
from app.models import Token, UserSession


def test_argon2id_hash_and_verify():
    h = security.hash_password("a-long-password-1")
    assert h.startswith("$argon2id$")
    assert security.verify_password(h, "a-long-password-1")
    assert not security.verify_password(h, "wrong-password-xx")
    assert not security.verify_password(None, "anything")


def test_password_policy():
    assert security.password_problem("short") == "password_weak"
    assert security.password_problem("password123456") == "password_weak"  # common list
    assert security.password_problem("x" * 1025) == "password_weak"
    assert security.password_problem("correct horse battery") is None


def test_token_single_use_and_expiry(db, make_user):
    user = make_user(status="invited")
    secret = security.issue_token(db, user, "invite")
    assert db.query(Token).one().token_hash == security.hash_secret(secret)
    assert secret not in db.query(Token).one().token_hash
    assert security.take_token(db, secret, "invite", consume=False).user_id == user.id
    assert security.take_token(db, secret, "reset", consume=True) is None  # wrong kind
    assert security.take_token(db, secret, "invite", consume=True).user_id == user.id
    assert security.take_token(db, secret, "invite", consume=True) is None  # used

    expired = security.issue_token(db, user, "reset",
                                   now=datetime.now(UTC) - timedelta(minutes=31))
    assert security.take_token(db, expired, "reset", consume=True) is None


def test_new_token_invalidates_older_ones(db, make_user):
    user = make_user()
    old = security.issue_token(db, user, "reset")
    new = security.issue_token(db, user, "reset")
    assert security.take_token(db, old, "reset", consume=True) is None
    assert security.take_token(db, new, "reset", consume=True) is not None


def test_invite_lasts_7_days_reset_30_minutes(db, make_user):
    user = make_user()
    security.issue_token(db, user, "invite")
    security.issue_token(db, user, "reset")
    by_kind = {t.kind: t.expires_at - t.created_at for t in db.query(Token)}
    assert abs(by_kind["invite"] - timedelta(days=7)) < timedelta(seconds=5)
    assert abs(by_kind["reset"] - timedelta(minutes=30)) < timedelta(seconds=5)


def test_session_absolute_and_idle_expiry(db, make_user):
    user = make_user()
    secret = security.open_session(db, user)
    assert security.session_user(db, secret).id == user.id
    assert security.session_user(db, "not-a-session") is None

    s = db.query(UserSession).one()
    s.last_seen_at = datetime.now(UTC) - timedelta(hours=25)
    db.commit()
    assert security.session_user(db, secret) is None  # idle > 24 h

    secret2 = security.open_session(db, user)
    s2 = db.query(UserSession).filter_by(token_hash=security.hash_secret(secret2)).one()
    s2.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()
    assert security.session_user(db, secret2) is None  # past 7-day absolute expiry


def test_disabled_user_session_rejected(db, make_user):
    user = make_user()
    secret = security.open_session(db, user)
    user.status = "disabled"
    db.commit()
    assert security.session_user(db, secret) is None
