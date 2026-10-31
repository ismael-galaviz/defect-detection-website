"""Meeting slot grid and availability (spec FR-007; research R8). Pure functions, no I/O."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

CDMX = ZoneInfo("America/Mexico_City")
SLOT_HOURS = (9, 10, 11, 12, 13, 16, 17)  # same grid as the site's picker
SLOT_LENGTH = timedelta(hours=1)
MIN_LEAD = timedelta(hours=24)
MAX_DAYS_AHEAD = 60

Interval = tuple[datetime, datetime]


def _window_ok(start: datetime, now: datetime) -> bool:
    last_day = now.astimezone(CDMX).date() + timedelta(days=MAX_DAYS_AHEAD)
    return start - now >= MIN_LEAD and start.astimezone(CDMX).date() <= last_day


def is_bookable(start: datetime, now: datetime) -> bool:
    """On the grid (weekday, grid hour, on the hour) and inside the booking window."""
    local = start.astimezone(CDMX)
    on_grid = (local.weekday() < 5 and local.hour in SLOT_HOURS
               and local.minute == local.second == local.microsecond == 0)
    return on_grid and _window_ok(start, now)


def overlaps(start: datetime, busy: list[Interval]) -> bool:
    end = start + SLOT_LENGTH
    return any(b_start < end and b_end > start for b_start, b_end in busy)


def free_slots(first: date, last: date, *, busy: list[Interval], booked: set[datetime],
               now: datetime) -> list[datetime]:
    """Bookable slot starts (CDMX-aware) from `first` to `last` inclusive."""
    slots = []
    day = first
    while day <= last:
        for hour in SLOT_HOURS:
            start = datetime(day.year, day.month, day.day, hour, tzinfo=CDMX)
            if is_bookable(start, now) and start not in booked and not overlaps(start, busy):
                slots.append(start)
        day += timedelta(days=1)
    return slots
