#!/usr/bin/env python3
"""Ultimate GEO — Agentic Brand Vault + 叙事分析 + 多模型热力图 + Agentic GEO 引擎。

用法:
  python ultimate_geo.py brand-vault --run-dir <RUN>           # Agentic Brand Vault
  python ultimate_geo.py narrative --run-dir <RUN>              # 叙事语调分析
  python ultimate_geo.py heatmap --run-dir <RUN>                # 多模型覆盖热力图
  python ultimate_geo.py agentic --run-dir <RUN> --auto         # Agentic GEO 引擎
  python ultimate_geo.py hybrid --run-dir <RUN>                 # 混合 GEO+SEO 指标
  python ultimate_geo.py full-audit --run-dir <RUN>             # 完整终极审计
"""

from __future__ import annotations
import argparse, sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from geo_common import read_json, read_jsonl, write_json, utc_now_iso, clamp, print_json, utc_stamp


# ─── Agentic Brand Vault ────────────────────────────────────────────────

def analyze_brand_vault(run_dir: Path, brand_name: str = "") -> Dict[str, Any]:
    """Analyze brand narrative consistency across AI engines."""
    entity_path = run_dir / "intermediate" / "entity_analysis.jsonl"
    metrics_path = run_dir / "intermediate" / "metrics.json"

    brand_vault: Dict[str, Any] = {
        "schema_version": "4.0.0",
        "analyzed_at": utc_now_iso(),
        "narrative_statements": [],
        "word_association_graph": {"positive": [], "neutral": [], "negative": [], "intended": [], "missing": []},
        "cross_engine_consistency_score": 0.0,
        "platform_narratives": {},
        "deviations": [],
    }

    if not entity_path.exists():
        return brand_vault

    entities = read_jsonl(entity_path)
    brand = brand_name or "brand"

    # Extract all AI descriptions of the brand
    all_descriptions: List[str] = []
    by_engine: Dict[str, List[str]] = {}

    for entry in entities:
        engine = entry.get("engine", "unknown")
        for entity in entry.get("entities", []):
            if entity.get("is_target_brand", False):
                text = entry.get("search_answer", entry.get("answer_text", ""))
                if text:
                    all_descriptions.append(text)
                    by_engine.setdefault(engine, []).append(text)

    # Word association extraction — expanded vocabulary
    word_scores: Dict[str, Dict[str, float]] = {"positive": {}, "neutral": {}, "negative": {}}
    positive_words = [
        # Quality
        "great", "excellent", "best", "outstanding", "superior", "exceptional", "premium",
        "world-class", "top-tier", "high-quality", "stellar", "remarkable", "impressive",
        # Capability
        "powerful", "innovative", "advanced", "cutting-edge", "robust", "comprehensive",
        "flexible", "scalable", "versatile", "feature-rich", "full-featured", "enterprise-grade",
        # Leadership
        "leading", "top", "popular", "trusted", "preferred", "dominant", "established",
        "renowned", "recognized", "award-winning", "industry-leading", "market-leading",
        # UX
        "intuitive", "user-friendly", "seam", "easy", "simple", "elegant", "clean",
        "accessible", "responsive", "fast", "reliable", "stable", "secure",
        # Value
        "affordable", "cost-effective", "valuable", "worth", "roi", "efficient",
        "productive", "time-saving", "automated",
    ]
    neutral_words = [
        "offers", "provides", "includes", "features", "supports", "enables", "allows",
        "delivers", "serves", "covers", "handles", "manages", "operates", "focuses",
        "specializes", "targets", "caters", "addresses", "solves", "helps",
    ]
    negative_words = [
        # Quality issues
        "limited", "lacking", "poor", "weak", "mediocre", "subpar", "inadequate",
        "disappointing", "underwhelming", "unreliable", "buggy", "glitchy", "unstable",
        # Cost/Complexity
        "expensive", "overpriced", "costly", "complex", "complicated", "confusing",
        "difficult", "steep", "learning-curve", "cumbersome", "clunky", "bloated",
        # Performance
        "slow", "sluggish", "laggy", "delayed", "timeout", "downtime",
        # Missing
        "missing", "absent", "limited", "restricted", "locked", "paywall", "premium-only",
        # Negative sentiment
        "frustrating", "annoying", "terrible", "awful", "worst", "avoid", "regret",
    ]

    for desc in all_descriptions:
        words = desc.lower().split()
        for i, w in enumerate(words):
            w = w.strip(".,!?;:\"'()[]")
            if w in positive_words:
                word_scores["positive"][w] = word_scores["positive"].get(w, 0) + 1
            elif w in neutral_words:
                word_scores["neutral"][w] = word_scores["neutral"].get(w, 0) + 1
            elif w in negative_words:
                word_scores["negative"][w] = word_scores["negative"].get(w, 0) + 1

    brand_vault["word_association_graph"] = {
        "positive": sorted([{"word": k, "frequency": v} for k, v in word_scores["positive"].items()], key=lambda x: x["frequency"], reverse=True)[:10],
        "neutral": sorted([{"word": k, "frequency": v} for k, v in word_scores["neutral"].items()], key=lambda x: x["frequency"], reverse=True)[:10],
        "negative": sorted([{"word": k, "frequency": v} for k, v in word_scores["negative"].items()], key=lambda x: x["frequency"], reverse=True)[:5],
        "intended": [],
        "missing": [],
    }

    # Cross-engine consistency
    if by_engine:
        engine_narratives = {}
        for engine, texts in by_engine.items():
            avg_len = sum(len(t) for t in texts) / len(texts) if texts else 0
            engine_narratives[engine] = {
                "count": len(texts),
                "avg_length": round(avg_len, 1),
                "sentiment": _estimate_sentiment(texts),
            }
        brand_vault["platform_narratives"] = engine_narratives

        # Consistency score (simplified: lower std dev = more consistent)
        if len(engine_narratives) >= 2:
            sentiments = [e["sentiment"] for e in engine_narratives.values()]
            mean_s = sum(sentiments) / len(sentiments)
            var_s = sum((s - mean_s) ** 2 for s in sentiments) / len(sentiments)
            brand_vault["cross_engine_consistency_score"] = round(clamp(1.0 - var_s ** 0.5 / 50, 0, 1), 4)

    return brand_vault


def _estimate_sentiment(texts: List[str]) -> float:
    """Estimate sentiment 0-100 from text samples."""
    pos_words = ["great", "best", "excellent", "powerful", "leading", "innovative",
                 "reliable", "intuitive", "robust", "comprehensive", "flexible",
                 "trusted", "popular", "award-winning", "seamless", "efficient"]
    neg_words = ["limited", "expensive", "complex", "lacking", "poor", "difficult",
                 "slow", "unreliable", "buggy", "frustrating", "confusing",
                 "overpriced", "clunky", "missing", "terrible", "worst"]
    pos_signals = sum(1 for t in texts for w in pos_words if w in t.lower())
    neg_signals = sum(1 for t in texts for w in neg_words if w in t.lower())
    total = pos_signals + neg_signals
    if total == 0:
        return 50.0
    return round(clamp(50 + 25 * (pos_signals - neg_signals) / total, 0, 100), 1)


# ─── Narrative & Tone Analysis ──────────────────────────────────────────

def analyze_narrative(run_dir: Path, brand_name: str = "") -> Dict[str, Any]:
    """Analyze brand narrative framing and tone across AI engines."""
    entity_path = run_dir / "intermediate" / "entity_analysis.jsonl"
    brand_vault = analyze_brand_vault(run_dir, brand_name)

    narrative: Dict[str, Any] = {
        "schema_version": "4.0.0",
        "analyzed_at": utc_now_iso(),
        "framing": "unknown",
        "tone": "neutral",
        "language_patterns": [],
        "positioning_deviation": None,
        "competitor_narratives": {},
        "narrative_deviation_score": None,
    }

    # Determine framing — multi-dimensional analysis
    sentiment = 50
    platform_narratives = brand_vault.get("platform_narratives", {})
    if platform_narratives:
        sentiments = [en.get("sentiment", 50) for en in platform_narratives.values()]
        sentiment = sum(sentiments) / len(sentiments)

    # Read entity analysis for recommendation type data
    rec_counts = {"top_pick": 0, "strong_alternative": 0, "conditional": 0, "mentioned_only": 0, "discouraged": 0}
    if entity_path.exists():
        entities = read_jsonl(entity_path)
        for entry in entities:
            for entity in entry.get("entities", []):
                if entity.get("entity_type") == "target_brand" or entity.get("is_target_brand"):
                    rec_type = entity.get("recommendation_type", "")
                    if rec_type in rec_counts:
                        rec_counts[rec_type] += 1

    total_recs = sum(rec_counts.values())
    leader_signals = rec_counts.get("top_pick", 0)
    challenger_signals = rec_counts.get("strong_alternative", 0)

    # Multi-dimensional framing decision
    if sentiment >= 75 and leader_signals > total_recs * 0.3:
        narrative["framing"] = "leader"
        narrative["tone"] = "positive"
    elif sentiment >= 60 and (challenger_signals + leader_signals) > total_recs * 0.3:
        narrative["framing"] = "challenger"
        narrative["tone"] = "positive"
    elif sentiment >= 45 or rec_counts.get("conditional", 0) > total_recs * 0.3:
        narrative["framing"] = "specialist"
        narrative["tone"] = "neutral"
    elif sentiment < 35 or rec_counts.get("discouraged", 0) > total_recs * 0.2:
        narrative["framing"] = "niche_player"
        narrative["tone"] = "mixed"
    else:
        narrative["framing"] = "specialist"
        narrative["tone"] = "neutral"

    narrative["recommendation_distribution"] = rec_counts

    # Language patterns from word associations
    word_graph = brand_vault.get("word_association_graph", {})
    positive_words = [w["word"] for w in word_graph.get("positive", [])[:5]]
    if positive_words:
        narrative["language_patterns"].append(f"AI models positively associate brand with: {', '.join(positive_words)}")

    negative_words = [w["word"] for w in word_graph.get("negative", [])[:3]]
    if negative_words:
        narrative["language_patterns"].append(f"AI models negatively associate brand with: {', '.join(negative_words)}")

    # Positioning deviation
    if entity_path.exists():
        entities = read_jsonl(entity_path)
        all_entities: List[str] = []
        for entry in entities:
            for entity in entry.get("entities", []):
                if not entity.get("is_target_brand", False):
                    all_entities.append(entity.get("entity_id", entity.get("name", "")))

        narrative["competitor_narratives"] = {
            "top_co_mentioned": sorted(set(all_entities), key=lambda x: all_entities.count(x), reverse=True)[:5],
        }

    return narrative


# ─── Multi-Model Coverage Heatmap ───────────────────────────────────────

def build_coverage_heatmap(run_dir: Path) -> Dict[str, Any]:
    """Build per-platform brand coverage heatmap."""
    engine_responses_path = run_dir / "raw" / "engine_responses.jsonl"
    entity_path = run_dir / "intermediate" / "entity_analysis.jsonl"

    heatmap: Dict[str, Any] = {
        "schema_version": "4.0.0",
        "analyzed_at": utc_now_iso(),
        "by_platform": {},
        "favorability_ranking": [],
        "coverage_gaps": {},
        "recommended_strategies": [],
    }

    if not engine_responses_path.exists() and not entity_path.exists():
        return heatmap

    # Gather per-platform data
    platform_data: Dict[str, Dict[str, Any]] = {}

    if engine_responses_path.exists():
        responses = read_jsonl(engine_responses_path)
        for r in responses:
            engine = r.get("engine", "unknown")
            if engine not in platform_data:
                platform_data[engine] = {"total": 0, "success": 0, "brand_mentioned": 0, "word_count": []}
            platform_data[engine]["total"] += 1
            if r.get("status") == "success":
                platform_data[engine]["success"] += 1
                text = r.get("answer_text", "")
                platform_data[engine]["word_count"].append(len(text))

    if entity_path.exists():
        entities = read_jsonl(entity_path)
        for entry in entities:
            engine = entry.get("engine", "unknown")
            if engine not in platform_data:
                platform_data[engine] = {"total": 0, "success": 0, "brand_mentioned": 0, "word_count": []}
            platform_data[engine]["total"] += 1
            for entity in entry.get("entities", []):
                if entity.get("is_target_brand", False):
                    platform_data[engine]["brand_mentioned"] += 1

    # Compute per-platform metrics
    for engine, data in platform_data.items():
        mention_rate = round(data["brand_mentioned"] / data["total"], 4) if data["total"] > 0 else 0
        avg_length = round(sum(data["word_count"]) / len(data["word_count"]), 1) if data["word_count"] else 0
        success_rate = round(data["success"] / data["total"], 4) if data["total"] > 0 else 0

        heatmap["by_platform"][engine] = {
            "total_queries": data["total"],
            "mention_rate": mention_rate,
            "success_rate": success_rate,
            "avg_response_length": avg_length,
            "favorability": _compute_favorability(mention_rate, avg_length),
        }

    # Favorability ranking
    if heatmap["by_platform"]:
        ranking = sorted(heatmap["by_platform"].items(), key=lambda x: x[1]["favorability"], reverse=True)
        heatmap["favorability_ranking"] = [{"platform": p, "score": d["favorability"], "mention_rate": d["mention_rate"]} for p, d in ranking]

        # Platform-specific strategies
        strategies = []
        for platform, score in ranking[:3]:
            strategies.append(_platform_strategy(platform))
        heatmap["recommended_strategies"] = strategies[:3]

    return heatmap


def _compute_favorability(mention_rate: float, avg_length: float) -> float:
    """Compute platform favorability score 0-100."""
    base = mention_rate * 100
    length_bonus = min(10, avg_length / 100)
    return round(clamp(base + length_bonus, 0, 100), 1)


def _platform_strategy(platform: str) -> Dict[str, str]:
    strategies = {
        "chatgpt": {
            "platform": "ChatGPT",
            "strategy": "Create authoritative content with story-driven narratives. ChatGPT prefers well-structured brand stories with third-party validation.",
        },
        "perplexity": {
            "platform": "Perplexity",
            "strategy": "Focus on citation-dense content with academic and technical depth. Perplexity favors well-sourced, factual responses.",
        },
        "claude": {
            "platform": "Claude",
            "strategy": "Develop structured analytical content with clear headings and logical flow. Claude prefers depth and structure.",
        },
        "gemini": {
            "platform": "Gemini",
            "strategy": "Optimize Google Business Profile and Google Reviews. Gemini heavily favors Google ecosystem content.",
        },
        "grok": {
            "platform": "Grok",
            "strategy": "Build real-time social proof on X/Twitter. Grok prioritizes current social signals and viral content.",
        },
    }
    return strategies.get(platform, {"platform": platform, "strategy": "Standard GEO optimization applies."})


# ─── Agentic GEO Engine ─────────────────────────────────────────────────

def run_agentic_geo(run_dir: Path, auto_mode: bool = False) -> Dict[str, Any]:
    """Simulate Agentic GEO optimization engine."""
    cycle_id = utc_stamp()

    engine: Dict[str, Any] = {
        "schema_version": "4.0.0",
        "engine_status": "running" if auto_mode else "idle",
        "cycle_id": cycle_id,
        "started_at": utc_now_iso(),
        "last_optimization": None,
        "optimization_cycle_count": 0,
        "total_actions_executed": 0,
        "active_agents": [],
        "agent_log": [],
        "next_scheduled_run": None,
    }

    # Read real data for meaningful diagnostics
    gaps_path = run_dir / "intermediate" / "metrics.json"
    opps_path = run_dir / "intermediate" / "opportunities.json"
    issues = []
    real_opps = []

    if gaps_path.exists():
        metrics = read_json(gaps_path)
        geo = metrics.get("geo_score", {})
        score = geo.get("score", 0)
        mention = metrics.get("mention_rate", {}).get("rate")
        rec = metrics.get("recommendation_rate", {}).get("rate")

        if score < 86:
            issues.append(f"GEO score {score}/100 (below excellent threshold)")
        if mention is not None and mention < 0.5:
            issues.append(f"Mention rate {mention:.0%} (below 50%)")
        if rec is not None and rec < 0.4:
            issues.append(f"Recommendation rate {rec:.0%} (below 40%)")

    if opps_path.exists():
        opps = read_json(opps_path)
        real_opps = opps if isinstance(opps, list) else opps.get("opportunities", [])
        for opp in real_opps[:3]:
            issues.append(f"Opportunity: {opp.get('title', opp.get('description', 'unknown'))[:80]}")

    engine["data_status"] = "simulated_with_real_metrics" if issues else "simulated_no_data"

    if not auto_mode:
        # Dry run: simulate what the engine would do
        gaps_path = run_dir / "intermediate" / "metrics.json"
        issues = []
        if gaps_path.exists():
            metrics = read_json(gaps_path)
            geo = metrics.get("geo_score", {})
            score = geo.get("score", 0)

            if score < 86:
                issues.append(f"GEO score is {score}/100 (below excellent threshold of 86)")

        engine["active_agents"] = [
            {"name": "Monitor Agent", "status": "active", "last_check": utc_now_iso(), "interval_hours": 24},
            {"name": "Diagnosis Agent", "status": "idle", "last_check": None, "interval_hours": 24},
            {"name": "Optimization Agent", "status": "idle", "last_check": None, "interval_hours": 168},
            {"name": "Validation Agent", "status": "idle", "last_check": None, "interval_hours": 168},
            {"name": "Reporting Agent", "status": "idle", "last_check": None, "interval_hours": 720},
        ]
        engine["agent_log"] = [{
            "ts": utc_now_iso(),
            "agent": "Monitor Agent",
            "action": "dry_run_initiated",
            "detail": "Simulation mode: no actions executed",
        }]

        if issues:
            for issue in issues:
                engine["agent_log"].append({
                    "ts": utc_now_iso(),
                    "agent": "Diagnosis Agent",
                    "action": "issue_detected",
                    "detail": issue,
                })
    else:
        # Auto mode: simulate a full optimization cycle
        engine["optimization_cycle_count"] = 1
        engine["total_actions_executed"] = 3
        engine["last_optimization"] = utc_now_iso()
        engine["next_scheduled_run"] = _next_run_time()
        engine["status"] = "running"

        engine["active_agents"] = [
            {"name": "Monitor Agent", "status": "active", "last_check": utc_now_iso(), "interval_hours": 24},
            {"name": "Diagnosis Agent", "status": "active", "last_check": utc_now_iso(), "interval_hours": 24},
            {"name": "Optimization Agent", "status": "active", "last_check": utc_now_iso(), "interval_hours": 168},
            {"name": "Validation Agent", "status": "pending", "last_check": None, "interval_hours": 168},
            {"name": "Reporting Agent", "status": "pending", "last_check": None, "interval_hours": 720},
        ]
        engine["agent_log"] = [
            {"ts": utc_now_iso(), "agent": "Monitor Agent", "action": "visibility_checked",
             "detail": f"Found {len(issues)} issues to address" if issues else "No critical issues detected"},
            {"ts": utc_now_iso(), "agent": "Diagnosis Agent", "action": "gaps_analyzed",
             "detail": f"{len(real_opps)} opportunities identified from audit data" if real_opps else "No opportunities data available"},
            {"ts": utc_now_iso(), "agent": "Optimization Agent", "action": "actions_prioritized",
             "detail": "Optimization cycle completed"},
        ]

    return engine


def _next_run_time() -> str:
    from datetime import datetime, timedelta, timezone
    return (datetime.now(timezone.utc) + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")


# ─── Hybrid GEO+SEO Metrics ─────────────────────────────────────────────

def compute_hybrid_metrics(
    run_dir: Path,
    brand: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compute Unified Brand Score (UBS) combining GEO + SEO + Brand metrics."""
    metrics_path = run_dir / "intermediate" / "metrics.json"

    geo_score = 50.0
    seo_score = 50.0
    brand_score = 50.0

    if metrics_path.exists():
        metrics = read_json(metrics_path)
        geo = metrics.get("geo_score", {})
        geo_score = geo.get("score", 50)

    # SEO score (placeholder — real integration needs GSC data)
    brand = brand or {}
    seo_signals = 0
    seo_total = 0
    if brand.get("website"):
        seo_total += 1
        if brand.get("site_readiness_score", 0) > 50:
            seo_signals += 1
    if brand.get("competitors"):
        seo_total += 1
        seo_signals += 1
    seo_score = round(seo_signals / seo_total * 100, 1) if seo_total > 0 else 50

    # Brand score from entity data
    entity_path = run_dir / "intermediate" / "entity_analysis.jsonl"
    if entity_path.exists():
        entities = read_jsonl(entity_path)
        brand_mentions = sum(1 for e in entities for en in e.get("entities", []) if en.get("is_target_brand"))
        total_mentions = sum(len(e.get("entities", [])) for e in entities)
        brand_score = round(brand_mentions / total_mentions * 100, 1) if total_mentions > 0 else 50

    ubs = round(0.4 * geo_score + 0.3 * seo_score + 0.3 * brand_score, 1)

    return {
        "schema_version": "4.0.0",
        "analyzed_at": utc_now_iso(),
        "ubs": ubs,
        "geo_score": geo_score,
        "seo_score": seo_score,
        "brand_score": brand_score,
        "breakdown": {
            "geo_contribution": round(0.4 * geo_score, 1),
            "seo_contribution": round(0.3 * seo_score, 1),
            "brand_contribution": round(0.3 * brand_score, 1),
        },
        "weights": {"geo": 0.4, "seo": 0.3, "brand": 0.3},
    }


# ─── Full Audit ─────────────────────────────────────────────────────────

def run_full_ultimate_audit(run_dir: Path, brand_name: str = "") -> Dict[str, Any]:
    """Run ALL ultimate GEO capabilities and produce a combined report."""
    audit: Dict[str, Any] = {
        "schema_version": "4.0.0",
        "version": "4.0.0",
        "audited_at": utc_now_iso(),
    }

    audit["brand_vault"] = analyze_brand_vault(run_dir, brand_name)
    audit["narrative_analysis"] = analyze_narrative(run_dir, brand_name)
    audit["coverage_heatmap"] = build_coverage_heatmap(run_dir)
    audit["agentic_engine"] = run_agentic_geo(run_dir)

    brand_path = run_dir / "input" / "brand.json"
    brand = read_json(brand_path) if brand_path.exists() else {}
    audit["hybrid_metrics"] = compute_hybrid_metrics(run_dir, brand)

    # Save
    output_path = run_dir / "intermediate" / "ultimate_geo_audit.json"
    write_json(output_path, audit)

    return audit


# ─── CLI ────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="Ultimate GEO")
    sub = p.add_subparsers(dest="command")

    bv = sub.add_parser("brand-vault", help="Agentic Brand Vault")
    bv.add_argument("--run-dir", required=True)
    bv.add_argument("--brand", default="")

    nr = sub.add_parser("narrative", help="Narrative & Tone Analysis")
    nr.add_argument("--run-dir", required=True)
    nr.add_argument("--brand", default="")

    hm = sub.add_parser("heatmap", help="Multi-Model Coverage Heatmap")
    hm.add_argument("--run-dir", required=True)

    ag = sub.add_parser("agentic", help="Agentic GEO Engine")
    ag.add_argument("--run-dir", required=True)
    ag.add_argument("--auto", action="store_true", help="Enable auto mode")

    hy = sub.add_parser("hybrid", help="Hybrid GEO+SEO Metrics")
    hy.add_argument("--run-dir", required=True)

    fa = sub.add_parser("full-audit", help="Complete Ultimate Audit")
    fa.add_argument("--run-dir", required=True)
    fa.add_argument("--brand", default="")

    args = p.parse_args()

    if args.command == "brand-vault":
        result = analyze_brand_vault(Path(args.run_dir), args.brand)
        print_json(result)

    elif args.command == "narrative":
        result = analyze_narrative(Path(args.run_dir), args.brand)
        print_json(result)

    elif args.command == "heatmap":
        result = build_coverage_heatmap(Path(args.run_dir))
        print_json(result)

    elif args.command == "agentic":
        result = run_agentic_geo(Path(args.run_dir), args.auto)
        print_json(result)

    elif args.command == "hybrid":
        result = compute_hybrid_metrics(Path(args.run_dir))
        print_json(result)

    elif args.command == "full-audit":
        result = run_full_ultimate_audit(Path(args.run_dir), args.brand)
        summary = {
            "status": "complete",
            "ubs": result.get("hybrid_metrics", {}).get("ubs"),
            "cross_engine_consistency": result.get("brand_vault", {}).get("cross_engine_consistency_score"),
            "framing": result.get("narrative_analysis", {}).get("framing"),
            "top_platform": result.get("coverage_heatmap", {}).get("favorability_ranking", [{}])[0].get("platform") if result.get("coverage_heatmap", {}).get("favorability_ranking") else None,
            "agentic_status": result.get("agentic_engine", {}).get("engine_status"),
        }
        print_json(summary)

    else:
        p.print_help()

if __name__ == "__main__":
    main()