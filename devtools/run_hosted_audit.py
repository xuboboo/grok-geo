#!/usr/bin/env python3
"""Stub: run hosted audit via Responses API (requires network + keys)."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run hosted GEO audit (stub)")
    parser.add_argument("--input", required=True)
    parser.add_argument("--container-id", default=os.environ.get("GEO_CONTAINER_ID"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    payload = {
        "status": "dry_run" if args.dry_run or not os.environ.get("OPENAI_API_KEY") else "not_implemented_live",
        "brand_name": data.get("brand_name"),
        "container_id": args.container_id,
        "hint": "Use Responses API with web_search + shell + skill_reference; see reem.md §21.",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())