# grok-geo

版本：v5.0.0

一次性 AI 搜索 / GEO 品牌诊断 Skill。通过 `web_search` 采集证据，用标准库 Python 脚本做确定性指标与报告生成。

## 目录

- `SKILL.md` — Agent 工作流与约束
- `scripts/` — 确定性 CLI 脚本
- `schemas/` — JSON Schema
- `examples/` — 最小/完整输入与 offline fixture
- `references/` — 规则说明
- `templates/` — 报告模板片段
- `evals/` — 轻量评估用例

## 本地 offline 演示

```bash
python examples/run_offline_demo.py --base-dir ./geo-audit-runs --keep
```

产物位于 `geo-audit-runs/geo_offline_demo_00000001/output/`。

## 脚本列表

### 核心脚本（v1.0-v1.8）

| 脚本 | 作用 |
| --- | --- |
| validate_input.py | 输入 Schema + 业务校验 |
| initialize_run.py | 创建 run 目录与 manifest |
| update_manifest.py | 更新状态/计数 |
| validate_questions.py | 问题比例约束 |
| append_search_result.py | 追加 search_results.jsonl |
| normalize_entities.py | 实体名规范化 |
| normalize_urls.py | URL 规范化 |
| classify_citations.py | 引用分类 |
| calculate_metrics.py | 确定性指标 |
| rank_opportunities.py | 机会评分排序（≤10） |
| render_report.py | report.md/json + CSV |
| validate_report.py | 报告一致性与 URL 追溯 |
| package_outputs.py | 输出打包 |
| map_publisher_influence.py | 发布者影响力映射（v1.8） |
| compute_journey_metrics.py | 购买旅程指标计算（v1.8） |
| generate_optimization_actions.py | 优化动作生成（v1.8） |

### 搜索增强脚本（v1.4-v1.6）

| 脚本 | 作用 |
| --- | --- |
| execute_search_batch.py | 批量搜索执行管理 |
| extract_search_signals.py | 搜索结果信号提取 |
| score_search_result.py | 搜索质量评分 + 重试策略 |
| detect_drift.py | 语义漂移检测 |
| chain_runs.py | Run 链接脚本 |
| generate_improvement_plan.py | 改进计划生成 |

### 漏斗与告警脚本（v1.7）

| 脚本 | 作用 |
| --- | --- |
| classify_funnel_stage.py | 问题漏斗阶段分类 |
| extract_attribute_analysis.py | 产品属性提取与强调评分 |
| detect_visibility_alerts.py | 可见度告警检测 |

### 合规与 Schema 脚本（v1.9）

| 脚本 | 作用 |
| --- | --- |
| geo_lint.py | GEO Lint 合规检查（92 规则） |
| generate_schema_files.py | AI 可读文件生成（5 类型） |

### 多引擎脚本（v2.0）

| 脚本 | 作用 |
| --- | --- |
| multi_engine_query.py | 多引擎真实 AI 查询（6 引擎） |

### 实体与国际化脚本（v2.1-v2.2）

| 脚本 | 作用 |
| --- | --- |
| score_entity_kg.py | 实体 KG 评分（5 维度） |
| score_i18n.py | 国际化评分（4 维度） |

### 闭环与分析脚本（v2.3-v2.4）

| 脚本 | 作用 |
| --- | --- |
| generate_closed_loop_actions.py | 闭环优化动作生成 |
| analyze_ai_referrers.py | AI Referrer 分析（GSC + GA4） |

### 前沿技术脚本（v3.0）

| 脚本 | 作用 |
| --- | --- |
| cutting_edge_geo.py | ChatGPT Shopping + Prompt Discovery + AI SOV + Agentic Search |

### 终极能力脚本（v4.0）

| 脚本 | 作用 |
| --- | --- |
| ultimate_geo.py | Agentic Brand Vault + 叙事分析 + 热力图 + Agentic GEO + 混合评分 |

### 天花板级脚本（v5.0）

| 脚本 | 作用 |
| --- | --- |
| ceiling_geo.py | Agentic Commerce + Defensive GEO + A2A + 多模态 + 预测 |

运行环境默认 runs 目录：

- Hosted：`/mnt/data/geo-audit-runs`
- Local：`GEO_AUDIT_RUNS_DIR` 或 `./geo-audit-runs`