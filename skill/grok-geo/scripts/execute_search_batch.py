#!/usr/bin/env python3
"""Execute a search batch with multi-variant support and immediate signal extraction.

This script manages batch execution for the search phase:
- Loads questions and generates variants
- Tracks which questions have been searched
- Validates batch results
- Updates manifest with search statistics

The actual web_search call is made by the Agent; this script handles
the deterministic bookkeeping around it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (  # noqa: E402
    append_event,
    load_manifest,
    read_json,
    save_manifest,
    utc_now_iso,
    write_json,
)


def load_questions(path: Path) -> List[Dict[str, Any]]:
    data = read_json(path)
    if isinstance(data, dict) and "questions" in data:
        return list(data["questions"])
    if isinstance(data, list):
        return list(data)
    raise ValueError("invalid questions file")


def get_searched_question_ids(run_dir: Path) -> set:
    """Get set of question_ids that already have search results."""
    raw_path = run_dir / "raw" / "search_results.jsonl"
    if not raw_path.exists():
        return set()
    ids = set()
    with raw_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                qid = row.get("question_id", "")
                if qid:
                    ids.add(qid)
            except json.JSONDecodeError:
                continue
    return ids


def generate_search_queue(
    questions: Sequence[Dict[str, Any]],
    searched_ids: set,
    *,
    batch_size: int = 5,
    include_variants: bool = True,
) -> List[List[Dict[str, Any]]]:
    """Generate batches of questions to search, skipping already-searched ones.

    Each batch is a list of question objects to search.
    Variants are queued in separate batches from originals.
    """
    originals = []
    variants = []

    for q in questions:
        qid = q.get("id", "")
        if not qid or qid in searched_ids:
            continue
        originals.append(q)

        if include_variants and q.get("variant_group"):
            variant_id = f"{qid}-v"
            if variant_id not in searched_ids:
                variant_copy = dict(q)
                variant_copy["id"] = variant_id
                variant_copy["query_variant"] = "synonym"
                variants.append(variant_copy)

    # Build batches: originals first, then variants
    all_items = originals + variants
    batches = []
    for i in range(0, len(all_items), batch_size):
        batches.append(all_items[i : i + batch_size])

    return batches


def compute_batch_stats(run_dir: Path) -> Dict[str, Any]:
    """Compute search statistics from raw results."""
    raw_path = run_dir / "raw" / "search_results.jsonl"
    if not raw_path.exists():
        return {"total": 0, "successful": 0, "failed": 0, "with_brand_mention": 0, "with_citation": 0}

    total = 0
    successful = 0
    failed = 0
    with_brand = 0
    with_citation = 0

    with raw_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            total += 1
            if row.get("status") == "success":
                successful += 1
            elif row.get("status") == "failed":
                failed += 1
            signals = row.get("extracted_signals") or {}
            if signals.get("brand_mentioned"):
                with_brand += 1
            if signals.get("brand_cited") or signals.get("brand_domain_cited"):
                with_citation += 1

    return {
        "total": total,
        "successful": successful,
        "failed": failed,
        "success_rate": round(successful / total, 4) if total > 0 else 0.0,
        "with_brand_mention": with_brand,
        "with_brand_citation": with_citation,
        "mention_rate": round(with_brand / successful, 4) if successful > 0 else 0.0,
        "citation_rate": round(with_citation / successful, 4) if successful > 0 else 0.0,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Manage search batch execution for GEO audit"
    )
    parser.add_argument("--run-dir", required=True, help="Run directory path")
    parser.add_argument("--action", required=True, choices=["queue", "stats", "next-batch"],
                        help="Action to perform")
    parser.add_argument("--batch-size", type=int, default=5, help="Questions per batch")
    parser.add_argument("--no-variants", action="store_true", help="Skip variant generation")
    parser.add_argument("--output", default=None, help="Output file path")
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir)
    manifest = load_manifest(run_dir)

    if args.action == "queue":
        questions = load_questions(run_dir / "intermediate" / "questions.json")
        searched = get_searched_question_ids(run_dir)
        batches = generate_search_queue(
            questions, searched,
            batch_size=args.batch_size,
            include_variants=not args.no_variants,
        )
        result = {
            "total_questions": len(questions),
            "already_searched": len(searched),
            "remaining": sum(len(b) for b in batches),
            "batch_count": len(batches),
            "batches": [[q["id"] for q in batch] for batch in batches],
        }
        out_path = args.output or str(run_dir / "intermediate" / "search_queue.json")
        write_json(out_path, result)
        print(json.dumps(result, ensure_ascii=False))

    elif args.action == "stats":
        stats = compute_batch_stats(run_dir)
        out_path = args.output or str(run_dir / "intermediate" / "search_stats.json")
        write_json(out_path, stats)
        print(json.dumps(stats, ensure_ascii=False))

    elif args.action == "next-batch":
        questions = load_questions(run_dir / "intermediate" / "questions.json")
        searched = get_searched_question_ids(run_dir)
        batches = generate_search_queue(
            questions, searched,
            batch_size=args.batch_size,
            include_variants=not args.no_variants,
        )
        if batches:
            next_batch = batches[0]
            result = {
                "batch_number": manifest.get("current_batch", 0) + 1,
                "question_ids": [q["id"] for q in next_batch],
                "questions": [
                    {
                        "id": q["id"],
                        "text": q.get("normalized_text") or q.get("text", ""),
                        "intent": q.get("intent", ""),
                        "variant": q.get("query_variant", "original"),
                    }
                    for q in next_batch
                ],
            }
        else:
            result = {"batch_number": 0, "question_ids": [], "questions": [], "done": True}

        out_path = args.output or str(run_dir / "intermediate" / "next_batch.json")
        write_json(out_path, result)
        print(json.dumps(result, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())