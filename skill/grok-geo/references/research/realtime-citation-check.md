# 实时品牌引用检查工作流

## 目标

在搜索执行阶段（Phase 4），不仅记录搜索结果，还**实时检测品牌在 AI 搜索回答中的引用状态**——品牌是否被提及、被推荐、被引用、被正确描述。

## 与现有 Phase 4 的区别

| 维度 | Phase 4 原有 | v1.4 增强 |
|------|-------------|-----------|
| 搜索方式 | 单问题单查询 | 多变体并行查询 |
| 结果处理 | 原始落盘 | 即时信号提取 |
| 品牌检测 | Phase 5 后置分析 | Phase 4 即时检测 |
| 平台识别 | 无 | 从响应特征推断平台 |
| 引用追踪 | 被动记录 | 主动检测 brand_cited / domain_cited |

## 实时引用检查流程

```
Phase 4 搜索执行（v1.4 增强版）
    │
    ├─ 1. 加载问题地图
    │
    ├─ 2. 对每个问题生成变体查询
    │     ├─ 原始问题文本
    │     ├─ 同义词替换变体
    │     └─ 不同 persona 变体
    │
    ├─ 3. 执行搜索（每批 5 个问题）
    │     ├─ 调用 web_search
    │     ├─ 保存原始响应
    │     └─ 即时提取信号 ← v1.4 新增
    │           ├─ brand_mentioned: bool
    │           ├─ brand_cited: bool
    │           ├─ brand_domain_cited: bool
    │           ├─ recommendation_detected: bool
    │           ├─ competitor_mentioned: list[str]
    │           ├─ citation_domains: list[str]
    │           ├─ platform_hints: dict
    │           └─ response_quality: dict
    │
    ├─ 4. 写入 search_results.jsonl（含信号）
    │
    └─ 5. 更新 manifest（含信号统计）
```

## 搜索结果对象（v1.4 增强）

```json
{
  "schema_version": "1.4",
  "run_id": "geo_...",
  "question_id": "q-001",
  "query_text": "适合五十人研发团队的项目管理软件有哪些？",
  "query_variant": "original",
  "variant_group": "vg-001",
  "search_environment": "openai_web_search",
  "executed_at": "2026-07-17T08:42:12Z",
  "status": "success",
  "answer_text": "...",
  "citations": [...],
  "sources": [...],
  "error": null,
  "extracted_signals": {
    "brand_mentioned": true,
    "brand_cited": true,
    "brand_domain_cited": false,
    "recommendation_detected": true,
    "recommendation_strength": "recommended",
    "brand_position_in_answer": 2,
    "competitor_mentioned": ["竞争品牌A", "竞争品牌B"],
    "citation_domains": ["techblog.com", "review-site.com"],
    "platform_hints": {
      "detected_engine": "perplexity",
      "has_inline_citations": true,
      "has_source_cards": true,
      "response_length": 1247,
      "has_list_structure": true
    },
    "response_quality": {
      "answer_completeness": 0.85,
      "citation_density": 0.03,
      "factual_specificity": "high"
    }
  }
}
```

## 平台特征检测

从搜索响应特征推断底层引擎（Agent 任务，非确定性）：

| 特征 | ChatGPT | Perplexity | Claude | Gemini |
|------|---------|------------|--------|--------|
| 内联引用标注 | 偶尔 | 总是 | 偶尔 | 偶尔 |
| Source Cards | 有 | 有 | 无 | 有 |
| 回答风格 | 叙述式 | 引用密集 | 分析式 | 列表式 |
| 典型长度 | 中等 | 长 | 中等 | 短 |
| 列表结构 | 常见 | 常见 | 不常见 | 常见 |

## 即时信号提取规则

### brand_mentioned

```text
在 answer_text 中检测：
- 品牌全名（精确匹配）
- 品牌别名（已知别名列表）
- 品牌产品名（已知产品列表）
- 域名提及（品牌域名出现在正文中，非引用标注）
```

### brand_cited

```text
满足以下任一条件：
- citations[] 中包含品牌官网 URL
- answer_text 中包含品牌官网 URL 作为引用来源
- source_cards 中包含品牌域名
```

### recommendation_detected

```text
在品牌提及的上下文（前后 100 字）中检测：
- 推荐词：推荐、建议、适合、首选、最佳、不错
- 排名信号：第一、Top 1、首选
- 对比信号：比...更好、优于、相比...更
- 场景信号：如果你是...，推荐
```

## 搜索批次管理

### 标准模式（30 问题 × 2 变体）

```text
批次 1: q-001, q-002, q-003, q-004, q-005（原始）
批次 2: q-001v, q-002v, q-003v, q-004v, q-005v（变体）
...
批次 11: q-026~q-030（原始）
批次 12: q-026v~q-030v（变体）
总计：12 批 × 5 = 60 次搜索
```

### Quick 模式（10 问题 × 1 变体）

```text
批次 1: q-001~q-010（分 2 批，每批 5）
总计：2 批 × 5 = 10 次搜索
```

### 失败重试

```text
- 单题失败：记录错误，不阻断
- 自动重试：最多 1 次
- 重试仍失败：标记 status=failed，继续下一题
- 批次完成后：更新 manifest.search_result_count
```

## 变体生成规则

### 同义词变体

```text
原始："适合五十人研发团队的项目管理软件有哪些？"
变体："50人开发团队用什么项目管理工具好？"
```

### Persona 变体

```text
原始（研发负责人视角）："适合五十人研发团队的项目管理软件有哪些？"
变体（CTO 视角）："作为 CTO，如何为 50 人技术团队选择项目管理工具？"
```

### 约束

- 每个问题最多 2 个变体（原始 + 1 个）
- 变体不得改变问题核心意图
- 变体不得引入品牌偏见
- 变体使用不同表达但保留关键约束（团队规模、行业、场景）

## Agent 使用指南

1. Phase 4 开始前，先从 questions.json 加载问题列表
2. 对每个问题按规则生成变体（如有）
3. 分批执行搜索，每批 5 个
4. **每次搜索后立即**：
   a. 保存原始结果到 `raw/search_results.jsonl`
   b. 提取 `extracted_signals` 字段
   c. 更新 manifest 计数器
5. 批次之间更新 manifest.current_batch
6. 全部完成后进入 Phase 5