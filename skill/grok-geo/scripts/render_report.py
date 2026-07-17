#!/usr/bin/env python3
"""Render report.md, report.json, and CSV outputs (§15-16)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (  # noqa: E402
    LIMITATION_TEXT,
    SKILL_NAME,
    SKILL_VERSION,
    append_event,
    load_manifest,
    print_json,
    read_json,
    read_jsonl,
    save_manifest,
    utc_now_iso,
    write_csv,
    write_json,
)


def _rate_pct(rate_obj: Optional[Dict[str, Any]]) -> str:
    if not rate_obj or rate_obj.get("rate") is None:
        return "数据不足"
    return f"{rate_obj['rate'] * 100:.1f}% ({rate_obj.get('numerator')}/{rate_obj.get('denominator')})"


def _ci_str(rate_obj: Optional[Dict[str, Any]]) -> str:
    if not rate_obj or not rate_obj.get("wilson_ci_95"):
        return "n/a"
    ci = rate_obj["wilson_ci_95"]
    return f"[{ci['low']*100:.1f}%, {ci['high']*100:.1f}%]"


def load_questions(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    data = read_json(path)
    if isinstance(data, list):
        return data
    return list(data.get("questions") or [])


def build_report_json(run_dir: Path) -> Dict[str, Any]:
    run_dir = Path(run_dir)
    brand = read_json(run_dir / "input" / "brand.json")
    manifest = load_manifest(run_dir)
    questions = load_questions(run_dir / "intermediate" / "questions.json")
    metrics = read_json(run_dir / "intermediate" / "metrics.json")
    opps_path = run_dir / "intermediate" / "opportunities.json"
    opportunities = []
    if opps_path.exists():
        opd = read_json(opps_path)
        opportunities = opd if isinstance(opd, list) else list(opd.get("opportunities") or [])

    briefs_path = run_dir / "intermediate" / "content_briefs.json"
    briefs: List[Dict[str, Any]] = []
    if briefs_path.exists():
        bd = read_json(briefs_path)
        briefs = bd if isinstance(bd, list) else list(bd.get("content_briefs") or [])
    briefs = briefs[:5]

    citations = []
    cit_path = run_dir / "intermediate" / "citations.json"
    if cit_path.exists():
        cd = read_json(cit_path)
        citations = cd if isinstance(cd, list) else list(cd.get("citations") or [])

    claims = []
    cl_path = run_dir / "intermediate" / "claims.json"
    if cl_path.exists():
        cld = read_json(cl_path)
        claims = cld if isinstance(cld, list) else list(cld.get("claims") or [])

    search_rows = read_jsonl(run_dir / "raw" / "search_results.jsonl")
    entities_path = run_dir / "intermediate" / "entity_analysis.jsonl"
    entities = read_jsonl(entities_path) if entities_path.exists() else []

    # evidence index from search citations
    evidence_index: List[Dict[str, Any]] = []
    seen_urls = set()
    for row in search_rows:
        for cit in row.get("citations") or []:
            url = cit.get("url") or ""
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            evidence_index.append(
                {
                    "url": url,
                    "title": cit.get("title") or "",
                    "question_id": row.get("question_id"),
                    "source": "search_result",
                }
            )
    for fact in brand.get("known_facts") or []:
        url = fact.get("source_url") or ""
        if url and url not in seen_urls:
            seen_urls.add(url)
            evidence_index.append(
                {
                    "url": url,
                    "title": "user_known_fact",
                    "question_id": None,
                    "source": "user_input",
                }
            )

    # question analysis summary
    ent_by_q = {e.get("question_id"): e for e in entities}
    q_analysis = []
    for q in questions:
        qid = q.get("id")
        er = ent_by_q.get(qid) or {}
        te = None
        for ent in er.get("entities") or []:
            if ent.get("entity_type") == "target_brand":
                te = ent
                break
        q_analysis.append(
            {
                "question_id": qid,
                "text": q.get("text"),
                "intent": q.get("intent"),
                "business_value": q.get("business_value"),
                "brand_mentioned": bool(te and te.get("mentioned")),
                "mention_type": (te or {}).get("mention_type"),
                "recommendation_rank": (te or {}).get("recommendation_rank"),
            }
        )

    # competitor analysis
    comp_stats: Dict[str, Dict[str, Any]] = {}
    for er in entities:
        for ent in er.get("entities") or []:
            if ent.get("entity_type") != "competitor":
                continue
            name = ent.get("canonical_name") or ent.get("entity_id")
            st = comp_stats.setdefault(
                name, {"name": name, "mentions": 0, "recommendations": 0}
            )
            if ent.get("mentioned"):
                st["mentions"] += 1
            if ent.get("mention_type") in {
                "strongly_recommended",
                "recommended",
                "weakly_recommended",
            }:
                st["recommendations"] += 1
    competitor_analysis = list(comp_stats.values())

    # citation analysis
    by_type: Dict[str, int] = {}
    for c in citations:
        t = c.get("source_type") or "unknown"
        by_type[t] = by_type.get(t, 0) + 1

    claim_risks = [
        c
        for c in claims
        if c.get("verification_status")
        in {"incorrect", "outdated", "entity_confusion", "partially_correct"}
        or c.get("risk_level") == "high"
    ]

    success = sum(1 for r in search_rows if r.get("status") == "success" and (r.get("answer_text") or "").strip())
    total_sr = len(search_rows)
    success_rate = (success / total_sr) if total_sr else 0.0

    report = {
        "metadata": {
            "skill_name": SKILL_NAME,
            "skill_version": SKILL_VERSION,
            "run_id": manifest.get("run_id"),
            "generated_at": utc_now_iso(),
            "mode": manifest.get("mode") or brand.get("mode"),
            "status": manifest.get("status"),
        },
        "input": {
            "brand_name": brand.get("brand_name"),
            "website": brand.get("website"),
            "industry": brand.get("industry"),
            "target_customer": brand.get("target_customer"),
            "target_region": brand.get("target_region"),
            "competitors": brand.get("competitors"),
            "language": brand.get("language"),
        },
        "methodology": {
            "search_environment": "openai_web_search or offline_import",
            "question_count": len(questions),
            "batch_size": 5,
            "metrics_script": "scripts/calculate_metrics.py",
            "notes": [
                "所有数值指标由确定性脚本计算。",
                "引用必须来自实际搜索结果或用户输入。",
            ],
        },
        "execution_summary": {
            "search_result_count": total_sr,
            "successful_result_count": success,
            "failed_result_count": total_sr - success,
            "success_rate": success_rate,
            "question_count": len(questions),
            "opportunity_count": len(opportunities),
            "content_brief_count": len(briefs),
        },
        "metrics": metrics,
        "question_analysis": q_analysis,
        "competitor_analysis": competitor_analysis,
        "citation_analysis": {
            "total": len(citations),
            "by_source_type": by_type,
            "citations": citations,
        },
        "claim_risks": claim_risks,
        "opportunities": opportunities[:10],
        "content_briefs": briefs,
        "limitations": [LIMITATION_TEXT],
        "evidence_index": evidence_index,
        "thirty_day_plan": [
            "第1周：修复高风险错误声明，补齐官网核心事实页。",
            "第2周：发布 Top3 机会对应的选购/对比内容。",
            "第3周：补充第三方可引用证据与案例。",
            "第4周：用相同问题样本复测提及率与推荐率。",
        ],
    }
    return report


def render_markdown(report: Dict[str, Any]) -> str:
    m = report.get("metrics") or {}
    brand = (report.get("input") or {}).get("brand_name") or ""
    meta = report.get("metadata") or {}
    exe = report.get("execution_summary") or {}
    lines: List[str] = []
    lines.append(f"# GEO 品牌诊断报告：{brand}")
    lines.append("")
    lines.append(f"- Run ID: `{meta.get('run_id')}`")
    lines.append(f"- 生成时间: {meta.get('generated_at')}")
    lines.append(f"- 模式: {meta.get('mode')}")
    lines.append(f"- Skill: {meta.get('skill_name')} v{meta.get('skill_version')}")
    lines.append("")
    lines.append("## 1. 执行摘要")
    lines.append("")
    lines.append(
        f"本次诊断覆盖 {exe.get('question_count')} 个问题，"
        f"成功搜索 {exe.get('successful_result_count')}/{exe.get('search_result_count')}。"
    )
    mr = m.get("mention_rate") or {}
    rr = m.get("recommendation_rate") or {}
    vs = m.get("visibility_score") or {}
    lines.append(
        f"目标品牌提及率 {_rate_pct(mr)}（Wilson 95% {_ci_str(mr)}），"
        f"推荐率 {_rate_pct(rr)}，可见度分 {vs.get('score')}。"
    )
    lines.append("")
    lines.append("## 2. 品牌和诊断范围")
    lines.append("")
    inp = report.get("input") or {}
    lines.append(f"- 品牌：{inp.get('brand_name')}")
    lines.append(f"- 官网：{inp.get('website')}")
    lines.append(f"- 行业：{inp.get('industry')}")
    lines.append(f"- 目标客户：{inp.get('target_customer')}")
    lines.append(f"- 地区：{', '.join(inp.get('target_region') or []) or '未指定'}")
    comps = inp.get("competitors") or []
    if comps:
        lines.append("- 竞争对手：" + "、".join(c.get("name") for c in comps if c.get("name")))
    lines.append("")
    lines.append("## 3. 方法说明")
    lines.append("")
    for n in (report.get("methodology") or {}).get("notes") or []:
        lines.append(f"- {n}")
    lines.append("")
    lines.append("## 4. 搜索样本")
    lines.append("")
    lines.append(
        f"- 问题数：{exe.get('question_count')}\n"
        f"- 搜索结果：{exe.get('search_result_count')}\n"
        f"- 成功：{exe.get('successful_result_count')}\n"
        f"- 失败：{exe.get('failed_result_count')}\n"
        f"- 成功率：{(exe.get('success_rate') or 0)*100:.1f}%"
    )
    lines.append("")
    lines.append("## 5. 核心指标")
    lines.append("")
    lines.append("| 指标 | 值 | 分子/分母 | Wilson 95% |")
    lines.append("| --- | --- | --- | --- |")
    for key, label in [
        ("mention_rate", "提及率"),
        ("recommendation_rate", "推荐率"),
        ("owned_citation_rate", "自有引用率"),
        ("earned_support_rate", "第三方支持率"),
        ("question_coverage", "问题覆盖率"),
    ]:
        obj = m.get(key) or {}
        rate = obj.get("rate")
        rate_s = f"{rate*100:.2f}%" if rate is not None else "数据不足"
        lines.append(
            f"| {label} | {rate_s} | {obj.get('numerator')}/{obj.get('denominator')} | {_ci_str(obj)} |"
        )
    lines.append(
        f"| 可见度分 | {vs.get('score')} | {vs.get('numerator'):.4f}/{vs.get('denominator'):.4f} | n/a |"
        if vs.get("denominator") is not None
        else f"| 可见度分 | {vs.get('score')} | n/a | n/a |"
    )
    sov = m.get("recommendation_sov") or {}
    sov_r = sov.get("rate")
    lines.append(
        f"| 推荐份额 | {sov_r*100:.2f}% | {sov.get('brand_positive_score')}/{sov.get('denominator')} | n/a |"
        if sov_r is not None
        else "| 推荐份额 | 数据不足 | n/a | n/a |"
    )
    acc = m.get("accuracy_score") or {}
    acc_s = acc.get("score")
    lines.append(
        f"| 信息准确率 | {acc_s*100:.2f}% | correct+0.5*partial / verifiable | n/a |"
        if acc_s is not None
        else "| 信息准确率 | 数据不足 | n/a | n/a |"
    )
    lines.append("")
    lines.append("## 6. 用户问题地图")
    lines.append("")
    for qa in report.get("question_analysis") or []:
        flag = "✓" if qa.get("brand_mentioned") else "·"
        lines.append(
            f"- [{flag}] `{qa.get('question_id')}` ({qa.get('intent')}, bv={qa.get('business_value')}): {qa.get('text')}"
        )
    lines.append("")
    lines.append("## 7. 品牌出现和推荐分析")
    lines.append("")
    mentioned = [qa for qa in report.get("question_analysis") or [] if qa.get("brand_mentioned")]
    lines.append(f"目标品牌在 {len(mentioned)} 个有效问题中被提及。")
    for qa in mentioned:
        lines.append(
            f"- {qa.get('question_id')}: {qa.get('mention_type')} rank={qa.get('recommendation_rank')}"
        )
    lines.append("")
    lines.append("## 8. 竞争对手分析")
    lines.append("")
    for c in report.get("competitor_analysis") or []:
        lines.append(
            f"- {c.get('name')}: 提及 {c.get('mentions')}，推荐 {c.get('recommendations')}"
        )
    if not report.get("competitor_analysis"):
        lines.append("- 无竞争对手信号或未提供竞品。")
    lines.append("")
    lines.append("## 9. 引用来源分析")
    lines.append("")
    ca = report.get("citation_analysis") or {}
    lines.append(f"总引用数：{ca.get('total')}")
    for t, n in sorted((ca.get("by_source_type") or {}).items()):
        lines.append(f"- {t}: {n}")
    lines.append("")
    lines.append("## 10. 自有官网引用情况")
    lines.append("")
    lines.append(f"自有域名引用率：{_rate_pct(m.get('owned_citation_rate'))}")
    owned_cits = [
        c
        for c in (ca.get("citations") or [])
        if c.get("source_type") == "owned"
    ]
    for c in owned_cits[:20]:
        lines.append(f"- [{c.get('title') or c.get('domain')}]({c.get('canonical_url') or c.get('original_url')})")
    lines.append("")
    lines.append("## 11. 错误和过期信息")
    lines.append("")
    risks = report.get("claim_risks") or []
    if not risks:
        lines.append("- 未发现高风险或错误声明，或声明样本不足。")
    for c in risks:
        ref = c.get("reference_url") or ""
        ref_s = f" 来源: {ref}" if ref else ""
        lines.append(
            f"- [{c.get('verification_status')}/{c.get('risk_level')}] {c.get('claim_text')}{ref_s}"
        )
    lines.append("")
    lines.append("## 12. 内容缺口")
    lines.append("")
    lines.append("基于高价值问题中品牌缺席、竞品占优、自有引用不足与事实错误识别内容缺口。")
    lines.append("")
    lines.append("## 13. 十项优先机会")
    lines.append("")
    for opp in report.get("opportunities") or []:
        sc = opp.get("scores") or {}
        lines.append(f"### {opp.get('id')}: {opp.get('title')}")
        lines.append(f"- 类型: {opp.get('opportunity_type')}")
        lines.append(f"- 缺口: {opp.get('observed_gap')}")
        lines.append(f"- 竞品证据: {opp.get('competitor_evidence')}")
        lines.append(f"- 推荐资产: {opp.get('recommended_asset')}")
        lines.append(f"- 总分: {sc.get('total')}")
        lines.append("")
    lines.append("## 14. 五份内容 Brief")
    lines.append("")
    briefs = report.get("content_briefs") or []
    if not briefs:
        lines.append("- 无（可由 Agent 基于机会生成，最多 5 份）。")
    for b in briefs:
        lines.append(f"### {b.get('working_title') or b.get('opportunity_id')}")
        lines.append(f"- 渠道: {b.get('channel')}")
        lines.append(f"- 受众: {b.get('target_audience')}")
        lines.append(f"- 目标: {b.get('business_goal')}")
        lines.append(f"- 人工审核: {b.get('human_review_required', True)}")
        lines.append("")
    lines.append("## 15. 三十天行动计划")
    lines.append("")
    for step in report.get("thirty_day_plan") or []:
        lines.append(f"- {step}")
    lines.append("")
    lines.append("## 16. 方法限制")
    lines.append("")
    for lim in report.get("limitations") or []:
        lines.append(lim)
    lines.append("")
    lines.append("## 17. 证据索引")
    lines.append("")
    for ev in report.get("evidence_index") or []:
        title = ev.get("title") or ev.get("url")
        lines.append(f"- [{title}]({ev.get('url')}) (q={ev.get('question_id')}, {ev.get('source')})")
    lines.append("")
    return "\n".join(lines)


def write_csvs(run_dir: Path, report: Dict[str, Any]) -> None:
    out = Path(run_dir) / "output"
    questions_rows = []
    for qa in report.get("question_analysis") or []:
        questions_rows.append(
            {
                "question_id": qa.get("question_id"),
                "text": qa.get("text"),
                "intent": qa.get("intent"),
                "business_value": qa.get("business_value"),
                "brand_mentioned": qa.get("brand_mentioned"),
                "mention_type": qa.get("mention_type"),
                "recommendation_rank": qa.get("recommendation_rank"),
            }
        )
    write_csv(
        out / "questions.csv",
        questions_rows,
        [
            "question_id",
            "text",
            "intent",
            "business_value",
            "brand_mentioned",
            "mention_type",
            "recommendation_rank",
        ],
    )

    evidence_rows = []
    for ev in report.get("evidence_index") or []:
        evidence_rows.append(
            {
                "url": ev.get("url"),
                "title": ev.get("title"),
                "question_id": ev.get("question_id"),
                "source": ev.get("source"),
            }
        )
    write_csv(
        out / "evidence.csv",
        evidence_rows,
        ["url", "title", "question_id", "source"],
    )

    opp_rows = []
    for opp in report.get("opportunities") or []:
        sc = opp.get("scores") or {}
        opp_rows.append(
            {
                "id": opp.get("id"),
                "title": opp.get("title"),
                "opportunity_type": opp.get("opportunity_type"),
                "total_score": sc.get("total"),
                "business_value": sc.get("business_value"),
                "target_question_ids": ",".join(opp.get("target_question_ids") or []),
                "recommended_asset": opp.get("recommended_asset"),
            }
        )
    write_csv(
        out / "opportunities.csv",
        opp_rows,
        [
            "id",
            "title",
            "opportunity_type",
            "total_score",
            "business_value",
            "target_question_ids",
            "recommended_asset",
        ],
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Render GEO audit reports")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--report-json", default=None)
    parser.add_argument("--markdown-output", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir)
    report = build_report_json(run_dir)

    report_json_path = Path(args.report_json) if args.report_json else run_dir / "output" / "report.json"
    md_path = Path(args.markdown_output) if args.markdown_output else run_dir / "output" / "report.md"

    write_json(report_json_path, report)
    md_path.write_text(render_markdown(report), encoding="utf-8")
    write_csvs(run_dir, report)

    # ensure manifest exists in output
    try:
        manifest = load_manifest(run_dir)
        manifest["status"] = "RENDERING_REPORT"
        manifest.setdefault("outputs", {})
        manifest["outputs"].update(
            {
                "report_md": str(md_path),
                "report_json": str(report_json_path),
                "questions_csv": str(run_dir / "output" / "questions.csv"),
                "evidence_csv": str(run_dir / "output" / "evidence.csv"),
                "opportunities_csv": str(run_dir / "output" / "opportunities.csv"),
            }
        )
        save_manifest(run_dir, manifest)
    except FileNotFoundError:
        print("warn: manifest not found, report outputs not recorded", file=sys.stderr)

    append_event(run_dir, "report_rendered", {"report_json": str(report_json_path)})
    if args.json:
        print_json({"report_json": str(report_json_path), "report_md": str(md_path)})
    else:
        print(str(report_json_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())