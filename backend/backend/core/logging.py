from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
import uuid
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import TracebackType
from typing import Any

from config import config

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

_CONFIGURED = False
_GENERIC_SECRET_PATTERNS = [
    (
        re.compile(r"(?i)((?:mongodb(?:\+srv)?|redis|rediss)://[^:/\s]+:)([^@\s]+)(@)"),
        r"\1[REDACTED]\3",
    ),
    (re.compile(r"\b\d{5,}:[A-Za-z0-9_-]{20,}\b"), "[REDACTED]"),
    (
        re.compile(
            r"(?i)(token|api[_-]?hash|api[_-]?key|password|passwd|secret)"
            r"([\"']?\s*[:=]\s*[\"']?)([^\"'\s,;]+)"
        ),
        r"\1\2[REDACTED]",
    ),
]
_SENSITIVE_CONFIG_NAMES = (
    "TOKEN",
    "SUB_TOKEN",
    "API_HASH",
    "MONGO_URL",
    "REDIS_URL",
    "IMGBB_API_KEY",
    "STRING_SESSION",
)


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def set_request_id(request_id: str):
    return request_id_var.set(request_id or "-")


def reset_request_id(token) -> None:
    request_id_var.reset(token)


class LogRedactor:
    def __init__(self, secrets: list[str]) -> None:
        self._secret_patterns = [
            re.compile(re.escape(secret))
            for secret in secrets
            if isinstance(secret, str) and len(secret) >= 8
        ]

    def redact(self, value: Any) -> str:
        text = str(value)
        for pattern, replacement in _GENERIC_SECRET_PATTERNS:
            text = pattern.sub(replacement, text)
        for pattern in self._secret_patterns:
            text = pattern.sub("[REDACTED]", text)
        return text


class LoggingContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class TextFormatter(logging.Formatter):
    def __init__(self, redactor: LogRedactor, *, use_utc: bool) -> None:
        suffix = "Z" if use_utc else ""
        super().__init__(
            fmt=f"%(asctime)s{suffix} | %(levelname)-8s | %(name)s | rid=%(request_id)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        self.redactor = redactor
        if use_utc:
            self.converter = time.gmtime

    def format(self, record: logging.LogRecord) -> str:
        return self.redactor.redact(super().format(record))


class JsonFormatter(logging.Formatter):
    def __init__(self, redactor: LogRedactor, *, use_utc: bool) -> None:
        super().__init__()
        self.redactor = redactor
        self.use_utc = use_utc

    def format(self, record: logging.LogRecord) -> str:
        timestamp = time.gmtime(record.created) if self.use_utc else time.localtime(record.created)
        suffix = "Z" if self.use_utc else ""
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", timestamp) + suffix,
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.pathname:
            payload["source"] = f"{record.filename}:{record.lineno}"
        return self.redactor.redact(json.dumps(payload, ensure_ascii=True, default=str))


def _configured_secrets() -> list[str]:
    secrets: list[str] = []
    for name in _SENSITIVE_CONFIG_NAMES:
        value = getattr(config, name, None) or os.getenv(name)
        if value:
            secrets.append(str(value))
    return secrets


def _parse_level(value: str | int | None) -> int:
    if isinstance(value, int):
        return value
    name = str(value or "INFO").strip().upper()
    return logging._nameToLevel.get(name, logging.INFO)


def _build_formatter(redactor: LogRedactor) -> logging.Formatter:
    use_json = str(getattr(config, "LOG_FORMAT", "text")).strip().lower() == "json"
    use_utc = bool(getattr(config, "LOG_UTC", True))
    if use_json:
        return JsonFormatter(redactor, use_utc=use_utc)
    return TextFormatter(redactor, use_utc=use_utc)


def _add_handler(root: logging.Logger, handler: logging.Handler, formatter: logging.Formatter) -> None:
    handler.setFormatter(formatter)
    handler.addFilter(LoggingContextFilter())
    root.addHandler(handler)


def setup_logging(*, force: bool = False) -> logging.Logger:
    global _CONFIGURED
    if _CONFIGURED and not force:
        return logging.getLogger("backend")

    level = _parse_level(getattr(config, "LOG_LEVEL", "INFO"))
    redactor = LogRedactor(_configured_secrets())
    formatter = _build_formatter(redactor)

    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    root.setLevel(level)
    _add_handler(root, logging.StreamHandler(sys.stdout), formatter)

    if getattr(config, "LOG_FILE_ENABLED", True):
        log_dir = Path(getattr(config, "LOG_DIR", "logs"))
        log_file = Path(getattr(config, "LOG_FILE", "seal-bot.log"))
        if not log_file.is_absolute():
            log_file = log_dir / log_file
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=int(getattr(config, "LOG_MAX_BYTES", 10 * 1024 * 1024)),
                backupCount=int(getattr(config, "LOG_BACKUP_COUNT", 5)),
                encoding="utf-8",
            )
            _add_handler(root, file_handler, formatter)
        except OSError as exc:
            logging.getLogger("backend.logging").warning(
                "File logging disabled because log path is not writable: %s", exc
            )

    for logger_name, logger_level in {
        "asyncio": "WARNING",
        "httpcore": "WARNING",
        "httpx": "WARNING",
        "pyrogram": "WARNING",
        "pymongo": "WARNING",
        "redis": "WARNING",
        "uvicorn.access": "WARNING",
    }.items():
        logging.getLogger(logger_name).setLevel(_parse_level(logger_level))

    _CONFIGURED = True
    logger = logging.getLogger("backend")
    logger.info("Logging initialized: level=%s format=%s", logging.getLevelName(level), config.LOG_FORMAT)
    return logger


def get_logger(name: str) -> logging.Logger:
    if not _CONFIGURED:
        setup_logging()
    return logging.getLogger(name)


def install_exception_hooks(logger_name: str = "backend.runtime") -> None:
    logger = get_logger(logger_name)

    def _excepthook(
        exc_type: type[BaseException],
        exc: BaseException,
        tb: TracebackType | None,
    ) -> None:
        logger.critical("Uncaught exception", exc_info=(exc_type, exc, tb))

    sys.excepthook = _excepthook


def configure_event_loop_logging(logger_name: str = "backend.asyncio") -> None:
    logger = get_logger(logger_name)
    try:
        import asyncio

        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    def _handler(loop, context: dict[str, Any]) -> None:
        exc = context.get("exception")
        message = context.get("message") or "Unhandled event loop exception"
        if exc:
            logger.error(message, exc_info=(type(exc), exc, exc.__traceback__))
        else:
            logger.error("%s: %s", message, context)

    loop.set_exception_handler(_handler)
