# grok-geo

版本：v5.0.0

一次性 AI 搜索 / GEO 品牌诊断 Skill。通过 `web_search` 采集证据，用标准库 Python 脚本做确定性指标与报告生成。

## 目录

- `SKILL.md` — Agent 工作流与约束
- `scripts/` — 确定性 CLI 脚本
- `schemas/` — JSON Schema
- `examples/` — 最小/完整输入与 offline fixture
- `templates/` — 报告模板片段
- `evals/` — 轻量评估用例

## 本地 offline 演示

```bash
python examples/run_offline_demo.py --base-dir ./geo-audit-runs --keep
```

产物位于 `geo-audit-runs/geo_offline_demo_00000001/output/`。

## 脚本概览

本 Skill 包含以下类别的脚本：

- **输入验证与初始化**：校验输入、创建运行目录
- **问题生成与验证**：生成诊断问题并校验约束
- **搜索执行与分析**：批量搜索、信号提取、结果评分
- **实体与引用分析**：实体规范化、引用分类
- **指标计算**：确定性指标计算与排序
- **报告生成**：Markdown/JSON/CSV 报告输出
- **合规检查**：GEO 合规规则检查与 Schema 生成
- **多引擎查询**：支持多个 AI 引擎的真实查询
- **持续监控**：漂移检测、告警、改进计划生成

运行环境默认 runs 目录：

- Hosted：`/mnt/data/geo-audit-runs`
- Local：`GEO_AUDIT_RUNS_DIR` 或 `./geo-audit-runs`