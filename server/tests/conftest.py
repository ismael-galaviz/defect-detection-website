import os

TEST_DB = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://postgres:dev@localhost:5432/veritx_test"
)
SITE_ORIGIN = "https://site.example"
os.environ.update(
    DATABASE_URL=TEST_DB,
    STAFF_EMAIL="staff@example.com",
    PUBLIC_SITE_ORIGINS=f"{SITE_ORIGIN},https://preview-*.example",
    SITE_URL=SITE_ORIGIN,
    GOOGLE_FAKE="1",
)

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.db import get_engine  # noqa: E402
from app.google import FakeGoogle, get_google  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def schema():
    """Fresh schema built by the real migrations, so they are tested too."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public"))
    root = os.path.join(os.path.dirname(__file__), "..")
    cfg = Config(os.path.join(root, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(root, "migrations"))
    cfg.attributes["url"] = TEST_DB
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def clean_tables():
    yield
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    if tables:
        with get_engine().begin() as conn:
            conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def google():
    fake = FakeGoogle()
    app.dependency_overrides[get_google] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_google, None)


@pytest.fixture
def client(google):
    with TestClient(app, headers={"Origin": SITE_ORIGIN}) as c:
        yield c
