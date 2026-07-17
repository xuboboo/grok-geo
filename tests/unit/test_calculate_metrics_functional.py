#!/usr/bin/env python3
"""Functional tests for calculate_metrics.py — testing actual metric calculations."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skill" / "grok-geo" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from calculate_metrics import calculate_metrics
from geo_common import geo_score, position_score, rate_with_ci, wilson_ci


class TestCalculateMetricsFunctional(unittest.TestCase):
    """Functional tests for calculate_metrics — testing actual metric calculations."""

    def test_empty_questions_returns_zero_metrics(self):
        """Empty questions list should return zero metrics."""
        result = calculate_metrics([], {}, [], [])
        self.assertEqual(result["sample"]["valid_answer_count"], 0)
        self.assertEqual(result["mention_rate"]["rate"], None)
        self.assertEqual(result["recommendation_rate"]["rate"], None)

    def test_single_mentioned_brand(self):
        """Single question with brand mentioned should show 100% mention rate."""
        questions = [
            {"id": "q1", "intent": "recommendation", "business_value": 80}
        ]
        entities = {
            "q1": {
                "question_id": "q1",
                "entities": [
                    {
                        "entity_id": "target-brand",
                        "entity_type": "target_brand",
                        "mentioned": True,
                        "mention_type": "recommended",
                        "recommendation_rank": 1,
                        "sentiment_score": 85
                    }
                ]
            }
        }

        result = calculate_metrics(questions, entities, [], [])
        self.assertEqual(result["mention_rate"]["rate"], 1.0)
        self.assertEqual(result["recommendation_rate"]["rate"], 1.0)
        self.assertGreater(result["visibility_score"]["score"], 0)

    def test_brand_not_mentioned(self):
        """Brand not mentioned should show 0% mention rate."""
        questions = [
            {"id": "q1", "intent": "recommendation", "business_value": 80}
        ]
        entities = {
            "q1": {
                "question_id": "q1",
                "entities": [
                    {
                        "entity_id": "target-brand",
                        "entity_type": "target_brand",
                        "mentioned": False,
                        "mention_type": "not_mentioned"
                    }
                ]
            }
        }

        result = calculate_metrics(questions, entities, [], [])
        self.assertEqual(result["mention_rate"]["rate"], 0.0)

    def test_competitor_co_mentions(self):
        """Competitor co-mentions should be tracked correctly."""
        questions = [
            {"id": "q1", "intent": "recommendation", "business_value": 80},
            {"id": "q2", "intent": "recommendation", "business_value": 70}
        ]
        entities = {
            "q1": {
                "question_id": "q1",
                "entities": [
                    {
                        "entity_id": "target-brand",
                        "entity_type": "target_brand",
                        "mentioned": True,
                        "mention_type": "recommended",
                        "competitor_co_mentions": ["competitor-a", "competitor-b"]
                    },
                    {
                        "entity_id": "competitor-a",
                        "entity_type": "competitor",
                        "mentioned": True,
                        "mention_type": "recommended"
                    },
                    {
                        "entity_id": "competitor-b",
                        "entity_type": "competitor",
                        "mentioned": True,
                        "mention_type": "mentioned_only"
                    }
                ]
            },
            "q2": {
                "question_id": "q2",
                "entities": [
                    {
                        "entity_id": "target-brand",
                        "entity_type": "target_brand",
                        "mentioned": True,
                        "mention_type": "recommended",
                        "competitor_co_mentions": ["competitor-a"]
                    },
                    {
                        "entity_id": "competitor-a",
                        "entity_type": "competitor",
                        "mentioned": True,
                        "mention_type": "strongly_recommended"
                    }
                ]
            }
        }

        result = calculate_metrics(questions, entities, [], [])
        self.assertIn("competitor-a", result["competitor_co_mentions"])
        self.assertEqual(result["competitor_co_mentions"]["competitor-a"], 2)
        self.assertIn("competitor-b", result["competitor_co_mentions"])
        self.assertEqual(result["competitor_co_mentions"]["competitor-b"], 1)

    def test_sentiment_index_calculation(self):
        """Sentiment index should be average of sentiment scores."""
        questions = [
            {"id": "q1", "intent": "recommendation", "business_value": 80},
            {"id": "q2", "intent": "recommendation", "business_value": 70}
        ]
        entities = {
            "q1": {
                "question_id": "q1",
                "entities": [
                    {
                        "entity_id": "target-brand",
                        "entity_type": "target_brand",
                        "mentioned": True,
                        "sentiment_score": 80
                    }
                ]
            },
            "q2": {
                "question_id": "q2",
                "entities": [
                    {
                        "entity_id": "target-brand",
                        "entity_type": "target_brand",
                        "mentioned": True,
                        "sentiment_score": 60
                    }
                ]
            }
        }

        result = calculate_metrics(questions, entities, [], [])
        self.assertEqual(result["sentiment_index"]["score"], 70.0)  # (80 + 60) / 2

    def test_recommendation_type_distribution(self):
        """Recommendation type distribution should count each type."""
        questions = [
            {"id": "q1", "intent": "recommendation", "business_value": 80},
            {"id": "q2", "intent": "recommendation", "business_value": 70},
            {"id": "q3", "intent": "recommendation", "business_value": 60}
        ]
        entities = {
            "q1": {
                "question_id": "q1",
                "entities": [
                    {
                        "entity_id": "target-brand",
                        "entity_type": "target_brand",
                        "mentioned": True,
                        "recommendation_type": "top_pick"
                    }
                ]
            },
            "q2": {
                "question_id": "q2",
                "entities": [
                    {
                        "entity_id": "target-brand",
                        "entity_type": "target_brand",
                        "mentioned": True,
                        "recommendation_type": "strong_alternative"
                    }
                ]
            },
            "q3": {
                "question_id": "q3",
                "entities": [
                    {
                        "entity_id": "target-brand",
                        "entity_type": "target_brand",
                        "mentioned": True,
                        "recommendation_type": "top_pick"
                    }
                ]
            }
        }

        result = calculate_metrics(questions, entities, [], [])
        self.assertEqual(result["recommendation_type_distribution"]["top_pick"], 2)
        self.assertEqual(result["recommendation_type_distribution"]["strong_alternative"], 1)

    def test_geo_score_calculation(self):
        """GEO score should be weighted composite of visibility, mention, recommendation, citation."""
        # Test the geo_score function directly
        result = geo_score(
            visibility_score=80.0,
            mention_rate=0.9,
            recommendation_rate=0.8,
            owned_citation_rate=0.7
        )
        self.assertIn("score", result)
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)
        # Expected: 80*0.3 + 90*0.25 + 80*0.25 + 70*0.2 = 24 + 22.5 + 20 + 14 = 80.5
        self.assertAlmostEqual(result["score"], 80.5, places=1)

    def test_position_score_top_pick(self):
        """Top pick should get 1.0 (mapped to strongly_recommended with rank 1)."""
        score = position_score("strongly_recommended", 1)
        self.assertEqual(score, 1.0)

    def test_position_score_not_mentioned(self):
        """Not mentioned should get zero position score."""
        score = position_score("not_mentioned", None)
        self.assertEqual(score, 0.0)

    def test_rate_with_ci_perfect_rate(self):
        """Perfect rate (10/10) should return 1.0 with narrow CI."""
        result = rate_with_ci(10, 10)
        self.assertEqual(result["rate"], 1.0)
        self.assertEqual(result["numerator"], 10)
        self.assertEqual(result["denominator"], 10)
        # CI should be narrow for perfect rate
        ci = result["wilson_ci_95"]
        self.assertGreater(ci["low"], 0.7)
        self.assertLessEqual(ci["high"], 1.0)

    def test_rate_with_ci_zero_rate(self):
        """Zero rate (0/10) should return 0.0 with narrow CI."""
        result = rate_with_ci(0, 10)
        self.assertEqual(result["rate"], 0.0)
        ci = result["wilson_ci_95"]
        self.assertEqual(ci["low"], 0.0)
        self.assertLess(ci["high"], 0.3)

    def test_rate_with_ci_none_when_zero_denominator(self):
        """Zero denominator should return None rate."""
        result = rate_with_ci(5, 0)
        self.assertIsNone(result["rate"])

    def test_wilson_ci_bounds(self):
        """Wilson CI should always be within [0, 1]."""
        for numerator in range(0, 11):
            for denominator in range(1, 11):
                if numerator <= denominator:
                    ci = wilson_ci(numerator, denominator)
                    self.assertGreaterEqual(ci["low"], 0.0)
                    self.assertLessEqual(ci["high"], 1.0)
                    self.assertLessEqual(ci["low"], ci["high"])

    def test_accuracy_score_calculation(self):
        """Accuracy score should be calculated from claim verification."""
        questions = [{"id": "q1", "intent": "recommendation", "business_value": 80}]
        entities = {"q1": {"question_id": "q1", "entities": []}}
        claims = [
            {"question_id": "q1", "verification_status": "correct"},
            {"question_id": "q1", "verification_status": "correct"},
            {"question_id": "q1", "verification_status": "partially_correct"},
            {"question_id": "q1", "verification_status": "incorrect"}
        ]

        result = calculate_metrics(questions, entities, [], claims)
        # Expected: (2 + 0.5) / 4 = 0.625
        self.assertAlmostEqual(result["accuracy_score"]["score"], 0.625, places=3)
        self.assertEqual(result["accuracy_score"]["correct_count"], 2)
        self.assertEqual(result["accuracy_score"]["partially_correct_count"], 1)

    def test_owned_citation_rate(self):
        """Owned citation rate should count owned citations."""
        questions = [
            {"id": "q1", "intent": "recommendation", "business_value": 80},
            {"id": "q2", "intent": "recommendation", "business_value": 70}
        ]
        entities = {
            "q1": {"question_id": "q1", "entities": []},
            "q2": {"question_id": "q2", "entities": []}
        }
        citations = [
            {"question_id": "q1", "source_type": "owned"},
            {"question_id": "q2", "source_type": "earned_media"}
        ]

        result = calculate_metrics(questions, entities, citations, [])
        self.assertEqual(result["owned_citation_rate"]["rate"], 0.5)  # 1/2

    def test_schema_version_in_output(self):
        """Output should include schema_version from SCHEMA_VERSION constant."""
        result = calculate_metrics([], {}, [], [])
        self.assertEqual(result["schema_version"], "5.0.0")


class TestGeoScoreWeights(unittest.TestCase):
    """Test GEO score weight calculations."""

    def test_weights_sum_to_one(self):
        """GEO score weights should sum to 1.0."""
        from geo_common import GEO_SCORE_WEIGHTS
        total = sum(GEO_SCORE_WEIGHTS.values())
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_visibility_weight_highest(self):
        """Visibility should have highest weight (30%)."""
        from geo_common import GEO_SCORE_WEIGHTS
        self.assertEqual(GEO_SCORE_WEIGHTS["visibility"], 0.30)

    def test_geo_score_all_zeros(self):
        """All zero inputs should return zero score."""
        result = geo_score(0.0, 0.0, 0.0, 0.0)
        self.assertEqual(result["score"], 0.0)

    def test_geo_score_all_ones(self):
        """All 100% inputs should return 100 score."""
        result = geo_score(100.0, 1.0, 1.0, 1.0)
        self.assertEqual(result["score"], 100.0)

    def test_geo_score_clamp_high(self):
        """Score should be clamped at 100."""
        result = geo_score(150.0, 1.5, 1.5, 1.5)
        self.assertEqual(result["score"], 100.0)

    def test_geo_score_clamp_low(self):
        """Score should be clamped at 0."""
        result = geo_score(-50.0, -0.5, -0.5, -0.5)
        self.assertEqual(result["score"], 0.0)


if __name__ == "__main__":
    unittest.main()