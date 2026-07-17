#!/usr/bin/env python3
"""Validate question map ratio constraints (§8)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (  # noqa: E402
    RECOMMENDATION_INTENTS,
    contains_brand_token,
    load_schema,
    normalize_question_text,
    print_json,
    read_json,
    validate_against_schema,
    write_json,
)


def load_questions(path: Path) -> List[Dict[str, Any]]:
    data = read_json(path)
    if isinstance(data, dict) and "questions" in data:
        return list(data["questions"])
    if isinstance(data, list):
        return list(data)
    raise ValueError("questions must be list or {questions: [...]}")


def validate_questions(
    questions: Sequence[Dict[str, Any]],
    brand_name: str,
    aliases: Optional[Sequence[str]] = None,
    *,
    strict_schema: bool = True,
) -> Dict[str, Any]:
    schema = load_schema("question.schema.json")
    errors: List[str] = []
    warnings: List[str] = []
    n = len(questions)
    if n == 0:
        errors.append("empty question list")
        return {"ok": False, "errors": errors, "warnings": warnings, "stats": {}}

    no_brand = 0
    rec_comp = 0
    brand_fact = 0
    seen_norm = set()

    for i, q in enumerate(questions):
        if strict_schema:
            se = validate_against_schema(q, schema)
            if se:
                errors.extend([f"q[{i}] {e}" for e in se])
        qid = q.get("id") or f"idx-{i}"
        text = q.get("text") or ""
        if not q.get("normalized_text"):
            q = dict(q)
            q["normalized_text"] = normalize_question_text(text)

        contains = q.get("contains_target_brand")
        if contains is None:
            contains = contains_brand_token(text, brand_name, aliases)
        if not contains:
            no_brand += 1
        intent = q.get("intent") or ""
        if intent in RECOMMENDATION_INTENTS:
            rec_comp += 1
        if intent == "brand_fact":
            brand_fact += 1
        if q.get("business_value") is None:
            errors.append(f"{qid}: missing business_value")
        nt = q.get("normalized_text") or normalize_question_text(text)
        if nt in seen_norm:
            warnings.append(f"duplicate normalized question: {qid}")
        seen_norm.add(nt)

    no_brand_ratio = no_brand / n
    rec_ratio = rec_comp / n
    brand_fact_ratio = brand_fact / n

    if no_brand_ratio < 0.70:
        errors.append(f"non-brand questions ratio {no_brand_ratio:.3f} < 0.70")
    if rec_ratio < 0.30:
        errors.append(f"recommendation/comparison/purchase ratio {rec_ratio:.3f} < 0.30")
    if brand_fact_ratio > 0.20:
        errors.append(f"brand_fact ratio {brand_fact_ratio:.3f} > 0.20")

    stats = {
        "count": n,
        "no_brand_count": no_brand,
        "no_brand_ratio": no_brand_ratio,
        "recommendation_like_count": rec_comp,
        "recommendation_like_ratio": rec_ratio,
        "brand_fact_count": brand_fact,
        "brand_fact_ratio": brand_fact_ratio,
    }
    return {"ok": len(errors) == 0, "errors": errors, "warnings": warnings, "stats": stats}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate question map constraints")
    parser.add_argument("--questions", required=True, help="questions.json path")
    parser.add_argument("--brand-name", default=None)
    parser.add_argument("--input", default=None, help="brand/normalized input for brand_name")
    parser.add_argument("--output", default=None, help="optional validation result JSON")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    brand_name = args.brand_name
    aliases: List[str] = []
    if args.input:
        brand = read_json(args.input)
        brand_name = brand_name or brand.get("brand_name")
        aliases = list(brand.get("brand_aliases") or [])
    if not brand_name:
        print("brand_name required via --brand-name or --input", file=sys.stderr)
        return 2

    try:
        questions = load_questions(Path(args.questions))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    result = validate_questions(questions, brand_name, aliases)
    if args.output:
        write_json(args.output, result)
    if args.json or True:
        print_json(result)
    return 0 if result["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())