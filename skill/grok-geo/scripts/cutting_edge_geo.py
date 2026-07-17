#!/usr/bin/env python3
"""Cutting-Edge GEO — ChatGPT Shopping + Prompt Discovery + AI SOV + Agentic Search。

用法:
  # Prompt Discovery
  python cutting_edge_geo.py discover-prompts --seed "project management tool" --count 30

  # AI SOV 计算
  python cutting_edge_geo.py compute-sov --run-dir <RUN>

  # Agentic Readiness 检查
  python cutting_edge_geo.py agentic-check --input <brand.json> --run-dir <RUN>

  # ChatGPT Shopping 分析
  python cutting_edge_geo.py shopping-analysis --run-dir <RUN>
"""

from __future__ import annotations
import argparse, sys, re
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from geo_common import read_json, read_jsonl, write_json, utc_now_iso, clamp, print_json


# ─── Prompt Discovery ───────────────────────────────────────────────────

SHOPPING_TEMPLATES = [
    "best {category} for {use_case}",
    "top {category} under {price_range}",
    "{brand_a} vs {brand_b} comparison",
    "{category} recommendations for {persona}",
    "where to buy {category}",
    "{category} reviews and ratings",
    "affordable {category} options",
    "enterprise {category} solutions",
]

INTENT_TEMPLATES = {
    "awareness": [
        "what is {category}",
        "{category} explained",
        "how does {category} work",
        "{category} trends {year}",
        "types of {category}",
    ],
    "consideration": [
        "best {category} for {use_case}",
        "{category} comparison",
        "{category} alternatives to {competitor}",
        "{category} features to look for",
        "{category} pros and cons",
    ],
    "conversion": [
        "{brand} pricing",
        "{brand} vs {competitor} which is better",
        "{category} under {price}",
        "{brand} free trial",
        "{brand} reviews {year}",
    ],
    "retention": [
        "{brand} how to {action}",
        "{brand} integration with {tool}",
        "{brand} best practices",
        "{brand} support documentation",
        "{brand} advanced features",
    ],
}


def discover_prompts(
    seed: str,
    count: int = 30,
    competitors: Optional[List[str]] = None,
    brand_name: str = "",
) -> Dict[str, Any]:
    """Discover AI search prompts from seed keywords."""
    competitors = competitors or []
    prompts: List[Dict[str, Any]] = []
    pid = 0

    # Parse seed into category and use_case
    category = seed
    use_case = "business"
    price_range = "$50"

    for intent, templates in INTENT_TEMPLATES.items():
        per_intent = max(1, count // 4)
        for tmpl in templates[:per_intent]:
            pid += 1
            text = tmpl.format(
                category=category,
                use_case=use_case,
                brand=brand_name or category,
                competitor=competitors[0] if competitors else "alternative",
                year="2026",
                price=price_range,
                persona="small business",
                action="get started",
                tool="Slack",
            )
            quality = _score_prompt_quality(text, intent, brand_name)
            prompts.append({
                "id": f"pd_{pid:03d}",
                "text": text,
                "intent": intent,
                "template": tmpl,
                "quality_score": quality,
                "has_brand": bool(brand_name and brand_name.lower() in text.lower()),
            })

    # Sort by quality and take top N
    prompts.sort(key=lambda x: x["quality_score"], reverse=True)
    prompts = prompts[:count]

    # Stats
    by_intent: Dict[str, int] = {}
    for p in prompts:
        by_intent[p["intent"]] = by_intent.get(p["intent"], 0) + 1

    return {
        "schema_version": "3.0.0",
        "generated_at": utc_now_iso(),
        "seed": seed,
        "total_prompts": len(prompts),
        "prompts": prompts,
        "distribution": by_intent,
        "avg_quality": round(sum(p["quality_score"] for p in prompts) / len(prompts), 2) if prompts else 0,
    }


def _score_prompt_quality(text: str, intent: str, brand_name: str) -> float:
    """Score prompt quality 0-100."""
    score = 50.0  # base

    # Intent value
    intent_weights = {"conversion": 20, "consideration": 15, "retention": 10, "awareness": 5}
    score += intent_weights.get(intent, 0)

    # Specificity (longer = more specific = higher value)
    words = len(text.split())
    if words >= 5:
        score += 10
    if words >= 7:
        score += 5

    # Contains brand name
    if brand_name and brand_name.lower() in text.lower():
        score -= 10  # Non-brand prompts are more valuable for discovery

    # Contains comparison
    if any(w in text.lower() for w in ["vs", "comparison", "alternative", "better"]):
        score += 10

    # Contains action
    if any(w in text.lower() for w in ["best", "top", "recommend", "buy", "pricing"]):
        score += 10

    # Brand trigger proximity — how likely the prompt leads to brand mention
    brand_trigger_words = [
        "best", "top", "recommend", "alternative", "vs", "compare",
        "which", "should i", "help me choose", "what is the best",
        "most popular", "leading", "trusted", "reliable",
    ]
    trigger_count = sum(1 for w in brand_trigger_words if w in text.lower())
    if trigger_count >= 2:
        score += 5  # High brand trigger potential
    if trigger_count == 0 and intent in ("conversion", "consideration"):
        score -= 5  # Low trigger for high-intent prompts is penalized

    return round(clamp(score, 0, 100), 1)


# ─── AI Share of Voice ──────────────────────────────────────────────────

def compute_ai_sov(run_dir: Path) -> Dict[str, Any]:
    """Compute AI Share of Voice from search results."""
    entity_path = run_dir / "intermediate" / "entity_analysis.jsonl"
    questions_path = run_dir / "intermediate" / "questions.json"

    if not entity_path.exists():
        return {"status": "no_data", "reason": "entity_analysis.jsonl not found"}

    entities = read_jsonl(entity_path)
    questions = []
    if questions_path.exists():
        q_data = read_json(questions_path)
        questions = q_data if isinstance(q_data, list) else q_data.get("questions", [])

    # Build question intent map
    intent_map: Dict[str, str] = {}
    funnel_map: Dict[str, str] = {}
    for q in questions:
        qid = q.get("id", q.get("question_id", ""))
        intent_map[qid] = q.get("intent", "unknown")
        funnel_map[qid] = q.get("funnel_stage", "unknown")

    total_mentions = 0
    brand_mentions = 0
    competitor_mentions: Dict[str, int] = {}
    by_intent: Dict[str, Dict[str, int]] = {}
    by_platform: Dict[str, Dict[str, int]] = {}
    by_funnel: Dict[str, Dict[str, int]] = {}

    for entry in entities:
        qid = entry.get("question_id", "")
        intent = intent_map.get(qid, "unknown")
        funnel = funnel_map.get(qid, "unknown")

        for entity in entry.get("entities", []):
            total_mentions += 1
            is_brand = entity.get("is_target_brand", False)

            if is_brand:
                brand_mentions += 1
            else:
                name = entity.get("entity_id", entity.get("name", "unknown"))
                competitor_mentions[name] = competitor_mentions.get(name, 0) + 1

            # By intent
            bucket = by_intent.setdefault(intent, {"brand": 0, "total": 0})
            bucket["total"] += 1
            if is_brand:
                bucket["brand"] += 1

            # By funnel
            fbucket = by_funnel.setdefault(funnel, {"brand": 0, "total": 0})
            fbucket["total"] += 1
            if is_brand:
                fbucket["brand"] += 1

    overall_sov = round(brand_mentions / total_mentions, 4) if total_mentions > 0 else 0

    # Per-intent SOV
    intent_sov: Dict[str, float] = {}
    for intent, data in by_intent.items():
        intent_sov[intent] = round(data["brand"] / data["total"], 4) if data["total"] > 0 else 0

    # Per-funnel SOV
    funnel_sov: Dict[str, float] = {}
    for funnel, data in by_funnel.items():
        funnel_sov[funnel] = round(data["brand"] / data["total"], 4) if data["total"] > 0 else 0

    # Competitor ranking
    sorted_competitors = sorted(competitor_mentions.items(), key=lambda x: x[1], reverse=True)

    return {
        "schema_version": "3.0.0",
        "computed_at": utc_now_iso(),
        "overall_sov": overall_sov,
        "brand_mentions": brand_mentions,
        "total_mentions": total_mentions,
        "by_intent": intent_sov,
        "by_funnel_stage": funnel_sov,
        "competitor_sov": {
            name: {"mentions": count, "share": round(count / total_mentions, 4) if total_mentions > 0 else 0}
            for name, count in sorted_competitors[:10]
        },
        "top_competitor": sorted_competitors[0][0] if sorted_competitors else None,
        "trend": "stable",  # Needs historical data for real trend
    }


# ─── Agentic Readiness ──────────────────────────────────────────────────

def check_agentic_readiness(
    brand: Dict[str, Any],
    site_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Check readiness for Google Agentic Search (I/O 2026)."""
    site_data = site_data or {}
    items: List[Dict[str, Any]] = []
    total = 0

    # 1. Product schema completeness (25 pts)
    schema_items = site_data.get("schema_items", [])
    product_schema = next((s for s in schema_items if s.get("@type") == "Product"), None)
    product_score = 0
    if product_schema:
        required_fields = ["name", "description", "brand", "offers"]
        present = [f for f in required_fields if product_schema.get(f)]
        product_score = round(25 * len(present) / len(required_fields))
        # Bonus for offers details
        offers = product_schema.get("offers", {})
        if isinstance(offers, dict):
            if offers.get("price"):
                product_score = min(25, product_score + 2)
            if offers.get("availability"):
                product_score = min(25, product_score + 2)
    items.append({"check": "product_schema", "score": product_score, "max": 25,
                  "detail": f"{'complete' if product_score >= 20 else 'partial' if product_score > 0 else 'missing'}"})
    total += product_score

    # 2. Real-time data freshness (20 pts)
    freshness_score = 0
    if brand.get("has_pricing_api"):
        freshness_score += 8
    if brand.get("has_inventory_api"):
        freshness_score += 6
    if brand.get("has_reviews_api"):
        freshness_score += 6
    items.append({"check": "real_time_data", "score": freshness_score, "max": 20,
                  "detail": f"pricing={'Y' if brand.get('has_pricing_api') else 'N'}, inventory={'Y' if brand.get('has_inventory_api') else 'N'}, reviews={'Y' if brand.get('has_reviews_api') else 'N'}"})
    total += freshness_score

    # 3. API accessibility (20 pts)
    api_score = 0
    if brand.get("has_public_api"):
        api_score += 10
    if brand.get("api_documentation_url"):
        api_score += 5
    if brand.get("has_openapi_spec"):
        api_score += 5
    items.append({"check": "api_accessibility", "score": api_score, "max": 20,
                  "detail": f"public_api={'Y' if brand.get('has_public_api') else 'N'}, docs={'Y' if brand.get('api_documentation_url') else 'N'}"})
    total += api_score

    # 4. Task completion path (20 pts)
    task_score = 0
    if brand.get("has_checkout_url"):
        task_score += 8
    if brand.get("has_free_trial"):
        task_score += 6
    if brand.get("has_demo_booking"):
        task_score += 6
    items.append({"check": "task_completion", "score": task_score, "max": 20,
                  "detail": f"checkout={'Y' if brand.get('has_checkout_url') else 'N'}, trial={'Y' if brand.get('has_free_trial') else 'N'}"})
    total += task_score

    # 5. Structured data depth (15 pts)
    depth_score = 0
    schema_types = {s.get("@type") for s in schema_items if isinstance(s, dict)}
    important_types = {"Organization", "Product", "FAQPage", "BreadcrumbList", "Review", "Offer"}
    coverage = len(schema_types & important_types)
    depth_score = min(15, round(15 * coverage / len(important_types)))
    items.append({"check": "schema_depth", "score": depth_score, "max": 15,
                  "detail": f"{len(schema_types)} types, {coverage}/{len(important_types)} important types"})
    total += depth_score

    grade = "A" if total >= 90 else "B" if total >= 75 else "C" if total >= 60 else "D" if total >= 40 else "F"

    return {
        "schema_version": "3.0.0",
        "scored_at": utc_now_iso(),
        "agentic_readiness_score": total,
        "grade": grade,
        "items": items,
        "recommendations": _generate_agentic_recommendations(items),
    }


def _generate_agentic_recommendations(items: List[Dict[str, Any]]) -> List[str]:
    recs = []
    for item in items:
        if item["score"] == 0:
            if item["check"] == "product_schema":
                recs.append("创建完整的 Product schema (name/description/brand/offers/availability)")
            elif item["check"] == "real_time_data":
                recs.append("提供价格/库存/评价的 API 或动态更新机制")
            elif item["check"] == "api_accessibility":
                recs.append("发布公开 API 文档和 OpenAPI 规范")
            elif item["check"] == "task_completion":
                recs.append("确保从 AI 回答到购买/试用的路径畅通")
        elif item["score"] < item["max"] * 0.5:
            recs.append(f"改善 {item['check']}（当前 {item['score']}/{item['max']}）")
    return recs


# ─── ChatGPT Shopping Analysis ──────────────────────────────────────────

def analyze_shopping_visibility(
    run_dir: Path,
    brand_name: str = "",
) -> Dict[str, Any]:
    """Analyze brand visibility in shopping-related AI prompts."""
    entity_path = run_dir / "intermediate" / "entity_analysis.jsonl"
    questions_path = run_dir / "intermediate" / "questions.json"

    if not entity_path.exists():
        return {"status": "no_data"}

    entities = read_jsonl(entity_path)
    questions = []
    if questions_path.exists():
        q_data = read_json(questions_path)
        questions = q_data if isinstance(q_data, list) else q_data.get("questions", [])

    # Identify shopping/comparison questions
    shopping_keywords = ["best", "top", "recommend", "buy", "purchase", "price", "cost",
                        "comparison", "vs", "alternative", "review", "rating"]

    shopping_qids: set = set()
    for q in questions:
        text = q.get("text", q.get("question_text", "")).lower()
        if any(kw in text for kw in shopping_keywords):
            shopping_qids.add(q.get("id", q.get("question_id", "")))

    # Analyze shopping prompts
    shopping_results = []
    non_shopping_results = []

    for entry in entities:
        qid = entry.get("question_id", "")
        is_shopping = qid in shopping_qids

        brand_found = False
        brand_rank = -1
        competitors_found = []

        for i, entity in enumerate(entry.get("entities", [])):
            if entity.get("is_target_brand"):
                brand_found = True
                brand_rank = i + 1
            elif not entity.get("is_target_brand"):
                competitors_found.append(entity.get("entity_id", entity.get("name", "")))

        result = {
            "question_id": qid,
            "brand_mentioned": brand_found,
            "brand_rank": brand_rank,
            "competitors": competitors_found[:5],
        }

        if is_shopping:
            shopping_results.append(result)
        else:
            non_shopping_results.append(result)

    # Compute shopping metrics
    shopping_total = len(shopping_results)
    shopping_brand = sum(1 for r in shopping_results if r["brand_mentioned"])
    shopping_rate = round(shopping_brand / shopping_total, 4) if shopping_total > 0 else 0

    ranks = [r["brand_rank"] for r in shopping_results if r["brand_rank"] > 0]
    avg_rank = round(sum(ranks) / len(ranks), 1) if ranks else 0

    return {
        "schema_version": "3.0.0",
        "analyzed_at": utc_now_iso(),
        "shopping_prompts_total": shopping_total,
        "brand_appearance_rate": shopping_rate,
        "avg_product_rank": avg_rank,
        "top_rank_count": sum(1 for r in ranks if r <= 3),
        "competitor_frequency": _count_competitor_frequency(shopping_results),
    }


def _count_competitor_frequency(results: List[Dict[str, Any]]) -> Dict[str, int]:
    freq: Dict[str, int] = {}
    for r in results:
        for c in r.get("competitors", []):
            freq[c] = freq.get(c, 0) + 1
    return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10])


# ─── Persona-Based Prompt Tracking ────────────────────────────────────

PERSONA_DIMENSIONS = {
    "technical": {
        "keywords": ["api", "sdk", "integration", "architecture", "scalability", "performance", "security", "infrastructure"],
        "intents": ["retention", "consideration"],
    },
    "business": {
        "keywords": ["pricing", "roi", "cost", "enterprise", "team", "workflow", "productivity", "compliance"],
        "intents": ["conversion", "consideration"],
    },
    "end_user": {
        "keywords": ["easy", "simple", "free", "tutorial", "how to", "getting started", "beginner", "user-friendly"],
        "intents": ["awareness", "retention"],
    },
    "it_admin": {
        "keywords": ["deploy", "setup", "configuration", "migration", "backup", "monitoring", "sso", "admin"],
        "intents": ["conversion", "retention"],
    },
    "developer": {
        "keywords": ["open source", "github", "documentation", "library", "framework", "plugin", "extension", "custom"],
        "intents": ["consideration", "retention"],
    },
}


def analyze_persona_coverage(run_dir: Path) -> Dict[str, Any]:
    """Analyze prompt coverage by user persona dimension."""
    questions_path = run_dir / "intermediate" / "questions.json"
    entity_path = run_dir / "intermediate" / "entity_analysis.jsonl"

    if not questions_path.exists():
        return {"status": "no_data", "reason": "questions.json not found"}

    questions = read_json(questions_path)
    q_list = questions.get("questions", []) if isinstance(questions, dict) else questions

    # Map questions to personas
    persona_coverage: Dict[str, Dict[str, Any]] = {}
    for persona, config in PERSONA_DIMENSIONS.items():
        matched_questions = []
        for q in q_list:
            text = (q.get("text", "") or q.get("question", "")).lower()
            intent = q.get("intent", "")
            # Match by keywords in question text
            keyword_match = any(kw in text for kw in config["keywords"])
            # Match by intent alignment
            intent_match = intent in config["intents"]
            if keyword_match or (intent_match and any(kw in text for kw in ["how", "what", "which", "best"])):
                matched_questions.append(q.get("id", ""))

        total_q = len(q_list)
        coverage = len(matched_questions) / total_q if total_q > 0 else 0
        persona_coverage[persona] = {
            "matched_questions": len(matched_questions),
            "total_questions": total_q,
            "coverage_rate": round(coverage, 4),
            "question_ids": matched_questions[:10],  # limit for readability
        }

    # Overall coverage score
    avg_coverage = sum(p["coverage_rate"] for p in persona_coverage.values()) / len(persona_coverage) if persona_coverage else 0

    return {
        "schema_version": "3.0.0",
        "analyzed_at": utc_now_iso(),
        "persona_coverage": persona_coverage,
        "overall_coverage_score": round(avg_coverage, 4),
        "best_covered_persona": max(persona_coverage, key=lambda k: persona_coverage[k]["coverage_rate"]) if persona_coverage else None,
        "worst_covered_persona": min(persona_coverage, key=lambda k: persona_coverage[k]["coverage_rate"]) if persona_coverage else None,
    }


# ─── CLI ────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="Cutting-Edge GEO")
    sub = p.add_subparsers(dest="command")

    dp = sub.add_parser("discover-prompts", help="AI Prompt Discovery")
    dp.add_argument("--seed", required=True)
    dp.add_argument("--count", type=int, default=30)
    dp.add_argument("--brand", default="")
    dp.add_argument("--competitors", default="")

    sov = sub.add_parser("compute-sov", help="AI Share of Voice")
    sov.add_argument("--run-dir", required=True)

    ag = sub.add_parser("agentic-check", help="Agentic Readiness")
    ag.add_argument("--input", required=True)
    ag.add_argument("--run-dir")

    sh = sub.add_parser("shopping-analysis", help="ChatGPT Shopping Analysis")
    sh.add_argument("--run-dir", required=True)
    sh.add_argument("--brand", default="")

    pt = sub.add_parser("persona-tracking", help="Persona-Based Prompt Tracking")
    pt.add_argument("--run-dir", required=True)

    args = p.parse_args()

    if args.command == "discover-prompts":
        comps = [c.strip() for c in args.competitors.split(",") if c.strip()]
        result = discover_prompts(args.seed, args.count, comps, args.brand)
        print_json(result)

    elif args.command == "compute-sov":
        result = compute_ai_sov(Path(args.run_dir))
        print_json(result)

    elif args.command == "agentic-check":
        brand = read_json(args.input)
        site_data = {}
        if args.run_dir:
            mp = Path(args.run_dir) / "intermediate" / "metrics.json"
            if mp.exists():
                site_data = read_json(mp).get("site_readiness", {})
        result = check_agentic_readiness(brand, site_data)
        print_json(result)

    elif args.command == "shopping-analysis":
        result = analyze_shopping_visibility(Path(args.run_dir), args.brand)
        print_json(result)

    elif args.command == "persona-tracking":
        result = analyze_persona_coverage(Path(args.run_dir))
        print_json(result)

    else:
        p.print_help()


if __name__ == "__main__":
    main()