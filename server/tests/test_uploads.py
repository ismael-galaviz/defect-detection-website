import pytest

from app import uploads

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 20
PDF = b"%PDF-1.7\n" + b"\x00" * 20


@pytest.mark.parametrize("content,expected", [
    (PNG, "image/png"), (JPEG, "image/jpeg"), (PDF, "application/pdf"),
    (b"MZ\x90\x00 renamed exe", None), (b"<svg onload=alert(1)>", None), (b"", None),
])
def test_sniff_by_content_not_name(content, expected):
    assert uploads.sniff(content) == expected


@pytest.mark.parametrize("name,expected", [
    ("screenshot.png", "screenshot.png"),
    ("../../etc/passwd", "passwd"),
    ("C:\\Users\\ana\\falla línea 3.jpg", "falla línea 3.jpg"),
    ('bad"name\r\n.pdf', "bad_name__.pdf"),
    ("", "file"),
    ("x" * 300 + ".png", "x" * 251 + ".png"),
])
def test_sanitize_filename(name, expected):
    assert uploads.sanitize_filename(name) == expected


def test_size_limit_constant():
    assert uploads.MAX_BYTES == 2 * 1024 * 1024
