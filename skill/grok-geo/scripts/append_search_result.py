#!/usr/bin/env python3
"""Append a search result to raw/search_results.jsonl with lock and dedupe."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (  # noqa: E402
    append_event,
    append_jsonl,
    file_lock,
    load_manifest,
    load_schema,
    print_json,
    read_json,
    read_jsonl,
    save_manifest,
    utc_now_iso,
    validate_against_schema,
)


def is_success(row: Dict[str, Any]) -> bool:
    if row.get("status") != "success":
        return False
    answer = (row.get("answer_text") or "").strip()
    if not answer:
        return False
    return True


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Append search result to run raw JSONL")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--input", required=True, help="single search result JSON")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir)
    result_path = Path(args.input)
    if not result_path.exists():
        print(f"input not found: {result_path}", file=sys.stderr)
        return 10

    row = read_json(result_path)
    if not isinstance(row, dict):
        print("search result must be object", file=sys.stderr)
        return 11

    row.setdefault("schema_version", "1.0")
    row.setdefault("executed_at", utc_now_iso())
    if "run_id" not in row:
        try:
            manifest = load_manifest(run_dir)
            row["run_id"] = manifest.get("run_id")
        except FileNotFoundError:
            print("warn: manifest not found, run_id not set", file=sys.stderr)

    # citation_status
    citations = row.get("citations") or []
    if row.get("status") == "success":
        row["citation_status"] = "present" if citations else "none"
        if not (row.get("answer_text") or "").strip():
            row["status"] = "failed"
            row["error"] = row.get("error") or "EMPTY_ANSWER"

    schema = load_schema("search-result.schema.json")
    errors = validate_against_schema(row, schema)
    if errors:
        print("INVALID_SEARCH_RESULT:\n" + "\n".join(errors), file=sys.stderr)
        return 12

    jsonl_path = run_dir / "raw" / "search_results.jsonl"
    lock_target = run_dir / "raw" / "search_results"
    with file_lock(lock_target):
        existing = read_jsonl(jsonl_path)
        key = (row.get("question_id"), row.get("query_text"))
        for prev in existing:
            if (prev.get("question_id"), prev.get("query_text")) == key:
                msg = {
                    "appended": False,
                    "reason": "duplicate",
                    "question_id": row.get("question_id"),
                }
                if args.json:
                    print_json(msg)
                else:
                    print("duplicate")
                return 0
        append_jsonl(jsonl_path, row)

        # recount
        all_rows = existing + [row]
        success = sum(1 for r in all_rows if is_success(r))
        failed = len(all_rows) - success
        try:
            manifest = load_manifest(run_dir)
            manifest["search_result_count"] = len(all_rows)
            manifest["successful_result_count"] = success
            manifest["failed_result_count"] = failed
            if manifest.get("status") in {None, "INITIALIZED", "WAITING_FOR_SEARCH", "GENERATING_QUESTIONS"}:
                manifest["status"] = "SEARCHING"
            save_manifest(run_dir, manifest)
        except FileNotFoundError:
            print("warn: manifest not found, counts not updated", file=sys.stderr)

    append_event(
        run_dir,
        "search_result_appended",
        {
            "question_id": row.get("question_id"),
            "status": row.get("status"),
        },
    )
    out = {
        "appended": True,
        "question_id": row.get("question_id"),
        "status": row.get("status"),
        "path": str(jsonl_path),
    }
    if args.json:
        print_json(out)
    else:
        print(str(jsonl_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())