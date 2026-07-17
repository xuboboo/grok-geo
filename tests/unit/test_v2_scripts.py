#!/usr/bin/env python3
"""Unit tests for v2.0-v2.4 scripts: multi_engine_query, score_entity_kg, score_i18n, generate_closed_loop_actions, analyze_ai_referrers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skill" / "grok-geo" / "scripts"
sys.path.insert(0, str(SCRIPTS))


class TestScoreEntityKG(unittest.TestCase):
    """Test score_entity_kg.py — Entity knowledge graph completeness scoring."""

    def test_import(self):
        """Test that score_entity_kg module can be imported."""
        import score_entity_kg
        self.assertTrue(hasattr(score_entity_kg, 'score_entity_kg'))
        self.assertTrue(hasattr(score_entity_kg, 'generate_action_items'))

    def test_function_signature(self):
        """Test score_entity_kg function signature."""
        import inspect
        from score_entity_kg import score_entity_kg
        sig = inspect.signature(score_entity_kg)
        params = list(sig.parameters.keys())
        self.assertIn('brand', params)
        self.assertIn('site_data', params)
        self.assertIn('search_data', params)


class TestScoreI18n(unittest.TestCase):
    """Test score_i18n.py — Internationalization scoring."""

    def test_import(self):
        """Test that score_i18n module can be imported."""
        import score_i18n
        self.assertTrue(hasattr(score_i18n, 'score_i18n'))

    def test_function_signature(self):
        """Test score_i18n function signature."""
        import inspect
        from score_i18n import score_i18n
        sig = inspect.signature(score_i18n)
        params = list(sig.parameters.keys())
        self.assertIn('brand', params)
        self.assertIn('site_data', params)


class TestGenerateClosedLoopActions(unittest.TestCase):
    """Test generate_closed_loop_actions.py — Closed-loop optimization actions."""

    def test_import(self):
        """Test that generate_closed_loop_actions module can be imported."""
        import generate_closed_loop_actions
        self.assertTrue(hasattr(generate_closed_loop_actions, 'generate_actions'))
        self.assertTrue(hasattr(generate_closed_loop_actions, 'detect_gaps'))

    def test_function_signature(self):
        """Test generate_actions function signature."""
        import inspect
        from generate_closed_loop_actions import generate_actions
        sig = inspect.signature(generate_actions)
        params = list(sig.parameters.keys())
        self.assertIn('gaps', params)


class TestAnalyzeAiReferrers(unittest.TestCase):
    """Test analyze_ai_referrers.py — AI referrer analytics."""

    def test_import(self):
        """Test that analyze_ai_referrers module can be imported."""
        import analyze_ai_referrers
        self.assertTrue(hasattr(analyze_ai_referrers, 'build_report'))

    def test_function_signature(self):
        """Test build_report function signature."""
        import inspect
        from analyze_ai_referrers import build_report
        sig = inspect.signature(build_report)
        params = list(sig.parameters.keys())
        # build_report should accept some parameters
        self.assertGreater(len(params), 0)


if __name__ == "__main__":
    unittest.main()