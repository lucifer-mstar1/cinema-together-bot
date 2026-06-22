from app.models import Payment, User
from app.services import parse_invoice_payload, payment_days, star_price, make_invoice_payload


def make_user():
    return User(id=42, telegram_id=123, preferred_language="uz", anon_name="A", plan="free")


def test_v12_star_price_configured():
    assert star_price("plus", 1) == 50
    assert star_price("pro", 1) == 150
    assert star_price("plus", 12) == 550


def test_v12_payment_days():
    assert payment_days(1) == 30
    assert payment_days(12) == 360


def test_v12_invoice_payload_roundtrip():
    payload = make_invoice_payload(make_user(), "plus", 3)
    parsed = parse_invoice_payload(payload)
    assert parsed is not None
    assert parsed["user_id"] == 42
    assert parsed["plan"] == "plus"
    assert parsed["months"] == 3


def test_v12_payment_model_defaults():
    p = Payment(user_id=1, plan="pro", duration_months=1, stars_amount=150, invoice_payload="payload")
    assert p.status is None or p.status == "pending"
    assert p.plan == "pro"
