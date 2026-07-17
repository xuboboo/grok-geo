#!/usr/bin/env python3
"""Stub: download artifacts from hosted container /mnt/data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Download hosted artifacts (stub)")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--dest", default="./downloads")
    parser.add_argument("--dry-run", action="store_true", default=True)
    args = parser.parse_args()
    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    print(
        json.dumps(
            {
                "status": "dry_run",
                "run_id": args.run_id,
                "dest": str(dest.resolve()),
                "note": "Hosted download depends on container file APIs; copy /mnt/data/geo-audit-runs/<run_id> manually if needed.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())