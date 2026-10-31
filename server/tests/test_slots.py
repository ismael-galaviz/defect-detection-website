from datetime import UTC, date, datetime, timedelta

from app.booking import CDMX, free_slots, is_bookable

# Monday 2026-11-02 08:00 CDMX
NOW = datetime(2026, 11, 2, 8, 0, tzinfo=CDMX)


def cdmx(day, hour):
    return datetime(2026, 11, day, hour, 0, tzinfo=CDMX)


def test_grid_weekdays_only_and_24h_lead():
    slots = free_slots(date(2026, 11, 2), date(2026, 11, 8), busy=[], booked=set(), now=NOW)
    days = {s.date() for s in slots}
    assert date(2026, 11, 7) not in days and date(2026, 11, 8) not in days  # weekend
    assert all(s - NOW >= timedelta(hours=24) for s in slots)
    assert cdmx(2, 9) not in slots and cdmx(3, 8) not in slots
    assert [s.hour for s in slots if s.date() == date(2026, 11, 4)] == [9, 10, 11, 12, 13, 16, 17]
    assert cdmx(3, 9) in slots  # exactly 25 h ahead


def test_offsets_are_mexico_city_without_dst():
    slots = free_slots(date(2026, 11, 4), date(2026, 11, 4), busy=[], booked=set(), now=NOW)
    assert slots[0].isoformat() == "2026-11-04T09:00:00-06:00"


def test_busy_overlap_excludes_slot():
    busy = [(datetime(2026, 11, 4, 16, 30, tzinfo=UTC), datetime(2026, 11, 4, 17, 15, tzinfo=UTC))]
    # 16:30–17:15 UTC = 10:30–11:15 CDMX → blocks 10:00 and 11:00
    hours = [s.hour for s in free_slots(date(2026, 11, 4), date(2026, 11, 4), busy=busy,
                                        booked=set(), now=NOW)]
    assert hours == [9, 12, 13, 16, 17]


def test_touching_busy_interval_does_not_block():
    busy = [(cdmx(4, 8), cdmx(4, 9))]
    slots = free_slots(date(2026, 11, 4), date(2026, 11, 4), busy=busy, booked=set(), now=NOW)
    assert cdmx(4, 9) in slots


def test_booked_slots_excluded_and_60_day_window():
    slots = free_slots(date(2026, 11, 4), date(2027, 2, 1), busy=[], booked={cdmx(4, 9)},
                       now=NOW)
    assert cdmx(4, 9) not in slots
    assert max(s.date() for s in slots) <= NOW.date() + timedelta(days=60)


def test_is_bookable():
    assert is_bookable(cdmx(4, 10), NOW)
    assert not is_bookable(cdmx(4, 14), NOW)  # lunch gap, not on grid
    assert not is_bookable(cdmx(4, 10).replace(minute=30), NOW)
    assert not is_bookable(cdmx(7, 10), NOW)  # Saturday
    assert not is_bookable(cdmx(2, 17), NOW)  # < 24 h
    assert is_bookable(cdmx(4, 10).astimezone(UTC), NOW)  # same instant in UTC is fine
