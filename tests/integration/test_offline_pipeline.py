#!/usr/bin/env python3
"""Integration: offline fixture full pipeline."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skill" / "grok-geo"
SCRIPTS = SKILL / "scripts"
EXAMPLES = SKILL / "examples"


class TestOfflineIntegration(unittest.TestCase):
    def test_offline_pipeline(self):
        py = sys.executable
        base = Path(tempfile.mkdtemp(prefix="geo-int-"))
        try:
            # remove sticky run id if re-run
            run_id = "geo_integration_test_01"
            run_dir = base / run_id
            if run_dir.exists():
                shutil.rmtree(run_dir)
            cmd = [
                py,
                str(EXAMPLES / "run_offline_demo.py"),
                "--base-dir",
                str(base),
                "--keep",
            ]
            # demo uses fixed run id; patch by running steps if conflict
            # Prefer invoking demo after ensuring clean
            # Override: reimplement with unique run via initialize
            work = Path(tempfile.mkdtemp())
            norm = work / "norm.json"
            subprocess.check_call(
                [
                    py,
                    str(SCRIPTS / "validate_input.py"),
                    "--input",
                    str(EXAMPLES / "input.complete.json"),
                    "--output",
                    str(norm),
                ]
            )
            out = subprocess.check_output(
                [
                    py,
                    str(SCRIPTS / "initialize_run.py"),
                    "--input",
                    str(norm),
                    "--base-dir",
                    str(base),
                ],
                text=True,
            )
            info = json.loads(out)
            run_dir = Path(info["run_dir"])
            inter = run_dir / "intermediate"
            inter.mkdir(exist_ok=True)
            shutil.copy(EXAMPLES / "questions.offline.json", inter / "questions.json")
            subprocess.check_call(
                [
                    py,
                    str(SCRIPTS / "validate_questions.py"),
                    "--questions",
                    str(inter / "questions.json"),
                    "--input",
                    str(run_dir / "input" / "brand.json"),
                ]
            )
            for line in (EXAMPLES / "offline-results.jsonl").read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                row["run_id"] = info["run_id"]
                tmp = work / f"{row['question_id']}.json"
                tmp.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
                subprocess.check_call(
                    [
                        py,
                        str(SCRIPTS / "append_search_result.py"),
                        "--run-dir",
                        str(run_dir),
                        "--input",
                        str(tmp),
                    ]
                )
            shutil.copy(EXAMPLES / "entity_analysis.offline.jsonl", inter / "entity_analysis.jsonl")
            shutil.copy(EXAMPLES / "claims.offline.json", inter / "claims.json")
            shutil.copy(EXAMPLES / "content_briefs.offline.json", inter / "content_briefs.json")
            subprocess.check_call(
                [
                    py,
                    str(SCRIPTS / "classify_citations.py"),
                    "--run-dir",
                    str(run_dir),
                    "--output",
                    str(inter / "citations.json"),
                ]
            )
            subprocess.check_call(
                [
                    py,
                    str(SCRIPTS / "calculate_metrics.py"),
                    "--questions",
                    str(inter / "questions.json"),
                    "--entities",
                    str(inter / "entity_analysis.jsonl"),
                    "--citations",
                    str(inter / "citations.json"),
                    "--claims",
                    str(inter / "claims.json"),
                    "--output",
                    str(inter / "metrics.json"),
                ]
            )
            subprocess.check_call(
                [
                    py,
                    str(SCRIPTS / "rank_opportunities.py"),
                    "--input",
                    str(EXAMPLES / "opportunities.offline.json"),
                    "--output",
                    str(inter / "opportunities.json"),
                ]
            )
            subprocess.check_call([py, str(SCRIPTS / "render_report.py"), "--run-dir", str(run_dir)])
            val = subprocess.run(
                [
                    py,
                    str(SCRIPTS / "validate_report.py"),
                    "--run-dir",
                    str(run_dir),
                    "--update-manifest",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(val.returncode, 0, val.stdout + val.stderr)
            result = json.loads(val.stdout)
            self.assertTrue(result["ok"], result)
            for name in (
                "report.md",
                "report.json",
                "questions.csv",
                "evidence.csv",
                "opportunities.csv",
                "manifest.json",
            ):
                self.assertTrue((run_dir / "output" / name).exists(), name)
            metrics = json.loads((inter / "metrics.json").read_text(encoding="utf-8"))
            self.assertIsNotNone(metrics["mention_rate"]["rate"])
            self.assertEqual(metrics["sample"]["valid_answer_count"], 10)
        finally:
            shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()