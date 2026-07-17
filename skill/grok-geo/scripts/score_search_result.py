#!/usr/bin/env python3
"""Score a single search result's quality and decide retry strategy.

Deterministic scoring of search result quality. Retry strategy
recommendation is also deterministic based on result characteristics.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import read_json, write_json, clamp  # noqa: E402


# Quality thresholds
MIN_RESPONSE_LENGTH = 50
MIN_CITATION_COUNT = 0
HIGH_VALUE_MENTION_THRESHOLD = 0.7

# Retry strategies
RETRY_STRATEGIES = {
    "A": "reinforce_prompt",
    "B": "rewrite_query",
    "C": "delay_retry",
    "D": "simplify_request",
    "E": "specify_sources",
    "F": "change_angle",
    "G": "add_context",
}

# Hard failure error codes (no retry)
HARD_FAILURES = frozenset({
    "WEB_SEARCH_UNAVAILABLE",
    "REFUSED",
    "TOOL_TIMEOUT",
})

# Soft failure error codes (retry with strategy)
SOFT_FAILURES = {
    "WEB_SEARCH_NOT_USED": "A",
    "EMPTY_ANSWER": "B",
    "RATE_LIMITED": "C",
    "INVALID_TOOL_OUTPUT": "D",
}


def score_response_quality(result: Dict[str, Any]) -> Dict[str, Any]:
    """Score the quality of a search result (0-100)."""
    answer_text = result.get("answer_text", "")
    citations = result.get("citations") or []
    sources = result.get("sources") or []
    signals = result.get("extracted_signals") or {}
    quality = signals.get("response_quality") or {}

    score = 100.0
    issues = []

    # Response length check
    resp_len = len(answer_text)
    if resp_len < MIN_RESPONSE_LENGTH:
        deduction = min(30, (MIN_RESPONSE_LENGTH - resp_len) * 0.6)
        score -= deduction
        issues.append({"type": "short_response", "severity": "high", "detail": f"Response length {resp_len} < {MIN_RESPONSE_LENGTH}"})

    # Citation count check
    cit_count = len(citations) + len(sources)
    if cit_count == 0:
        score -= 25
        issues.append({"type": "no_citations", "severity": "high", "detail": "No citations or sources"})

    # Refusal check
    if quality.get("is_refusal"):
        score -= 40
        issues.append({"type": "refusal", "severity": "critical", "detail": "Response is a refusal"})

    # Factual specificity
    specificity = quality.get("factual_specificity", "medium")
    if specificity == "low":
        score -= 10
        issues.append({"type": "low_specificity", "severity": "medium", "detail": "Low factual specificity"})

    # List/table structure (positive signal)
    platform = signals.get("platform_hints") or {}
    if platform.get("has_list_structure"):
        score += 5
    if platform.get("has_table_structure"):
        score += 5

    # Inline citations (positive signal)
    if platform.get("has_inline_citations"):
        score += 5

    score = clamp(round(score, 1), 0.0, 100.0)

    if score >= 80:
        band = "high_quality"
    elif score >= 60:
        band = "acceptable"
    elif score >= 40:
        band = "low_quality"
    else:
        band = "poor"

    return {
        "quality_score": score,
        "quality_band": band,
        "response_length": resp_len,
        "citation_count": cit_count,
        "issues": issues,
        "issue_count": len(issues),
    }


def recommend_retry_strategy(
    result: Dict[str, Any],
    quality: Dict[str, Any],
    question_business_value: int = 50,
) -> Optional[Dict[str, Any]]:
    """Recommend a retry strategy based on result quality and error type.

    Returns None if no retry recommended.
    """
    status = result.get("status", "success")
    error = result.get("error")

    # Hard failures: no retry
    if error in HARD_FAILURES:
        return None

    # Already retried: no retry
    if result.get("retry"):
        return None

    # Soft failures: use mapped strategy
    if error in SOFT_FAILURES:
        strategy = SOFT_FAILURES[error]
        return {
            "strategy": strategy,
            "strategy_name": RETRY_STRATEGIES[strategy],
            "reason": f"Soft failure: {error}",
            "priority": "high",
        }

    # Low quality results
    q_score = quality.get("quality_score", 100)
    issues = quality.get("issues", [])

    if q_score < 40 and question_business_value >= 70:
        # High-value question with poor quality: try rewrite
        return {
            "strategy": "B",
            "strategy_name": "rewrite_query",
            "reason": f"Poor quality ({q_score}) on high-value question",
            "priority": "high",
        }

    if q_score < 60:
        # Check specific issues
        issue_types = {i["type"] for i in issues}

        if "no_citations" in issue_types:
            return {
                "strategy": "E",
                "strategy_name": "specify_sources",
                "reason": "No citations in response",
                "priority": "medium",
            }

        if "refusal" in issue_types:
            return {
                "strategy": "F",
                "strategy_name": "change_angle",
                "reason": "Response is a refusal",
                "priority": "medium",
            }

        if "short_response" in issue_types:
            return {
                "strategy": "B",
                "strategy_name": "rewrite_query",
                "reason": "Response too short",
                "priority": "medium",
            }

    # Brand not mentioned in high-value question
    signals = result.get("extracted_signals") or {}
    if not signals.get("brand_mentioned") and question_business_value >= 80:
        return {
            "strategy": "G",
            "strategy_name": "add_context",
            "reason": "Brand not mentioned in high-value question",
            "priority": "low",
        }

    return None


def create_snapshot(result: Dict[str, Any], brand_name: str) -> Dict[str, Any]:
    """Create an archival snapshot from a search result."""
    import hashlib

    answer_text = result.get("answer_text", "")
    answer_hash = hashlib.sha256(answer_text.encode("utf-8")).hexdigest()[:16]

    signals = result.get("extracted_signals") or {}

    return {
        "snapshot_id": f"snap_{result.get('executed_at', '').replace(':', '').replace('-', '')[:15]}_{result.get('question_id', 'unknown')}",
        "question_id": result.get("question_id", ""),
        "query_text": result.get("query_text", ""),
        "query_variant": result.get("query_variant", "original"),
        "captured_at": result.get("executed_at", ""),
        "answer_hash": f"sha256:{answer_hash}",
        "answer_length": len(answer_text),
        "citation_count": len(result.get("citations") or []),
        "brand_snapshot": {
            "mentioned": signals.get("brand_mentioned", False),
            "cited": signals.get("brand_cited", False),
            "domain_cited": signals.get("brand_domain_cited", False),
            "position": signals.get("brand_position_in_answer"),
            "in_heading": signals.get("brand_in_heading", False),
        },
        "competitor_snapshots": {
            comp: {"mentioned": True}
            for comp in (signals.get("competitor_mentioned") or [])
        },
        "quality_snapshot": {
            "factual_specificity": (signals.get("response_quality") or {}).get("factual_specificity", "unknown"),
            "citation_density": (signals.get("response_quality") or {}).get("citation_density", 0),
        },
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Score search result quality and recommend retry strategy"
    )
    parser.add_argument("--search-result", required=True, help="Path to search result JSON")
    parser.add_argument("--brand-name", default="", help="Brand name for snapshot")
    parser.add_argument("--business-value", type=int, default=50, help="Question business value (0-100)")
    parser.add_argument("--output", default=None, help="Output file path")
    parser.add_argument("--snapshot-output", default=None, help="Snapshot output path")
    args = parser.parse_args(argv)

    result = read_json(args.search_result)

    # Score quality
    quality = score_response_quality(result)

    # Recommend retry
    retry = recommend_retry_strategy(result, quality, args.business_value)

    # Create snapshot
    snapshot = create_snapshot(result, args.brand_name)

    output = {
        "quality": quality,
        "retry_recommendation": retry,
        "snapshot": snapshot,
    }

    text = json.dumps(output, ensure_ascii=False, indent=2)
    if args.output:
        write_json(args.output, output)
    print(text)

    if args.snapshot_output:
        write_json(args.snapshot_output, snapshot)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())