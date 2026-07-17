#!/usr/bin/env python3
"""Stub: upload skill zip to OpenAI Skills API (requires OPENAI_API_KEY + openai pkg)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload grok-geo skill zip")
    parser.add_argument("--zip", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    z = Path(args.zip)
    if not z.exists():
        print(f"zip not found: {z}", file=sys.stderr)
        return 1
    if args.dry_run or not os.environ.get("OPENAI_API_KEY"):
        print(
            json_dumps(
                {
                    "status": "dry_run",
                    "zip": str(z.resolve()),
                    "note": "Set OPENAI_API_KEY and install openai to upload.",
                }
            )
        )
        return 0
    try:
        from openai import OpenAI  # type: ignore
    except ImportError:
        print("openai package not installed", file=sys.stderr)
        return 2
    client = OpenAI()
    with z.open("rb") as fh:
        skill = client.skills.create(files=fh)
    print(json_dumps({"skill_id": getattr(skill, "id", None)}))
    return 0


def json_dumps(obj: object) -> str:
    import json

    return json.dumps(obj, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())