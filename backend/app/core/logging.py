"""
Structured logging configuration for Secret Signal.

Replaces print() debugging with structured, contextual logs.

Every log entry contains:
  - timestamp (ISO 8601)
  - level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - service (backend, frontend, worker, ml)
  - request_id (UUID, set by middleware)
  - game_id (set when in game context)
  - room_id (set when in room context)
  - user_id (set when authenticated)
  - message (human-readable description)
  - extra (arbitrary structured data)

Usage:
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("game_started", game_id=42, room_code="ABC123", player_count=8)

Output (JSON in production):
    {"timestamp":"2025-01-15T10:30:00Z","level":"INFO","service":"backend",
     "logger":"app.game_engine.service","message":"game_started",
     "game_id":42,"room_code":"ABC123","player_count":8}
"""

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings

# ---------------------------------------------------------------------------
# Context variables — set per-request, accessible anywhere in the call stack
# ---------------------------------------------------------------------------
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[int | None] = ContextVar("user_id", default=None)
game_id_var: ContextVar[int | None] = ContextVar("game_id", default=None)
room_id_var: ContextVar[str | None] = ContextVar("room_id", default=None)


def generate_request_id() -> str:
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# JSON Formatter — structured log output for production
# ---------------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    """Outputs log entries as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "backend",
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Inject context variables
        req_id = request_id_var.get("")
        if req_id:
            log_entry["request_id"] = req_id

        uid = user_id_var.get(None)
        if uid is not None:
            log_entry["user_id"] = uid

        gid = game_id_var.get(None)
        if gid is not None:
            log_entry["game_id"] = gid

        rid = room_id_var.get(None)
        if rid is not None:
            log_entry["room_id"] = rid

        # Include any extra fields passed via logger.info("msg", key=val)
        for key in (
            "game_id",
            "room_id",
            "user_id",
            "room_code",
            "player_count",
            "winner",
            "phase",
            "round_number",
            "event_type",
            "scan_id",
            "model_version",
            "sequence_number",
        ):
            val = getattr(record, key, None)
            if val is not None and key not in log_entry:
                log_entry[key] = val

        # Include exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


# ---------------------------------------------------------------------------
# Human-readable formatter for development
# ---------------------------------------------------------------------------
class DevFormatter(logging.Formatter):
    """Colored, human-readable logs for local development."""

    COLORS = {
        "DEBUG": "\033[36m",  # cyan
        "INFO": "\033[32m",  # green
        "WARNING": "\033[33m",  # yellow
        "ERROR": "\033[31m",  # red
        "CRITICAL": "\033[41m",  # red bg
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        req_id = request_id_var.get("")
        req_part = f" [{req_id}]" if req_id else ""

        ts = datetime.now().strftime("%H:%M:%S")
        msg = record.getMessage()

        return f"{color}{ts} {record.levelname:8s}{self.RESET}{req_part} {record.name}: {msg}"


# ---------------------------------------------------------------------------
# Logger setup
# ---------------------------------------------------------------------------
def setup_logging() -> None:
    """Configure the root logger based on the current environment."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Remove existing handlers
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if settings.environment == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(DevFormatter())

    root.addHandler(handler)

    # Quieten noisy libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger. Use this everywhere instead of print()."""
    return logging.getLogger(name)
