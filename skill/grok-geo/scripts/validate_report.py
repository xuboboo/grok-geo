#!/usr/bin/env python3
"""Validate report consistency and URL traceability (§17.6)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (  # noqa: E402
    FORBIDDEN_PROMISE_PATTERNS,
    LIMITATION_TEXT,
    append_event,
    load_manifest,
    load_schema,
    print_json,
    read_json,
    read_jsonl,
    save_manifest,
    utc_now_iso,
    validate_against_schema,
)
from normalize_urls import normalize_url  # noqa: E402


REQUIRED_OUTPUTS = [
    "report.md",
    "report.json",
    "questions.csv",
    "evidence.csv",
    "opportunities.csv",
    "manifest.json",
]


def collect_evidence_urls(run_dir: Path) -> Set[str]:
    urls: Set[str] = set()
    sr = run_dir / "raw" / "search_results.jsonl"
    if sr.exists():
        for row in read_jsonl(sr):
            for cit in row.get("citations") or []:
                u = cit.get("url")
                if u:
                    urls.add(u)
                    n = normalize_url(u)
                    if n.get("canonical_url"):
                        urls.add(n["canonical_url"])
            for src in row.get("sources") or []:
                u = src.get("url")
                if u:
                    urls.add(u)
                    n = normalize_url(u)
                    if n.get("canonical_url"):
                        urls.add(n["canonical_url"])
    brand_path = run_dir / "input" / "brand.json"
    if brand_path.exists():
        brand = read_json(brand_path)
        if brand.get("website"):
            urls.add(brand["website"])
            n = normalize_url(brand["website"])
            if n.get("canonical_url"):
                urls.add(n["canonical_url"])
        for fact in brand.get("known_facts") or []:
            u = fact.get("source_url")
            if u:
                urls.add(u)
                n = normalize_url(u)
                if n.get("canonical_url"):
                    urls.add(n["canonical_url"])
        for c in brand.get("competitors") or []:
            u = c.get("website")
            if u:
                urls.add(u)
    return urls


def extract_md_urls(text: str) -> List[str]:
    # markdown links + bare urls
    urls = re.findall(r"\((https?://[^)\s]+)\)", text)
    urls += re.findall(r"(?<![\(\[])(https?://[^\s\)\]\>]+)", text)
    return urls


def metrics_match(report_metrics: Dict[str, Any], file_metrics: Dict[str, Any]) -> List[str]:
    errors = []
    for key in (
        "mention_rate",
        "recommendation_rate",
        "owned_citation_rate",
        "earned_support_rate",
        "question_coverage",
    ):
        a = (report_metrics.get(key) or {}).get("rate")
        b = (file_metrics.get(key) or {}).get("rate")
        if a is None and b is None:
            continue
        if a is None or b is None or abs(float(a) - float(b)) > 1e-9:
            errors.append(f"metric mismatch {key}: report={a} file={b}")
    ra = (report_metrics.get("visibility_score") or {}).get("score")
    rb = (file_metrics.get("visibility_score") or {}).get("score")
    if ra is not None and rb is not None and abs(float(ra) - float(rb)) > 1e-9:
        errors.append(f"visibility_score mismatch: {ra} vs {rb}")
    return errors


def validate_report(run_dir: Path) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    out_dir = run_dir / "output"

    for name in REQUIRED_OUTPUTS:
        if not (out_dir / name).exists():
            errors.append(f"missing output file: {name}")

    report_path = out_dir / "report.json"
    report = None
    if report_path.exists():
        try:
            report = read_json(report_path)
        except Exception as exc:
            errors.append(f"REPORT_JSON_INVALID: {exc}")

    if report is not None:
        schema = load_schema("report.schema.json")
        se = validate_against_schema(report, schema)
        errors.extend([f"schema: {e}" for e in se])

        if len(report.get("opportunities") or []) > 10:
            errors.append("opportunities > 10")
        if len(report.get("content_briefs") or []) > 5:
            errors.append("content_briefs > 5")

        limitations = report.get("limitations") or []
        lim_text = " ".join(str(x) for x in limitations)
        if LIMITATION_TEXT[:20] not in lim_text and "不保证" not in lim_text:
            errors.append("missing methodology limitation statement")

        md_path = out_dir / "report.md"
        if md_path.exists():
            md = md_path.read_text(encoding="utf-8")
            for pat in FORBIDDEN_PROMISE_PATTERNS:
                if re.search(pat, md):
                    errors.append(f"REPORT_FORBIDDEN_CLAIM: pattern {pat}")
            if "方法限制" not in md and "不保证" not in md:
                errors.append("REPORT_MISSING_SECTION: limitations")

            evidence_urls = collect_evidence_urls(run_dir)
            # normalize evidence set
            evidence_canon = set()
            for u in evidence_urls:
                evidence_canon.add(u)
                n = normalize_url(u)
                if n.get("canonical_url"):
                    evidence_canon.add(n["canonical_url"])

            for url in extract_md_urls(md):
                n = normalize_url(url)
                cand = {url, n.get("canonical_url") or ""}
                if not cand.intersection(evidence_canon):
                    # allow example.com style only if in evidence; otherwise error
                    errors.append(f"REPORT_UNTRACEABLE_URL: {url}")

            for ev in report.get("evidence_index") or []:
                url = ev.get("url") or ""
                if not url:
                    continue
                n = normalize_url(url)
                if url not in evidence_canon and (n.get("canonical_url") not in evidence_canon):
                    errors.append(f"REPORT_UNTRACEABLE_URL evidence_index: {url}")

        metrics_path = run_dir / "intermediate" / "metrics.json"
        if metrics_path.exists() and report.get("metrics"):
            file_metrics = read_json(metrics_path)
            errors.extend(metrics_match(report.get("metrics") or {}, file_metrics))

        exe = report.get("execution_summary") or {}
        if (exe.get("failed_result_count") or 0) > 0:
            # failure disclosure expected in markdown
            md_path = out_dir / "report.md"
            if md_path.exists():
                md = md_path.read_text(encoding="utf-8")
                if "失败" not in md and "failed" not in md.lower():
                    warnings.append("failed samples not clearly disclosed in markdown")

    try:
        manifest = load_manifest(run_dir)
    except FileNotFoundError:
        errors.append("manifest missing")
        manifest = {}

    success = int(manifest.get("successful_result_count") or 0)
    total = int(manifest.get("search_result_count") or 0)
    rate = (success / total) if total else 0.0

    result = {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "success_rate": rate,
        "suggested_status": None,
    }

    if result["ok"]:
        if rate >= 0.90:
            result["suggested_status"] = "COMPLETED"
        elif rate >= 0.80:
            result["suggested_status"] = "PARTIAL"
        else:
            result["suggested_status"] = "FAILED"
            result["ok"] = False
            result["errors"].append("effective search rate < 80%")
    else:
        result["suggested_status"] = "FAILED"

    return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate GEO report outputs")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--update-manifest", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir)
    result = validate_report(run_dir)

    if args.update_manifest:
        try:
            manifest = load_manifest(run_dir)
            manifest["status"] = result["suggested_status"]
            if result["suggested_status"] in {"COMPLETED", "PARTIAL", "FAILED"}:
                manifest["completed_at"] = utc_now_iso()
            if not result["ok"]:
                errs = list(manifest.get("errors") or [])
                for e in result["errors"]:
                    errs.append({"ts": utc_now_iso(), "message": e})
                manifest["errors"] = errs
            save_manifest(run_dir, manifest)
        except FileNotFoundError:
            print("warn: manifest not found, validation not recorded", file=sys.stderr)

    append_event(run_dir, "report_validated", result)
    print_json(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())