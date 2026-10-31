"""Invite-only accounts: sign-in, invites, password reset, Vision Home data (Story 3)."""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import emails, security
from app.config import get_settings
from app.db import get_db
from app.google import GoogleError, get_google
from app.http import ApiError, client_ip
from app.models import Company, Payment, Subscription, User
from app.routes.forms import Lang, _email

log = logging.getLogger(__name__)
router = APIRouter()


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginIn(_Body):
    email: str = Field(max_length=320)
    password: str = Field(max_length=1024)

    @field_validator("email")
    @classmethod
    def normalize(cls, v: str) -> str:
        return v.strip().lower()  # no format check: any unknown email is just a failed login


class ForgotIn(_Body):
    email: str
    lang: Lang
    _check_email = field_validator("email")(_email)


class SetPasswordIn(_Body):
    token: str = Field(max_length=200)
    password: str = Field(max_length=2048)


def _set_cookie(response: Response, secret: str) -> None:
    response.set_cookie(security.COOKIE, secret, max_age=int(security.SESSION_TTL.total_seconds()),
                        httponly=True, secure=True, samesite="lax", path="/api")


def _link(route: str, secret: str) -> str:
    return f"{get_settings().site_url}/#/{route}?token={secret}"


def send_invite(db: Session, user: User, google, ip: str | None = None) -> None:
    """Issue a fresh 7-day invite and email it (used by the staff CLI)."""
    company = db.get(Company, user.company_id)
    secret = security.issue_token(db, user, "invite")
    google.send_email(user.email, *emails.invite(user.lang, user.name, company.name,
                                                 _link("accept-invite", secret)))
    security.audit(db, "invite_sent", email=user.email, user_id=user.id, ip=ip)
    db.commit()


def _send_reset(to: str, lang: str, link: str, google) -> None:
    try:
        google.send_email(to, *emails.reset(lang, link))
    except GoogleError:
        log.exception("reset email failed")


@router.post("/auth/login", status_code=204)
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = client_ip(request)
    retry_after = security.login_retry_after(db, body.email)
    if retry_after:
        raise ApiError(429, "locked", retry_after=retry_after)
    user = db.scalar(select(User).where(User.email == body.email))
    ok = security.verify_password(user.password_hash if user else None, body.password)
    if not ok or user.status != "active":
        security.audit(db, "login_failed", email=body.email, ip=ip,
                       user_id=user.id if user else None)
        db.commit()
        raise ApiError(401, "invalid_credentials")
    if security.needs_rehash(user.password_hash):
        user.password_hash = security.hash_password(body.password)
    security.audit(db, "login_ok", email=user.email, ip=ip, user_id=user.id)
    _set_cookie(response, security.open_session(db, user))


@router.post("/auth/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    secret = request.cookies.get(security.COOKIE)
    user = security.session_user(db, secret)
    if user:
        security.end_sessions(db, user.id, secret)
        security.audit(db, "logout", email=user.email, ip=client_ip(request), user_id=user.id)
        db.commit()
    response.delete_cookie(security.COOKIE, path="/api", secure=True, httponly=True,
                           samesite="lax")


@router.get("/auth/invite/{token}")
def invite_info(token: str, db: Session = Depends(get_db)):
    found = security.take_token(db, token, "invite", consume=False)
    user = db.get(User, found.user_id) if found else None
    if user is None or user.status != "invited":
        raise ApiError(410, "link_expired")
    return {"email": user.email, "name": user.name,
            "company": db.get(Company, user.company_id).name}


@router.post("/auth/accept-invite", status_code=204)
def accept_invite(body: SetPasswordIn, request: Request, response: Response,
                  db: Session = Depends(get_db)):
    token = security.take_token(db, body.token, "invite", consume=False)
    user = db.get(User, token.user_id) if token else None
    if user is None or user.status != "invited":
        raise ApiError(410, "link_expired")
    if problem := security.password_problem(body.password):
        raise ApiError(422, "invalid", fields={"password": problem})
    security.take_token(db, body.token, "invite", consume=True)
    user.password_hash = security.hash_password(body.password)
    user.status = "active"
    security.audit(db, "invite_accepted", email=user.email, ip=client_ip(request),
                   user_id=user.id)
    _set_cookie(response, security.open_session(db, user))


@router.post("/auth/forgot", status_code=202)
def forgot(body: ForgotIn, request: Request, background: BackgroundTasks,
           db: Session = Depends(get_db), google=Depends(get_google)):
    ip = client_ip(request)
    if security.reset_limited(db, body.email, ip):
        raise ApiError(429, "rate_limited")
    user = db.scalar(select(User).where(User.email == body.email, User.status == "active"))
    security.audit(db, "reset_requested", email=body.email, ip=ip,
                   user_id=user.id if user else None)
    db.commit()
    if user:
        link = _link("forgot-password", security.issue_token(db, user, "reset"))
        background.add_task(_send_reset, user.email, body.lang, link, google)
    return {"ok": True}  # same answer whether or not the account exists (FR-018)


@router.post("/auth/reset", status_code=204)
def reset_password(body: SetPasswordIn, request: Request, db: Session = Depends(get_db)):
    if problem := security.password_problem(body.password):
        raise ApiError(422, "invalid", fields={"password": problem})
    token = security.take_token(db, body.token, "reset", consume=True)
    user = db.get(User, token.user_id) if token else None
    if user is None or user.status != "active":
        db.rollback()
        raise ApiError(410, "link_expired")
    user.password_hash = security.hash_password(body.password)
    security.end_sessions(db, user.id)  # FR-020: every other session ends
    security.audit(db, "reset_done", email=user.email, ip=client_ip(request), user_id=user.id)
    db.commit()


def portal_data(db: Session, user: User) -> dict:
    """Everything Vision Home shows, scoped to the user's company only (FR-022)."""
    cid = user.company_id
    subs = db.scalars(select(Subscription).where(Subscription.company_id == cid)
                      .order_by(Subscription.id))
    pays = db.scalars(select(Payment).where(Payment.company_id == cid)
                      .order_by(Payment.paid_on.desc(), Payment.id.desc()))
    return {
        "user": {"name": user.name, "email": user.email, "lang": user.lang},
        "company": {"name": db.get(Company, cid).name},
        "subscriptions": [{"name": s.name, "status": s.status} for s in subs],
        "payments": [{"paid_on": p.paid_on.isoformat(), "amount": f"{p.amount:.2f}",
                      "currency": p.currency} for p in pays],
        "tickets": [],
    }


@router.get("/me")
def me(user: User = Depends(security.current_user), db: Session = Depends(get_db)):
    return portal_data(db, user)
