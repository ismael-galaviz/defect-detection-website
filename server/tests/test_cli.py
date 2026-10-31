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
