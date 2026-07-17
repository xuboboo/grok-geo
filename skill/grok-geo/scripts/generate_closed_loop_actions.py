#!/usr/bin/env python3
"""Closed-Loop Optimization — 闭环优化动作生成与追踪。

用法:
  python generate_closed_loop_actions.py --run-dir <RUN> --output <RUN>/output/closed_loop_actions.json
"""

from __future__ import annotations
import argparse, sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from geo_common import read_json, write_json, utc_now_iso, print_json

ACTION_TYPES = (
    "content_creation", "content_update", "technical_fix",
    "outreach_building", "misperception_correction", "schema_optimization", "faq_creation",
)

ACTION_EFFORT = {
    "content_creation": {"hours": 8, "deadline_days": 14, "validation": "re-query same questions"},
    "content_update": {"hours": 4, "deadline_days": 7, "validation": "re-query and verify facts"},
    "technical_fix": {"hours": 2, "deadline_days": 3, "validation": "re-run GEO Lint"},
    "outreach_building": {"hours": 6, "deadline_days": 30, "validation": "check citation source diversity"},
    "misperception_correction": {"hours": 3, "deadline_days": 7, "validation": "re-query and verify accuracy"},
    "schema_optimization": {"hours": 3, "deadline_days": 3, "validation": "re-run GEO Lint schema dimension"},
    "faq_creation": {"hours": 4, "deadline_days": 14, "validation": "re-query FAQ-type questions"},
}


def detect_gaps(run_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Detect gaps from run data."""
    gaps: Dict[str, List[Dict[str, Any]]] = {
        "citation_gaps": [],
        "competitor_advantages": [],
        "entity_missing": [],
        "funnel_breakpoints": [],
        "misperceptions": [],
        "technical_issues": [],
    }

    # From metrics
    metrics_path = run_dir / "intermediate" / "metrics.json"
    if metrics_path.exists():
        metrics = read_json(metrics_path)

        # Low citation rate → citation gap
        geo = metrics.get("geo_score", {})
        breakdown = geo.get("breakdown", {})
        if breakdown.get("owned_citation_rate", 0) < 0.3:
            gaps["citation_gaps"].append({
                "issue": "owned_citation_rate_low",
                "value": breakdown.get("owned_citation_rate", 0),
                "threshold": 0.3,
            })

        # Competitor advantages
        comp_share = metrics.get("citation_share_by_competitor", {})
        for comp, data in comp_share.items():
            if isinstance(data, dict) and data.get("share", 0) > 0.4:
                gaps["competitor_advantages"].append({
                    "competitor": comp,
                    "share": data.get("share", 0),
                })

    # From GEO Lint
    lint_path = run_dir / "output" / "geo_lint_report.json"
    if lint_path.exists():
        lint = read_json(lint_path)
        for issue in lint.get("issues", []):
            if issue.get("severity") == "ERROR":
                gaps["technical_issues"].append({
                    "rule_id": issue["rule_id"],
                    "message": issue["message"],
                    "fix": issue.get("fix_suggestion", ""),
                })

    # From entity analysis
    entity_path = run_dir / "intermediate" / "entity_analysis.jsonl"
    if entity_path.exists():
        from geo_common import read_jsonl
        entities = read_jsonl(entity_path)
        for e in entities:
            for entity in e.get("entities", []):
                if entity.get("brand_mentioned") and entity.get("misperception"):
                    gaps["misperceptions"].append({
                        "question_id": e.get("question_id", ""),
                        "misperception": entity.get("misperception", ""),
                    })

    return gaps


def generate_actions(gaps: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Generate prioritized actions from detected gaps."""
    actions: List[Dict[str, Any]] = []
    act_id = 0

    # Technical issues → P0 technical_fix
    for issue in gaps.get("technical_issues", [])[:5]:
        act_id += 1
        effort = ACTION_EFFORT["technical_fix"]
        actions.append({
            "id": f"act_{act_id:03d}",
            "type": "technical_fix",
            "priority": "P0",
            "title": f"Fix: {issue['rule_id']}",
            "description": issue["message"],
            "fix_suggestion": issue.get("fix", ""),
            "effort_hours": effort["hours"],
            "deadline_days": effort["deadline_days"],
            "validation_method": effort["validation"],
            "status": "pending",
        })

    # Misperceptions → P0 misperception_correction
    for mis in gaps.get("misperceptions", [])[:3]:
        act_id += 1
        effort = ACTION_EFFORT["misperception_correction"]
        actions.append({
            "id": f"act_{act_id:03d}",
            "type": "misperception_correction",
            "priority": "P0",
            "title": "Correct AI misperception",
            "description": mis.get("misperception", ""),
            "target_question": mis.get("question_id", ""),
            "effort_hours": effort["hours"],
            "deadline_days": effort["deadline_days"],
            "validation_method": effort["validation"],
            "status": "pending",
        })

    # Citation gaps → P1 content_creation + outreach
    for gap in gaps.get("citation_gaps", [])[:2]:
        act_id += 1
        effort = ACTION_EFFORT["content_creation"]
        actions.append({
            "id": f"act_{act_id:03d}",
            "type": "content_creation",
            "priority": "P1",
            "title": "Create citable content for AI engines",
            "description": f"Citation rate ({gap['value']:.0%}) below threshold ({gap['threshold']:.0%})",
            "effort_hours": effort["hours"],
            "deadline_days": effort["deadline_days"],
            "validation_method": effort["validation"],
            "status": "pending",
        })

    # Competitor advantages → P1 outreach
    for comp in gaps.get("competitor_advantages", [])[:3]:
        act_id += 1
        effort = ACTION_EFFORT["outreach_building"]
        actions.append({
            "id": f"act_{act_id:03d}",
            "type": "outreach_building",
            "priority": "P1",
            "title": f"Build citations to counter {comp['competitor']}",
            "description": f"Competitor has {comp['share']:.0%} citation share",
            "effort_hours": effort["hours"],
            "deadline_days": effort["deadline_days"],
            "validation_method": effort["validation"],
            "status": "pending",
        })

    # Schema optimization from lint
    for gap in gaps.get("technical_issues", []):
        if gap["rule_id"].startswith("SCHEMA-"):
            act_id += 1
            effort = ACTION_EFFORT["schema_optimization"]
            actions.append({
                "id": f"act_{act_id:03d}",
                "type": "schema_optimization",
                "priority": "P2",
                "title": f"Optimize: {gap['rule_id']}",
                "description": gap["message"],
                "effort_hours": effort["hours"],
                "deadline_days": effort["deadline_days"],
                "validation_method": effort["validation"],
                "status": "pending",
            })
            break  # One schema action is enough

    return actions


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--run-dir", required=True)
    p.add_argument("--output")
    args = p.parse_args()

    run_dir = Path(args.run_dir)
    gaps = detect_gaps(run_dir)
    actions = generate_actions(gaps)

    report = {
        "schema_version": "2.3.0",
        "generated_at": utc_now_iso(),
        "gap_analysis": gaps,
        "action_plan": actions,
        "summary": {
            "total_actions": len(actions),
            "p0_count": sum(1 for a in actions if a["priority"] == "P0"),
            "p1_count": sum(1 for a in actions if a["priority"] == "P1"),
            "p2_count": sum(1 for a in actions if a["priority"] == "P2"),
            "total_effort_hours": sum(a.get("effort_hours", 0) for a in actions),
        },
    }

    output_path = args.output or str(run_dir / "output" / "closed_loop_actions.json")
    write_json(output_path, report)
    print(f"Generated {len(actions)} actions ({report['summary']['p0_count']} P0, {report['summary']['p1_count']} P1, {report['summary']['p2_count']} P2)")
    print(f"Total effort: {report['summary']['total_effort_hours']} hours")

if __name__ == "__main__":
    main()