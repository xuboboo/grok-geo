#!/usr/bin/env python3
"""Initialize a GEO audit run directory and manifest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (  # noqa: E402
    append_event,
    default_runs_base_dir,
    ensure_run_dirs,
    generate_run_id,
    new_manifest,
    print_json,
    read_json,
    save_manifest,
    sha256_json,
    write_json,
)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize GEO audit run")
    parser.add_argument("--input", required=True, help="Normalized input JSON")
    parser.add_argument(
        "--base-dir",
        default=None,
        help="Runs base directory (default: GEO_AUDIT_RUNS_DIR or ./geo-audit-runs)",
    )
    parser.add_argument("--run-id", default=None, help="Optional fixed run_id")
    args = parser.parse_args(argv)

    data = read_json(args.input)
    if not isinstance(data, dict):
        print("input must be JSON object", file=sys.stderr)
        return 1

    base = Path(args.base_dir).expanduser().resolve() if args.base_dir else default_runs_base_dir()
    base.mkdir(parents=True, exist_ok=True)

    run_id = args.run_id or generate_run_id()
    run_dir = base / run_id
    if run_dir.exists():
        print(f"run directory already exists: {run_dir}", file=sys.stderr)
        return 2

    paths = ensure_run_dirs(run_dir)
    brand_path = paths["input"] / "brand.json"
    # persist brand without internal-only keys if needed
    brand = {k: v for k, v in data.items() if not str(k).startswith("_")}
    write_json(brand_path, brand)

    input_sha = data.get("_meta", {}).get("input_sha256") or sha256_json(brand)
    question_count = int((data.get("options") or {}).get("question_count") or 0)
    mode = data.get("mode") or "standard"
    manifest = new_manifest(run_id, mode, input_sha, question_count=question_count)
    save_manifest(run_dir, manifest)
    append_event(
        run_dir,
        "run_initialized",
        {"run_id": run_id, "mode": mode, "question_count": question_count},
    )

    result = {"run_id": run_id, "run_dir": str(run_dir.resolve())}
    print_json(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())