#!/usr/bin/env python3
"""End-to-end offline_import demo using packaged examples."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
EXAMPLES = SKILL_ROOT / "examples"


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run offline GEO audit demo")
    parser.add_argument(
        "--base-dir",
        default=None,
        help="runs base dir (default: temp or GEO_AUDIT_RUNS_DIR)",
    )
    parser.add_argument("--keep", action="store_true", help="keep run dir (print path)")
    args = parser.parse_args()

    py = sys.executable
    base = Path(args.base_dir) if args.base_dir else Path(tempfile.mkdtemp(prefix="geo-runs-"))
    base.mkdir(parents=True, exist_ok=True)

    work = Path(tempfile.mkdtemp(prefix="geo-offline-"))
    try:
        norm = work / "normalized_input.json"
        run(
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
                "--run-id",
                "geo_offline_demo_00000001",
            ],
            text=True,
        )
        info = json.loads(out)
        run_dir = Path(info["run_dir"])
        inter = run_dir / "intermediate"
        inter.mkdir(parents=True, exist_ok=True)

        shutil.copy(EXAMPLES / "questions.offline.json", inter / "questions.json")
        run(
            [
                py,
                str(SCRIPTS / "validate_questions.py"),
                "--questions",
                str(inter / "questions.json"),
                "--input",
                str(run_dir / "input" / "brand.json"),
            ]
        )

        # import search results
        for line in (EXAMPLES / "offline-results.jsonl").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            row["run_id"] = info["run_id"]
            tmp = work / f"{row['question_id']}.json"
            tmp.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
            run(
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

        run(
            [
                py,
                str(SCRIPTS / "classify_citations.py"),
                "--run-dir",
                str(run_dir),
                "--output",
                str(inter / "citations.json"),
            ]
        )
        run(
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
        run(
            [
                py,
                str(SCRIPTS / "rank_opportunities.py"),
                "--input",
                str(EXAMPLES / "opportunities.offline.json"),
                "--output",
                str(inter / "opportunities.json"),
            ]
        )
        run([py, str(SCRIPTS / "render_report.py"), "--run-dir", str(run_dir)])
        run(
            [
                py,
                str(SCRIPTS / "validate_report.py"),
                "--run-dir",
                str(run_dir),
                "--update-manifest",
            ]
        )
        run([py, str(SCRIPTS / "package_outputs.py"), "--run-dir", str(run_dir)])

        print(json.dumps({"ok": True, "run_dir": str(run_dir)}, ensure_ascii=False, indent=2))
        return 0
    finally:
        if not args.keep:
            # keep base run if user wants inspection via printed path; always cleanup work
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())