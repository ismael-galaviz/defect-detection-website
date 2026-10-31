from app import cli
from app.routes.forms import send_notifications
from tests.test_forms import CONTACT, rows


def test_list_and_resend_pending(client, google, capsys):
    google.fail = True
    client.post("/api/contact", json=CONTACT)
    assert cli.main(["list", "pending"]) == 0
    assert "1 pending" in capsys.readouterr().out

    google.fail = False
    assert cli.cmd_resend_pending(None, google=google) == 0
    assert rows()[0].notification_status == "sent"
    assert "resent 1" in capsys.readouterr().out
    assert send_notifications(rows()[0].id, google) == "sent"


def test_company_invite_and_account_data(google, db, capsys):
    from app.models import Company, Payment, Subscription, User, UserSession
    from app.security import open_session

    assert cli.main(["company-add", "--name", "Textiles Ruiz"]) == 0
    assert cli.main(["company-add", "--name", "Textiles Ruiz"]) == 1  # duplicate
    args = ["invite", "--company", "Textiles Ruiz", "--email", "Ana@Example.com", "--name", "Ana",
            "--lang", "en"]
    assert cli.main(args, google=google) == 0
    user = db.query(User).one()
    assert user.email == "ana@example.com" and user.status == "invited"
    assert "#/accept-invite?token=" in google.sent[-1]["text"]
    assert cli.main(args, google=google) == 0  # re-invite sends a fresh link
    assert len(google.sent) == 2

    user.status = "active"
    db.commit()
    assert cli.main(args, google=google) == 1  # refuses an active user
    assert cli.main(["invite", "--company", "Nope", "--email", "x@example.com", "--name", "X"],
                    google=google) == 1

    open_session(db, user)
    assert cli.main(["user-disable", "--email", "ana@example.com"]) == 0
    db.expire_all()
    assert db.get(User, user.id).status == "disabled"
    assert db.query(UserSession).count() == 0
    assert cli.main(["user-enable", "--email", "ana@example.com"]) == 0

    assert cli.main(["subscription-add", "--company", "Textiles Ruiz", "--name", "Vision A"]) == 0
    sub = db.query(Subscription).one()
    assert cli.main(["subscription-set", "--id", str(sub.id), "--status", "paused"]) == 0
    db.expire_all()
    assert db.get(Subscription, sub.id).status == "paused"

    ok = ["payment-add", "--company", "Textiles Ruiz", "--date", "2026-10-05", "--amount",
          "8500", "--currency", "MXN"]
    assert cli.main(ok) == 0
    assert db.query(Payment).one().amount == 8500
    assert cli.main(ok[:-1] + ["pesos"]) == 2  # argparse rejects bad currency
    assert cli.main(["payment-add", "--company", "Textiles Ruiz", "--date", "2026-10-05",
                     "--amount", "-1", "--currency", "MXN"]) == 2

    capsys.readouterr()
    assert cli.main(["list", "users"]) == 0
    assert "ana@example.com" in capsys.readouterr().out
    assert db.query(Company).count() == 1
