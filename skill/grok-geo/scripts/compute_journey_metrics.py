#!/usr/bin/env python3
"""Compute buying journey metrics from questions, entities, and citations.

Deterministic script: maps funnel stages to journey stages, computes per-stage
mention/recommendation rates, and calculates journey conversion transitions.

Usage:
    python compute_journey_metrics.py \
        --questions <path> \
        --entities <path> \
        --citations <path> \
        --output <path>
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (
    FUNNEL_TO_JOURNEY,
    JOURNEY_STAGES,
    RECOMMENDATION_INTENTS,
    is_recommendation_mention,
    rate_with_ci,
    read_json,
    read_jsonl,
    write_json,
)


def compute_stage_metrics(
    questions: List[Dict[str, Any]],
    entities: Dict[str, Dict[str, Any]],
    citations: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Compute per-journey-stage metrics.

    Args:
        questions: List of question dicts with 'id', 'funnel_stage'
        entities: Dict mapping question_id → entity analysis dict
        citations: Optional list of citation dicts

    Returns:
        Dict with stage_metrics, journey_coverage, transitions
    """
    citations = citations or []

    if not questions:
        return {
            "stage_metrics": {stage: _empty_stage_metric() for stage in JOURNEY_STAGES},
            "journey_coverage": 0.0,
            "transitions": [],
        }

    # Group questions by journey stage via funnel mapping
    stage_questions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for q in questions:
        qid = q.get("id", "")
        funnel = q.get("funnel_stage", "")
        journey_stage = FUNNEL_TO_JOURNEY.get(funnel)
        if journey_stage:
            stage_questions[journey_stage].append(q)

    # Compute per-stage metrics
    stage_metrics: Dict[str, Dict[str, Any]] = {}
    mention_rates: Dict[str, float] = {}

    for stage in JOURNEY_STAGES:
        qs = stage_questions.get(stage, [])
        total = len(qs)

        if total == 0:
            stage_metrics[stage] = _empty_stage_metric()
            mention_rates[stage] = 0.0
            continue

        mention_count = 0
        rec_count = 0

        for q in qs:
            qid = q.get("id", "")
            entity_data = entities.get(qid, {})
            entity_list = entity_data.get("entities", [])

            for ent in entity_list:
                if ent.get("entity_type") == "target_brand" and ent.get("mentioned"):
                    mention_count += 1
                    if is_recommendation_mention(ent.get("mention_type")):
                        rec_count += 1
                    break

        mention_rate_info = rate_with_ci(mention_count, total)
        rec_rate_info = rate_with_ci(rec_count, total)
        mention_rates[stage] = mention_rate_info["rate"] or 0.0

        stage_metrics[stage] = {
            "total_questions": total,
            "mention_rate": mention_rate_info,
            "recommendation_rate": rec_rate_info,
        }

    # Journey coverage: stages with at least one mention / total stages
    stages_with_mention = sum(1 for r in mention_rates.values() if r > 0)
    journey_coverage = round(stages_with_mention / len(JOURNEY_STAGES), 4)

    # Transitions: visibility rate at each stage boundary
    transitions: List[Dict[str, Any]] = []
    for i in range(len(JOURNEY_STAGES) - 1):
        from_stage = JOURNEY_STAGES[i]
        to_stage = JOURNEY_STAGES[i + 1]
        from_rate = mention_rates.get(from_stage, 0.0)
        to_rate = mention_rates.get(to_stage, 0.0)
        transitions.append({
            "from_stage": from_stage,
            "to_stage": to_stage,
            "from_visibility": from_rate,
            "to_visibility": to_rate,
            "drop_off": round(from_rate - to_rate, 4),
        })

    return {
        "stage_metrics": stage_metrics,
        "journey_coverage": journey_coverage,
        "transitions": transitions,
    }


def _empty_stage_metric() -> Dict[str, Any]:
    return {
        "total_questions": 0,
        "mention_rate": {"rate": 0.0, "numerator": 0, "denominator": 0},
        "recommendation_rate": {"rate": 0.0, "numerator": 0, "denominator": 0},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute buying journey metrics")
    parser.add_argument("--questions", required=True, help="Path to questions.json")
    parser.add_argument("--entities", required=True, help="Path to entity_analysis.jsonl")
    parser.add_argument("--citations", default=None, help="Path to citations.json (optional)")
    parser.add_argument("--output", required=True, help="Output path for journey_metrics.json")
    args = parser.parse_args()

    questions_data = read_json(args.questions)
    questions = questions_data.get("questions", questions_data) if isinstance(questions_data, dict) else questions_data

    entities_list = read_jsonl(args.entities)
    entities = {}
    for e in entities_list:
        qid = e.get("question_id", "")
        if qid:
            entities[qid] = e

    citations = []
    if args.citations:
        citations_data = read_json(args.citations)
        citations = citations_data if isinstance(citations_data, list) else []

    result = compute_stage_metrics(questions, entities, citations)
    write_json(args.output, result)
    print(f"✓ Journey metrics computed: coverage={result['journey_coverage']}")


if __name__ == "__main__":
    main()