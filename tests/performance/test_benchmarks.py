#!/usr/bin/env python3
"""Performance benchmarks for grok-geo — establishing baseline performance metrics."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skill" / "grok-geo" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from calculate_metrics import calculate_metrics
from geo_common import geo_score, position_score, rate_with_ci


def generate_test_questions(count: int) -> list:
    """Generate test questions for benchmarking."""
    return [
        {"id": f"q{i}", "intent": "recommendation", "business_value": 50 + (i % 50)}
        for i in range(count)
    ]


def generate_test_entities(count: int) -> dict:
    """Generate test entities for benchmarking."""
    entities = {}
    for i in range(count):
        entities[f"q{i}"] = {
            "question_id": f"q{i}",
            "entities": [
                {
                    "entity_id": "target-brand",
                    "entity_type": "target_brand",
                    "mentioned": i % 3 != 0,  # 2/3 mentioned
                    "mention_type": "recommended" if i % 3 != 0 else "not_mentioned",
                    "recommendation_rank": (i % 5) + 1 if i % 3 != 0 else None,
                    "sentiment_score": 50 + (i % 50),
                    "recommendation_type": "top_pick" if i % 5 == 0 else "strong_alternative"
                },
                {
                    "entity_id": "competitor-a",
                    "entity_type": "competitor",
                    "mentioned": i % 2 == 0,
                    "mention_type": "recommended" if i % 2 == 0 else "not_mentioned"
                }
            ]
        }
    return entities


def generate_test_citations(count: int) -> list:
    """Generate test citations for benchmarking."""
    return [
        {"question_id": f"q{i}", "source_type": "owned" if i % 3 == 0 else "earned_media"}
        for i in range(count)
    ]


def generate_test_claims(count: int) -> list:
    """Generate test claims for benchmarking."""
    statuses = ["correct", "partially_correct", "incorrect", "unverifiable"]
    return [
        {"question_id": f"q{i}", "verification_status": statuses[i % 4]}
        for i in range(count)
    ]


class TestPerformanceBenchmarks(unittest.TestCase):
    """Performance benchmarks — establishing baseline performance metrics."""

    def test_calculate_metrics_10_questions(self):
        """Benchmark: 10 questions metric calculation."""
        questions = generate_test_questions(10)
        entities = generate_test_entities(10)
        citations = generate_test_citations(10)
        claims = generate_test_claims(10)

        result = calculate_metrics(questions, entities, citations, claims)
        self.assertIsNotNone(result)
        self.assertEqual(result["sample"]["valid_answer_count"], 10)

    def test_calculate_metrics_100_questions(self):
        """Benchmark: 100 questions metric calculation."""
        questions = generate_test_questions(100)
        entities = generate_test_entities(100)
        citations = generate_test_citations(100)
        claims = generate_test_claims(100)

        result = calculate_metrics(questions, entities, citations, claims)
        self.assertIsNotNone(result)
        self.assertEqual(result["sample"]["valid_answer_count"], 100)

    def test_calculate_metrics_1000_questions(self):
        """Benchmark: 1000 questions metric calculation."""
        questions = generate_test_questions(1000)
        entities = generate_test_entities(1000)
        citations = generate_test_citations(1000)
        claims = generate_test_claims(1000)

        result = calculate_metrics(questions, entities, citations, claims)
        self.assertIsNotNone(result)
        self.assertEqual(result["sample"]["valid_answer_count"], 1000)

    def test_geo_score_10000_calculations(self):
        """Benchmark: 10000 geo_score calculations."""
        for i in range(10000):
            visibility = float(i % 100)
            mention_rate = (i % 100) / 100.0
            recommendation_rate = (i % 100) / 100.0
            citation_rate = (i % 100) / 100.0
            result = geo_score(visibility, mention_rate, recommendation_rate, citation_rate)
            self.assertIn("score", result)
            self.assertGreaterEqual(result["score"], 0)
            self.assertLessEqual(result["score"], 100)

    def test_position_score_10000_calculations(self):
        """Benchmark: 10000 position_score calculations."""
        mention_types = ["top_pick", "strongly_recommended", "recommended", 
                        "weakly_recommended", "mentioned_only", "not_mentioned"]
        for i in range(10000):
            mention_type = mention_types[i % len(mention_types)]
            rank = (i % 10) + 1
            score = position_score(mention_type, rank)
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 1.0)

    def test_rate_with_ci_10000_calculations(self):
        """Benchmark: 10000 rate_with_ci calculations."""
        for i in range(10000):
            numerator = i % 100
            denominator = 100
            result = rate_with_ci(numerator, denominator)
            self.assertIsNotNone(result["rate"])
            self.assertGreaterEqual(result["rate"], 0)
            self.assertLessEqual(result["rate"], 1)

    def test_json_read_write_performance(self):
        """Benchmark: JSON read/write performance."""
        data = {
            "questions": generate_test_questions(100),
            "entities": generate_test_entities(100),
            "citations": generate_test_citations(100),
            "claims": generate_test_claims(100)
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            # Read performance
            for _ in range(100):
                with open(temp_path, 'r') as f:
                    loaded = json.load(f)
                self.assertIsNotNone(loaded)

            # Write performance
            for _ in range(100):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(data, f)
        finally:
            Path(temp_path).unlink()


class TestMemoryBenchmarks(unittest.TestCase):
    """Memory usage benchmarks."""

    def test_large_dataset_memory(self):
        """Benchmark: Memory usage with large dataset."""
        import sys

        questions = generate_test_questions(1000)
        entities = generate_test_entities(1000)
        citations = generate_test_citations(1000)
        claims = generate_test_claims(1000)

        # Calculate memory usage
        initial_size = sys.getsizeof(questions) + sys.getsizeof(entities)

        result = calculate_metrics(questions, entities, citations, claims)

        # Verify result is not excessively large
        result_size = sys.getsizeof(result)
        self.assertLess(result_size, 100000)  # Should be less than 100KB


if __name__ == "__main__":
    unittest.main()