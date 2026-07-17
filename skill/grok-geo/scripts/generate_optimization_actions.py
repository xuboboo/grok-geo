#!/usr/bin/env python3
"""Generate prioritized optimization actions from audit findings.

Deterministic script: generates actions from opportunities, drift analysis,
and metrics, deduplicates them, scores by impact×urgency×feasibility,
and outputs max 15 actions.

Usage:
    python generate_optimization_actions.py \
        --opportunities <path> \
        --metrics <path> \
        [--drift <path>] \
        [--attributes <path>] \
        --output <path>
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (
    OPTIMIZATION_ACTION_CATEGORIES,
    read_json,
    write_json,
)

MAX_ACTIONS = 15

_OPPORTUNITY_TYPE_TO_CATEGORY = {
    "missing_recommendation_content": "content_creation",
    "competitor_comparison_gap": "content_creation",
    "geographic_gap": "content_creation",
    "content_quality_gap": "content_update",
    "technical_seo_gap": "technical_fix",
    "citation_gap": "backlink_building",
}

_ATTRIBUTE_TO_CATEGORY = {
    "pricing": "content_update",
    "core_features": "content_creation",
    "ease_of_use": "faq_creation",
    "support": "content_creation",
    "integrations": "content_creation",
    "security": "content_creation",
    "scalability": "content_creation",
    "performance": "content_creation",
}


def _generate_id(seed: str) -> str:
    """Generate a short deterministic action ID."""
    h = hashlib.sha256(seed.encode()).hexdigest()[:8]
    return f"act-{h}"


def score_action(action: Dict[str, Any]) -> float:
    """Compute priority_score = impact × urgency × feasibility, normalized to 0-100.

    Each factor should be 0-100.
    """
    impact = action.get("impact", 50)
    urgency = action.get("urgency", 50)
    feasibility = action.get("feasibility", 50)
    raw = impact * urgency * feasibility
    # Normalize: max possible = 100*100*100 = 1_000_000 → scale to 100
    return round(min(raw / 1_000_000 * 100, 100.0), 2)


def generate_actions(
    opportunities: Optional[List[Dict[str, Any]]] = None,
    drift: Optional[Dict[str, Any]] = None,
    metrics: Optional[Dict[str, Any]] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Generate prioritized optimization actions from all findings.

    Returns list of action dicts sorted by priority_score descending, max 15.
    """
    opportunities = opportunities or []
    raw_actions: List[Dict[str, Any]] = []

    # From opportunities
    for opp in opportunities:
        opp_type = opp.get("opportunity_type", "")
        category = _OPPORTUNITY_TYPE_TO_CATEGORY.get(opp_type, "content_creation")
        opp_score = opp.get("scores", {}).get("total", 50)

        action_id = _generate_id(f"opp:{opp.get('id', '')}:{category}")
        raw_actions.append({
            "title": f"Address: {opp.get('title', opp_type)}",
            "description": f"Opportunity gap with score {opp_score}",
            "category": category,
            "target_questions": opp.get("target_question_ids", []),
            "expected_impact": opp_score,
            "effort_estimate": "medium",
            "validation_method": "Re-run audit after 14 days",
            "deadline_days": 14,
            "impact": min(opp_score, 100),
            "urgency": 60,
            "feasibility": 70,
        })

    # From drift analysis
    if drift:
        for cd in drift.get("critical_drifts", []):
            for d in cd.get("drifts", []):
                severity = d.get("severity", "warning")
                impact = 90 if severity == "critical" else 70
                urgency = 90 if severity == "critical" else 60

                raw_actions.append({
                    "title": f"Fix {d.get('type', 'unknown')} drift",
                    "description": f"Drift severity: {severity}",
                    "category": "content_update",
                    "target_questions": [cd.get("question_id", "")],
                    "expected_impact": impact,
                    "effort_estimate": "medium",
                    "validation_method": "Re-run audit after 7 days",
                    "deadline_days": 7 if severity == "critical" else 14,
                    "impact": impact,
                    "urgency": urgency,
                    "feasibility": 60,
                })

    # From attribute gaps
    if attributes:
        for gap in attributes.get("attribute_gaps", []):
            category_attr = gap.get("category", "")
            category = _ATTRIBUTE_TO_CATEGORY.get(category_attr, "content_creation")

            raw_actions.append({
                "title": f"Fill {category_attr} attribute gap",
                "description": f"AI answers lack {category_attr} coverage",
                "category": category,
                "target_questions": gap.get("question_ids", []),
                "expected_impact": gap.get("gap_score", 50),
                "effort_estimate": "medium",
                "validation_method": "Re-run audit after 14 days",
                "deadline_days": 14,
                "impact": 100 - gap.get("gap_score", 50),
                "urgency": 50,
                "feasibility": 70,
            })

    # Score all actions
    for action in raw_actions:
        action["priority_score"] = score_action(action)

    # Deduplicate
    deduplicated = _deduplicate_actions(raw_actions)

    # Sort by priority_score descending, cap at MAX_ACTIONS
    deduplicated.sort(key=lambda a: a["priority_score"], reverse=True)
    return deduplicated[:MAX_ACTIONS]


def _deduplicate_actions(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge actions with same category and overlapping target questions."""
    groups: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for action in actions:
        key = (action["category"], tuple(sorted(action.get("target_questions", []))))
        groups[key].append(action)

    result: List[Dict[str, Any]] = []
    for group in groups.values():
        if len(group) == 1:
            result.append(group[0])
        else:
            merged = max(group, key=lambda a: a.get("priority_score", 0))
            all_qs: set = set()
            for a in group:
                all_qs.update(a.get("target_questions", []))
            merged["target_questions"] = sorted(all_qs)
            merged["priority_score"] = max(a.get("priority_score", 0) for a in group)
            result.append(merged)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate optimization actions")
    parser.add_argument("--opportunities", required=True, help="Path to opportunities.json")
    parser.add_argument("--metrics", required=True, help="Path to metrics.json")
    parser.add_argument("--drift", default=None, help="Path to drift_analysis.json")
    parser.add_argument("--attributes", default=None, help="Path to attribute_analysis.json")
    parser.add_argument("--output", required=True, help="Output path")
    args = parser.parse_args()

    opps = read_json(args.opportunities)
    if isinstance(opps, dict):
        opps = opps.get("opportunities", opps.get("items", []))

    metrics = read_json(args.metrics)
    drift = read_json(args.drift) if args.drift else None
    attributes = read_json(args.attributes) if args.attributes else None

    actions = generate_actions(opportunities=opps, drift=drift, metrics=metrics, attributes=attributes)

    output = {
        "total_actions": len(actions),
        "actions": actions,
    }

    write_json(args.output, output)
    print(f"✓ Generated {len(actions)} optimization actions")


if __name__ == "__main__":
    main()