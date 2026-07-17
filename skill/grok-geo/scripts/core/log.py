"""Centralized logging configuration for grok-geo scripts.

Usage:
    from core.log import get_logger
    logger = get_logger(__name__)
    logger.info("message")
    logger.warning("sensitive data should not appear here")

Design:
    - All diagnostic/status messages go to stderr via logging
    - Structured data output (JSON) goes to stdout via print_json (untouched)
    - This separation ensures pipeline scripts never mix logs with data
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Optional

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

_initialized = False


def _init_root() -> None:
    global _initialized
    if _initialized:
        return
    _initialized = True

    level_name = os.getenv("GEO_LOG_LEVEL", "WARNING").upper()
    level = getattr(logging, level_name, logging.WARNING)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))

    root = logging.getLogger("grok-geo")
    root.setLevel(level)
    root.addHandler(handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger under the grok-geo namespace."""
    _init_root()
    if name is None:
        return logging.getLogger("grok-geo")
    # Strip module path prefix for cleaner output
    short = name.replace("skill.grok-geo.scripts.", "").replace("scripts.", "")
    return logging.getLogger(f"grok-geo.{short}")