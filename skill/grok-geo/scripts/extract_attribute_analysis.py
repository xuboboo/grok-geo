#!/usr/bin/env python3
"""Extract product attribute mentions from search result answer texts.

v1.7 — Detects 8 attribute categories with Chinese + English keyword matching.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set

# Allow import from scripts/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import ATTRIBUTE_CATEGORIES, ATTRIBUTE_KEYWORDS, read_json, read_jsonl, write_json


def detect_attributes(text: str) -> List[str]:
    """Detect which attribute categories are mentioned in text.

    Returns list of attribute category names detected.
    """
    if not text:
        return []

    detected: Set[str] = set()
    text_lower = text.lower()

    for category in ATTRIBUTE_CATEGORIES:
        keywords = ATTRIBUTE_KEYWORDS.get(category, [])
        for kw in keywords:
            if kw.lower() in text_lower:
                detected.add(category)
                break

    return sorted(detected)


def analyze_search_results(
    search_results: List[Dict[str, Any]],
    brand_name: str = "",
) -> Dict[str, Any]:
    """Analyze attribute mentions across all search results.

    Returns per-question and aggregate attribute analysis.
    """
    per_question: Dict[str, Any] = {}
    total_mentions: Counter = Counter()
    brand_total_mentions: Counter = Counter()
    total_results = 0

    for result in search_results:
        qid = result.get("question_id", result.get("qid", f"q_{total_results}"))
        answer_text = result.get("answer_text", result.get("text", ""))
        total_results += 1

        # Detect attributes in answer text
        attrs = detect_attributes(answer_text)
        per_question[qid] = {
            "attributes_detected": attrs,
        }

        for attr in attrs:
            total_mentions[attr] += 1

        # If brand is mentioned, track brand-specific attribute mentions
        if brand_name and brand_name.lower() in answer_text.lower():
            for attr in attrs:
                brand_total_mentions[attr] += 1

    # Compute aggregate with emphasis scores
    aggregate = {}
    for category in ATTRIBUTE_CATEGORIES:
        count = total_mentions.get(category, 0)
        # Emphasis score: normalized by total results, scaled to 0-100
        emphasis = min(100, round((count / max(total_results, 1)) * 100, 1)) if total_results > 0 else 0

        if emphasis >= 60:
            band = "primary_focus"
        elif emphasis >= 30:
            band = "secondary"
        elif emphasis >= 10:
            band = "marginal"
        else:
            band = "absent"

        aggregate[category] = {
            "count": count,
            "emphasis_score": emphasis,
            "band": band,
        }

    return {
        "total_results_analyzed": total_results,
        "per_question": per_question,
        "aggregate": aggregate,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract product attribute mentions from search results (v1.7)"
    )
    parser.add_argument(
        "--search-results", required=True, help="Path to search_results.jsonl"
    )
    parser.add_argument(
        "--brand", required=True, help="Path to brand.json"
    )
    parser.add_argument(
        "--output", required=True, help="Output path for attribute analysis JSON"
    )
    args = parser.parse_args()

    search_results = read_jsonl(args.search_results)
    brand_data = read_json(args.brand)
    brand_name = brand_data.get("brand_name", "") if isinstance(brand_data, dict) else ""

    result = analyze_search_results(search_results, brand_name)
    write_json(args.output, result)
    print(json.dumps({
        "total_results": result["total_results_analyzed"],
        "attributes_found": {
            k: v["count"] for k, v in result["aggregate"].items() if v["count"] > 0
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()