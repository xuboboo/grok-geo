#!/usr/bin/env python3
"""Unit tests for v1.9 scripts: geo_lint and generate_schema_files."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skill" / "grok-geo" / "scripts"
sys.path.insert(0, str(SCRIPTS))


class TestGeoLint(unittest.TestCase):
    """Test geo_lint.py — GEO compliance lint (92 rules, 6 dimensions)."""

    def test_import(self):
        """Test that geo_lint module can be imported."""
        import geo_lint
        self.assertTrue(hasattr(geo_lint, 'run_lint'))

    def test_run_lint_function_signature(self):
        """Test run_lint function signature."""
        import inspect
        from geo_lint import run_lint
        sig = inspect.signature(run_lint)
        params = list(sig.parameters.keys())
        self.assertGreater(len(params), 0)


class TestGenerateSchemaFiles(unittest.TestCase):
    """Test generate_schema_files.py — AI-readable file generation (5 types)."""

    def test_import(self):
        """Test that generate_schema_files module can be imported."""
        import generate_schema_files
        self.assertTrue(hasattr(generate_schema_files, 'generate_llms_txt'))
        self.assertTrue(hasattr(generate_schema_files, 'generate_llms_full_txt'))
        self.assertTrue(hasattr(generate_schema_files, 'generate_entity_json'))
        self.assertTrue(hasattr(generate_schema_files, 'generate_brand_json'))
        self.assertTrue(hasattr(generate_schema_files, 'generate_aeo_json'))

    def test_generate_llms_txt_function_signature(self):
        """Test generate_llms_txt function signature."""
        import inspect
        from generate_schema_files import generate_llms_txt
        sig = inspect.signature(generate_llms_txt)
        params = list(sig.parameters.keys())
        self.assertIn('brand', params)

    def test_generate_entity_json_function_signature(self):
        """Test generate_entity_json function signature."""
        import inspect
        from generate_schema_files import generate_entity_json
        sig = inspect.signature(generate_entity_json)
        params = list(sig.parameters.keys())
        self.assertIn('brand', params)


if __name__ == "__main__":
    unittest.main()