# GEO 品牌审计工作流

## 完整流程

```
用户输入品牌信息
    │
    ▼
[1] validate_input.py ──→ normalized_input.json
    │  校验必填字段、URL 格式、敏感信息、品牌-竞品冲突
    ▼
[2] initialize_run.py ──→ run_dir/input/brand.json + manifest.json
    │  创建 run 目录结构、生成 run_id、写入初始 manifest
    ▼
[3] Agent: 研究品牌官网 ──→ 补充 known_facts
    │  用 web_search 查看官网，提取可验证事实
    ▼
[4] Agent: 生成问题地图 ──→ intermediate/questions.json
    │  按 intent 分布生成 10/30 个问题
    ▼
[5] validate_questions.py ──→ 校验约束（70%无品牌、30%推荐类）
    │
    ▼
[6] 分批搜索 ──→ 逐条 append_search_result.py ──→ raw/search_results.jsonl
    │  每条搜索结果立即落盘；失败不阻断后续
    ▼
[7] Agent: 实体分析 ──→ intermediate/entity_analysis.jsonl
    │  识别品牌、竞品、mention_type、recommendation_rank
    ▼
[8] classify_citations.py ──→ intermediate/citations.json
    │  URL 规范化、来源分类（owned/earned_media/social/...）
    ▼
[9] Agent: 声明校验 ──→ intermediate/claims.json
    │  抽取声明、对照 known_facts、标记 verification_status 和 risk_level
    ▼
[10] calculate_metrics.py ──→ intermediate/metrics.json
    │  确定性计算所有指标 + Wilson CI
    ▼
[11] Agent: 生成机会 ──→ rank_opportunities.py ──→ intermediate/opportunities.json
    │  最多 10 条，按 total_score 降序
    ▼
[12] Agent: 生成内容 Brief（最多 5 份，可选）
    │
    ▼
[13] render_report.py ──→ output/report.md + report.json + 3 个 CSV
    │
    ▼
[14] validate_report.py --update-manifest ──→ manifest 状态更新为 COMPLETED
    │
    ▼
[15] package_outputs.py ──→ output/{run_id}-outputs.zip（可选）
```

## 断点恢复

- manifest.json 记录当前状态和进度
- 重跑时检查 manifest.status 决定从哪一步继续
- search_results.jsonl 支持追加和去重（按 question_id + query_text）
- 中间文件存在则跳过对应步骤

## 失败处理

- 单个搜索失败不阻断整个流程
- 有效搜索率 < 80% 时标记为 FAILED
- 有效搜索率 80-90% 时标记为 PARTIAL
- 有效搜索率 >= 90% 时标记为 COMPLETED