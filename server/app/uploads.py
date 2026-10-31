"""Ticket attachment checks (FR-026; research R9). Type is judged by content, not by name."""

import re

MAX_BYTES = 2 * 1024 * 1024
MAX_PER_TICKET = 3
_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"%PDF-", "application/pdf"),
)
_UNSAFE = re.compile(r'[\x00-\x1f\x7f"<>:|?*]')


def sniff(content: bytes) -> str | None:
    for signature, content_type in _SIGNATURES:
        if content.startswith(signature):
            return content_type
    return None


def sanitize_filename(name: str) -> str:
    """Last path component, no control/quote/reserved characters, at most 255 characters."""
    base = re.split(r"[\\/]", name)[-1].strip()
    base = _UNSAFE.sub("_", base) or "file"
    if len(base) > 255:
        stem, dot, ext = base.rpartition(".")
        base = (stem[: 255 - len(ext) - 1] + dot + ext) if dot and len(ext) <= 10 else base[:255]
    return base
