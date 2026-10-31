"""Passwords, link tokens, sessions, audit log and auth rate limits (research R4–R6)."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, Request
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.db import get_db
from app.http import ApiError
from app.models import AuditLog, Token, User, UserSession

COOKIE = "vx_session"
TOKEN_TTL = {"invite": timedelta(days=7), "reset": timedelta(minutes=30)}
SESSION_TTL = timedelta(days=7)
SESSION_IDLE = timedelta(hours=24)
MAX_LOGIN_FAILURES = 5
LOCK_WINDOW = timedelta(minutes=15)
RESET_WINDOW = timedelta(hours=1)
RESET_LIMIT_PER_EMAIL = 3
RESET_LIMIT_PER_IP = 10

_hasher = PasswordHasher()  # Argon2id, RFC 9106 low-memory profile
# Verified against when the email is unknown, so both cases take the same time.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))

COMMON_PASSWORDS = {
    "password123456", "123456789012", "qwertyuiop123", "letmein123456", "admin12345678",
    "welcome123456", "iloveyou123456", "contraseña123", "contrasena123", "123456789abc",
    "passwordpassword", "qwertyqwerty", "abc123abc123", "veritxvision1", "veritxvision123",
}


def _now() -> datetime:
    return datetime.now(UTC)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(stored_hash: str | None, password: str) -> bool:
    try:
        return _hasher.verify(stored_hash or _DUMMY_HASH, password) and stored_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def needs_rehash(stored_hash: str) -> bool:
    return _hasher.check_needs_rehash(stored_hash)


def password_problem(password: str) -> str | None:
    """'password_weak' unless 12–1024 characters and not a common password (FR-015)."""
    if not 12 <= len(password) <= 1024 or password.lower() in COMMON_PASSWORDS:
        return "password_weak"
    return None


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def issue_token(db: Session, user: User, kind: str, now: datetime | None = None) -> str:
    """New single-use link secret; earlier unused links of the same kind stop working."""
    now = now or _now()
    db.execute(update(Token).where(Token.user_id == user.id, Token.kind == kind,
                                   Token.used_at.is_(None)).values(used_at=now))
    secret = secrets.token_urlsafe(32)
    db.add(Token(user_id=user.id, kind=kind, token_hash=hash_secret(secret),
                 expires_at=now + TOKEN_TTL[kind], created_at=now))
    db.commit()
    return secret


def take_token(db: Session, secret: str, kind: str, *, consume: bool) -> Token | None:
    token = db.scalar(select(Token).where(
        Token.token_hash == hash_secret(secret), Token.kind == kind,
        Token.used_at.is_(None), Token.expires_at > _now()).with_for_update())
    if token and consume:
        token.used_at = _now()
        db.flush()
    return token


def open_session(db: Session, user: User) -> str:
    secret = secrets.token_urlsafe(32)
    now = _now()
    db.add(UserSession(user_id=user.id, token_hash=hash_secret(secret),
                       expires_at=now + SESSION_TTL, last_seen_at=now))
    db.commit()
    return secret


def session_user(db: Session, secret: str | None) -> User | None:
    """The active user behind a session cookie, or None (FR-017, disable → signed out)."""
    if not secret:
        return None
    now = _now()
    row = db.execute(select(UserSession, User).join(User, User.id == UserSession.user_id).where(
        UserSession.token_hash == hash_secret(secret), UserSession.expires_at > now,
        UserSession.last_seen_at > now - SESSION_IDLE, User.status == "active")).first()
    if row is None:
        return None
    session, user = row
    session.last_seen_at = now
    db.commit()
    return user


def end_sessions(db: Session, user_id: int, secret: str | None = None) -> None:
    """End one session (by secret) or all of a user's sessions."""
    query = delete(UserSession).where(UserSession.user_id == user_id)
    if secret:
        query = query.where(UserSession.token_hash == hash_secret(secret))
    db.execute(query)


def audit(db: Session, kind: str, *, email: str, ip: str | None = None,
          user_id: int | None = None) -> None:
    db.add(AuditLog(kind=kind, email=email, ip=ip, user_id=user_id))


def _count(db: Session, kind: str, since: datetime, **where) -> int:
    conditions = [AuditLog.kind == kind, AuditLog.created_at > since]
    conditions += [getattr(AuditLog, k) == v for k, v in where.items()]
    return db.scalar(select(func.count()).select_from(AuditLog).where(*conditions))


def login_retry_after(db: Session, email: str) -> int:
    """Seconds until sign-in is allowed again for this email (0 = not locked, FR-019)."""
    since = _now() - LOCK_WINDOW
    if _count(db, "login_failed", since, email=email) < MAX_LOGIN_FAILURES:
        return 0
    oldest = db.scalar(select(func.min(AuditLog.created_at)).where(
        AuditLog.kind == "login_failed", AuditLog.email == email, AuditLog.created_at > since))
    return max(1, int((oldest + LOCK_WINDOW - _now()).total_seconds()))


def reset_limited(db: Session, email: str, ip: str) -> bool:
    since = _now() - RESET_WINDOW
    return (_count(db, "reset_requested", since, email=email) >= RESET_LIMIT_PER_EMAIL
            or _count(db, "reset_requested", since, ip=ip) >= RESET_LIMIT_PER_IP)


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = session_user(db, request.cookies.get(COOKIE))
    if user is None:
        raise ApiError(401, "unauthenticated")
    return user
