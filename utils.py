"""
Utilities Module
Shared helper functions: logging setup, URL validation, text sanitization.
"""

import re
import logging
import os
from datetime import datetime


def setup_logging(level: str = None) -> None:
    """
    Configure root logger with a console handler and optional file handler.
    Level can be overridden with LOG_LEVEL environment variable.
    """
    log_level = getattr(logging, (level or os.getenv("LOG_LEVEL", "INFO")).upper(), logging.INFO)

    fmt = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(name)-25s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(log_level)

    # Console handler
    if not root.handlers:
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        root.addHandler(ch)

    # Optional file handler
    log_file = os.getenv("LOG_FILE", "")
    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        root.addHandler(fh)


def is_valid_url(url: str) -> bool:
    """Return True if `url` looks like a valid http/https URL."""
    return bool(re.match(r"^https?://[^\s/$.?#].[^\s]*$", url or "", re.IGNORECASE))


def sanitize_name(name: str) -> str:
    """Remove control characters and excess whitespace from a business name."""
    return re.sub(r"\s+", " ", re.sub(r"[\x00-\x1f\x7f]", "", name or "")).strip()


def timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
