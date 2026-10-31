from datetime import date
from decimal import Decimal

from app.models import Company, Payment, Subscription


def test_me_shows_only_own_company_data(client, google, db, make_user):
    make_user(email="ana@example.com", company="Textiles Ruiz")
    make_user(email="luis@example.com", company="Textiles Ruiz", name="Luis")
    make_user(email="eva@example.com", company="Hilos Norte", name="Eva")
    ruiz = db.query(Company).filter_by(name="Textiles Ruiz").one()
    norte = db.query(Company).filter_by(name="Hilos Norte").one()
    db.add_all([
        Subscription(company_id=ruiz.id, name="Vision A — Final Inspection", status="active"),
        Payment(company_id=ruiz.id, paid_on=date(2026, 10, 5), amount=Decimal("8500.00"),
                currency="MXN"),
        Subscription(company_id=norte.id, name="Vision A — Norte line", status="active"),
    ])
    db.commit()

    def me(email):
        client.cookies.clear()
        client.post("/api/auth/login", json={"email": email, "password": "a-long-password-1"})
        return client.get("/api/me").json()

    ana, luis, eva = me("ana@example.com"), me("luis@example.com"), me("eva@example.com")
    assert ana["subscriptions"] == luis["subscriptions"] == [
        {"name": "Vision A — Final Inspection", "status": "active"}]
    assert ana["payments"] == [{"paid_on": "2026-10-05", "amount": "8500.00", "currency": "MXN"}]
    assert eva["subscriptions"] == [{"name": "Vision A — Norte line", "status": "active"}]
    assert eva["payments"] == []
    assert ana["user"] == {"name": "Ana Ruiz", "email": "ana@example.com", "lang": "es"}
