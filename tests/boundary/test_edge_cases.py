#!/usr/bin/env python3
"""Boundary tests for grok-geo — testing edge cases and boundary conditions."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skill" / "grok-geo" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from geo_common import (
    clamp,
    geo_score,
    position_score,
    rate_with_ci,
    wilson_ci,
    normalize_entity_name,
    freshness_score,
    rag_readiness,
    citability_score,
    negative_signal_score,
    trust_stack_score,
    ai_perception_score,
)


class TestClampBoundary(unittest.TestCase):
    """Boundary tests for clamp function."""

    def test_clamp_within_range(self):
        """Value within range should be returned unchanged."""
        self.assertEqual(clamp(50, 0, 100), 50)

    def test_clamp_below_min(self):
        """Value below min should be clamped to min."""
        self.assertEqual(clamp(-10, 0, 100), 0)

    def test_clamp_above_max(self):
        """Value above max should be clamped to max."""
        self.assertEqual(clamp(150, 0, 100), 100)

    def test_clamp_at_min(self):
        """Value at min should be returned unchanged."""
        self.assertEqual(clamp(0, 0, 100), 0)

    def test_clamp_at_max(self):
        """Value at max should be returned unchanged."""
        self.assertEqual(clamp(100, 0, 100), 100)

    def test_clamp_float_values(self):
        """Float values should be clamped correctly."""
        self.assertAlmostEqual(clamp(50.5, 0.0, 100.0), 50.5, places=2)

    def test_clamp_negative_range(self):
        """Negative range should work correctly."""
        self.assertEqual(clamp(0, -100, -10), -10)
        self.assertEqual(clamp(-50, -100, -10), -50)
        self.assertEqual(clamp(-150, -100, -10), -100)


class TestPositionScoreBoundary(unittest.TestCase):
    """Boundary tests for position_score function."""

    def test_position_score_strongly_recommended_rank_1(self):
        """Strongly recommended with rank 1 should get 1.0."""
        self.assertEqual(position_score("strongly_recommended", 1), 1.0)

    def test_position_score_strongly_recommended(self):
        """Strongly recommended should get high score."""
        self.assertGreater(position_score("strongly_recommended", 1), 0.8)

    def test_position_score_recommended(self):
        """Recommended should get moderate score."""
        score = position_score("recommended", 2)
        self.assertGreater(score, 0.5)
        self.assertLess(score, 0.9)

    def test_position_score_mentioned_only(self):
        """Mentioned only should get low score."""
        score = position_score("mentioned_only", 5)
        self.assertLess(score, 0.3)

    def test_position_score_not_mentioned(self):
        """Not mentioned should get 0.0."""
        self.assertEqual(position_score("not_mentioned", None), 0.0)

    def test_position_score_none_type(self):
        """None type should get 0.0."""
        self.assertEqual(position_score(None, None), 0.0)

    def test_position_score_high_rank(self):
        """High rank (10+) should get moderate score (0.30 for recommended)."""
        score = position_score("recommended", 10)
        self.assertEqual(score, 0.30)  # position_score returns 0.30 for rank > 3

    def test_position_score_rank_1(self):
        """Rank 1 should get highest score for given type."""
        score_rank1 = position_score("recommended", 1)
        score_rank5 = position_score("recommended", 5)
        self.assertGreater(score_rank1, score_rank5)


class TestWilsonCIBoundary(unittest.TestCase):
    """Boundary tests for Wilson CI function."""

    def test_wilson_ci_perfect_rate(self):
        """Perfect rate (10/10) should have CI near 1.0."""
        ci = wilson_ci(10, 10)
        self.assertGreater(ci["low"], 0.7)
        self.assertLessEqual(ci["high"], 1.0)

    def test_wilson_ci_zero_rate(self):
        """Zero rate (0/10) should have CI near 0.0."""
        ci = wilson_ci(0, 10)
        self.assertEqual(ci["low"], 0.0)
        self.assertLess(ci["high"], 0.3)

    def test_wilson_ci_half_rate(self):
        """Half rate (5/10) should have CI around 0.5."""
        ci = wilson_ci(5, 10)
        self.assertGreater(ci["low"], 0.2)
        self.assertLess(ci["high"], 0.8)

    def test_wilson_ci_small_sample(self):
        """Small sample should have wide CI."""
        ci_wide = wilson_ci(1, 2)
        ci_narrow = wilson_ci(50, 100)
        # Small sample should have wider CI
        self.assertGreater(ci_wide["high"] - ci_wide["low"], 
                          ci_narrow["high"] - ci_narrow["low"])

    def test_wilson_ci_bounds_always_valid(self):
        """CI bounds should always be in [0, 1]."""
        for n in range(0, 21):
            for d in range(1, 21):
                if n <= d:
                    ci = wilson_ci(n, d)
                    self.assertGreaterEqual(ci["low"], 0.0)
                    self.assertLessEqual(ci["high"], 1.0)
                    self.assertLessEqual(ci["low"], ci["high"])


class TestRateWithCIBoundary(unittest.TestCase):
    """Boundary tests for rate_with_ci function."""

    def test_rate_with_ci_zero_denominator(self):
        """Zero denominator should return None rate."""
        result = rate_with_ci(5, 0)
        self.assertIsNone(result["rate"])
        self.assertIsNone(result["wilson_ci_95"])

    def test_rate_with_ci_zero_numerator(self):
        """Zero numerator should return 0.0 rate."""
        result = rate_with_ci(0, 10)
        self.assertEqual(result["rate"], 0.0)

    def test_rate_with_ci_equal_numerator_denominator(self):
        """Equal numerator and denominator should return 1.0 rate."""
        result = rate_with_ci(10, 10)
        self.assertEqual(result["rate"], 1.0)

    def test_rate_with_ci_large_numbers(self):
        """Large numbers should work correctly."""
        result = rate_with_ci(1000, 10000)
        self.assertEqual(result["rate"], 0.1)
        self.assertEqual(result["numerator"], 1000)
        self.assertEqual(result["denominator"], 10000)


class TestNormalizeEntityNameBoundary(unittest.TestCase):
    """Boundary tests for normalize_entity_name function."""

    def test_normalize_empty_string(self):
        """Empty string should return empty string."""
        self.assertEqual(normalize_entity_name(""), "")

    def test_normalize_whitespace_only(self):
        """Whitespace only should return empty string."""
        self.assertEqual(normalize_entity_name("   "), "")

    def test_normalize_company_suffix(self):
        """Company suffixes should be removed."""
        result = normalize_entity_name("TestCorp Inc.")
        self.assertNotIn("Inc.", result)

    def test_normalize_multiple_spaces(self):
        """Multiple spaces should be normalized to single space."""
        result = normalize_entity_name("Test   Brand   Name")
        self.assertNotIn("  ", result)

    def test_normalize_leading_trailing_spaces(self):
        """Leading and trailing spaces should be removed, and name should be lowercased."""
        result = normalize_entity_name("  TestBrand  ")
        self.assertEqual(result, "testbrand")  # normalize_entity_name lowercases the name


class TestFreshnessScoreBoundary(unittest.TestCase):
    """Boundary tests for freshness_score function."""

    def test_freshness_empty_signals(self):
        """Empty signals should return 100 (perfect freshness)."""
        result = freshness_score([])
        self.assertEqual(result["score"], 100)

    def test_freshness_no_decay(self):
        """No decay signals should return 100."""
        # Empty list means no decay signals
        result = freshness_score([])
        self.assertEqual(result["score"], 100)

    def test_freshness_high_severity_decay(self):
        """High severity decay should significantly reduce score."""
        result = freshness_score([{"pattern": "temporal", "severity": "high"}])
        self.assertLess(result["score"], 100)

    def test_freshness_low_severity_decay(self):
        """Low severity decay should slightly reduce score."""
        result = freshness_score([{"pattern": "temporal", "severity": "low"}])
        self.assertGreater(result["score"], 80)

    def test_freshness_multiple_signals(self):
        """Multiple signals should accumulate deductions."""
        result = freshness_score([
            {"pattern": "temporal", "severity": "high"},
            {"pattern": "statistical", "severity": "high"}
        ])
        self.assertLess(result["score"], 100)


class TestRAGReadinessBoundary(unittest.TestCase):
    """Boundary tests for rag_readiness function."""

    def test_rag_readiness_empty_dimensions(self):
        """Empty dimensions should return 0."""
        result = rag_readiness({})
        self.assertEqual(result["score"], 0)

    def test_rag_readiness_all_perfect(self):
        """All perfect dimensions should return 100."""
        result = rag_readiness({
            "paragraph_structure": {"score": 100, "issues": []},
            "heading_hierarchy": {"score": 100, "issues": []},
            "definition_openings": {"score": 100, "issues": []},
            "self_containment": {"score": 100, "issues": []},
            "anchor_sentences": {"score": 100, "issues": []},
            "structured_data": {"score": 100, "issues": []}
        })
        self.assertEqual(result["score"], 100)

    def test_rag_readiness_all_zero(self):
        """All zero dimensions should return 0."""
        result = rag_readiness({
            "paragraph_structure": {"score": 0, "issues": []},
            "heading_hierarchy": {"score": 0, "issues": []},
            "definition_openings": {"score": 0, "issues": []},
            "self_containment": {"score": 0, "issues": []},
            "anchor_sentences": {"score": 0, "issues": []},
            "structured_data": {"score": 0, "issues": []}
        })
        self.assertEqual(result["score"], 0)


class TestCitabilityScoreBoundary(unittest.TestCase):
    """Boundary tests for citability_score function."""

    def test_citability_empty_methods(self):
        """Empty methods should return 0."""
        result = citability_score({})
        self.assertEqual(result["score"], 0)

    def test_citability_high_cite_sources(self):
        """High cite_sources should significantly boost score."""
        result = citability_score({"cite_sources": {"score": 100, "issues": []}})
        self.assertGreater(result["score"], 50)

    def test_citability_statistics_boost(self):
        """Statistics should boost score."""
        result_without = citability_score({})
        result_with = citability_score({"statistics": {"score": 100, "issues": []}})
        self.assertGreater(result_with["score"], result_without["score"])


class TestNegativeSignalScoreBoundary(unittest.TestCase):
    """Boundary tests for negative_signal_score function."""

    def test_negative_signals_empty(self):
        """Empty signals should return 100 (no negative signals, perfect score)."""
        result = negative_signal_score([])
        self.assertEqual(result["score"], 100)

    def test_negative_signals_critical(self):
        """Critical signal should significantly increase score."""
        result = negative_signal_score([{"type": "cta_overload", "severity": "critical"}])
        self.assertGreater(result["score"], 50)

    def test_negative_signals_multiple(self):
        """Multiple signals should accumulate."""
        result = negative_signal_score([
            {"type": "cta_overload", "severity": "low"},
            {"type": "thin_content", "severity": "low"},
            {"type": "keyword_stuffing", "severity": "low"}
        ])
        self.assertGreater(result["score"], 0)


class TestTrustStackScoreBoundary(unittest.TestCase):
    """Boundary tests for trust_stack_score function."""

    def test_trust_stack_empty_layers(self):
        """Empty layers should return F grade."""
        result = trust_stack_score({})
        self.assertEqual(result["grade"], "F")

    def test_trust_stack_all_perfect(self):
        """All perfect layers should return A grade."""
        result = trust_stack_score({
            "technical": {"score": 100, "issues": []},
            "identity": {"score": 100, "issues": []},
            "social": {"score": 100, "issues": []},
            "academic": {"score": 100, "issues": []},
            "consistency": {"score": 100, "issues": []}
        })
        self.assertEqual(result["grade"], "A")

    def test_trust_stack_all_zero(self):
        """All zero layers should return F grade."""
        result = trust_stack_score({
            "technical": {"score": 0, "issues": []},
            "identity": {"score": 0, "issues": []},
            "social": {"score": 0, "issues": []},
            "academic": {"score": 0, "issues": []},
            "consistency": {"score": 0, "issues": []}
        })
        self.assertEqual(result["grade"], "F")

class TestAIPerceptionScoreBoundary(unittest.TestCase):
    """Boundary tests for ai_perception_score function."""

    def test_ai_perception_empty_dimensions(self):
        """Empty dimensions should return 0."""
        result = ai_perception_score({})
        self.assertEqual(result["score"], 0)

    def test_ai_perception_all_perfect(self):
        """All perfect dimensions should return 100."""
        result = ai_perception_score({
            "positioning_clarity": 1.0,
            "price_transparency": 1.0,
            "claim_consistency": 1.0,
            "sentiment_strength": 1.0,
            "competitor_framing": 1.0
        })
        self.assertEqual(result["score"], 100)

    def test_ai_perception_mixed_scores(self):
        """Mixed scores should be weighted average."""
        result = ai_perception_score({
            "positioning_clarity": 0.8,
            "price_transparency": 0.6,
            "claim_consistency": 0.4,
            "sentiment_strength": 0.2,
            "competitor_framing": 0.0
        })
        # Score should be between 0 and 100
        self.assertGreater(result["score"], 0)
        self.assertLess(result["score"], 100)


class TestGeoScoreBoundary(unittest.TestCase):
    """Boundary tests for geo_score function."""

    def test_geo_score_zero_inputs(self):
        """All zero inputs should return 0."""
        result = geo_score(0.0, 0.0, 0.0, 0.0)
        self.assertEqual(result["score"], 0.0)

    def test_geo_score_max_inputs(self):
        """All max inputs should return 100."""
        result = geo_score(100.0, 1.0, 1.0, 1.0)
        self.assertEqual(result["score"], 100.0)

    def test_geo_score_clamp_above_100(self):
        """Score above 100 should be clamped to 100."""
        result = geo_score(150.0, 1.5, 1.5, 1.5)
        self.assertEqual(result["score"], 100.0)

    def test_geo_score_clamp_below_0(self):
        """Score below 0 should be clamped to 0."""
        result = geo_score(-50.0, -0.5, -0.5, -0.5)
        self.assertEqual(result["score"], 0.0)

    def test_geo_score_visibility_weight(self):
        """Visibility should have 30% weight."""
        # Only visibility = 100, others = 0
        result = geo_score(100.0, 0.0, 0.0, 0.0)
        self.assertAlmostEqual(result["score"], 30.0, places=1)

    def test_geo_score_mention_weight(self):
        """Mention rate should have 25% weight."""
        # Only mention_rate = 1.0, others = 0
        result = geo_score(0.0, 1.0, 0.0, 0.0)
        self.assertAlmostEqual(result["score"], 25.0, places=1)

    def test_geo_score_recommendation_weight(self):
        """Recommendation rate should have 25% weight."""
        # Only recommendation_rate = 1.0, others = 0
        result = geo_score(0.0, 0.0, 1.0, 0.0)
        self.assertAlmostEqual(result["score"], 25.0, places=1)

    def test_geo_score_citation_weight(self):
        """Citation rate should have 20% weight."""
        # Only owned_citation_rate = 1.0, others = 0
        result = geo_score(0.0, 0.0, 0.0, 1.0)
        self.assertAlmostEqual(result["score"], 20.0, places=1)


if __name__ == "__main__":
    unittest.main()