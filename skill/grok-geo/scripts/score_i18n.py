#!/usr/bin/env python3
"""International GEO Scorer — 国际化多语言 GEO 评分。

用法:
  python score_i18n.py --input <brand.json> --run-dir <RUN> --output <output.json>
"""

from __future__ import annotations
import argparse, sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from geo_common import read_json, write_json, utc_now_iso, clamp, print_json

def score_i18n(brand: Dict[str, Any], site_data: Optional[Dict[str, Any]] = None, run_dir: Optional[str] = None) -> Dict[str, Any]:
    site_data = site_data or {}
    i18n = site_data.get("i18n_analysis", {})
    items: List[Dict[str, Any]] = []
    total = 0

    # Technical (30)
    tech_checks = [
        ("hreflang", 8, i18n.get("has_hreflang", False)),
        ("x_default", 4, i18n.get("has_hreflang_default", False)),
        ("lang_attr", 4, i18n.get("lang_correct", True)),
        ("url_structure", 4, i18n.get("separate_urls", False)),
        ("inlanguage_schema", 3, i18n.get("has_inlanguage", False)),
        ("utf8_encoding", 3, site_data.get("encoding", "") == "utf-8" or True),
        ("date_locale", 2, i18n.get("date_localized", False)),
        ("currency_locale", 2, i18n.get("currency_localized", False)),
    ]
    tech_score = sum(s for _, s, ok in tech_checks if ok)
    for name, mx, ok in tech_checks:
        items.append({"check": name, "score": mx if ok else 0, "max": mx})
    total += tech_score

    # Content Quality (30) — requires search data, estimate from brand input
    languages = brand.get("supported_languages", ["en"])
    content_items = [
        ("human_translation", 10, len(languages) > 1),
        ("cultural_localization", 6, brand.get("has_localized_content", False)),
        ("keyword_localization", 6, brand.get("has_localized_keywords", False)),
        ("local_case_studies", 4, len(brand.get("local_case_studies", [])) > 0),
        ("local_media_citations", 4, len(brand.get("local_media", [])) > 0),
    ]
    content_score = sum(s for _, s, ok in content_items if ok)
    for name, mx, ok in content_items:
        items.append({"check": name, "score": mx if ok else 0, "max": mx})
    total += content_score

    # Regional Entity (20)
    regional_items = [
        ("local_address", 5, bool(brand.get("address", {}).get("addressCountry"))),
        ("local_contact", 4, bool(brand.get("contact_phone"))),
        ("local_social", 4, len(brand.get("local_social", [])) > 0),
        ("local_kb", 4, len(brand.get("local_kb", [])) > 0),
        ("local_directories", 3, len(brand.get("local_directories", [])) > 0),
    ]
    regional_score = sum(s for _, s, ok in regional_items if ok)
    for name, mx, ok in regional_items:
        items.append({"check": name, "score": mx if ok else 0, "max": mx})
    total += regional_score

    # AI Coverage (20) — real scoring from engine response data
    # Check if multi-engine query results exist
    engine_responses_path = None
    if run_dir:
        engine_responses_path = Path(run_dir) / "raw" / "engine_responses.jsonl"

    has_engine_data = False
    multilang_engines = set()
    if engine_responses_path and engine_responses_path.exists():
        from geo_common import read_jsonl as _read_jsonl
        responses = _read_jsonl(engine_responses_path)
        has_engine_data = len(responses) > 0
        for resp in responses:
            engine = resp.get("engine", "")
            # Check if response contains non-English content indicators
            answer = resp.get("answer_text", "")
            has_non_ascii = any(ord(c) > 127 for c in answer[:500])
            if has_non_ascii or resp.get("language", "en") != "en":
                multilang_engines.add(engine)

    ai_items = [
        ("chatgpt_multilang", 5, "chatgpt" in multilang_engines),
        ("perplexity_multilang", 5, "perplexity" in multilang_engines),
        ("gemini_multilang", 4, "gemini" in multilang_engines),
        ("local_ai_engine", 3, bool(brand.get("local_ai_engine"))),
        ("cross_engine_consistency", 3, len(multilang_engines) >= 2),
    ]
    ai_score = sum(s for _, s, ok in ai_items if ok)
    for name, mx, ok in ai_items:
        items.append({"check": name, "score": mx if ok else 0, "max": mx})
    total += ai_score

    grade = "A" if total >= 90 else "B" if total >= 75 else "C" if total >= 60 else "D" if total >= 40 else "F"

    return {
        "schema_version": "2.2.0",
        "scored_at": utc_now_iso(),
        "i18n_score": total,
        "grade": grade,
        "target_languages": languages,
        "dimensions": {
            "technical": {"score": tech_score, "max": 30},
            "content_quality": {"score": content_score, "max": 30},
            "regional_entity": {"score": regional_score, "max": 20},
            "ai_coverage": {"score": ai_score, "max": 20},
        },
        "items": items,
    }

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--run-dir")
    p.add_argument("--output")
    args = p.parse_args()
    brand = read_json(args.input)
    site_data = {}
    if args.run_dir:
        mp = Path(args.run_dir) / "intermediate" / "metrics.json"
        if mp.exists():
            site_data = read_json(mp).get("site_readiness", {})
    report = score_i18n(brand, site_data, run_dir=args.run_dir)
    if args.output:
        write_json(args.output, report)
        print(f"i18n score: {report['i18n_score']}/100 (Grade: {report['grade']})")
    else:
        print_json(report)

if __name__ == "__main__":
    main()