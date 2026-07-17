#!/usr/bin/env python3
"""Unit tests for v3.0 scripts: cutting_edge_geo (5 subcommands)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skill" / "grok-geo" / "scripts"
sys.path.insert(0, str(SCRIPTS))


class TestCuttingEdgeGeo(unittest.TestCase):
    """Test cutting_edge_geo.py — ChatGPT Shopping + Prompt Discovery + AI SOV + Agentic Search."""

    def test_import(self):
        """Test that cutting_edge_geo module can be imported."""
        import cutting_edge_geo
        self.assertTrue(hasattr(cutting_edge_geo, 'discover_prompts'))
        self.assertTrue(hasattr(cutting_edge_geo, 'compute_ai_sov'))
        self.assertTrue(hasattr(cutting_edge_geo, 'check_agentic_readiness'))
        self.assertTrue(hasattr(cutting_edge_geo, 'analyze_shopping_visibility'))

    def test_discover_prompts_function_signature(self):
        """Test discover_prompts function signature."""
        import inspect
        from cutting_edge_geo import discover_prompts
        sig = inspect.signature(discover_prompts)
        params = list(sig.parameters.keys())
        self.assertIn('seed', params)
        self.assertIn('count', params)
        self.assertIn('competitors', params)

    def test_compute_ai_sov_function_signature(self):
        """Test compute_ai_sov function signature."""
        import inspect
        from cutting_edge_geo import compute_ai_sov
        sig = inspect.signature(compute_ai_sov)
        params = list(sig.parameters.keys())
        self.assertIn('run_dir', params)

    def test_check_agentic_readiness_function_signature(self):
        """Test check_agentic_readiness function signature."""
        import inspect
        from cutting_edge_geo import check_agentic_readiness
        sig = inspect.signature(check_agentic_readiness)
        params = list(sig.parameters.keys())
        self.assertGreater(len(params), 0)

    def test_analyze_shopping_visibility_function_signature(self):
        """Test analyze_shopping_visibility function signature."""
        import inspect
        from cutting_edge_geo import analyze_shopping_visibility
        sig = inspect.signature(analyze_shopping_visibility)
        params = list(sig.parameters.keys())
        self.assertIn('run_dir', params)


if __name__ == "__main__":
    unittest.main()