#!/usr/bin/env python3
"""Detect semantic drift between baseline and current search snapshots.

Compares snapshots across runs to detect position, citation, sentiment,
recommendation, competitor, and source drifts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import clamp, read_json, read_jsonl, write_json  # noqa: E402


# Drift deduction caps
POSITION_DRIFT_PER_STEP = 8
POSITION_DRIFT_MAX = 40
CITATION_LOST = 15
COMPETITOR_NEW_CITATION = 10
SENTIMENT_PER_POINT = 0.5
SENTIMENT_DRIFT_MAX = 25
RECOMMENDATION_DOWNGRADE = 20
COMPETITOR_NEW = 10
COMPETITOR_OVERTOOK = 15


def detect_single_drift(
    baseline: Dict[str, Any],
    current: Dict[str, Any],
) -> Dict[str, Any]:
    """Detect drift between baseline and current snapshot for one question."""

    b_brand = baseline.get("brand_snapshot") or {}
    c_brand = current.get("brand_snapshot") or {}
    b_comp = baseline.get("competitor_snapshots") or {}
    c_comp = current.get("competitor_snapshots") or {}

    drifts = []
    total_deduction = 0

    # ── Position Drift ──
    b_pos = b_brand.get("position")
    c_pos = c_brand.get("position")
    if b_pos is not None and c_pos is not None:
        delta = c_pos - b_pos
        if abs(delta) >= 2:
            deduction = min(abs(delta) * POSITION_DRIFT_PER_STEP, POSITION_DRIFT_MAX)
            severity = "positive" if delta < 0 else ("critical" if delta >= 4 else "warning")
            total_deduction += deduction if delta > 0 else 0
            drifts.append({
                "type": "position",
                "severity": severity,
                "baseline": {"position": b_pos},
                "current": {"position": c_pos},
                "delta": delta,
                "evidence": f"品牌从第{b_pos}位{'提升' if delta < 0 else '下降'}到第{c_pos}位",
            })
    elif b_pos is not None and c_pos is None:
        total_deduction += POSITION_DRIFT_MAX
        drifts.append({
            "type": "position",
            "severity": "critical",
            "baseline": {"position": b_pos},
            "current": {"position": None},
            "evidence": "品牌从回答中消失",
        })
    elif b_pos is None and c_pos is not None:
        drifts.append({
            "type": "position",
            "severity": "positive",
            "baseline": {"position": None},
            "current": {"position": c_pos},
            "evidence": f"品牌新出现在第{c_pos}位",
        })

    # ── Citation Drift ──
    b_cited = b_brand.get("cited", False)
    c_cited = c_brand.get("cited", False)
    if b_cited and not c_cited:
        total_deduction += CITATION_LOST
        drifts.append({
            "type": "citation",
            "severity": "warning",
            "baseline": {"cited": True},
            "current": {"cited": False},
            "evidence": "品牌引用消失",
        })
    elif not b_cited and c_cited:
        drifts.append({
            "type": "citation",
            "severity": "positive",
            "baseline": {"cited": False},
            "current": {"cited": True},
            "evidence": "品牌新增引用",
        })

    # ── Sentiment Drift ──
    b_sent = b_brand.get("sentiment_score")
    c_sent = c_brand.get("sentiment_score")
    if b_sent is not None and c_sent is not None:
        delta_sent = c_sent - b_sent
        if abs(delta_sent) >= 15:
            deduction = min(abs(delta_sent) * SENTIMENT_PER_POINT, SENTIMENT_DRIFT_MAX)
            severity = "positive" if delta_sent > 0 else ("critical" if delta_sent <= -30 else "warning")
            total_deduction += deduction if delta_sent < 0 else 0
            drifts.append({
                "type": "sentiment",
                "severity": severity,
                "baseline": {"sentiment_score": b_sent},
                "current": {"sentiment_score": c_sent},
                "delta": delta_sent,
                "evidence": f"情感分从{b_sent}{'提升' if delta_sent > 0 else '下降'}到{c_sent}",
            })

    # ── Recommendation Drift ──
    REC_ORDER = {"discouraged": 0, "mentioned_only": 1, "conditional": 2, "strong_alternative": 3, "top_pick": 4}
    b_rec = baseline.get("brand_snapshot", {}).get("recommendation_type")
    c_rec = current.get("brand_snapshot", {}).get("recommendation_type")
    if b_rec and c_rec and b_rec != c_rec:
        b_val = REC_ORDER.get(b_rec, 1)
        c_val = REC_ORDER.get(c_rec, 1)
        if c_val < b_val:
            total_deduction += RECOMMENDATION_DOWNGRADE
            drifts.append({
                "type": "recommendation",
                "severity": "critical" if c_val == 0 else "warning",
                "baseline": {"recommendation_type": b_rec},
                "current": {"recommendation_type": c_rec},
                "evidence": f"推荐类型从 {b_rec} 降级为 {c_rec}",
            })
        elif c_val > b_val:
            drifts.append({
                "type": "recommendation",
                "severity": "positive",
                "baseline": {"recommendation_type": b_rec},
                "current": {"recommendation_type": c_rec},
                "evidence": f"推荐类型从 {b_rec} 升级为 {c_rec}",
            })

    # ── Competitor Drift ──
    new_comps = set(c_comp.keys()) - set(b_comp.keys())
    lost_comps = set(b_comp.keys()) - set(c_comp.keys())
    if new_comps:
        total_deduction += len(new_comps) * COMPETITOR_NEW
        drifts.append({
            "type": "competitor",
            "severity": "warning",
            "evidence": f"新竞品出现: {', '.join(new_comps)}",
        })
    if lost_comps:
        drifts.append({
            "type": "competitor",
            "severity": "positive",
            "evidence": f"竞品消失: {', '.join(lost_comps)}",
        })

    drift_score = clamp(100.0 - total_deduction, 0.0, 100.0)

    if drift_score >= 86:
        band = "stable"
    elif drift_score >= 68:
        band = "minor_drift"
    elif drift_score >= 36:
        band = "significant_drift"
    else:
        band = "major_drift"

    return {
        "question_id": baseline.get("question_id", current.get("question_id", "")),
        "drift_score": round(drift_score, 1),
        "drift_band": band,
        "drift_count": len(drifts),
        "critical_count": sum(1 for d in drifts if d.get("severity") == "critical"),
        "positive_count": sum(1 for d in drifts if d.get("severity") == "positive"),
        "drifts": drifts,
    }


def detect_run_drift(
    baseline_snapshots: Sequence[Dict[str, Any]],
    current_snapshots: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """Detect drift across all questions between two runs."""
    baseline_by_q = {s["question_id"]: s for s in baseline_snapshots if "question_id" in s}
    current_by_q = {s["question_id"]: s for s in current_snapshots if "question_id" in s}

    results = []
    for qid in sorted(set(baseline_by_q.keys()) | set(current_by_q.keys())):
        b = baseline_by_q.get(qid)
        c = current_by_q.get(qid)
        if b and c:
            results.append(detect_single_drift(b, c))

    if not results:
        return {"overall_drift_score": None, "questions_analyzed": 0}

    # Overall score: weighted average
    total_score = sum(r["drift_score"] for r in results)
    overall = round(total_score / len(results), 1)

    if overall >= 86:
        band = "stable"
    elif overall >= 68:
        band = "minor_drift"
    elif overall >= 36:
        band = "significant_drift"
    else:
        band = "major_drift"

    critical_drifts = [r for r in results if r["critical_count"] > 0]
    positive_drifts = [r for r in results if r["positive_count"] > 0]

    return {
        "overall_drift_score": overall,
        "drift_band": band,
        "questions_analyzed": len(results),
        "questions_with_drift": sum(1 for r in results if r["drift_count"] > 0),
        "critical_drifts": [r for r in critical_drifts],
        "positive_drifts": [r for r in positive_drifts],
        "per_question": results,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect semantic drift between baseline and current snapshots"
    )
    parser.add_argument("--baseline", required=True, help="Path to baseline snapshots JSON/JSONL")
    parser.add_argument("--current", required=True, help="Path to current snapshots JSON/JSONL")
    parser.add_argument("--output", default=None, help="Output file path")
    args = parser.parse_args(argv)

    baseline_path = Path(args.baseline)
    current_path = Path(args.current)

    if baseline_path.suffix == ".jsonl":
        baseline = read_jsonl(baseline_path)
    else:
        data = read_json(baseline_path)
        baseline = data if isinstance(data, list) else data.get("snapshots", [])

    if current_path.suffix == ".jsonl":
        current = read_jsonl(current_path)
    else:
        data = read_json(current_path)
        current = data if isinstance(data, list) else data.get("snapshots", [])

    result = detect_run_drift(baseline, current)

    if args.output:
        write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())