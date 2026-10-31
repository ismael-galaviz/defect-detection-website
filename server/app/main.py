"""FastAPI app: everything is served under /api (same origin as the site via the Vercel rewrite)."""

import json
import logging
import time
from fnmatch import fnmatchcase

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError

from app.config import get_settings
from app.http import ApiError, error


class JsonFormatter(logging.Formatter):
    _std = set(vars(logging.makeLogRecord({})))

    def format(self, record: logging.LogRecord) -> str:
        data = {"level": record.levelname, "logger": record.name, "msg": record.getMessage()}
        data.update({k: v for k, v in vars(record).items() if k not in self._std})
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        return json.dumps(data, default=str)


def _setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)


log = logging.getLogger("app")
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def origin_allowed(origin: str) -> bool:
    return any(fnmatchcase(origin, pattern) for pattern in get_settings().public_site_origins)


_FIELD_CODES = {
    "missing": "required", "string_too_long": "too_long", "string_too_short": "required",
    "invalid_email": "invalid_email"}


def _field_errors(exc: RequestValidationError) -> dict[str, str]:
    fields: dict[str, str] = {}
    for err in exc.errors():
        loc = [str(p) for p in err["loc"] if p != "body"]
        name = ".".join(loc) or "body"
        fields.setdefault(name, _FIELD_CODES.get(err["type"], "invalid"))
    return fields


def create_app() -> FastAPI:
    _setup_logging()
    app = FastAPI(title="VeritX API", docs_url="/api/docs", openapi_url="/api/openapi.json",
                  redoc_url=None)

    @app.middleware("http")
    async def origin_and_logging(request: Request, call_next):
        start = time.perf_counter()
        if request.method not in SAFE_METHODS and not origin_allowed(
                request.headers.get("origin", "")):
            response = error(403, "bad_origin")
        else:
            response = await call_next(request)
        log.info("request", extra={
            "method": request.method, "path": request.url.path, "status": response.status_code,
            "ms": round((time.perf_counter() - start) * 1000)})
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request, exc: RequestValidationError):
        return error(422, "invalid", fields=_field_errors(exc))

    @app.exception_handler(ApiError)
    async def api_error_handler(_request, exc: ApiError):
        return error(exc.status, exc.code, **exc.extra)

    api = APIRouter(prefix="/api")

    @api.get("/health")
    def health():
        return {"ok": True}

    from app.routes import auth, booking, forms
    for module in (forms, booking, auth):
        api.include_router(module.router)
    app.include_router(api)
    return app


app = create_app()
