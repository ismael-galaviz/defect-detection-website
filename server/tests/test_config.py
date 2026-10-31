import pytest

from app.config import normalize_database_url


@pytest.mark.parametrize("url,expected", [
    ("postgresql://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
    ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
    ("postgresql+psycopg://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
])
def test_railway_urls_get_the_psycopg_driver(url, expected):
    assert normalize_database_url(url) == expected
