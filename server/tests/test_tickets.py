from app import cli
from tests.test_uploads import PDF, PNG

PW = "a-long-password-1"


def sign_in(client, email="ana@example.com"):
    client.cookies.clear()
    assert client.post("/api/auth/login", json={"email": email, "password": PW}).status_code == 204


def upload(client, name="shot.png", content=PNG, mime="image/png"):
    return client.post("/api/attachments", files={"file": (name, content, mime)})


def ticket(client, **kw):
    body = {"subject": "Camera 2 offline", "description": "Since 9am", "priority": "high",
            "attachment_ids": [], **kw}
    return client.post("/api/tickets", json=body)


def test_ticket_with_attachments_emails_staff(client, google, make_user):
    make_user()
    sign_in(client)
    a1 = upload(client).json()
    a2 = upload(client, "report.pdf", PDF, "application/pdf").json()
    assert a1["content_type"] == "image/png" and a1["size"] == len(PNG)
    r = ticket(client, attachment_ids=[a1["id"], a2["id"]])
    assert r.status_code == 201
    [mail] = google.sent
    assert mail["to"] == "staff@example.com" and mail["reply_to"] == "ana@example.com"
    assert "Camera 2 offline" in mail["subject"] and "Since 9am" in mail["text"]
    assert [a[0] for a in mail["attachments"]] == ["shot.png", "report.pdf"]
    me = client.get("/api/me").json()
    [t] = me["tickets"]
    assert t["status"] == "open" and t["priority"] == "high"
    assert [a["filename"] for a in t["attachments"]] == ["shot.png", "report.pdf"]


def test_upload_rejections(client, google, make_user):
    make_user()
    sign_in(client)
    r = upload(client, "virus.png", b"MZ\x90\x00 exe", "image/png")
    assert r.status_code == 415 and r.json()["error"] == "unsupported_type"
    r = upload(client, "big.png", PNG + b"\x00" * (2 * 1024 * 1024), "image/png")
    assert r.status_code == 413 and r.json()["error"] == "too_large"


def test_uploads_need_a_session(client, google):
    assert upload(client).status_code == 401
    assert ticket(client).status_code == 401


def test_attachment_id_rules(client, google, make_user):
    make_user()
    make_user(email="eva@example.com", company="Hilos Norte", name="Eva")
    sign_in(client, "eva@example.com")
    foreign = upload(client).json()["id"]
    sign_in(client)
    ids = [upload(client).json()["id"] for _ in range(4)]
    assert ticket(client, attachment_ids=ids).status_code == 422          # more than 3
    assert ticket(client, attachment_ids=[foreign]).status_code == 422    # someone else's
    assert ticket(client, attachment_ids=[ids[0]]).status_code == 201
    assert ticket(client, attachment_ids=[ids[0]]).status_code == 422     # already linked
    assert ticket(client, subject="").status_code == 422
    assert ticket(client, priority="urgent").status_code == 422


def test_other_company_cannot_see_ticket_or_files(client, google, make_user):
    make_user()
    make_user(email="luis@example.com", name="Luis")  # same company
    make_user(email="eva@example.com", company="Hilos Norte", name="Eva")
    sign_in(client)
    att = upload(client).json()["id"]
    ticket(client, attachment_ids=[att])

    sign_in(client, "luis@example.com")
    assert len(client.get("/api/me").json()["tickets"]) == 1
    r = client.get(f"/api/attachments/{att}")
    assert r.status_code == 200 and r.content == PNG
    assert r.headers["content-type"] == "image/png"
    assert r.headers["content-disposition"].startswith("attachment")
    assert r.headers["x-content-type-options"] == "nosniff"

    sign_in(client, "eva@example.com")
    assert client.get("/api/me").json()["tickets"] == []
    assert client.get(f"/api/attachments/{att}").status_code == 404


def test_ticket_status_cli_and_resend(client, google, make_user, capsys):
    make_user()
    sign_in(client)
    google.fail = True
    tid = ticket(client).json()["id"]
    assert cli.main(["list", "pending"]) == 0
    assert "ticket" in capsys.readouterr().out
    google.fail = False
    assert cli.main(["resend-pending"], google=google) == 0
    assert cli.main(["ticket-status", "--id", str(tid), "--status", "resolved"]) == 0
    assert client.get("/api/me").json()["tickets"][0]["status"] == "resolved"
    assert cli.main(["ticket-status", "--id", "999", "--status", "closed"]) == 1
    assert cli.main(["list", "tickets"]) == 0
    assert "Camera 2 offline" in capsys.readouterr().out
