# grok-geo — Metric Definitions

> Version: 5.0.0

## Metric Tiering System

| Tier | Name | Description |
|------|------|-------------|
| **T1** | Core | 高置信度指标，基于搜索结果的确定性计算 |
| **T2** | Extended | 需要更丰富数据源的确定性指标 |
| **T3** | Experimental | 实验性指标，报告中需明确标注为实验性 |

---

## Core Metrics (T1)

| Metric | Description |
|--------|-------------|
| `geo_score` | GEO 综合评分 (0-100) |
| `sentiment_index` | 品牌情感倾向指数 (0-100) |
| `recommendation_type_distribution` | 推荐类型分布统计 |
| `citation_share_by_competitor` | 竞品引用份额对比 |
| `competitor_co_mentions` | 竞品共现分析 |
| `platform_citation_map` | 跨平台引用分布 |
| `freshness` | 内容新鲜度评分 |
| `citability` | 内容可引用性评分 |
| `negative_signals` | 反向信号检测评分 |
| `ai_perception` | AI 感知快照 |
| `geo_lint_score` | GEO 合规评分 |
| `geo_lint_grade` | GEO 合规等级 (A-F) |
| `geo_lint_errors` | GEO 合规错误数 |
| `geo_lint_warnings` | GEO 合规警告数 |
| `schema_files_generated` | 生成的 AI 可读文件数 |
| `schema_validation_passed` | Schema 跨文件验证结果 |
| `engines_used` | 使用的 AI 引擎列表 |
| `cross_engine_citation_consistency` | 跨引擎引用一致性 |
| `engine_success_rate` | 各引擎查询成功率 |
| `engine_citation_rate` | 各引擎引用率 |
| `engine_unique_domains` | 各引擎唯一引用域名数 |
| `ai_sov_overall` | AI 整体声量份额 |
| `ai_sov_by_intent` | 按意图分层的 AI 声量份额 |
| `ai_sov_by_platform` | 按平台分层的 AI 声量份额 |
| `cross_engine_consistency_score` | 跨引擎品牌叙事一致性 |

## Extended Metrics (T2)

| Metric | Description |
|--------|-------------|
| `site_readiness_score` | 网站技术就绪度评分 |
| `rag_readiness` | RAG 分块就绪度评分 |
| `trust_stack` | 五层信任栈评分 |
| `entity_kg_score` | 实体知识图谱完整度评分 |
| `entity_kg_grade` | 实体知识图谱等级 (A-F) |
| `entity_action_items` | 实体优化行动项 |
| `i18n_score` | 国际化评分 |
| `i18n_grade` | 国际化等级 (A-F) |
| `per_language_scores` | 各语言单项评分 |
| `closed_loop_actions` | 闭环优化行动项 |
| `citation_growth_rate` | 引用增长率 |
| `outreach_response_rate` | 外联响应率 |
| `ai_traffic_sessions` | AI 来源流量会话数 |
| `ai_traffic_share` | AI 来源流量占比 |
| `ai_engagement_rate` | AI 用户参与率 |
| `ai_conversion_rate` | AI 用户转化率 |
| `ai_top_landing_pages` | AI 流量热门着陆页 |
| `academic_evidence_count` | 学术研究采纳数 |
| `optimization_methods_covered` | 已实施的优化方法数 |
| `research_freshness` | 引用研究的时效性 |
| `chatgpt_shopping_rate` | ChatGPT 购物场景推荐率 |
| `chatgpt_product_rank` | 产品平均排名位置 |
| `prompt_discovery_count` | 发现的 AI 提示词数 |
| `prompt_quality_avg` | 提示词平均质量分 |
| `agentic_readiness_score` | Agentic Search 就绪度 |
| `ai_crawl_coverage` | AI 爬虫覆盖率 |
| `persona_tracking_coverage` | 用户画像追踪覆盖度 |
| `word_association_pos` | 正面词汇关联 |
| `word_association_neg` | 负面词汇关联 |
| `narrative_framing` | 品牌叙事框架分类 |
| `narrative_deviation_score` | 叙事偏差评分 |
| `platform_favorability` | 各平台品牌好感度 |
| `ubs` | 统一品牌评分 |
| `agentic_conversion_rate` | Agent 转化就绪度 |
| `agent_ready_score` | Agent-Ready Hub 就绪度 |
| `hallucinations_detected` | 品牌幻觉检测 |
| `defensive_geo_status` | 防御性 GEO 状态 |
| `a2a_score` | Agent-to-Agent 就绪度 |
| `agent_manifest_exists` | Agent Manifest 存在性 |

## Experimental Metrics (T3)

> ⚠️ 以下指标使用启发式估算，报告中必须标注为实验性。

| Metric | Description |
|--------|-------------|
| `agentic_engine_status` | Agentic GEO 引擎状态 |
| `agentic_cycle_count` | 自主优化周期计数 |
| `multimodal_score` | 多模态 GEO 综合评分 |
| `predict_30d` | 30 天趋势外推 |
| `predict_90d` | 90 天趋势外推 |
| `predict_confidence` | 趋势预测置信区间 |

---

## Version Mapping

| Feature Version | Description |
|----------------|-------------|
| v1.0 | 核心功能发布 |
| v1.1 | 深度评分扩展 |
| v1.9 | Schema 自动化 + GEO 合规检查 |
| v2.0 | 多引擎支持 |
| v2.1 | 实体知识图谱 |
| v2.2 | 国际化评分 |
| v2.3 | 闭环优化 |
| v2.4 | 流量分析集成 |
| v3.0 | 前沿技术集成 |
| v4.0 | Agentic 品牌分析 |
| v5.0 | 架构重构 + 指标分级 |