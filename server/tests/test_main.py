from app.http import client_ip


def test_health(client):
    assert client.get("/api/health").json() == {"ok": True}


def test_post_without_allowed_origin_is_refused(client):
    r = client.post("/api/contact", json={}, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403 and r.json() == {"error": "bad_origin"}


def test_wildcard_origin_matches_previews(client):
    r = client.post("/api/health", headers={"Origin": "https://preview-abc.example"})
    assert r.status_code == 405  # origin passed; health is GET-only


def test_client_ip_uses_leftmost_forwarded_for_and_ignores_garbage():
    class Req:
        def __init__(self, xff):
            self.headers = {"x-forwarded-for": xff}
            self.client = type("C", (), {"host": "10.0.0.1"})()

    assert client_ip(Req("203.0.113.7, 10.1.1.1")) == "203.0.113.7"
    assert client_ip(Req("not-an-ip")) == "10.0.0.1"
