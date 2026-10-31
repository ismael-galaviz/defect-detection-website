"""Small helpers shared by routes: error responses and client IP."""

import ipaddress

from fastapi import Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """Raise from routes or dependencies to answer with the contract's error format."""

    def __init__(self, status: int, code: str, **extra):
        super().__init__(code)
        self.status, self.code, self.extra = status, code, extra


def error(status: int, code: str, **extra) -> JSONResponse:
    """Error body per contracts/api.md: {"error": code, ...}."""
    return JSONResponse({"error": code, **extra}, status_code=status)


def client_ip(request: Request) -> str:
    """Leftmost X-Forwarded-For entry (set by Vercel). Best-effort: spoofable if Railway is
    called directly, so only used for soft limits (research R6)."""
    candidates = [request.headers.get("x-forwarded-for", "").split(",")[0].strip()]
    if request.client:
        candidates.append(request.client.host)
    for candidate in candidates:
        try:
            return str(ipaddress.ip_address(candidate))
        except ValueError:
            continue
    return "0.0.0.0"  # noqa: S104 (unknown client; not a bind address)
