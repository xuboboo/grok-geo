#!/usr/bin/env python3
"""Lightweight eval runner for grok-geo (no model calls)."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
SKILL_ROOT = EVAL_DIR.parent
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from geo_common import (  # noqa: E402
    position_score,
    rate_with_ci,
    geo_score,
    citability_score,
    trust_stack_score,
    freshness_score,
    rag_readiness,
)
from rank_opportunities import score_opportunity  # noqa: E402


def eval_metric_fixtures() -> list[dict]:
    data = json.loads((EVAL_DIR / "metric-fixtures.json").read_text(encoding="utf-8"))
    results = []
    for fix in data["fixtures"]:
        exp = fix["expected"]
        mr = rate_with_ci(fix["brand_mentions"], fix["valid_answers"])["rate"]
        rr = rate_with_ci(fix["brand_recommendations"], fix["recommendation_answers"])["rate"]
        oc = rate_with_ci(fix["owned_citation_answers"], fix["valid_answers"])["rate"]
        ok = True
        msgs = []
        for name, got, want in [
            ("mention_rate", mr, exp["mention_rate"]),
            ("recommendation_rate", rr, exp["recommendation_rate"]),
            ("owned_citation_rate", oc, exp["owned_citation_rate"]),
        ]:
            if want is None and got is None:
                continue
            if want is None or got is None or abs(got - want) > 1e-9:
                ok = False
                msgs.append(f"{name}: got {got} want {want}")
        results.append({"id": fix["id"], "ok": ok, "detail": "; ".join(msgs)})

    for i, row in enumerate(data.get("position_scores") or []):
        got = position_score(row["mention_type"], row.get("rank"))
        ok = abs(got - row["expected"]) < 1e-9
        results.append(
            {
                "id": f"POS{i+1}",
                "ok": ok,
                "detail": "" if ok else f"got {got} want {row['expected']}",
            }
        )

    for i, row in enumerate(data.get("opportunity_scores") or []):
        got = score_opportunity(row["scores"])
        ok = abs(got - row["expected_total"]) < 1e-9
        results.append(
            {
                "id": f"OPP{i+1}",
                "ok": ok,
                "detail": "" if ok else f"got {got} want {row['expected_total']}",
            }
        )
    return results


def eval_trigger_heuristic() -> list[dict]:
    """Keyword heuristic proxy for skill description matching (not a model)."""
    positive_kw = (
        "geo", "ai搜索", "ai 搜索", "品牌诊断", "品牌审计", "引用",
        "推荐我的竞争", "visibility", "chatgpt", "诊断", "曝光",
        "perplexity", "claude", "引用率", "推荐份额", "generative engine",
        "竞争对手.*推荐", "品牌.*提及", "可见度",
    )
    negative_kw = (
        "写一篇", "解释一下", "抓取", "关键词研究", "保证", "收费网站",
        "公众号", "小红书推广", "爬虫",
    )
    negative_re = (r"部署.*平台", r"部署.*saaS", r"注册.*账号")
    results = []
    with (EVAL_DIR / "trigger-prompts.csv").open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            prompt = (row["prompt"] or "").lower()
            should = str(row["should_trigger"]).lower() == "true"
            import re as _re
            score_pos = sum(1 for k in positive_kw if k.lower() in prompt)
            score_pos += sum(
                1 for k in ("竞争对手.*推荐", "品牌.*提及", "推荐.*分析")
                if _re.search(k, prompt)
            )
            score_neg = sum(1 for k in negative_kw if k.lower() in prompt)
            score_neg += sum(1 for k in negative_re if _re.search(k, prompt))
            predict = score_pos > 0 and score_neg == 0
            if "seo" in prompt and "geo" not in prompt:
                predict = False
            results.append(
                {
                    "id": row["id"],
                    "ok": predict == should,
                    "detail": f"predict={predict} should={should}",
                }
            )
    return results


def eval_security_cases() -> list[dict]:
    results = []
    for line in (EVAL_DIR / "security-cases.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        case = json.loads(line)
        results.append({"id": case["id"], "ok": bool(case.get("expect")), "detail": case.get("expect")})
    return results


def eval_security_structural() -> list[dict]:
    """Verify security-relevant code structures exist."""
    results = []
    skill_md = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    results.append({"id": "SEC_SKILL_SAFETY", "ok": "## Safety" in skill_md, "detail": "SKILL.md must contain Safety section"})
    results.append({"id": "SEC_NO_SECRETS", "ok": "never read secrets" in skill_md.lower(), "detail": "SKILL.md must prohibit reading secrets"})
    results.append({"id": "SEC_NO_FABRICATE", "ok": "fabricate" in skill_md.lower(), "detail": "SKILL.md must prohibit fabricating citations"})
    results.append({"id": "SEC_NO_GUARANTEE", "ok": "guarantee" in skill_md.lower(), "detail": "SKILL.md must prohibit guaranteeing rankings"})

    constants_src = (SCRIPTS / "core" / "constants.py").read_text(encoding="utf-8")
    path_utils_src = (SCRIPTS / "core" / "path_utils.py").read_text(encoding="utf-8")
    results.append({"id": "SEC_FORBIDDEN_PROMISES", "ok": "FORBIDDEN_PROMISE_PATTERNS" in constants_src, "detail": "core/constants.py must define FORBIDDEN_PROMISE_PATTERNS"})
    results.append({"id": "SEC_PATH_CONTAINMENT", "ok": "resolve_under" in path_utils_src and "escapes base directory" in path_utils_src, "detail": "core/path_utils.py must have path containment logic"})

    vr_src = (SCRIPTS / "validate_report.py").read_text(encoding="utf-8")
    results.append({"id": "SEC_REPORT_VALIDATES_PROMISES", "ok": "FORBIDDEN_PROMISE_PATTERNS" in vr_src, "detail": "validate_report.py must check FORBIDDEN_PROMISE_PATTERNS"})
    results.append({"id": "SEC_REPORT_TRACEABILITY", "ok": "evidence_urls" in vr_src and "UNTRACEABLE_URL" in vr_src, "detail": "validate_report.py must verify URL traceability"})

    vi_src = (SCRIPTS / "validate_input.py").read_text(encoding="utf-8")
    results.append({"id": "SEC_INPUT_SENSITIVE_SCAN", "ok": "scan_sensitive" in vi_src and "api_key" in vi_src.lower(), "detail": "validate_input.py must scan for sensitive data patterns"})

    return results


def eval_workflow_cases() -> list[dict]:
    results = []
    for line in (EVAL_DIR / "workflow-cases.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        case = json.loads(line)
        results.append({"id": case["id"], "ok": case.get("expected") is True, "detail": case.get("check")})
    return results


# ─── New v1.1+ eval functions ────────────────────────────────────────

def eval_geo_score_cases() -> list[dict]:
    """Test geo_score composite scoring and band assignment."""
    data = json.loads((EVAL_DIR / "metric-fixtures.json").read_text(encoding="utf-8"))
    results = []
    for case in data.get("geo_score_cases") or []:
        got = geo_score(
            case["visibility_score"],
            case["mention_rate"],
            case["recommendation_rate"],
            case["owned_citation_rate"],
        )
        ok = got["band"] == case["expected_band"]
        results.append({
            "id": case["id"],
            "ok": ok,
            "detail": "" if ok else f"band={got['band']} want={case['expected_band']} score={got['score']}",
        })
    return results


def eval_recommendation_types() -> list[dict]:
    """Test RECOMMENDATION_TYPE_SCORES mapping."""
    from geo_common import RECOMMENDATION_TYPE_SCORES
    data = json.loads((EVAL_DIR / "metric-fixtures.json").read_text(encoding="utf-8"))
    results = []
    for case in data.get("recommendation_types") or []:
        got = RECOMMENDATION_TYPE_SCORES.get(case["type"])
        ok = got is not None and abs(got - case["expected_score"]) < 1e-9
        results.append({
            "id": f"RT_{case['type']}",
            "ok": ok,
            "detail": "" if ok else f"got={got} want={case['expected_score']}",
        })
    return results


def eval_sentiment_cases() -> list[dict]:
    """Test sentiment index calculation (average of scores)."""
    data = json.loads((EVAL_DIR / "metric-fixtures.json").read_text(encoding="utf-8"))
    results = []
    for case in data.get("sentiment_cases") or []:
        scores = case["scores"]
        if not scores:
            got = None
        else:
            got = round(sum(scores) / len(scores), 1)
        want = case["expected_index"]
        ok = (got is None and want is None) or (got is not None and want is not None and abs(got - want) < 1e-9)
        results.append({
            "id": case["id"],
            "ok": ok,
            "detail": "" if ok else f"got={got} want={want}",
        })
    return results


def eval_citability_cases() -> list[dict]:
    """Test citability_score function."""
    data = json.loads((EVAL_DIR / "metric-fixtures.json").read_text(encoding="utf-8"))
    results = []
    for case in data.get("citability_cases") or []:
        got = citability_score(case["method_scores"])
        ok = got["band"] == case["expected_band"]
        results.append({
            "id": case["id"],
            "ok": ok,
            "detail": "" if ok else f"band={got['band']} want={case['expected_band']} score={got['score']}",
        })
    return results


def eval_trust_stack_cases() -> list[dict]:
    """Test trust_stack_score function."""
    data = json.loads((EVAL_DIR / "metric-fixtures.json").read_text(encoding="utf-8"))
    results = []
    for case in data.get("trust_stack_cases") or []:
        got = trust_stack_score(case["layers"])
        ok = got["grade"] == case["expected_grade"]
        results.append({
            "id": case["id"],
            "ok": ok,
            "detail": "" if ok else f"grade={got['grade']} want={case['expected_grade']} score={got['score']}",
        })
    return results


def eval_freshness_cases() -> list[dict]:
    """Test freshness_score function."""
    data = json.loads((EVAL_DIR / "metric-fixtures.json").read_text(encoding="utf-8"))
    results = []
    for case in data.get("freshness_cases") or []:
        got = freshness_score(case["decay_signals"])
        ok = got["band"] == case["expected_band"]
        results.append({
            "id": case["id"],
            "ok": ok,
            "detail": "" if ok else f"band={got['band']} want={case['expected_band']} score={got['score']}",
        })
    return results


def eval_rag_readiness_cases() -> list[dict]:
    """Test rag_readiness function."""
    data = json.loads((EVAL_DIR / "metric-fixtures.json").read_text(encoding="utf-8"))
    results = []
    for case in data.get("rag_readiness_cases") or []:
        got = rag_readiness(case["dimensions"])
        ok = got["band"] == case["expected_band"]
        results.append({
            "id": case["id"],
            "ok": ok,
            "detail": "" if ok else f"band={got['band']} want={case['expected_band']} score={got['score']}",
        })
    return results


def _grade_from_score(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def eval_geo_lint_cases() -> list[dict]:
    """Test GEO lint grading logic."""
    data = json.loads((EVAL_DIR / "metric-fixtures.json").read_text(encoding="utf-8"))
    results = []
    weights = {"schema": 0.25, "crawler": 0.20, "citability": 0.25, "entity": 0.15, "multimodal": 0.08, "i18n": 0.07}
    for case in data.get("geo_lint_cases") or []:
        dims = case["dimension_scores"]
        raw = sum(dims.get(k, 0) * w for k, w in weights.items())
        error_deduction = case.get("errors", 0) * 5
        warning_deduction = case.get("warnings", 0) * 2
        score = max(0.0, raw - error_deduction - warning_deduction)
        got_grade = _grade_from_score(score)
        ok = got_grade == case["expected_grade"]
        results.append({
            "id": case["id"],
            "ok": ok,
            "detail": "" if ok else f"grade={got_grade} want={case['expected_grade']} score={score:.1f}",
        })
    return results


def eval_entity_kg_cases() -> list[dict]:
    """Test entity KG grading logic."""
    data = json.loads((EVAL_DIR / "metric-fixtures.json").read_text(encoding="utf-8"))
    results = []
    for case in data.get("entity_kg_cases") or []:
        dims = case["dimensions"]
        score = sum(dims.values())
        got_grade = _grade_from_score(score)
        ok = got_grade == case["expected_grade"]
        results.append({
            "id": case["id"],
            "ok": ok,
            "detail": "" if ok else f"grade={got_grade} want={case['expected_grade']} score={score}",
        })
    return results


def eval_i18n_cases() -> list[dict]:
    """Test i18n grading logic."""
    data = json.loads((EVAL_DIR / "metric-fixtures.json").read_text(encoding="utf-8"))
    results = []
    for case in data.get("i18n_cases") or []:
        dims = case["dimensions"]
        score = sum(dims.values())
        got_grade = _grade_from_score(score)
        ok = got_grade == case["expected_grade"]
        results.append({
            "id": case["id"],
            "ok": ok,
            "detail": "" if ok else f"grade={got_grade} want={case['expected_grade']} score={score}",
        })
    return results


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Run grok-geo evals")
    parser.add_argument("--output", default=None, help="Save JSON report to file")
    args, _ = parser.parse_known_args()

    all_results = []
    # Core v1.0 evals
    all_results.extend(eval_metric_fixtures())
    all_results.extend(eval_trigger_heuristic())
    all_results.extend(eval_security_cases())
    all_results.extend(eval_security_structural())
    all_results.extend(eval_workflow_cases())
    # Grey area fixes (v1.1 fixtures that existed but were untested)
    all_results.extend(eval_geo_score_cases())
    all_results.extend(eval_recommendation_types())
    # New v1.1+ metric evals
    all_results.extend(eval_sentiment_cases())
    all_results.extend(eval_citability_cases())
    all_results.extend(eval_trust_stack_cases())
    all_results.extend(eval_freshness_cases())
    all_results.extend(eval_rag_readiness_cases())
    all_results.extend(eval_geo_lint_cases())
    all_results.extend(eval_entity_kg_cases())
    all_results.extend(eval_i18n_cases())

    failed = [r for r in all_results if not r["ok"]]
    report = {
        "total": len(all_results),
        "passed": len(all_results) - len(failed),
        "failed": len(failed),
        "failures": failed,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.output:
        from geo_common import write_json
        write_json(Path(args.output), report)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())