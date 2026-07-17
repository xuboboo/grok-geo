#!/usr/bin/env python3
"""Unit tests: URL normalize, entity normalize, metrics, input validation."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skill" / "grok-geo" / "scripts"
EXAMPLES = ROOT / "skill" / "grok-geo" / "examples"
sys.path.insert(0, str(SCRIPTS))

from calculate_metrics import calculate_metrics  # noqa: E402
from geo_common import (  # noqa: E402
    RECOMMENDATION_TYPE_SCORES,
    SEARCH_TEMPLATE_TYPES,
    STANDARD_TEMPLATE_DISTRIBUTION,
    QUICK_TEMPLATE_DISTRIBUTION,
    FUNNEL_STAGES,
    ATTRIBUTE_CATEGORIES,
    ATTRIBUTE_KEYWORDS,
    ALERT_THRESHOLDS,
    INTENT_TO_FUNNEL,
    PUBLISHER_CATEGORIES,
    JOURNEY_STAGES,
    FUNNEL_TO_JOURNEY,
    OPTIMIZATION_ACTION_CATEGORIES,
    PUBLISHER_DOMAIN_PATTERNS,
    aggregate_platform_citations,
    ai_perception_score,
    citability_score,
    freshness_score,
    geo_score,
    negative_signal_score,
    normalize_entity_name,
    position_score,
    rag_readiness,
    rate_with_ci,
    trust_stack_score,
    wilson_ci,
)

from extract_search_signals import (  # noqa: E402
    classify_citation_source,
    contains_brand,
    detect_list_structure,
    detect_table_structure,
    extract_domain,
    extract_signals,
    find_brand_position,
)

from score_search_result import (  # noqa: E402
    create_snapshot,
    recommend_retry_strategy,
    score_response_quality,
)

from detect_drift import detect_single_drift  # noqa: E402
from normalize_urls import normalize_url  # noqa: E402
from rank_opportunities import rank_opportunities, score_opportunity  # noqa: E402
from validate_input import normalize_input, scan_sensitive  # noqa: E402
from validate_questions import validate_questions  # noqa: E402
from chain_runs import compute_run_deltas  # noqa: E402
from generate_improvement_plan import generate_plan  # noqa: E402
from classify_funnel_stage import classify_question_stage  # noqa: E402
from extract_attribute_analysis import detect_attributes  # noqa: E402
from detect_visibility_alerts import detect_alerts  # noqa: E402
from map_publisher_influence import compute_publisher_influence  # noqa: E402
from compute_journey_metrics import compute_stage_metrics  # noqa: E402
from generate_optimization_actions import score_action  # noqa: E402


class TestUrlNormalize(unittest.TestCase):
    def test_strip_utm_and_fragment(self):
        r = normalize_url("https://Example.com/path/?utm_source=x&id=1#frag")
        self.assertEqual(r["canonical_url"], "https://example.com/path?id=1")
        self.assertEqual(r["domain"], "example.com")
        self.assertTrue(r["url_sha256"])

    def test_default_port(self):
        r = normalize_url("https://example.com:443/a/")
        self.assertEqual(r["canonical_url"], "https://example.com/a")

    def test_tracking_params(self):
        r = normalize_url("https://x.com/a?gclid=1&fbclid=2&keep=yes")
        self.assertIn("keep=yes", r["canonical_url"])
        self.assertNotIn("gclid", r["canonical_url"])


class TestEntityNormalize(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(normalize_entity_name("示例科技有限公司"), "示例科技")
        self.assertEqual(normalize_entity_name("Example Inc."), "example")
        self.assertEqual(normalize_entity_name("  Foo   Bar™ "), "foo bar")


class TestMetrics(unittest.TestCase):
    def test_fixture_rates(self):
        questions = [
            {"id": f"q-{i}", "intent": "recommendation" if i < 5 else "use_case", "business_value": 100}
            for i in range(10)
        ]
        entities = {}
        for i in range(10):
            mentioned = i < 4
            rec = i < 2
            entities[f"q-{i}"] = {
                "question_id": f"q-{i}",
                "entities": [
                    {
                        "entity_id": "target-brand",
                        "entity_type": "target_brand",
                        "mentioned": mentioned,
                        "mention_type": "recommended" if rec else ("positive_mention" if mentioned else None),
                        "recommendation_rank": 1 if rec else None,
                    }
                ],
            }
        citations = [{"question_id": "q-0", "source_type": "owned", "supports_target_brand": False}]
        metrics = calculate_metrics(questions, entities, citations, [], valid_question_ids=[f"q-{i}" for i in range(10)])
        self.assertAlmostEqual(metrics["mention_rate"]["rate"], 0.4, places=9)
        self.assertAlmostEqual(metrics["recommendation_rate"]["rate"], 0.4, places=9)
        self.assertAlmostEqual(metrics["owned_citation_rate"]["rate"], 0.1, places=9)

    def test_position_and_wilson(self):
        self.assertEqual(position_score("recommended", 1), 1.0)
        self.assertEqual(position_score("not_recommended", None), -0.3)
        ci = wilson_ci(4, 10)
        self.assertIsNotNone(ci)
        self.assertLessEqual(ci["low"], 0.4)
        self.assertGreaterEqual(ci["high"], 0.4)

    def test_accuracy(self):
        claims = [
            {"verification_status": "correct"},
            {"verification_status": "partially_correct"},
            {"verification_status": "incorrect"},
            {"verification_status": "unverifiable"},
        ]
        metrics = calculate_metrics(
            [{"id": "q-1", "intent": "brand_fact", "business_value": 50}],
            {"q-1": {"question_id": "q-1", "entities": []}},
            [],
            claims,
            valid_question_ids=["q-1"],
        )
        # (1 + 0.5) / 3
        self.assertAlmostEqual(metrics["accuracy_score"]["score"], 1.5 / 3, places=9)

    def test_opportunity_score(self):
        total = score_opportunity(
            {
                "business_value": 90,
                "competitive_gap": 85,
                "brand_absence": 100,
                "executability": 80,
                "evidence_readiness": 60,
                "risk_penalty": 0,
            }
        )
        self.assertAlmostEqual(total, 86.25, places=9)
        ranked = rank_opportunities(
            [
                {"title": "a", "opportunity_type": "x", "recommended_asset": "y", "scores": {"business_value": 10, "competitive_gap": 10, "brand_absence": 10, "executability": 10, "evidence_readiness": 10, "risk_penalty": 0}},
                {"title": "b", "opportunity_type": "z", "recommended_asset": "w", "scores": {"business_value": 90, "competitive_gap": 90, "brand_absence": 90, "executability": 90, "evidence_readiness": 90, "risk_penalty": 0}},
            ]
            * 6,
            max_items=10,
        )
        self.assertLessEqual(len(ranked), 10)


class TestInputValidation(unittest.TestCase):
    def test_minimal(self):
        data = json.loads((EXAMPLES / "input.minimal.json").read_text(encoding="utf-8"))
        out = normalize_input(data)
        self.assertEqual(out["mode"], "standard")
        self.assertEqual(out["options"]["question_count"], 30)

    def test_conflict(self):
        data = {
            "brand_name": "Foo",
            "website": "https://foo.com",
            "industry": "x",
            "target_customer": "y",
            "competitors": [{"name": "Foo"}],
        }
        with self.assertRaises(ValueError):
            normalize_input(data)

    def test_sensitive(self):
        hits = scan_sensitive({"x": "sk-abcdefghijklmnopqrstuvwxyz123456"})
        self.assertTrue(hits)

    def test_questions_ratio(self):
        qs = json.loads((EXAMPLES / "questions.offline.json").read_text(encoding="utf-8"))["questions"]
        result = validate_questions(qs, "示例科技", ["示例项目"])
        self.assertTrue(result["ok"], result["errors"])


class TestGeoScore(unittest.TestCase):
    """v1.1 — Tests for composite GEO score and new metric fields."""

    def test_perfect_score(self):
        result = geo_score(100.0, 1.0, 1.0, 1.0)
        self.assertEqual(result["band"], "excellent")
        self.assertGreaterEqual(result["score"], 86)

    def test_zero_score(self):
        result = geo_score(0.0, 0.0, 0.0, 0.0)
        self.assertEqual(result["band"], "critical")
        self.assertEqual(result["score"], 0.0)

    def test_mid_score(self):
        result = geo_score(50.0, 0.5, 0.4, 0.3)
        self.assertIn(result["band"], ("foundation", "good"))
        self.assertGreater(result["score"], 0)
        self.assertLess(result["score"], 100)

    def test_weights_sum_to_one(self):
        w = result = geo_score(50, 0.5, 0.5, 0.5)["weights"]
        self.assertAlmostEqual(sum(w.values()), 1.0, places=9)

    def test_breakdown_populated(self):
        result = geo_score(75.0, 0.8, 0.6, 0.4)
        self.assertIn("visibility", result["breakdown"])
        self.assertIn("mention_rate", result["breakdown"])
        self.assertIn("recommendation_rate", result["breakdown"])
        self.assertIn("owned_citation_rate", result["breakdown"])

    def test_recommendation_type_scores(self):
        self.assertEqual(RECOMMENDATION_TYPE_SCORES["top_pick"], 1.0)
        self.assertEqual(RECOMMENDATION_TYPE_SCORES["discouraged"], 0.0)
        self.assertGreater(
            RECOMMENDATION_TYPE_SCORES["strong_alternative"],
            RECOMMENDATION_TYPE_SCORES["conditional"],
        )

    def test_metrics_includes_v11_fields(self):
        """calculate_metrics output contains v1.1 keys."""
        questions = [{"id": "q-1", "intent": "recommendation", "business_value": 100}]
        entities = {
            "q-1": {
                "question_id": "q-1",
                "entities": [
                    {
                        "entity_id": "target-brand",
                        "entity_type": "target_brand",
                        "mentioned": True,
                        "mention_type": "recommended",
                        "recommendation_rank": 1,
                        "recommendation_type": "top_pick",
                        "sentiment_score": 85,
                        "competitor_co_mentions": ["comp-a"],
                    },
                    {
                        "entity_id": "comp-a",
                        "entity_type": "competitor",
                        "mentioned": True,
                        "mention_type": "recommended",
                        "recommendation_rank": 2,
                    },
                ],
            }
        }
        metrics = calculate_metrics(questions, entities, [], [], valid_question_ids=["q-1"])
        # v1.1 keys exist
        self.assertIn("geo_score", metrics)
        self.assertIn("sentiment_index", metrics)
        self.assertIn("recommendation_type_distribution", metrics)
        self.assertIn("citation_share_by_competitor", metrics)
        self.assertIn("competitor_co_mentions", metrics)
        # geo_score structure
        self.assertIn("score", metrics["geo_score"])
        self.assertIn("band", metrics["geo_score"])
        self.assertIn("breakdown", metrics["geo_score"])
        # sentiment
        self.assertEqual(metrics["sentiment_index"]["score"], 85.0)
        self.assertEqual(metrics["sentiment_index"]["sample_size"], 1)
        # recommendation_type_distribution
        self.assertEqual(metrics["recommendation_type_distribution"]["top_pick"], 1)
        # competitor_co_mentions
        self.assertEqual(metrics["competitor_co_mentions"]["comp-a"], 1)


class TestFreshnessScore(unittest.TestCase):
    """v1.2 — Tests for content freshness scoring."""

    def test_no_decay(self):
        result = freshness_score([])
        self.assertEqual(result["score"], 100.0)
        self.assertEqual(result["band"], "fresh")
        self.assertEqual(result["decay_count"], 0)

    def test_high_temporal_decay(self):
        signals = [{"pattern": "temporal", "severity": "high", "evidence": "old"}]
        result = freshness_score(signals)
        self.assertEqual(result["total_deduction"], 30)
        self.assertEqual(result["score"], 70.0)
        self.assertEqual(result["band"], "aging")

    def test_multiple_decay_signals(self):
        signals = [
            {"pattern": "temporal", "severity": "high"},
            {"pattern": "statistical", "severity": "medium"},
            {"pattern": "price", "severity": "low"},
        ]
        result = freshness_score(signals)
        # 30 + 25*0.6 + 10*0.3 = 30 + 15 + 3 = 48
        self.assertEqual(result["total_deduction"], 48)
        self.assertEqual(result["score"], 52.0)
        self.assertEqual(result["band"], "stale")

    def test_rotting(self):
        signals = [
            {"pattern": "temporal", "severity": "high"},
            {"pattern": "statistical", "severity": "high"},
            {"pattern": "version", "severity": "high"},
            {"pattern": "event", "severity": "high"},
            {"pattern": "price", "severity": "high"},
        ]
        result = freshness_score(signals)
        # 30+25+20+15+10 = 100
        self.assertEqual(result["score"], 0.0)
        self.assertEqual(result["band"], "rotting")


class TestRagReadiness(unittest.TestCase):
    """v1.2 — Tests for RAG chunk readiness scoring."""

    def test_perfect(self):
        dims = {k: {"score": 100} for k in [
            "paragraph_structure", "heading_hierarchy", "definition_openings",
            "self_containment", "anchor_sentences", "structured_data",
        ]}
        result = rag_readiness(dims)
        self.assertEqual(result["score"], 100.0)
        self.assertEqual(result["band"], "rag_ready")

    def test_zero(self):
        dims = {k: {"score": 0, "issues": ["missing"]} for k in [
            "paragraph_structure", "heading_hierarchy", "definition_openings",
            "self_containment", "anchor_sentences", "structured_data",
        ]}
        result = rag_readiness(dims)
        self.assertEqual(result["score"], 0.0)
        self.assertEqual(result["band"], "not_ready")

    def test_moderate(self):
        dims = {
            "paragraph_structure": {"score": 80},
            "heading_hierarchy": {"score": 90},
            "definition_openings": {"score": 50},
            "self_containment": {"score": 60},
            "anchor_sentences": {"score": 40},
            "structured_data": {"score": 70},
        }
        result = rag_readiness(dims)
        # 80*0.25 + 90*0.20 + 50*0.15 + 60*0.20 + 40*0.10 + 70*0.10
        # = 20 + 18 + 7.5 + 12 + 4 + 7 = 68.5
        self.assertAlmostEqual(result["score"], 68.5, places=1)
        self.assertEqual(result["band"], "good")

    def test_missing_dimension_treated_as_zero(self):
        dims = {"paragraph_structure": {"score": 100}}
        result = rag_readiness(dims)
        self.assertLess(result["score"], 50)


class TestPlatformCitationMap(unittest.TestCase):
    """v1.2 — Tests for cross-platform citation aggregation."""

    def test_basic_aggregation(self):
        results = [
            {"question_id": "q-1", "platform": "chatgpt", "brand_mentioned": True, "brand_cited": False,
             "citations": [{"domain": "example.com"}, {"domain": "news.com"}]},
            {"question_id": "q-1", "platform": "perplexity", "brand_mentioned": True, "brand_cited": True,
             "citations": [{"domain": "example.com"}]},
            {"question_id": "q-2", "platform": "chatgpt", "brand_mentioned": False, "brand_cited": False,
             "citations": [{"domain": "other.com"}]},
            {"question_id": "q-2", "platform": "perplexity", "brand_mentioned": True, "brand_cited": False,
             "citations": [{"domain": "example.com"}]},
        ]
        agg = aggregate_platform_citations(results)
        # q-1: both platforms mention → cross_platform; q-2: only perplexity → not cross
        self.assertEqual(agg["cross_platform_visibility_score"], 0.5)
        self.assertIn("chatgpt", agg["platform_mention_rates"])
        self.assertIn("perplexity", agg["platform_mention_rates"])
        # perplexity mention rate: 2/2 = 1.0
        self.assertEqual(agg["platform_mention_rates"]["perplexity"], 1.0)
        # platform advantage
        self.assertEqual(agg["platform_advantage_map"]["best_platform"], "perplexity")
        # source overlap: example.com on 2 platforms
        self.assertGreater(agg["cross_platform_domains"], 0)

    def test_empty_results(self):
        agg = aggregate_platform_citations([])
        self.assertIsNone(agg["cross_platform_visibility_score"])


class TestCitabilityScore(unittest.TestCase):
    """v1.3 — Tests for citability scoring."""

    def test_perfect(self):
        methods = {f"m{i}": {"score": 5, "max": 5} for i in range(20)}
        result = citability_score(methods)
        self.assertEqual(result["score"], 100.0)
        self.assertEqual(result["band"], "highly_citable")

    def test_zero(self):
        methods = {f"m{i}": {"score": 0, "max": 5} for i in range(20)}
        result = citability_score(methods)
        self.assertEqual(result["score"], 0.0)
        self.assertEqual(result["band"], "not_citable")

    def test_partial(self):
        methods = {
            "cite_sources": {"score": 7, "max": 8, "evidence": "3 links"},
            "statistics": {"score": 3, "max": 7, "evidence": "some numbers"},
            "quotation": {"score": 0, "max": 6},
        }
        result = citability_score(methods)
        self.assertGreater(result["score"], 0)
        self.assertLess(result["score"], 100)
        self.assertEqual(result["total_points"], 10.0)
        self.assertEqual(result["max_points"], 21.0)

    def test_strengths_and_weaknesses(self):
        methods = {
            "cite_sources": {"score": 8, "max": 8},
            "statistics": {"score": 7, "max": 7},
            "quotation": {"score": 0, "max": 6},
        }
        result = citability_score(methods)
        self.assertEqual(len(result["top_strengths"]), 2)
        self.assertTrue(any(w["method"] == "quotation" for w in result["top_weaknesses"]))


class TestNegativeSignalScore(unittest.TestCase):
    """v1.3 — Tests for negative signal scoring."""

    def test_no_signals(self):
        result = negative_signal_score([])
        self.assertEqual(result["score"], 100.0)
        self.assertEqual(result["band"], "clean")

    def test_critical_signal(self):
        signals = [{"type": "login_wall", "severity": "critical", "evidence": "requires login"}]
        result = negative_signal_score(signals)
        self.assertEqual(result["score"], 85.0)
        self.assertEqual(result["band"], "minor_issues")

    def test_multiple_signals(self):
        signals = [
            {"type": "cta_overload", "severity": "high"},
            {"type": "thin_content", "severity": "high"},
            {"type": "missing_author", "severity": "medium"},
            {"type": "missing_trust", "severity": "low"},
        ]
        result = negative_signal_score(signals)
        # 10 + 10 + 5 + 2 = 27
        self.assertEqual(result["total_deduction"], 27)
        self.assertEqual(result["score"], 73.0)
        self.assertEqual(result["band"], "minor_issues")

    def test_severe(self):
        signals = [
            {"type": "login_wall", "severity": "critical"},
            {"type": "captcha", "severity": "critical"},
            {"type": "keyword_stuffing", "severity": "high"},
            {"type": "cta_overload", "severity": "high"},
            {"type": "thin_content", "severity": "high"},
            {"type": "missing_author", "severity": "medium"},
        ]
        result = negative_signal_score(signals)
        # 15+15+10+10+10+5 = 65
        self.assertEqual(result["score"], 35.0)
        self.assertEqual(result["band"], "severe")


class TestTrustStackScore(unittest.TestCase):
    """v1.3 — Tests for trust stack scoring."""

    def test_grade_a(self):
        layers = {
            "technical": {"score": 95},
            "identity": {"score": 92},
            "social": {"score": 90},
            "academic": {"score": 88},
            "consistency": {"score": 91},
        }
        result = trust_stack_score(layers)
        self.assertEqual(result["grade"], "A")
        self.assertGreaterEqual(result["score"], 90)

    def test_grade_f(self):
        layers = {
            "technical": {"score": 20},
            "identity": {"score": 10},
            "social": {"score": 15},
            "academic": {"score": 5},
            "consistency": {"score": 25},
        }
        result = trust_stack_score(layers)
        self.assertEqual(result["grade"], "F")

    def test_weakest_and_strongest(self):
        layers = {
            "technical": {"score": 90},
            "identity": {"score": 30},
            "social": {"score": 70},
            "academic": {"score": 80},
            "consistency": {"score": 60},
        }
        result = trust_stack_score(layers)
        self.assertEqual(result["weakest_layer"], "identity")
        self.assertEqual(result["strongest_layer"], "technical")

    def test_missing_layer_treated_as_zero(self):
        layers = {"technical": {"score": 100}}
        result = trust_stack_score(layers)
        self.assertEqual(result["grade"], "F")


class TestAiPerceptionScore(unittest.TestCase):
    """v1.3 — Tests for AI perception scoring."""

    def test_excellent(self):
        dims = {
            "positioning_clarity": 1.0,
            "price_transparency": 0.9,
            "claim_consistency": 0.95,
            "sentiment_strength": 1.0,
            "competitor_framing": 0.85,
        }
        result = ai_perception_score(dims)
        self.assertEqual(result["band"], "excellent")
        self.assertGreaterEqual(result["score"], 86)

    def test_negative(self):
        dims = {
            "positioning_clarity": 0.1,
            "price_transparency": 0.0,
            "claim_consistency": 0.1,
            "sentiment_strength": 0.0,
            "competitor_framing": 0.0,
        }
        result = ai_perception_score(dims)
        self.assertEqual(result["band"], "negative")

    def test_mixed(self):
        dims = {
            "positioning_clarity": 0.6,
            "price_transparency": 0.5,
            "claim_consistency": 0.4,
            "sentiment_strength": 0.5,
            "competitor_framing": 0.3,
        }
        result = ai_perception_score(dims)
        self.assertEqual(result["band"], "mixed")

    def test_breakdown_populated(self):
        dims = {"positioning_clarity": 0.8, "sentiment_strength": 0.7}
        result = ai_perception_score(dims)
        self.assertIn("positioning_clarity", result["breakdown"])
        self.assertIn("sentiment_strength", result["breakdown"])


class TestSearchSignalExtraction(unittest.TestCase):
    """v1.4 — Tests for search signal extraction."""

    def test_contains_brand(self):
        result = contains_brand("示例科技是最佳选择", "示例科技", ["示例项目"])
        self.assertTrue(result["mentioned"])
        self.assertGreaterEqual(result["match_count"], 1)

    def test_brand_not_mentioned(self):
        result = contains_brand("竞争品牌A是最佳选择", "示例科技")
        self.assertFalse(result["mentioned"])

    def test_extract_domain(self):
        self.assertEqual(extract_domain("https://Example.com/path?x=1"), "example.com")
        self.assertEqual(extract_domain("https://www.test.com"), "test.com")

    def test_classify_citation_owned(self):
        result = classify_citation_source("example.com", "example.com", [])
        self.assertEqual(result, "owned")

    def test_classify_citation_competitor(self):
        result = classify_citation_source("competitor.com", "example.com", ["competitor.com"])
        self.assertEqual(result, "competitor_owned")

    def test_classify_citation_social(self):
        result = classify_citation_source("twitter.com", "example.com", [])
        self.assertEqual(result, "social")

    def test_classify_citation_earned(self):
        result = classify_citation_source("techblog.com", "example.com", [])
        self.assertEqual(result, "earned_media")

    def test_find_brand_position(self):
        text = "第一段内容。\n\n第二段提到示例科技。\n\n第三段。"
        pos = find_brand_position(text, "示例科技")
        self.assertEqual(pos, 1)

    def test_detect_list_structure(self):
        self.assertTrue(detect_list_structure("1. 第一点\n2. 第二点"))
        self.assertTrue(detect_list_structure("- 项目A\n- 项目B"))
        self.assertFalse(detect_list_structure("这是一段普通文本"))

    def test_detect_table_structure(self):
        self.assertTrue(detect_table_structure("| 列1 | 列2 | 列3 |"))
        self.assertFalse(detect_table_structure("普通文本没有表格"))

    def test_extract_signals_full(self):
        search_result = {
            "answer_text": "示例科技是最佳项目管理软件，推荐给50人团队。竞品A也不错。",
            "citations": [
                {"url": "https://example.com/product", "title": "产品页"},
                {"url": "https://techblog.com/review", "title": "评测"},
            ],
            "sources": [],
        }
        signals = extract_signals(
            search_result, "示例科技", "example.com",
            competitors=["竞品A"], aliases=["示例项目"],
        )
        self.assertTrue(signals["brand_mentioned"])
        self.assertTrue(signals["brand_cited"])
        self.assertTrue(signals["brand_domain_cited"])
        self.assertIn("竞品a", signals["competitor_mentioned"])
        self.assertGreater(signals["citation_count"], 0)
        self.assertIn("example.com", signals["citation_domains"])

    def test_search_template_constants(self):
        self.assertEqual(len(SEARCH_TEMPLATE_TYPES), 5)
        self.assertEqual(sum(STANDARD_TEMPLATE_DISTRIBUTION.values()), 30)
        self.assertEqual(sum(QUICK_TEMPLATE_DISTRIBUTION.values()), 10)


class TestSearchQualityScoring(unittest.TestCase):
    """v1.5 — Tests for search result quality scoring."""

    def test_high_quality_result(self):
        result = {
            "answer_text": "根据最新评测，以下是2026年最值得推荐的项目管理软件：\n1. 示例科技 - 适合50人团队\n2. 竞品A - 企业级方案\n\n这些工具各有特色，建议根据团队规模选择。",
            "citations": [{"url": "https://example.com"}, {"url": "https://review.com"}],
            "sources": [],
            "extracted_signals": {
                "platform_hints": {"has_list_structure": True, "has_inline_citations": True},
                "response_quality": {"factual_specificity": "high", "is_refusal": False},
            },
        }
        quality = score_response_quality(result)
        self.assertGreaterEqual(quality["quality_score"], 70)
        self.assertIn(quality["quality_band"], ("high_quality", "acceptable"))

    def test_poor_quality_result(self):
        result = {
            "answer_text": "不确定。",
            "citations": [],
            "sources": [],
            "extracted_signals": {
                "platform_hints": {},
                "response_quality": {"factual_specificity": "low", "is_refusal": True},
            },
        }
        quality = score_response_quality(result)
        self.assertLess(quality["quality_score"], 40)
        self.assertEqual(quality["quality_band"], "poor")

    def test_no_citations_issue(self):
        result = {
            "answer_text": "这是一段较长的回答内容，包含了足够的信息量，但是没有任何引用来源支撑。",
            "citations": [],
            "sources": [],
            "extracted_signals": {
                "platform_hints": {},
                "response_quality": {"factual_specificity": "medium", "is_refusal": False},
            },
        }
        quality = score_response_quality(result)
        self.assertTrue(any(i["type"] == "no_citations" for i in quality["issues"]))


class TestRetryStrategy(unittest.TestCase):
    """v1.5 — Tests for retry strategy recommendation."""

    def test_hard_failure_no_retry(self):
        result = {"status": "failed", "error": "WEB_SEARCH_UNAVAILABLE"}
        quality = {"quality_score": 0, "issues": []}
        retry = recommend_retry_strategy(result, quality)
        self.assertIsNone(retry)

    def test_soft_failure_retry(self):
        result = {"status": "failed", "error": "EMPTY_ANSWER"}
        quality = {"quality_score": 0, "issues": []}
        retry = recommend_retry_strategy(result, quality)
        self.assertIsNotNone(retry)
        self.assertEqual(retry["strategy"], "B")

    def test_low_quality_high_value(self):
        result = {"status": "success", "answer_text": "短", "citations": [],
                  "extracted_signals": {"brand_mentioned": False}}
        quality = {"quality_score": 30, "issues": [{"type": "short_response"}]}
        retry = recommend_retry_strategy(result, quality, question_business_value=80)
        self.assertIsNotNone(retry)
        self.assertEqual(retry["strategy"], "B")

    def test_no_retry_for_good_result(self):
        result = {"status": "success", "answer_text": "长回答", "citations": [{"url": "x"}],
                  "extracted_signals": {"brand_mentioned": True}}
        quality = {"quality_score": 85, "issues": []}
        retry = recommend_retry_strategy(result, quality)
        self.assertIsNone(retry)


class TestSnapshotCreation(unittest.TestCase):
    """v1.5 — Tests for snapshot creation."""

    def test_snapshot_structure(self):
        result = {
            "question_id": "q-001",
            "query_text": "测试问题",
            "executed_at": "2026-07-17T08:42:12Z",
            "answer_text": "测试回答内容",
            "citations": [{"url": "https://example.com"}],
            "extracted_signals": {
                "brand_mentioned": True,
                "brand_cited": True,
                "brand_position_in_answer": 1,
                "competitor_mentioned": ["竞品A"],
                "response_quality": {"factual_specificity": "high", "citation_density": 5.0},
            },
        }
        snapshot = create_snapshot(result, "测试品牌")
        self.assertIn("snapshot_id", snapshot)
        self.assertEqual(snapshot["question_id"], "q-001")
        self.assertTrue(snapshot["brand_snapshot"]["mentioned"])
        self.assertIn("竞品A", snapshot["competitor_snapshots"])


class TestDriftDetection(unittest.TestCase):
    """v1.5 — Tests for semantic drift detection."""

    def test_no_drift(self):
        baseline = {
            "question_id": "q-001",
            "brand_snapshot": {"mentioned": True, "cited": True, "position": 2, "sentiment_score": 75, "recommendation_type": "recommended"},
            "competitor_snapshots": {"竞品A": {"mentioned": True}},
        }
        current = {
            "question_id": "q-001",
            "brand_snapshot": {"mentioned": True, "cited": True, "position": 2, "sentiment_score": 75, "recommendation_type": "recommended"},
            "competitor_snapshots": {"竞品A": {"mentioned": True}},
        }
        result = detect_single_drift(baseline, current)
        self.assertEqual(result["drift_score"], 100.0)
        self.assertEqual(result["drift_band"], "stable")
        self.assertEqual(result["drift_count"], 0)

    def test_position_drift_down(self):
        baseline = {
            "question_id": "q-001",
            "brand_snapshot": {"position": 1},
            "competitor_snapshots": {},
        }
        current = {
            "question_id": "q-001",
            "brand_snapshot": {"position": 5},
            "competitor_snapshots": {},
        }
        result = detect_single_drift(baseline, current)
        self.assertLess(result["drift_score"], 100)
        self.assertTrue(any(d["type"] == "position" for d in result["drifts"]))

    def test_brand_disappeared(self):
        baseline = {
            "question_id": "q-001",
            "brand_snapshot": {"position": 2},
            "competitor_snapshots": {},
        }
        current = {
            "question_id": "q-001",
            "brand_snapshot": {"position": None},
            "competitor_snapshots": {},
        }
        result = detect_single_drift(baseline, current)
        self.assertTrue(any(d["severity"] == "critical" for d in result["drifts"]))

    def test_recommendation_downgrade(self):
        baseline = {
            "question_id": "q-001",
            "brand_snapshot": {"recommendation_type": "top_pick"},
            "competitor_snapshots": {},
        }
        current = {
            "question_id": "q-001",
            "brand_snapshot": {"recommendation_type": "mentioned_only"},
            "competitor_snapshots": {},
        }
        result = detect_single_drift(baseline, current)
        self.assertTrue(any(d["type"] == "recommendation" and d["severity"] == "warning" for d in result["drifts"]))


class TestRunChaining(unittest.TestCase):
    """v1.6 — Tests for run chaining."""

    def test_compute_deltas_improvement(self):
        baseline_metrics = {
            "mention_rate": {"rate": 0.3},
            "recommendation_rate": {"rate": 0.2},
            "geo_score": {"score": 45.0},
            "visibility_score": {"score": 40.0},
        }
        current_metrics = {
            "mention_rate": {"rate": 0.6},
            "recommendation_rate": {"rate": 0.4},
            "geo_score": {"score": 68.0},
            "visibility_score": {"score": 65.0},
        }
        deltas = compute_run_deltas(baseline_metrics, current_metrics)
        self.assertGreater(deltas["mention_rate"]["delta"], 0)
        self.assertGreater(deltas["geo_score"]["delta"], 0)
        self.assertEqual(deltas["improvement_direction"], "improving")

    def test_compute_deltas_regression(self):
        baseline_metrics = {
            "mention_rate": {"rate": 0.7},
            "recommendation_rate": {"rate": 0.5},
            "geo_score": {"score": 75.0},
            "visibility_score": {"score": 70.0},
        }
        current_metrics = {
            "mention_rate": {"rate": 0.3},
            "recommendation_rate": {"rate": 0.2},
            "geo_score": {"score": 40.0},
            "visibility_score": {"score": 35.0},
        }
        deltas = compute_run_deltas(baseline_metrics, current_metrics)
        self.assertLess(deltas["mention_rate"]["delta"], 0)
        self.assertEqual(deltas["improvement_direction"], "regressing")


class TestImprovementPlan(unittest.TestCase):
    """v1.6 — Tests for improvement plan generation."""

    def test_generate_plan_from_drift(self):
        drift = {
            "critical_drifts": [
                {"question_id": "q-007", "drifts": [{"type": "recommendation", "severity": "critical"}]}
            ],
            "positive_drifts": [],
        }
        opportunities = [
            {"id": "opp-001", "title": "创建选购指南", "target_question_ids": ["q-001", "q-009"],
             "opportunity_type": "missing_recommendation_content", "scores": {"total": 86.25}}
        ]
        metrics = {"geo_score": {"score": 55.0}}
        plan = generate_plan(drift, opportunities, metrics)
        self.assertGreater(len(plan["actions"]), 0)
        self.assertIn("priority", plan["actions"][0])
        self.assertIn("action_type", plan["actions"][0])
        self.assertIn("deadline_days", plan["actions"][0])
        self.assertIn("validation_method", plan["actions"][0])

    def test_generate_plan_empty(self):
        plan = generate_plan({"critical_drifts": [], "positive_drifts": []}, [], {"geo_score": {"score": 90.0}})
        self.assertEqual(len(plan["actions"]), 0)


class TestFunnelStageClassification(unittest.TestCase):
    """v1.7 — Tests for funnel stage classification."""

    def test_awareness_intent(self):
        self.assertEqual(classify_question_stage({"intent": "category_knowledge"}), "awareness")

    def test_consideration_intent(self):
        self.assertEqual(classify_question_stage({"intent": "recommendation"}), "consideration")

    def test_conversion_intent(self):
        self.assertEqual(classify_question_stage({"intent": "purchase"}), "conversion")

    def test_retention_intent(self):
        self.assertEqual(classify_question_stage({"intent": "brand_fact"}), "retention")

    def test_keyword_fallback(self):
        self.assertEqual(classify_question_stage({"intent": "unknown", "text": "最好的项目管理软件有哪些"}), "awareness")

    def test_constants(self):
        self.assertEqual(len(FUNNEL_STAGES), 4)
        self.assertEqual(len(INTENT_TO_FUNNEL), 7)


class TestAttributeAnalysis(unittest.TestCase):
    """v1.7 — Tests for attribute detection."""

    def test_detect_pricing(self):
        attrs = detect_attributes("这个产品价格合理，有免费版和付费版")
        self.assertIn("pricing", attrs)

    def test_detect_security(self):
        attrs = detect_attributes("支持端到端加密和合规认证")
        self.assertIn("security", attrs)

    def test_detect_multiple(self):
        attrs = detect_attributes("功能强大，API集成方便，性能优秀")
        self.assertTrue(len(attrs) >= 2)

    def test_detect_none(self):
        attrs = detect_attributes("今天天气不错")
        self.assertEqual(len(attrs), 0)

    def test_constants(self):
        self.assertEqual(len(ATTRIBUTE_CATEGORIES), 8)
        self.assertEqual(len(ATTRIBUTE_KEYWORDS), 8)


class TestVisibilityAlerts(unittest.TestCase):
    """v1.7 — Tests for visibility alert detection."""

    def test_no_alerts(self):
        current = {"mention_rate": {"rate": 0.7}, "recommendation_rate": {"rate": 0.5},
                   "geo_score": {"score": 70}, "visibility_score": {"score": 65}}
        baseline = {"mention_rate": {"rate": 0.7}, "recommendation_rate": {"rate": 0.5},
                    "geo_score": {"score": 70}, "visibility_score": {"score": 65}}
        alerts = detect_alerts(current, baseline)
        self.assertEqual(len(alerts), 0)

    def test_mention_drop_warning(self):
        current = {"mention_rate": {"rate": 0.5}, "recommendation_rate": {"rate": 0.5},
                   "geo_score": {"score": 70}, "visibility_score": {"score": 65}}
        baseline = {"mention_rate": {"rate": 0.7}, "recommendation_rate": {"rate": 0.5},
                    "geo_score": {"score": 70}, "visibility_score": {"score": 65}}
        alerts = detect_alerts(current, baseline)
        self.assertTrue(any(a["alert_type"] == "mention_drop" for a in alerts))

    def test_geo_score_critical(self):
        current = {"mention_rate": {"rate": 0.7}, "recommendation_rate": {"rate": 0.5},
                   "geo_score": {"score": 40}, "visibility_score": {"score": 65}}
        baseline = {"mention_rate": {"rate": 0.7}, "recommendation_rate": {"rate": 0.5},
                    "geo_score": {"score": 70}, "visibility_score": {"score": 65}}
        alerts = detect_alerts(current, baseline)
        critical = [a for a in alerts if a["severity"] == "critical"]
        self.assertTrue(len(critical) > 0)

    def test_alert_thresholds_constant(self):
        self.assertIn("mention_rate", ALERT_THRESHOLDS)
        self.assertIn("warning", ALERT_THRESHOLDS["mention_rate"])


class TestPublisherInfluence(unittest.TestCase):
    """v1.8 — Tests for publisher influence mapping."""

    def test_basic_influence(self):
        citations = [
            {"domain": "techblog.com", "question_id": "q-1", "supports_target_brand": True},
            {"domain": "techblog.com", "question_id": "q-2", "supports_target_brand": True},
            {"domain": "techblog.com", "question_id": "q-3", "supports_target_brand": False},
            {"domain": "review.com", "question_id": "q-1", "supports_target_brand": True},
        ]
        result = compute_publisher_influence(citations)
        self.assertTrue(len(result) > 0)
        # techblog.com has 3 citations, review.com has 1
        tech = next(r for r in result if r["domain"] == "techblog.com")
        self.assertEqual(tech["citation_count"], 3)

    def test_empty_citations(self):
        result = compute_publisher_influence([])
        self.assertEqual(len(result), 0)

    def test_constants(self):
        self.assertEqual(len(PUBLISHER_CATEGORIES), 8)
        self.assertEqual(len(JOURNEY_STAGES), 5)


class TestJourneyMetrics(unittest.TestCase):
    """v1.8 — Tests for journey metrics computation."""

    def test_stage_mapping(self):
        self.assertEqual(FUNNEL_TO_JOURNEY["awareness"], "problem_awareness")
        self.assertEqual(FUNNEL_TO_JOURNEY["conversion"], "purchase_decision")


class TestOptimizationActions(unittest.TestCase):
    """v1.8 — Tests for optimization action scoring."""

    def test_score_action(self):
        action = {
            "impact": 80,
            "urgency": 70,
            "feasibility": 60,
        }
        score = score_action(action)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)

    def test_constants(self):
        self.assertEqual(len(OPTIMIZATION_ACTION_CATEGORIES), 7)


if __name__ == "__main__":
    unittest.main()