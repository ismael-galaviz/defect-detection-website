"""Staff command-line tool (specs/001-backend/contracts/cli.md).

Run against production with: railway run python -m app.cli <command>
"""

import argparse
import http.server
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date

from sqlalchemy import select

from app.google import SCOPES, TOKEN_URL


def cmd_google_auth(_args) -> int:
    """One-time OAuth consent on the owner's machine; prints the refresh token."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET first.", file=sys.stderr)
        return 2
    received: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            received.update(dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query)))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Done. You can close this tab.")

        def log_message(self, *_):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    redirect = f"http://127.0.0.1:{server.server_port}"
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": client_id, "redirect_uri": redirect, "response_type": "code",
        "scope": " ".join(SCOPES), "access_type": "offline", "prompt": "consent"})
    print(f"Open this URL, signed in as the VeritX Google account:\n\n{url}\n")
    server.handle_request()
    if "code" not in received:
        print(f"No code received: {received.get('error', 'unknown error')}", file=sys.stderr)
        return 1
    body = urllib.parse.urlencode({
        "code": received["code"], "client_id": client_id, "client_secret": client_secret,
        "redirect_uri": redirect, "grant_type": "authorization_code"}).encode()
    with urllib.request.urlopen(TOKEN_URL, data=body, timeout=15) as resp:  # noqa: S310
        token = json.load(resp)
    if "refresh_token" not in token:
        print("Google returned no refresh token; revoke the app's access and retry.",
              file=sys.stderr)
        return 1
    print(f"GOOGLE_REFRESH_TOKEN={token['refresh_token']}")
    return 0


def _pending():
    from app.db import new_session
    from app.models import ContactRequest

    with new_session() as db:
        return db.scalars(select(ContactRequest).where(
            ContactRequest.notification_status != "sent").order_by(ContactRequest.id)).all()


def cmd_list(args) -> int:
    from app.models import Company, User

    if args.what in ("companies", "users"):
        with _db() as db:
            if args.what == "companies":
                for c in db.scalars(select(Company).order_by(Company.name)):
                    print(f"{c.id}\t{c.name}")
            else:
                query = select(User, Company).join(Company, Company.id == User.company_id)
                if args.company:
                    query = query.where(Company.name == args.company)
                for u, c in db.execute(query.order_by(Company.name, User.email)):
                    print(f"{u.email}\t{u.status}\t{u.name}\t{c.name}")
        return 0
    if args.what == "pending":
        rows = _pending()
        for r in rows:
            print(f"{r.id}\t{r.created_at:%Y-%m-%d %H:%M}\t{r.kind}\t{r.email}\t"
                  f"{r.notification_status}")
        print(f"{len(rows)} pending notification(s)")
    return 0


def cmd_resend_pending(_args, google=None) -> int:
    from app.google import get_google
    from app.routes.forms import send_notifications

    google = google or get_google()
    results = [send_notifications(r.id, google) for r in _pending()]
    print(f"resent {results.count('sent')}, still failing {results.count('failed')}")
    return 0 if "failed" not in results else 1


def _db():
    from app.db import new_session

    return new_session()


def _company(db, name):
    from app.models import Company

    company = db.scalar(select(Company).where(Company.name == name))
    if company is None:
        print(f"No company named {name!r}", file=sys.stderr)
    return company


def _user(db, email):
    from app.models import User

    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None:
        print(f"No user {email!r}", file=sys.stderr)
    return user


def cmd_company_add(args) -> int:
    from sqlalchemy.exc import IntegrityError

    from app.models import Company

    with _db() as db:
        db.add(Company(name=args.name))
        try:
            db.commit()
        except IntegrityError:
            print(f"Company {args.name!r} already exists", file=sys.stderr)
            return 1
    print(f"created company {args.name!r}")
    return 0


def cmd_invite(args, google=None) -> int:
    from app.google import get_google
    from app.models import User
    from app.routes.auth import send_invite

    email = args.email.strip().lower()
    with _db() as db:
        company = _company(db, args.company)
        if company is None:
            return 1
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(company_id=company.id, email=email, name=args.name, lang=args.lang,
                        status="invited")
            db.add(user)
            db.commit()
        elif user.status != "invited":
            print(f"{email} already has an account ({user.status}); not changed",
                  file=sys.stderr)
            return 1
        send_invite(db, user, google or get_google())
    print(f"invite sent to {email} (valid 7 days)")
    return 0


def _set_user_status(args, status, audit_kind) -> int:
    from app import security

    with _db() as db:
        user = _user(db, args.email)
        if user is None:
            return 1
        user.status = status
        if status == "disabled":
            security.end_sessions(db, user.id)
        security.audit(db, audit_kind, email=user.email, user_id=user.id)
        db.commit()
    print(f"{args.email}: {status}")
    return 0


def cmd_user_disable(args) -> int:
    return _set_user_status(args, "disabled", "user_disabled")


def cmd_user_enable(args) -> int:
    return _set_user_status(args, "active", "user_enabled")


def cmd_subscription_add(args) -> int:
    from app.models import Subscription

    with _db() as db:
        company = _company(db, args.company)
        if company is None:
            return 1
        sub = Subscription(company_id=company.id, name=args.name, status=args.status)
        db.add(sub)
        db.commit()
        print(f"subscription {sub.id} added to {args.company!r}")
    return 0


def cmd_subscription_set(args) -> int:
    from app.models import Subscription

    with _db() as db:
        sub = db.get(Subscription, args.id)
        if sub is None:
            print(f"No subscription {args.id}", file=sys.stderr)
            return 1
        sub.status = args.status
        db.commit()
    print(f"subscription {args.id}: {args.status}")
    return 0


def cmd_payment_add(args) -> int:
    from app.models import Payment

    with _db() as db:
        company = _company(db, args.company)
        if company is None:
            return 1
        db.add(Payment(company_id=company.id, paid_on=args.date, amount=args.amount,
                       currency=args.currency))
        db.commit()
    print(f"payment {args.amount} {args.currency} on {args.date} added to {args.company!r}")
    return 0


def cmd_cleanup(_args) -> int:
    from datetime import UTC, datetime

    from sqlalchemy import delete, or_

    from app.models import Token, UserSession
    from app.security import SESSION_IDLE

    now = datetime.now(UTC)
    with _db() as db:
        sessions = db.execute(delete(UserSession).where(or_(
            UserSession.expires_at < now, UserSession.last_seen_at < now - SESSION_IDLE)))
        tokens = db.execute(delete(Token).where(or_(Token.expires_at < now,
                                                    Token.used_at.is_not(None))))
        db.commit()
    print(f"deleted {sessions.rowcount} sessions, {tokens.rowcount} tokens")
    return 0


def _positive_amount(text):
    from decimal import Decimal, InvalidOperation

    try:
        value = Decimal(text)
    except InvalidOperation:
        raise argparse.ArgumentTypeError("not a number") from None
    if value <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return value


def _currency(text):
    if len(text) != 3 or not text.isalpha() or not text.isupper():
        raise argparse.ArgumentTypeError("use a 3-letter ISO code like MXN")
    return text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("google-auth", help="get GOOGLE_REFRESH_TOKEN").set_defaults(
        func=cmd_google_auth)
    p = sub.add_parser("list", help="print records")
    p.add_argument("what", choices=["companies", "users", "pending"])
    p.add_argument("--company")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("company-add", help="create a customer company")
    p.add_argument("--name", required=True)
    p.set_defaults(func=cmd_company_add)

    p = sub.add_parser("invite", help="create (or re-invite) a user and email a 7-day link")
    p.add_argument("--company", required=True)
    p.add_argument("--email", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--lang", choices=["es", "en", "fr"], default="es")
    p.set_defaults(func=cmd_invite, needs_google=True)

    for name, func, text in (("user-disable", cmd_user_disable, "disable and sign out a user"),
                             ("user-enable", cmd_user_enable, "re-enable a user")):
        p = sub.add_parser(name, help=text)
        p.add_argument("--email", required=True)
        p.set_defaults(func=func)

    p = sub.add_parser("subscription-add", help="add a subscription to a company")
    p.add_argument("--company", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--status", choices=["active", "paused", "cancelled"], default="active")
    p.set_defaults(func=cmd_subscription_add)

    p = sub.add_parser("subscription-set", help="change a subscription's status")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--status", choices=["active", "paused", "cancelled"], required=True)
    p.set_defaults(func=cmd_subscription_set)

    p = sub.add_parser("payment-add", help="record a payment for a company")
    p.add_argument("--company", required=True)
    p.add_argument("--date", type=date.fromisoformat, required=True)
    p.add_argument("--amount", type=_positive_amount, required=True)
    p.add_argument("--currency", type=_currency, required=True)
    p.set_defaults(func=cmd_payment_add)

    sub.add_parser("cleanup", help="delete expired sessions and used/expired links").set_defaults(
        func=cmd_cleanup)
    sub.add_parser("resend-pending", help="retry unsent notification emails").set_defaults(
        func=cmd_resend_pending)
    return parser


def main(argv: list[str] | None = None, google=None) -> int:
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as e:  # argparse error or --help
        return int(e.code or 0)
    if getattr(args, "needs_google", False) or args.func is cmd_resend_pending:
        return args.func(args, google=google)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
