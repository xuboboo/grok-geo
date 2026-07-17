#!/usr/bin/env python3
"""Unit tests for v4.0 scripts: ultimate_geo (6 subcommands)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skill" / "grok-geo" / "scripts"
sys.path.insert(0, str(SCRIPTS))


class TestUltimateGeo(unittest.TestCase):
    """Test ultimate_geo.py — Agentic Brand Vault + Narrative Analysis + Heatmap + Agentic GEO + Hybrid Score."""

    def test_import(self):
        """Test that ultimate_geo module can be imported."""
        import ultimate_geo
        self.assertTrue(hasattr(ultimate_geo, 'analyze_brand_vault'))
        self.assertTrue(hasattr(ultimate_geo, 'analyze_narrative'))
        self.assertTrue(hasattr(ultimate_geo, 'build_coverage_heatmap'))
        self.assertTrue(hasattr(ultimate_geo, 'run_agentic_geo'))
        self.assertTrue(hasattr(ultimate_geo, 'compute_hybrid_metrics'))

    def test_analyze_brand_vault_function_signature(self):
        """Test analyze_brand_vault function signature."""
        import inspect
        from ultimate_geo import analyze_brand_vault
        sig = inspect.signature(analyze_brand_vault)
        params = list(sig.parameters.keys())
        self.assertIn('run_dir', params)

    def test_analyze_narrative_function_signature(self):
        """Test analyze_narrative function signature."""
        import inspect
        from ultimate_geo import analyze_narrative
        sig = inspect.signature(analyze_narrative)
        params = list(sig.parameters.keys())
        self.assertIn('run_dir', params)

    def test_build_coverage_heatmap_function_signature(self):
        """Test build_coverage_heatmap function signature."""
        import inspect
        from ultimate_geo import build_coverage_heatmap
        sig = inspect.signature(build_coverage_heatmap)
        params = list(sig.parameters.keys())
        self.assertIn('run_dir', params)

    def test_run_agentic_geo_function_signature(self):
        """Test run_agentic_geo function signature."""
        import inspect
        from ultimate_geo import run_agentic_geo
        sig = inspect.signature(run_agentic_geo)
        params = list(sig.parameters.keys())
        self.assertIn('run_dir', params)

    def test_compute_hybrid_metrics_function_signature(self):
        """Test compute_hybrid_metrics function signature."""
        import inspect
        from ultimate_geo import compute_hybrid_metrics
        sig = inspect.signature(compute_hybrid_metrics)
        params = list(sig.parameters.keys())
        self.assertGreater(len(params), 0)


if __name__ == "__main__":
    unittest.main()