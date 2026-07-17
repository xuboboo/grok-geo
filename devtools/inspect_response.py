#!/usr/bin/env python3
"""Inspect a saved Responses API JSON for web_search_call sources (stdlib)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def walk(obj: Any, found: List[Dict[str, Any]]) -> None:
    if isinstance(obj, dict):
        if obj.get("type") == "web_search_call" or "web_search_call" in str(obj.get("type", "")):
            found.append({"type": obj.get("type"), "id": obj.get("id"), "keys": list(obj.keys())})
        if "citations" in obj and isinstance(obj["citations"], list):
            found.append({"type": "citations", "count": len(obj["citations"])})
        if "sources" in obj and isinstance(obj["sources"], list):
            found.append({"type": "sources", "count": len(obj["sources"]), "sample": obj["sources"][:3]})
        for v in obj.values():
            walk(v, found)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, found)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Responses JSON for search evidence")
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    found: List[Dict[str, Any]] = []
    walk(data, found)
    print(json.dumps({"findings": found, "count": len(found)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())