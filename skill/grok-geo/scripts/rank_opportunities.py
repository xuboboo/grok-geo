#!/usr/bin/env python3
"""Rank content opportunities (§14). Max 10."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import print_json, read_json, write_json  # noqa: E402


def score_opportunity(scores: Dict[str, Any]) -> float:
    bv = float(scores.get("business_value") or 0)
    cg = float(scores.get("competitive_gap") or 0)
    ba = float(scores.get("brand_absence") or 0)
    ex = float(scores.get("executability") or 0)
    er = float(scores.get("evidence_readiness") or 0)
    risk = float(scores.get("risk_penalty") or 0)
    total = bv * 0.30 + cg * 0.25 + ba * 0.20 + ex * 0.15 + er * 0.10 - risk
    return total


def opportunity_key(opp: Dict[str, Any]) -> tuple:
    return (
        (opp.get("opportunity_type") or "").strip().lower(),
        (opp.get("recommended_asset") or "").strip().lower(),
        (opp.get("title") or "").strip().lower()[:40],
    )


def merge_opportunities(opps: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[tuple, Dict[str, Any]] = {}
    for opp in opps:
        key = opportunity_key(opp)
        if key not in groups:
            groups[key] = dict(opp)
            groups[key]["target_question_ids"] = list(opp.get("target_question_ids") or [])
            continue
        cur = groups[key]
        # merge question ids
        ids = list(cur.get("target_question_ids") or [])
        for qid in opp.get("target_question_ids") or []:
            if qid not in ids:
                ids.append(qid)
        cur["target_question_ids"] = ids
        # keep higher business value / total
        cs = cur.get("scores") or {}
        os_ = opp.get("scores") or {}
        if float(os_.get("business_value") or 0) > float(cs.get("business_value") or 0):
            cur["scores"] = dict(os_)
            for field in ("title", "observed_gap", "competitor_evidence", "validation_method"):
                if opp.get(field):
                    cur[field] = opp[field]
        # longer evidence
        if len(str(opp.get("competitor_evidence") or "")) > len(str(cur.get("competitor_evidence") or "")):
            cur["competitor_evidence"] = opp.get("competitor_evidence")
        # max risk penalty
        if float(os_.get("risk_penalty") or 0) > float((cur.get("scores") or {}).get("risk_penalty") or 0):
            cur.setdefault("scores", {})["risk_penalty"] = os_.get("risk_penalty")
    return list(groups.values())


def rank_opportunities(
    opportunities: Sequence[Dict[str, Any]],
    *,
    max_items: int = 10,
) -> List[Dict[str, Any]]:
    merged = merge_opportunities(opportunities)
    ranked: List[Dict[str, Any]] = []
    for i, opp in enumerate(merged):
        o = dict(opp)
        scores = dict(o.get("scores") or {})
        total = score_opportunity(scores)
        scores["total"] = total
        o["scores"] = scores
        if not o.get("id"):
            o["id"] = f"opp-{i+1:03d}"
        ranked.append(o)
    ranked.sort(key=lambda x: float((x.get("scores") or {}).get("total") or 0), reverse=True)
    # re-id top N for stability
    top = ranked[:max_items]
    for i, o in enumerate(top, 1):
        o["id"] = f"opp-{i:03d}"
        o["rank"] = i
    return top


def load_opportunities(path: Path) -> List[Dict[str, Any]]:
    data = read_json(path)
    if isinstance(data, list):
        return data
    return list(data.get("opportunities") or [])


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Score and rank opportunities (max 10)")
    parser.add_argument("--input", required=True, help="opportunities draft JSON")
    parser.add_argument("--output", required=True)
    parser.add_argument("--max", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    max_items = min(max(1, args.max), 10)
    opps = load_opportunities(Path(args.input))
    ranked = rank_opportunities(opps, max_items=max_items)
    payload = {"schema_version": "1.0", "opportunities": ranked}
    write_json(args.output, payload)
    if args.json:
        print_json(payload)
    else:
        print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())