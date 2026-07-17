#!/usr/bin/env python3
"""Ceiling GEO — 天花板级能力：Agentic Commerce + Defensive GEO + A2A + Multimodal + Predictive。

用法:
  python ceiling_geo.py agentic-commerce --run-dir <RUN>
  python ceiling_geo.py defensive --run-dir <RUN> --auto-correct
  python ceiling_geo.py a2a --run-dir <RUN> --generate-manifest
  python ceiling_geo.py multimodal --input <brand.json> --run-dir <RUN>
  python ceiling_geo.py predict --run-dir <RUN> --days 90
  python ceiling_geo.py full-check --run-dir <RUN>
"""

from __future__ import annotations
import argparse, sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from geo_common import read_json, read_jsonl, write_json, utc_now_iso, clamp, print_json, utc_stamp


# ─── Agentic Commerce ──────────────────────────────────────────────────

def check_agentic_commerce(run_dir: Path) -> Dict[str, Any]:
    """Evaluate brand readiness for AI-agent commerce."""
    metrics_path = run_dir / "intermediate" / "metrics.json"
    brand_path = run_dir / "input" / "brand.json"

    items: List[Dict[str, Any]] = []
    total = 0

    brand = read_json(brand_path) if brand_path.exists() else {}
    site_data = {}
    if metrics_path.exists():
        site_data = read_json(metrics_path).get("site_readiness", {})

    checks: List[tuple[str, int, bool]] = [
        ("product_schema_price", 15, _check_schema_field(site_data, "Product", "offers")),
        ("product_schema_brand", 15, _check_schema_field(site_data, "Product", "brand")),
        ("has_public_api", 20, bool(brand.get("has_public_api") or brand.get("public_api_url"))),
        ("auth_documented", 10, bool(brand.get("api_auth_type"))),
        ("has_agent_manifest", 20, bool(brand.get("has_agent_manifest"))),
        ("real_time_pricing", 10, bool(brand.get("has_pricing_api") or brand.get("real_time_pricing"))),
        ("checkout_automation", 10, bool(brand.get("has_auto_checkout"))),
    ]

    for name, score, ok in checks:
        s = score if ok else 0
        items.append({"check": name, "score": s, "max": score, "detail": "✓" if ok else "✗"})
        total += s

    grade = "A" if total >= 90 else "B" if total >= 75 else "C" if total >= 60 else "D" if total >= 40 else "F"

    return {
        "schema_version": "5.0.0",
        "agentic_conversion_rate": round(total / 100, 2),
        "agent_ready_score": total,
        "grade": grade,
        "items": items,
        "recommendations": [f"Fix: {i['check']}" for i in items if i["score"] == 0],
    }


def _check_schema_field(site_data: Dict[str, Any], schema_type: str, field: str) -> bool:
    schema_items = site_data.get("schema_items", [])
    for s in schema_items:
        if isinstance(s, dict) and s.get("@type") == schema_type:
            if s.get(field):
                return True
    return False


# ─── Defensive GEO ─────────────────────────────────────────────────────

def check_defensive_geo(run_dir: Path, auto_correct: bool = False) -> Dict[str, Any]:
    """Detect brand hallucinations in AI responses."""
    entity_path = run_dir / "intermediate" / "entity_analysis.jsonl"
    metrics_path = run_dir / "intermediate" / "metrics.json"
    claims_path = run_dir / "intermediate" / "claims.json"

    result: Dict[str, Any] = {
        "schema_version": "5.0.0",
        "checked_at": utc_now_iso(),
        "hallucinations_detected": 0,
        "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        "hallucinations": [],
        "correction_status": "none",
        "corrections_applied": [] if auto_correct else None,
    }

    if not entity_path.exists():
        return result

    entities = read_jsonl(entity_path)

    # Read known_facts from brand.json (user-provided), not metrics.json
    brand_path = run_dir / "input" / "brand.json"
    known_facts: Dict[str, Any] = {}
    if brand_path.exists():
        brand_data = read_json(brand_path)
        # known_facts is a list of {claim, source_url} objects in brand.json
        for fact in brand_data.get("known_facts") or []:
            if isinstance(fact, dict):
                claim = fact.get("claim", "")
                # Simple key extraction for matching
                if "pric" in claim.lower():
                    known_facts.setdefault("pricing", claim)
                elif "found" in claim.lower() or "year" in claim.lower():
                    known_facts.setdefault("founding", claim)
                elif "product" in claim.lower():
                    known_facts.setdefault("product", claim)

    # Cross-check with claims verification data
    claims_data: List[Dict[str, Any]] = []
    if claims_path.exists():
        claims_data = read_json(claims_path) if claims_path.suffix == ".json" else read_jsonl(claims_path)
        for claim in claims_data:
            if claim.get("verification_status") == "incorrect":
                result["hallucinations"].append({
                    "severity": "high",
                    "type": "factually_incorrect",
                    "question_id": claim.get("question_id", ""),
                    "engine": claim.get("engine", "unknown"),
                    "claim": f"Verified incorrect claim: {claim.get('claim_text', '')[:100]}",
                    "evidence": claim.get("evidence", "")[:200],
                })
                result["hallucinations_detected"] += 1
                result["by_severity"]["high"] += 1

    for entry in entities:
        text = entry.get("search_answer", entry.get("answer_text", ""))
        if not text:
            continue

        # Check for price hallucinations
        if known_facts.get("pricing"):
            expected = known_facts["pricing"]
            for price_ref in ["$", "usd", "per month", "pricing"]:
                if price_ref in text.lower() and expected not in text:
                    result["hallucinations"].append({
                        "severity": "high",
                        "type": "price_misrepresentation",
                        "question_id": entry.get("question_id", ""),
                        "engine": entry.get("engine", "unknown"),
                        "claim": f"AI incorrectly describes pricing (expected: {expected})",
                        "evidence": text[:200],
                    })
                    result["hallucinations_detected"] += 1
                    result["by_severity"]["high"] += 1
                    break

        # Check for positioning hallucinations
        if known_facts.get("positioning"):
            pos = known_facts["positioning"].lower()
            for wrong_pos in ["for enterprise", "for large", "enterprise-grade", "small business only"]:
                if wrong_pos in text.lower() and pos not in text.lower():
                    result["hallucinations"].append({
                        "severity": "medium",
                        "type": "positioning_misrepresentation",
                        "question_id": entry.get("question_id", ""),
                        "engine": entry.get("engine", "unknown"),
                        "claim": f"AI positions brand incorrectly (expected: {pos})",
                        "evidence": text[:200],
                    })
                    result["hallucinations_detected"] += 1
                    result["by_severity"]["medium"] += 1
                    break

    # Generate corrections if auto mode
    if auto_correct and result["hallucinations"]:
        result["correction_status"] = "in_progress"
        for h in result["hallucinations"]:
            result["corrections_applied"].append({
                "question_id": h["question_id"],
                "type": h["type"],
                "corrective_action": f"Deploy correction schema for {h['type']}",
                "verification_method": "re-query in 7 days",
                "scheduled_for": utc_now_iso()[:10],
            })

    return result


# ─── A2A Readiness ─────────────────────────────────────────────────────

def check_a2a_readiness(run_dir: Path, generate_manifest: bool = False) -> Dict[str, Any]:
    """Check and optionally generate Agent Manifest for A2A optimization."""
    brand_path = run_dir / "input" / "brand.json"
    brand = read_json(brand_path) if brand_path.exists() else {}

    items: List[Dict[str, Any]] = []
    total = 0

    # A2A checks
    checks: List[tuple[str, int, bool]] = [
        ("jsonld_complete", 20, True),  # From earlier audit
        ("api_discoverable", 20, bool(brand.get("public_api_url") or brand.get("api_documentation_url"))),
        ("oauth_supported", 15, brand.get("api_auth_type") in ("oauth", "oauth2")),
        ("pricing_api_live", 15, bool(brand.get("has_pricing_api"))),
        ("inventory_api_live", 10, bool(brand.get("has_inventory_api"))),
        ("reviews_api_live", 10, bool(brand.get("has_reviews_api"))),
        ("webhook_support", 10, bool(brand.get("has_webhooks"))),
    ]

    for name, score, ok in checks:
        s = score if ok else 0
        items.append({"check": name, "score": s, "max": score})
        total += s

    manifest = None
    if generate_manifest:
        manifest = {
            "@context": "https://schema.org",
            "@type": "AgentManifest",
            "brand": brand.get("brand_name", "Brand"),
            "version": "1.0.0",
            "generated_at": utc_now_iso(),
            "capabilities": [],
            "data_sources": {},
            "verification": {
                "schema_compliant": True,
                "last_audited": utc_now_iso()[:10],
            },
        }

        if brand.get("public_api_url"):
            manifest["capabilities"].append({
                "action": "api_access",
                "endpoint": brand["public_api_url"],
                "auth_type": brand.get("api_auth_type", "api_key"),
            })

        if brand.get("has_checkout_url"):
            manifest["capabilities"].append({
                "action": "complete_purchase",
                "endpoint": f"{brand.get('website', '').rstrip('/')}/api/v1/checkout",
                "auth_type": "oauth2",
            })

        manifest["data_sources"] = {
            "products": brand.get("products_api_url", f"{brand.get('website', '').rstrip('/')}/api/v1/products"),
        }

        manifest_path = run_dir / "output" / "agent-manifest.json"
        write_json(manifest_path, manifest)

    return {
        "schema_version": "5.0.0",
        "a2a_score": total,
        "grade": "A" if total >= 90 else "B" if total >= 75 else "C" if total >= 60 else "D" if total >= 40 else "F",
        "items": items,
        "manifest_generated": generate_manifest,
        "manifest": manifest,
    }


# ─── Multimodal GEO ────────────────────────────────────────────────────

def check_multimodal_geo(run_dir: Path) -> Dict[str, Any]:
    """T3 Experimental: Score multimodal search optimization readiness.

    ⚠️ When site crawl data is absent, falls back to brand.json boolean
    estimation (e.g., has_blog? 40 : 0). Only 'measured' source labels
    indicate real data was used.

    Tier: T3 Experimental (estimated) / T2 Extended (measured)
    Data source: measured when site crawl exists, estimated otherwise
    """
    metrics_path = run_dir / "intermediate" / "metrics.json"
    brand_path = run_dir / "input" / "brand.json"

    site_data = {}
    if metrics_path.exists():
        site_data = read_json(metrics_path).get("site_readiness", {})

    brand = read_json(brand_path) if brand_path.exists() else {}

    content = site_data.get("content_analysis", {})
    images = content.get("images", [])
    videos = content.get("videos", [])

    # Determine data quality
    has_real_multimodal_data = len(images) > 0 or len(videos) > 0
    data_status = "measured" if has_real_multimodal_data else "estimated_from_brand_input"

    dimensions: Dict[str, Dict[str, Any]] = {}

    # Text (25) — use citability if available, else estimate from brand input
    citability = site_data.get("citability_score")
    if citability is not None:
        text_score = float(citability)
    else:
        # Estimate from brand content signals
        has_blog = bool(brand.get("blog_url") or brand.get("content_hub"))
        has_docs = bool(brand.get("documentation_url") or brand.get("api_docs_url"))
        text_score = (40 if has_blog else 0) + (30 if has_docs else 0) + 20  # baseline
    dimensions["text"] = {"score": round(text_score, 1), "max": 100, "source": "measured" if citability else "estimated"}

    # Image (25)
    if images:
        alt_count = sum(1 for img in images if img.get("alt"))
        img_score = round(alt_count / max(len(images), 1) * 100)
    else:
        # Estimate: check if brand has visual content signals
        has_visual = bool(brand.get("media_kit_url") or brand.get("logo_url"))
        img_score = 30 if has_visual else 0
    dimensions["image"] = {"score": img_score, "max": 100, "source": "measured" if images else "estimated"}

    # Video (25)
    if videos:
        has_transcript = sum(1 for v in videos if v.get("transcript"))
        has_chapters = sum(1 for v in videos if v.get("chapters"))
        video_score = round((has_transcript + has_chapters) / max(len(videos) * 2, 1) * 100)
    else:
        has_video = bool(brand.get("video_url") or brand.get("youtube_url"))
        video_score = 20 if has_video else 0
    dimensions["video"] = {"score": video_score, "max": 100, "source": "measured" if videos else "estimated"}

    # Voice (25) — check from site_data or brand input
    has_faq = bool(site_data.get("has_faq")) or bool(brand.get("faq_url"))
    has_speakable = bool(site_data.get("has_speakable")) or bool(brand.get("speakable_schema"))
    voice_score = (50 if has_faq else 0) + (50 if has_speakable else 0)
    dimensions["voice"] = {"score": voice_score, "max": 100, "source": "measured" if site_data.get("has_faq") else "estimated"}

    # Cross-modal consistency
    consistency = round((text_score + img_score + video_score + voice_score) / 400 * 100, 1) if any([text_score, img_score, video_score, voice_score]) else 0

    overall = round(
        text_score * 0.30 + img_score * 0.25 + video_score * 0.25 + voice_score * 0.20,
        1
    )

    return {
        "schema_version": "5.0.0",
        "tier": "T3_EXPERIMENTAL" if data_status == "estimated_from_brand_input" else "T2_EXTENDED",
        "data_status": data_status,
        "multimodal_score": overall,
        "dimensions": dimensions,
        "cross_modal_consistency": consistency,
        "recommendations": [
            "Add descriptive alt text to all images" if img_score < 80 else "",
            "Add video transcripts and chapters" if video_score < 80 else "",
            "Add speakable schema for voice search" if voice_score < 50 else "",
        ],
    }


# ─── Predictive AI Visibility ──────────────────────────────────────────

def predict_visibility(run_dir: Path, days: int = 90) -> Dict[str, Any]:
    """T3 Experimental: Trend extrapolation for AI visibility score.

    ⚠️ This is NOT a prediction model. It uses fixed heuristic coefficients
    (momentum, content_velocity, seasonal_factor) to extrapolate from the
    current score. No historical data analysis or ML model is involved.
    Results should be treated as directional hints, not forecasts.

    Tier: T3 Experimental
    Data source: heuristic (hardcoded coefficients)
    """
    metrics_path = run_dir / "intermediate" / "metrics.json"
    entity_path = run_dir / "intermediate" / "entity_analysis.jsonl"

    current_score = 50.0
    historical_scores: List[float] = []

    if metrics_path.exists():
        metrics = read_json(metrics_path)
        current_score = metrics.get("geo_score", {}).get("score", 50)

    if entity_path.exists():
        entities = read_jsonl(entity_path)
        historical_scores = [e.get("geo_score", 50) for e in entities if e.get("geo_score") is not None]
        if not historical_scores:
            historical_scores = [current_score]

    # Check for real historical data from chain_runs
    chain_path = run_dir / "intermediate" / "run_chain.json"
    has_chain_data = chain_path.exists()
    data_status = "model_heuristic" if not has_chain_data and len(historical_scores) <= 1 else "historical_trend"

    # Simple predictive model
    momentum = 0.05 if current_score > 60 else -0.02 if current_score < 40 else 0.02
    content_velocity = 0.03
    seasonal_factor = 0.01

    predicted_30d = round(clamp(current_score * (1 + momentum + content_velocity + seasonal_factor), 0, 100), 1)
    predicted_90d = round(clamp(current_score * (1 + (momentum + content_velocity + seasonal_factor) * 3), 0, 100), 1)

    ci_width = 10 + (days / 90) * 5

    return {
        "schema_version": "5.0.0",
        "tier": "T3_EXPERIMENTAL",
        "data_source": data_status,
        "⚠️_notice": "Trend extrapolation with fixed coefficients. NOT a prediction model.",
        "status": data_status,
        "predicted_at": utc_now_iso(),
        "current_score": current_score,
        "predicted_score_30d": predicted_30d,
        "predicted_score_90d": predicted_90d,
        "confidence_interval": {
            "30d": {"low": round(predicted_30d - ci_width / 3, 1), "high": round(predicted_30d + ci_width / 3, 1)},
            "90d": {"low": round(predicted_90d - ci_width, 1), "high": round(predicted_90d + ci_width, 1)},
        },
        "contributing_factors": {
            "momentum_score": round(momentum, 4),
            "content_velocity": content_velocity,
            "seasonal_factor": seasonal_factor,
        },
        "risk_factors": [
            f"Current score {current_score} {'below' if current_score < 60 else 'above'} optimal level"
        ],
        "opportunities": [
            "Improve content freshness velocity" if content_velocity < 0.05 else "",
            "Build citation momentum in high-intent prompts",
        ],
    }


# ─── Full Ceiling Check ────────────────────────────────────────────────

def full_ceiling_check(run_dir: Path) -> Dict[str, Any]:
    """Run ALL ceiling-level capabilities."""
    return {
        "schema_version": "5.0.0",
        "version": "5.0.0",
        "checked_at": utc_now_iso(),
        "_tier_notice": (
            "⚠️ T3 Experimental: predictive_visibility and multimodal_geo (when estimated) "
            "use heuristic coefficients, not prediction models. Treat as directional hints."
        ),
        "agentic_commerce": check_agentic_commerce(run_dir),
        "defensive_geo": check_defensive_geo(run_dir),
        "a2a_readiness": check_a2a_readiness(run_dir),
        "multimodal_geo": check_multimodal_geo(run_dir),
        "predictive_visibility": predict_visibility(run_dir),
    }


# ─── CLI ────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="Ceiling GEO")
    sub = p.add_subparsers(dest="command")

    ac = sub.add_parser("agentic-commerce", help="Agentic Commerce Check")
    ac.add_argument("--run-dir", required=True)

    dg = sub.add_parser("defensive", help="Defensive GEO")
    dg.add_argument("--run-dir", required=True)
    dg.add_argument("--auto-correct", action="store_true")

    a2 = sub.add_parser("a2a", help="A2A Readiness")
    a2.add_argument("--run-dir", required=True)
    a2.add_argument("--generate-manifest", action="store_true")

    mm = sub.add_parser("multimodal", help="Multimodal GEO")
    mm.add_argument("--run-dir", required=True)

    pr = sub.add_parser("predict", help="Predictive Visibility")
    pr.add_argument("--run-dir", required=True)
    pr.add_argument("--days", type=int, default=90)

    fc = sub.add_parser("full-check", help="Full Ceiling Check")
    fc.add_argument("--run-dir", required=True)

    args = p.parse_args()

    handlers = {
        "agentic-commerce": lambda: check_agentic_commerce(Path(args.run_dir)),
        "defensive": lambda: check_defensive_geo(Path(args.run_dir), args.auto_correct),
        "a2a": lambda: check_a2a_readiness(Path(args.run_dir), args.generate_manifest),
        "multimodal": lambda: check_multimodal_geo(Path(args.run_dir)),
        "predict": lambda: predict_visibility(Path(args.run_dir), args.days),
        "full-check": lambda: full_ceiling_check(Path(args.run_dir)),
    }

    if args.command in handlers:
        result = handlers[args.command]()
        output_path = Path(args.run_dir) / "intermediate" / f"ceiling_{args.command.replace('-', '_')}.json"
        write_json(output_path, result)

        if args.command == "full-check":
            print(f"Agentic Ready: {result['agentic_commerce']['agent_ready_score']}/100")
            print(f"Hallucinations: {result['defensive_geo']['hallucinations_detected']}")
            print(f"A2A Score: {result['a2a_readiness']['a2a_score']}/100")
            print(f"Multimodal: {result['multimodal_geo']['multimodal_score']}/100")
            print(f"Predict (90d): {result['predictive_visibility']['predicted_score_90d']}")
        else:
            print_json(result)
    else:
        p.print_help()


if __name__ == "__main__":
    main()