#!/usr/bin/env python3
"""Shared utilities for grok-geo deterministic scripts.

BACKWARD-COMPATIBILITY SHIM — all symbols re-exported from sub-packages.
New code should import from `core.*` or `scoring.*` directly.

Architecture:
  core/constants.py   — all constant definitions
  core/io_utils.py    — JSON, JSONL, CSV, atomic write
  core/path_utils.py  — directories, manifests, skill root
  core/hashing.py     — SHA-256 helpers
  core/time_utils.py  — UTC timestamps
  core/validation.py  — JSON Schema validator
  core/locking.py     — FileLock
  core/text_utils.py  — entity/question normalization
  core/url_utils.py   — domain extraction
  core/cli_utils.py   — exit_with, print_json
  scoring/__init__.py — all scoring functions (geo_score, freshness_score, etc.)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure scripts/ is on sys.path so sub-package imports resolve
_scripts_dir = str(Path(__file__).resolve().parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

# Re-export everything from core and scoring
from core.constants import *  # noqa: F401,F403
from core.io_utils import *  # noqa: F401,F403
from core.path_utils import *  # noqa: F401,F403
from core.hashing import *  # noqa: F401,F403
from core.time_utils import *  # noqa: F401,F403
from core.validation import *  # noqa: F401,F403
from core.locking import FileLock, file_lock  # noqa: F401
from core.text_utils import *  # noqa: F401,F403
from core.url_utils import *  # noqa: F401,F403
from core.cli_utils import *  # noqa: F401,F403
from core.log import get_logger  # noqa: F401
from scoring import *  # noqa: F401,F403