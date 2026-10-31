"""Settings read from environment variables (see docs/deployment/environments.md)."""

import os
from dataclasses import dataclass
from functools import lru_cache


class ConfigError(RuntimeError):
    pass


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(f"Missing required environment variable {name}")
    return value


@dataclass(frozen=True)
class Settings:
    database_url: str
    staff_email: str
    public_site_origins: tuple[str, ...]
    site_url: str
    google_fake: bool
    google_client_id: str
    google_client_secret: str
    google_refresh_token: str
    google_calendar_id: str


@lru_cache
def get_settings() -> Settings:
    fake = os.environ.get("GOOGLE_FAKE", "") == "1"
    google = (lambda n: os.environ.get(n, "")) if fake else _required
    return Settings(
        database_url=_required("DATABASE_URL"),
        staff_email=_required("STAFF_EMAIL"),
        public_site_origins=tuple(
            o.strip() for o in _required("PUBLIC_SITE_ORIGINS").split(",") if o.strip()
        ),
        site_url=_required("SITE_URL").rstrip("/"),
        google_fake=fake,
        google_client_id=google("GOOGLE_CLIENT_ID"),
        google_client_secret=google("GOOGLE_CLIENT_SECRET"),
        google_refresh_token=google("GOOGLE_REFRESH_TOKEN"),
        google_calendar_id=os.environ.get("GOOGLE_CALENDAR_ID", "primary") or "primary",
    )
