#!/usr/bin/env python3
"""Generate a prioritised improvement plan from drift analysis, opportunities, and metrics.

Usage:
    python generate_improvement_plan.py \
        --drift <path> --opportunities <path> --metrics <path> --output <path>

Produces improvement_plan.json with prioritised actions.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from geo_common import (  # noqa: E402
    IMPROVEMENT_ACTION_TYPES,
    RETEST_INTERVALS,
    SKILL_NAME,
    SKILL_VERSION,
    read_json,
    utc_now_iso,
    write_json,
)

# ─── Action type mapping ────────────────────────────────────────────────────

# Maps drift types → suggested action type
_DRIFT_ACTION_MAP: dict[str, str] = {
    "recommendation": "create_content",
    "position": "update_content",
    "sentiment": "fix_misperception",
    "citation": "build_backlinks",
    "source": "build_backlinks",
    "competitor": "expand_coverage",
}

# Maps opportunity_type → suggested action type
_OPPORTUNITY_ACTION_MAP: dict[str, str] = {
    "missing_recommendation_content": "create_content",
    "outdated_content": "update_content",
    "misperception": "fix_misperception",
    "weak_backlink_profile": "build_backlinks",
    "technical_gap": "fix_technical",
    "platform_gap": "expand_coverage",
    "competitor_gap": "expand_coverage",
    "content_gap": "create_content",
    "citation_gap": "build_backlinks",
}

# Default deadline by action type
_DEADLINE_DAYS: dict[str, int] = dict(RETEST_INTERVALS)

# Validation methods by action type
_VALIDATION_METHODS: dict[str, str] = {
    "create_content": "Re-run search for target questions; verify brand mention and recommendation improve",
    "update_content": "Re-run search for target questions; verify content freshness signals and accuracy",
    "fix_misperception": "Re-run search for target questions; verify misperception is corrected in AI answers",
    "build_backlinks": "Re-run search after 30 days; verify citation count and source quality improve",
    "fix_technical": "Re-run site readiness check; verify technical score improves",
    "expand_coverage": "Re-run search for expanded question set; verify cross-platform mention improves",
}


# ─── Priority calculation ───────────────────────────────────────────────────


def _drift_priority(question_id: str, drift_entry: dict, metrics: dict) -> int:
    """Assign priority 1-5 for a drift-based action."""
    severity = drift_entry.get("severity", "warning")
    # Check if question has high business value (heuristic: geo_score < 60 → high need)
    geo = 0.0
    gs = metrics.get("geo_score")
    if isinstance(gs, dict):
        geo = float(gs.get("score", 0))
    elif isinstance(gs, (int, float)):
        geo = float(gs)

    if severity == "critical" and geo < 60:
        return 1
    if severity == "critical":
        return 2
    if severity == "warning" and geo < 70:
        return 3
    return 4


def _opportunity_priority(opp: dict) -> int:
    """Assign priority 1-5 for an opportunity-based action."""
    total = 0.0
    scores = opp.get("scores", {})
    if isinstance(scores, dict):
        total = float(scores.get("total", 0))

    if total >= 80:
        return 2
    if total >= 60:
        return 3
    if total >= 40:
        return 4
    return 5


# ─── Public API (imported by tests) ────────────────────────────────────────


def generate_plan(drift: dict, opportunities: list, metrics: dict) -> dict:
    """Generate an improvement plan from drift analysis, opportunities, and metrics.

    Parameters
    ----------
    drift : dict
        Drift analysis output with ``critical_drifts`` and ``positive_drifts``.
    opportunities : list
        List of opportunity dicts with ``id``, ``title``, ``target_question_ids``,
        ``opportunity_type``, and ``scores``.
    metrics : dict
        Current run metrics.

    Returns
    -------
    dict
        Improvement plan with ``actions`` list and metadata.
    """
    actions: list[dict] = []

    # 1. Generate actions from critical drifts
    for drift_group in drift.get("critical_drifts", []):
        qid = drift_group.get("question_id", "")
        for d in drift_group.get("drifts", []):
            drift_type = d.get("type", "")
            action_type = _DRIFT_ACTION_MAP.get(drift_type, "update_content")
            priority = _drift_priority(qid, d, metrics)

            actions.append({
                "priority": priority,
                "action_type": action_type,
                "target_question_ids": [qid],
                "description": f"Address {d.get('severity', 'critical')} {drift_type} drift on question {qid}",
                "expected_impact": f"Reverse {drift_type} drift; restore brand visibility for {qid}",
                "validation_method": _VALIDATION_METHODS.get(action_type, "Re-run audit and compare"),
                "deadline_days": _DEADLINE_DAYS.get(action_type, 14),
            })

    # 2. Generate actions from opportunities
    for opp in opportunities:
        opp_type = opp.get("opportunity_type", "content_gap")
        action_type = _OPPORTUNITY_ACTION_MAP.get(opp_type, "create_content")
        priority = _opportunity_priority(opp)
        target_qids = opp.get("target_question_ids", [])

        actions.append({
            "priority": priority,
            "action_type": action_type,
            "target_question_ids": target_qids,
            "description": opp.get("title", f"Execute opportunity: {opp_type}"),
            "expected_impact": f"Improve coverage for questions: {', '.join(target_qids[:5])}",
            "validation_method": _VALIDATION_METHODS.get(action_type, "Re-run audit and compare"),
            "deadline_days": _DEADLINE_DAYS.get(action_type, 14),
        })

    # 3. Sort by priority (lower = higher priority), then by type
    actions.sort(key=lambda a: (a["priority"], a["action_type"]))

    plan = {
        "schema_version": "1.0",
        "skill_name": SKILL_NAME,
        "skill_version": SKILL_VERSION,
        "generated_at": utc_now_iso(),
        "total_actions": len(actions),
        "actions": actions,
    }

    return plan


# ─── CLI ────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate improvement plan from drift analysis and opportunities."
    )
    parser.add_argument("--drift", required=True, help="Path to drift_analysis.json")
    parser.add_argument("--opportunities", required=True, help="Path to opportunities.json")
    parser.add_argument("--metrics", required=True, help="Path to metrics.json")
    parser.add_argument("--output", required=True, help="Output path for improvement_plan.json")
    args = parser.parse_args()

    drift_path = Path(args.drift)
    opps_path = Path(args.opportunities)
    metrics_path = Path(args.metrics)
    output_path = Path(args.output)

    # Load inputs (drift may not exist for first run)
    drift: dict = {}
    if drift_path.exists():
        drift = read_json(drift_path)

    opportunities: list = []
    if opps_path.exists():
        raw = read_json(opps_path)
        if isinstance(raw, list):
            opportunities = raw
        elif isinstance(raw, dict):
            opportunities = raw.get("opportunities", [])

    metrics: dict = {}
    if metrics_path.exists():
        metrics = read_json(metrics_path)

    plan = generate_plan(drift, opportunities, metrics)
    write_json(output_path, plan)
    print(f"Improvement plan written to {output_path} ({plan['total_actions']} actions)")


if __name__ == "__main__":
    main()