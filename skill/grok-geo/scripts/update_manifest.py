#!/usr/bin/env python3
"""Update run manifest status, counters, warnings, errors, outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (  # noqa: E402
    RUN_STATUSES,
    append_event,
    load_manifest,
    print_json,
    save_manifest,
    utc_now_iso,
)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Update GEO audit manifest")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--status", default=None, choices=list(RUN_STATUSES))
    parser.add_argument("--question-count", type=int, default=None)
    parser.add_argument("--search-result-count", type=int, default=None)
    parser.add_argument("--successful-result-count", type=int, default=None)
    parser.add_argument("--failed-result-count", type=int, default=None)
    parser.add_argument("--current-batch", type=int, default=None)
    parser.add_argument("--add-warning", action="append", default=[])
    parser.add_argument("--add-error", action="append", default=[])
    parser.add_argument(
        "--set-output",
        action="append",
        default=[],
        metavar="KEY=PATH",
        help="Set outputs[KEY]=PATH",
    )
    parser.add_argument("--completed", action="store_true", help="Set completed_at now")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir)
    try:
        manifest = load_manifest(run_dir)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    prev_status = manifest.get("status")
    if args.status:
        manifest["status"] = args.status
    if args.question_count is not None:
        manifest["question_count"] = args.question_count
    if args.search_result_count is not None:
        manifest["search_result_count"] = args.search_result_count
    if args.successful_result_count is not None:
        manifest["successful_result_count"] = args.successful_result_count
    if args.failed_result_count is not None:
        manifest["failed_result_count"] = args.failed_result_count
    if args.current_batch is not None:
        manifest["current_batch"] = args.current_batch

    warnings: List[Any] = list(manifest.get("warnings") or [])
    for w in args.add_warning:
        warnings.append({"ts": utc_now_iso(), "message": w})
    manifest["warnings"] = warnings

    errors: List[Any] = list(manifest.get("errors") or [])
    for e in args.add_error:
        errors.append({"ts": utc_now_iso(), "message": e})
    manifest["errors"] = errors

    outputs: Dict[str, Any] = dict(manifest.get("outputs") or {})
    for item in args.set_output:
        if "=" not in item:
            print(f"invalid --set-output: {item}", file=sys.stderr)
            return 2
        k, v = item.split("=", 1)
        outputs[k] = v
    manifest["outputs"] = outputs

    if args.completed or args.status in {"COMPLETED", "PARTIAL", "FAILED"}:
        manifest["completed_at"] = utc_now_iso()

    save_manifest(run_dir, manifest)
    append_event(
        run_dir,
        "manifest_updated",
        {"from_status": prev_status, "to_status": manifest.get("status")},
    )
    if args.json:
        print_json(manifest)
    else:
        print(manifest.get("status"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())