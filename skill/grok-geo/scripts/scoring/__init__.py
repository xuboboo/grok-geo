"""Scoring primitives — deterministic metric computation functions.

Split from geo_common.py for single-responsibility per module.
Each function is pure (no side effects, no IO) and deterministic.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# Allow import from parent package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.constants import (
    GEO_SCORE_WEIGHTS,
    NEGATIVE_SIGNAL_DEDUCTIONS,
    PERCEPTION_WEIGHTS,
    RAG_CHUNK_WEIGHTS,
    TRUST_STACK_WEIGHTS,
    FRESHNESS_DECAY_CAPS,
    RECOMMENDATION_MENTION_TYPES,
)


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def wilson_ci(successes: int, n: int, z: float = 1.96) -> Optional[Dict[str, float]]:
    """Wilson score interval for binomial proportion (95% default)."""
    if n <= 0:
        return None
    p = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    margin = (z * ((p * (1 - p) / n + z2 / (4 * n * n)) ** 0.5)) / denom
    low = max(0.0, center - margin)
    high = min(1.0, center + margin)
    return {"low": low, "high": high, "level": 0.95}


def rate_with_ci(num: int, den: int) -> Dict[str, Any]:
    rate = (num / den) if den > 0 else None
    return {
        "numerator": num,
        "denominator": den,
        "rate": rate,
        "sample_size": den,
        "wilson_ci_95": wilson_ci(num, den) if den > 0 else None,
    }


def geo_score(
    visibility_score: float,
    mention_rate: float,
    recommendation_rate: float,
    owned_citation_rate: float,
) -> Dict[str, Any]:
    """Composite GEO score (0-100).

    GEO = 0.30 × visibility + 0.25 × mention_rate
        + 0.25 × rec_rate   + 0.20 × owned_cite_rate
    """
    vis_norm = clamp(visibility_score / 100.0, 0.0, 1.0)
    mnt = clamp(mention_rate, 0.0, 1.0)
    rec = clamp(recommendation_rate, 0.0, 1.0)
    cite = clamp(owned_citation_rate, 0.0, 1.0)

    w = GEO_SCORE_WEIGHTS
    raw = (
        w["visibility"] * vis_norm
        + w["mention"] * mnt
        + w["recommendation"] * rec
        + w["citation"] * cite
    )
    score = round(clamp(raw * 100.0, 0.0, 100.0), 1)

    if score >= 86:
        band = "excellent"
    elif score >= 68:
        band = "good"
    elif score >= 36:
        band = "foundation"
    else:
        band = "critical"

    return {
        "score": score,
        "band": band,
        "breakdown": {
            "visibility": round(vis_norm * 100.0, 1),
            "mention_rate": round(mnt * 100.0, 1),
            "recommendation_rate": round(rec * 100.0, 1),
            "owned_citation_rate": round(cite * 100.0, 1),
        },
        "weights": dict(w),
    }


def freshness_score(decay_signals: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Content freshness score (0-100, higher = fresher)."""
    severity_mult = {"high": 1.0, "medium": 0.6, "low": 0.3}
    total_deduction = 0
    for sig in decay_signals:
        pattern = sig.get("pattern", "")
        sev = sig.get("severity", "medium")
        cap = FRESHNESS_DECAY_CAPS.get(pattern, 10)
        mult = severity_mult.get(sev, 0.5)
        total_deduction += int(cap * mult)

    score = clamp(100.0 - total_deduction, 0.0, 100.0)
    if score >= 86:
        band = "fresh"
    elif score >= 68:
        band = "aging"
    elif score >= 36:
        band = "stale"
    else:
        band = "rotting"

    return {
        "score": round(score, 1),
        "band": band,
        "total_deduction": total_deduction,
        "decay_count": len(decay_signals),
    }


def rag_readiness(dimensions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """RAG chunk readiness score (0-100, higher = more chunkable)."""
    weighted = 0.0
    breakdown = {}
    for dim, weight in RAG_CHUNK_WEIGHTS.items():
        d = dimensions.get(dim, {})
        s = float(d.get("score", 0))
        weighted += s * weight
        breakdown[dim] = {"score": round(s, 1), "weight": weight, "issues": d.get("issues", [])}

    score = clamp(round(weighted, 1), 0.0, 100.0)
    if score >= 86:
        band = "rag_ready"
    elif score >= 68:
        band = "good"
    elif score >= 36:
        band = "needs_work"
    else:
        band = "not_ready"

    return {"score": score, "band": band, "breakdown": breakdown}


def position_score(mention_type: Optional[str], recommendation_rank: Optional[int]) -> float:
    """Map mention type / rank to position score per §13.3."""
    if not mention_type:
        return 0.0
    mt = mention_type
    if mt == "not_recommended":
        return -0.30
    if mt == "strongly_recommended":
        if recommendation_rank == 1: return 1.00
        if recommendation_rank == 2: return 0.75
        if recommendation_rank == 3: return 0.55
        return 0.30
    if mt == "recommended":
        if recommendation_rank == 1: return 1.00
        if recommendation_rank == 2: return 0.75
        if recommendation_rank == 3: return 0.55
        return 0.30
    if mt == "weakly_recommended":
        return 0.20
    if mt == "positive_mention":
        return 0.10
    if mt == "neutral_mention":
        return 0.05
    if mt in {"comparison_only", "citation_only"}:
        return 0.05
    if mt == "negative_mention":
        return 0.0
    return 0.0


def is_recommendation_mention(mention_type: Optional[str]) -> bool:
    return mention_type in RECOMMENDATION_MENTION_TYPES


def citability_score(method_scores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Content citability score from 20 weighted method scores."""
    total = 0.0
    max_total = 0.0
    scored_methods = []

    for method, data in method_scores.items():
        s = float(data.get("score", 0))
        m = float(data.get("max", 1))
        total += s
        max_total += m
        scored_methods.append((method, s, m, data.get("evidence", "")))

    score = clamp(round((total / max_total) * 100.0, 1) if max_total > 0 else 0.0, 0.0, 100.0)

    if score >= 86:
        band = "highly_citable"
    elif score >= 68:
        band = "good"
    elif score >= 36:
        band = "foundation"
    else:
        band = "not_citable"

    sorted_by_util = sorted(scored_methods, key=lambda x: x[1] / x[2] if x[2] > 0 else 0, reverse=True)
    strengths = [{"method": m, "score": s, "max": mx, "evidence": e} for m, s, mx, e in sorted_by_util[:3] if s > 0]
    weaknesses = [{"method": m, "score": s, "max": mx, "evidence": e} for m, s, mx, e in sorted_by_util[-3:] if s < mx]

    return {
        "score": score, "band": band,
        "total_points": round(total, 1), "max_points": round(max_total, 1),
        "top_strengths": strengths, "top_weaknesses": weaknesses,
        "method_scores": {m: {"score": s, "max": mx} for m, s, mx, _ in scored_methods},
    }


def negative_signal_score(signals: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Negative signal score (0-100, higher = fewer problems)."""
    total_deduction = 0
    for sig in signals:
        sev = sig.get("severity", "medium")
        total_deduction += NEGATIVE_SIGNAL_DEDUCTIONS.get(sev, 5)

    score = clamp(100.0 - total_deduction, 0.0, 100.0)
    if score >= 86:
        band = "clean"
    elif score >= 68:
        band = "minor_issues"
    elif score >= 36:
        band = "problematic"
    else:
        band = "severe"

    return {
        "score": round(score, 1), "band": band,
        "signal_count": len(signals), "total_deduction": total_deduction,
    }


def trust_stack_score(layers: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """5-layer trust stack score (0-100, A-F grade)."""
    weighted = 0.0
    layer_details = {}
    weakest_name = ""
    weakest_score = 101.0
    strongest_name = ""
    strongest_score = -1.0

    for layer, weight in TRUST_STACK_WEIGHTS.items():
        d = layers.get(layer, {})
        s = float(d.get("score", 0))
        weighted += s * weight
        layer_details[layer] = {"score": round(s, 1), "weight": weight, "issues": d.get("issues", [])}
        if s < weakest_score:
            weakest_score = s
            weakest_name = layer
        if s > strongest_score:
            strongest_score = s
            strongest_name = layer

    score = clamp(round(weighted, 1), 0.0, 100.0)
    if score >= 90: grade = "A"
    elif score >= 75: grade = "B"
    elif score >= 60: grade = "C"
    elif score >= 40: grade = "D"
    else: grade = "F"

    return {
        "score": score, "grade": grade,
        "layers": layer_details,
        "weakest_layer": weakest_name, "strongest_layer": strongest_name,
    }


def ai_perception_score(dimensions: Dict[str, float]) -> Dict[str, Any]:
    """AI perception score (0-100)."""
    weighted = 0.0
    breakdown = {}

    for dim, weight in PERCEPTION_WEIGHTS.items():
        s = clamp(dimensions.get(dim, 0.0), 0.0, 1.0)
        weighted += s * weight
        breakdown[dim] = {"score": round(s * 100, 1), "weight": weight}

    score = clamp(round(weighted * 100.0, 1), 0.0, 100.0)
    if score >= 86: band = "excellent"
    elif score >= 68: band = "favorable"
    elif score >= 36: band = "mixed"
    else: band = "negative"

    return {"score": score, "band": band, "breakdown": breakdown}


def aggregate_platform_citations(
    search_results: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """Aggregate cross-platform citation data from search results."""
    from collections import defaultdict

    by_question: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in search_results:
        by_question[r.get("question_id", "")].append(r)

    cross_platform_count = 0
    total_questions = 0
    platform_mention_rates: Dict[str, List[bool]] = defaultdict(list)
    domain_platform_map: Dict[str, set] = defaultdict(set)

    for qid, results in by_question.items():
        total_questions += 1
        platforms_with_mention = set()
        for r in results:
            plat = r.get("platform", "")
            mentioned = bool(r.get("brand_mentioned"))
            platform_mention_rates[plat].append(mentioned)
            if mentioned:
                platforms_with_mention.add(plat)
            for cit in (r.get("citations") or []):
                dom = cit.get("domain", "")
                if dom:
                    domain_platform_map[dom].add(plat)
        if len(platforms_with_mention) >= 2:
            cross_platform_count += 1

    plat_rates = {}
    for plat, flags in platform_mention_rates.items():
        plat_rates[plat] = round(sum(flags) / len(flags), 4) if flags else 0.0

    if len(plat_rates) >= 2:
        rates = list(plat_rates.values())
        mean_r = sum(rates) / len(rates)
        var = sum((r - mean_r) ** 2 for r in rates) / len(rates)
        std = var ** 0.5
        parity = round(max(0.0, 1.0 - std), 4)
    else:
        parity = None

    total_domains = len(domain_platform_map)
    overlap_domains = sum(1 for plats in domain_platform_map.values() if len(plats) >= 2)
    overlap_rate = round(overlap_domains / total_domains, 4) if total_domains > 0 else None

    ranking = sorted(plat_rates.items(), key=lambda x: x[1], reverse=True)

    return {
        "cross_platform_visibility_score": round(cross_platform_count / total_questions, 4) if total_questions > 0 else None,
        "platform_parity_index": parity,
        "source_overlap_rate": overlap_rate,
        "platform_mention_rates": plat_rates,
        "platform_advantage_map": {
            "best_platform": ranking[0][0] if ranking else None,
            "worst_platform": ranking[-1][0] if ranking else None,
            "platform_ranking": [{"platform": p, "mention_rate": r} for p, r in ranking],
        },
        "total_questions_analyzed": total_questions,
        "total_domains_cited": total_domains,
        "cross_platform_domains": overlap_domains,
    }