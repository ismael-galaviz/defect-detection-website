import pytest

from app import emails

FREE_TEXT = {
    "name": "ZZNAMEZZ http://spam.example", "company": "ZZCOMPANYZZ",
    "message": "ZZMESSAGEZZ buy now", "country": "ZZCOUNTRYZZ", "stage": "ZZSTAGEZZ",
    "email": "visitor@example.com", "video_tool": "ZZTOOLZZ",
}
INPUTS = {"defects": {"rateBefore": 1.2, "rateAfter": 0.2, "volume": 500000, "costPerDefect": 150}}
RESULTS = {"defects": 750000, "total": 750000}


@pytest.mark.parametrize("lang", ["es", "en", "fr"])
def test_visitor_confirmation_never_echoes_free_text(lang):
    for subject, text in (emails.visitor_contact(lang),
                          emails.visitor_booking(lang, "2026-11-04T10:00:00-06:00"),
                          emails.EVENT_COPY[lang]):
        for value in FREE_TEXT.values():
            assert value not in subject and value not in text


@pytest.mark.parametrize("lang", ["es", "en", "fr"])
def test_visitor_booking_shows_the_slot(lang):
    assert "2026-11-04 10:00" in emails.visitor_booking(lang, "2026-11-04T10:00:00-06:00")[1]


@pytest.mark.parametrize("lang", ["es", "en", "fr"])
def test_visitor_calculator_has_numbers_and_labels_only(lang):
    subject, text = emails.visitor_calculator(lang, "MXN", INPUTS, RESULTS)
    assert "ZZ" not in text
    assert "750" in text and "MXN" in text
    assert emails.CALC_LABELS[lang]["sections"]["defects"] in text


def test_languages_differ():
    es, en, fr = (emails.visitor_contact(lang) for lang in ("es", "en", "fr"))
    assert es != en and fr != en


def test_staff_contact_contains_every_field():
    subject, text = emails.staff_contact(FREE_TEXT)
    for value in FREE_TEXT.values():
        assert value in text
    assert "ZZNAMEZZ" in subject


def test_money_formatting_per_language():
    assert emails.money(4550000, "MXN", "en") == "4,550,000 MXN"
    assert emails.money(4550000, "MXN", "es") == "4,550,000 MXN"
    assert emails.money(4550000, "EUR", "fr") == "4 550 000 EUR"
