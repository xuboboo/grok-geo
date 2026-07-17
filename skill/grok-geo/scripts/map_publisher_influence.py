#!/usr/bin/env python3
"""Map publisher influence from citation data.

Deterministic script: groups citations by domain, classifies publisher type,
computes influence scores, and outputs a sorted publisher list.

Usage:
    python map_publisher_influence.py \
        --citations <path> \
        --output <path>
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (
    PUBLISHER_CATEGORIES,
    PUBLISHER_DOMAIN_PATTERNS,
    read_json,
    write_json,
)


def classify_publisher_type(domain: str) -> str:
    """Classify a domain into one of the PUBLISHER_CATEGORIES."""
    domain = (domain or "").lower().strip()
    if domain.startswith("www."):
        domain = domain[4:]

    for category, patterns in PUBLISHER_DOMAIN_PATTERNS.items():
        for pattern in patterns:
            if pattern in domain:
                return category

    return "industry_media"


def compute_publisher_influence(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute per-publisher influence scores from citation list.

    Args:
        citations: List of dicts with 'domain', 'question_id', 'supports_target_brand'

    Returns:
        List of publisher dicts sorted by influence_score descending.
    """
    if not citations:
        return []

    domain_data: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "citation_count": 0,
        "question_ids": set(),
        "support_count": 0,
    })

    for cit in citations:
        domain = (cit.get("domain", "") or "").lower().strip()
        if not domain:
            continue
        domain_data[domain]["citation_count"] += 1
        qid = cit.get("question_id", "")
        if qid:
            domain_data[domain]["question_ids"].add(qid)
        if cit.get("supports_target_brand"):
            domain_data[domain]["support_count"] += 1

    publishers: List[Dict[str, Any]] = []
    for domain, data in domain_data.items():
        citation_count = data["citation_count"]
        support_ratio = data["support_count"] / citation_count if citation_count > 0 else 0.0
        influence_score = round(citation_count * support_ratio, 4)
        publisher_type = classify_publisher_type(domain)

        publishers.append({
            "domain": domain,
            "publisher_type": publisher_type,
            "citation_count": citation_count,
            "questions_cited_in": sorted(data["question_ids"]),
            "support_ratio": round(support_ratio, 4),
            "influence_score": influence_score,
        })

    publishers.sort(key=lambda p: p["influence_score"], reverse=True)
    return publishers


def main() -> None:
    parser = argparse.ArgumentParser(description="Map publisher influence from citations")
    parser.add_argument("--citations", required=True, help="Path to citations.json")
    parser.add_argument("--output", required=True, help="Output path for publisher_influence.json")
    args = parser.parse_args()

    citations = read_json(args.citations)
    if not isinstance(citations, list):
        print("Error: citations.json must be a list", file=sys.stderr)
        raise SystemExit(1)

    publishers = compute_publisher_influence(citations)
    write_json(args.output, {"publishers": publishers, "total": len(publishers)})
    print(f"✓ Publisher influence mapped: {len(publishers)} publishers")


if __name__ == "__main__":
    main()