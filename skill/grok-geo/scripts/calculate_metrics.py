#!/usr/bin/env python3
"""Deterministic metric calculation (§13). Model must not hand-compute these."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (  # noqa: E402
    RECOMMENDATION_INTENTS,
    RECOMMENDATION_TYPE_SCORES,
    SCHEMA_VERSION,
    aggregate_platform_citations,
    ai_perception_score,
    citability_score,
    clamp,
    freshness_score,
    geo_score,
    is_recommendation_mention,
    negative_signal_score,
    position_score,
    print_json,
    rag_readiness,
    rate_with_ci,
    read_json,
    read_jsonl,
    trust_stack_score,
    write_json,
)


def load_questions(path: Path) -> List[Dict[str, Any]]:
    data = read_json(path)
    if isinstance(data, dict) and "questions" in data:
        return list(data["questions"])
    if isinstance(data, list):
        return list(data)
    raise ValueError("invalid questions file")


def load_entities(path: Path) -> Dict[str, Dict[str, Any]]:
    """question_id -> entity analysis row."""
    if not path.exists():
        return {}
    if path.suffix == ".jsonl":
        rows = read_jsonl(path)
    else:
        data = read_json(path)
        rows = data if isinstance(data, list) else data.get("entities") or data.get("rows") or []
    return {r["question_id"]: r for r in rows if "question_id" in r}


def load_citations(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    data = read_json(path)
    if isinstance(data, list):
        return data
    return list(data.get("citations") or [])


def load_claims(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    data = read_json(path)
    if isinstance(data, list):
        return data
    return list(data.get("claims") or [])


def target_entity(entities: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for e in entities:
        if e.get("entity_type") == "target_brand" or e.get("entity_id") == "target-brand":
            return e
    return None


def competitor_entities(entities: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [e for e in entities if e.get("entity_type") == "competitor"]


def calculate_metrics(
    questions: Sequence[Dict[str, Any]],
    entities_by_qid: Dict[str, Dict[str, Any]],
    citations: Sequence[Dict[str, Any]],
    claims: Sequence[Dict[str, Any]],
    *,
    valid_question_ids: Optional[Sequence[str]] = None,
    # v1.2 optional inputs
    platform_search_results: Optional[Sequence[Dict[str, Any]]] = None,
    freshness_signals: Optional[Sequence[Dict[str, Any]]] = None,
    rag_dimensions: Optional[Dict[str, Dict[str, Any]]] = None,
    # v1.3 optional inputs
    citability_method_scores: Optional[Dict[str, Dict[str, Any]]] = None,
    negative_signals: Optional[Sequence[Dict[str, Any]]] = None,
    trust_layers: Optional[Dict[str, Dict[str, Any]]] = None,
    perception_dimensions: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    q_by_id = {q["id"]: q for q in questions if "id" in q}

    # valid answers: those with entity analysis rows OR explicitly provided
    if valid_question_ids is not None:
        valid_ids = list(valid_question_ids)
    else:
        valid_ids = [qid for qid in entities_by_qid.keys() if qid in q_by_id]
        if not valid_ids:
            # fall back to all questions marked ready/searched
            valid_ids = [
                q["id"]
                for q in questions
                if q.get("status") in {None, "ready", "searched", "success"}
            ]

    valid_n = len(valid_ids)

    brand_mention_ids = []
    brand_rec_ids = []
    rec_valid_ids = []
    owned_citation_ids = set()
    earned_support_ids = set()
    coverage_ids = set()
    negative_rec_count = 0

    visibility_num = 0.0
    visibility_den = 0.0

    # recommendation SOV scores
    brand_pos_score = 0.0
    competitor_pos_scores: Dict[str, float] = defaultdict(float)

    # v1.1 — new tracking variables
    sentiment_scores: List[float] = []
    rec_type_counts: Dict[str, int] = {}
    co_mention_counts: Dict[str, int] = {}

    citations_by_qid: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for c in citations:
        citations_by_qid[c.get("question_id") or ""].append(c)

    for qid in valid_ids:
        q = q_by_id.get(qid) or {}
        intent = q.get("intent") or ""
        bv = float(q.get("business_value") or 50)
        weight = bv / 100.0

        row = entities_by_qid.get(qid) or {"entities": []}
        ents = row.get("entities") or []
        te = target_entity(ents)

        mentioned = bool(te and te.get("mentioned"))
        mention_type = (te or {}).get("mention_type")
        rank = (te or {}).get("recommendation_rank")

        if mentioned:
            brand_mention_ids.append(qid)
            coverage_ids.add(qid)

        if intent in RECOMMENDATION_INTENTS:
            rec_valid_ids.append(qid)
            if is_recommendation_mention(mention_type):
                brand_rec_ids.append(qid)

        if mention_type == "not_recommended":
            negative_rec_count += 1

        pscore = position_score(mention_type if mentioned else None, rank)
        visibility_num += pscore * weight
        visibility_den += weight

        # SOV: positive recommendation position scores for brand + competitors
        if is_recommendation_mention(mention_type) and mentioned:
            brand_pos_score += max(pscore, 0.0) * weight

        # v1.1 — Sentiment index: average sentiment_score across brand mentions
        if mentioned and te:
            ss = te.get("sentiment_score")
            if isinstance(ss, (int, float)) and 0 <= ss <= 100:
                sentiment_scores.append(float(ss))

        # v1.1 — Recommendation type distribution
        if mentioned and te:
            rtype = te.get("recommendation_type")
            if rtype and rtype != "not_mentioned":
                rec_type_counts[rtype] = rec_type_counts.get(rtype, 0) + 1

        # v1.1 — Competitor co-mentions: count how often each competitor appears alongside brand
        if mentioned and te:
            for co_id in (te.get("competitor_co_mentions") or []):
                co_mention_counts[co_id] = co_mention_counts.get(co_id, 0) + 1

        for ce in competitor_entities(ents):
            if not ce.get("mentioned"):
                continue
            cmt = ce.get("mention_type")
            if is_recommendation_mention(cmt):
                cps = position_score(cmt, ce.get("recommendation_rank"))
                key = ce.get("canonical_name") or ce.get("entity_id") or "competitor"
                competitor_pos_scores[key] += max(cps, 0.0) * weight

        # citations
        for cit in citations_by_qid.get(qid, []):
            if cit.get("source_type") == "owned":
                owned_citation_ids.add(qid)
                coverage_ids.add(qid)
            if cit.get("source_type") == "earned_media" and cit.get("supports_target_brand"):
                earned_support_ids.add(qid)

    mention = rate_with_ci(len(brand_mention_ids), valid_n)
    rec = rate_with_ci(len(brand_rec_ids), len(rec_valid_ids))
    owned = rate_with_ci(len(owned_citation_ids), valid_n)
    earned = rate_with_ci(len(earned_support_ids), valid_n)
    coverage = rate_with_ci(len(coverage_ids), valid_n)

    if visibility_den > 0:
        vis = clamp((visibility_num / visibility_den) * 100.0, 0.0, 100.0)
        vis_raw = (visibility_num / visibility_den) * 100.0
    else:
        vis = 0.0
        vis_raw = 0.0

    sov_den = brand_pos_score + sum(competitor_pos_scores.values())
    recommendation_sov = (brand_pos_score / sov_den) if sov_den > 0 else None

    # accuracy
    correct = sum(1 for c in claims if c.get("verification_status") == "correct")
    partial = sum(1 for c in claims if c.get("verification_status") == "partially_correct")
    verifiable = [
        c
        for c in claims
        if c.get("verification_status")
        not in {None, "unverifiable"}
    ]
    # doc: unverifiable not in denominator; other statuses count
    verifiable_count = len(verifiable)
    accuracy = (
        (correct + partial * 0.5) / verifiable_count if verifiable_count > 0 else None
    )

    # v1.1 — Sentiment index
    sentiment_index = (
        round(sum(sentiment_scores) / len(sentiment_scores), 1)
        if sentiment_scores
        else None
    )

    # v1.1 — Citation share by competitor
    cit_by_competitor: Dict[str, Dict[str, Any]] = {}
    competitor_citation_total = sum(competitor_pos_scores.values())
    for cname, cscore in competitor_pos_scores.items():
        cit_by_competitor[cname] = {
            "positive_score": round(cscore, 4),
            "share": round(cscore / competitor_citation_total, 4) if competitor_citation_total > 0 else 0.0,
        }

    # v1.1 — Composite GEO score
    mention_rate_val = mention["rate"] if mention["rate"] is not None else 0.0
    rec_rate_val = rec["rate"] if rec["rate"] is not None else 0.0
    owned_rate_val = owned["rate"] if owned["rate"] is not None else 0.0
    geo = geo_score(vis, mention_rate_val, rec_rate_val, owned_rate_val)

    # ─── v1.2 Platform Citation Map ───
    platform_map = None
    if platform_search_results:
        platform_map = aggregate_platform_citations(platform_search_results)

    # ─── v1.2 Freshness Score ───
    freshness = None
    if freshness_signals is not None:
        freshness = freshness_score(freshness_signals)

    # ─── v1.2 RAG Readiness ───
    rag = None
    if rag_dimensions is not None:
        rag = rag_readiness(rag_dimensions)

    # ─── v1.3 Citability ───
    citability = None
    if citability_method_scores is not None:
        citability = citability_score(citability_method_scores)

    # ─── v1.3 Negative Signals ───
    neg_signals = None
    if negative_signals is not None:
        neg_signals = negative_signal_score(negative_signals)

    # ─── v1.3 Trust Stack ───
    trust = None
    if trust_layers is not None:
        trust = trust_stack_score(trust_layers)

    # ─── v1.3 AI Perception ───
    perception = None
    if perception_dimensions is not None:
        perception = ai_perception_score(perception_dimensions)

    return {
        "schema_version": SCHEMA_VERSION,
        "sample": {
            "valid_answer_count": valid_n,
            "valid_question_ids": valid_ids,
            "question_count": len(questions),
            "recommendation_question_count": len(rec_valid_ids),
            "claim_count": len(claims),
            "verifiable_claim_count": verifiable_count,
        },
        "mention_rate": mention,
        "recommendation_rate": rec,
        "visibility_score": {
            "score": vis,
            "raw_score": vis_raw,
            "numerator": visibility_num,
            "denominator": visibility_den,
            "negative_recommendation_count": negative_rec_count,
        },
        "recommendation_sov": {
            "rate": recommendation_sov,
            "brand_positive_score": brand_pos_score,
            "competitor_positive_scores": dict(competitor_pos_scores),
            "denominator": sov_den if sov_den > 0 else None,
        },
        "owned_citation_rate": owned,
        "earned_support_rate": earned,
        "accuracy_score": {
            "score": accuracy,
            "correct_count": correct,
            "partially_correct_count": partial,
            "verifiable_claim_count": verifiable_count,
        },
        "question_coverage": coverage,
        "geo_score": geo,
        "sentiment_index": {
            "score": sentiment_index,
            "sample_size": len(sentiment_scores),
        },
        "recommendation_type_distribution": rec_type_counts or None,
        "citation_share_by_competitor": cit_by_competitor or None,
        "competitor_co_mentions": co_mention_counts or None,
        "platform_citation_map": platform_map,
        "freshness": freshness,
        "rag_readiness": rag,
        "citability": citability,
        "negative_signals": neg_signals,
        "trust_stack": trust,
        "ai_perception": perception,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Calculate deterministic GEO metrics")
    parser.add_argument("--questions", required=True)
    parser.add_argument("--entities", required=True)
    parser.add_argument("--citations", required=True)
    parser.add_argument("--claims", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--valid-ids", default=None, help="optional JSON list of valid question ids")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    questions = load_questions(Path(args.questions))
    entities = load_entities(Path(args.entities))
    citations = load_citations(Path(args.citations))
    claims = load_claims(Path(args.claims))
    valid_ids = None
    if args.valid_ids:
        valid_ids = read_json(args.valid_ids)

    metrics = calculate_metrics(
        questions, entities, citations, claims, valid_question_ids=valid_ids
    )
    write_json(args.output, metrics)
    if args.json:
        print_json(metrics)
    else:
        print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())