"""CLI output utilities."""
from __future__ import annotations

import json
import sys
from typing import Any


def exit_with(code: int, message: str, *, stream: str = "stderr") -> None:
    out = sys.stderr if stream == "stderr" else sys.stdout
    print(message, file=out)
    raise SystemExit(code)


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))