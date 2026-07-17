#!/usr/bin/env python3
"""Unit tests for v5.0 scripts: ceiling_geo (5 subcommands)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skill" / "grok-geo" / "scripts"
sys.path.insert(0, str(SCRIPTS))


class TestCeilingGeo(unittest.TestCase):
    """Test ceiling_geo.py — Agentic Commerce + Defensive GEO + A2A + Multimodal + Predictive."""

    def test_import(self):
        """Test that ceiling_geo module can be imported."""
        import ceiling_geo
        self.assertTrue(hasattr(ceiling_geo, 'check_agentic_commerce'))
        self.assertTrue(hasattr(ceiling_geo, 'check_defensive_geo'))
        self.assertTrue(hasattr(ceiling_geo, 'check_a2a_readiness'))
        self.assertTrue(hasattr(ceiling_geo, 'check_multimodal_geo'))
        self.assertTrue(hasattr(ceiling_geo, 'predict_visibility'))

    def test_check_agentic_commerce_function_signature(self):
        """Test check_agentic_commerce function signature."""
        import inspect
        from ceiling_geo import check_agentic_commerce
        sig = inspect.signature(check_agentic_commerce)
        params = list(sig.parameters.keys())
        self.assertIn('run_dir', params)

    def test_check_defensive_geo_function_signature(self):
        """Test check_defensive_geo function signature."""
        import inspect
        from ceiling_geo import check_defensive_geo
        sig = inspect.signature(check_defensive_geo)
        params = list(sig.parameters.keys())
        self.assertIn('run_dir', params)

    def test_check_a2a_readiness_function_signature(self):
        """Test check_a2a_readiness function signature."""
        import inspect
        from ceiling_geo import check_a2a_readiness
        sig = inspect.signature(check_a2a_readiness)
        params = list(sig.parameters.keys())
        self.assertIn('run_dir', params)

    def test_check_multimodal_geo_function_signature(self):
        """Test check_multimodal_geo function signature."""
        import inspect
        from ceiling_geo import check_multimodal_geo
        sig = inspect.signature(check_multimodal_geo)
        params = list(sig.parameters.keys())
        self.assertIn('run_dir', params)

    def test_predict_visibility_function_signature(self):
        """Test predict_visibility function signature."""
        import inspect
        from ceiling_geo import predict_visibility
        sig = inspect.signature(predict_visibility)
        params = list(sig.parameters.keys())
        self.assertIn('run_dir', params)


if __name__ == "__main__":
    unittest.main()