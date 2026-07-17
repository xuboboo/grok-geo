# 跨平台引用映射

## 目标

回答一个核心问题：**同一组问题在不同 AI 平台上，品牌被引用的来源是否一致？哪些来源是跨平台通用的，哪些是平台特有的？**

## 数据模型

### 平台枚举

```text
chatgpt      — OpenAI GPT-4o / GPT-4o-search-preview
perplexity   — Perplexity Sonar (原生 web citations)
claude       — Anthropic Claude (web_search 工具)
gemini       — Google Gemini (Google Search grounding)
ai_overview  — Google AI Overview (SGE)
```

### 平台引用记录

每次搜索结果追加 `platform` 字段：

```json
{
  "question_id": "q-001",
  "platform": "chatgpt",
  "citations": [
    {
      "url": "https://example.com/page",
      "title": "页面标题",
      "domain": "example.com",
      "citation_order": 1
    }
  ],
  "brand_mentioned": true,
  "brand_cited": false
}
```

### 跨平台聚合输出

```json
{
  "question_id": "q-001",
  "platforms_checked": ["chatgpt", "perplexity", "claude", "gemini"],
  "brand_visibility": {
    "chatgpt":    { "mentioned": true,  "cited": false, "rank": 2 },
    "perplexity": { "mentioned": true,  "cited": true,  "rank": 1 },
    "claude":     { "mentioned": false, "cited": false, "rank": null },
    "gemini":     { "mentioned": true,  "cited": false, "rank": 3 }
  },
  "cross_platform_sources": {
    "example.com":       { "platforms": ["chatgpt", "perplexity", "gemini"], "count": 3 },
    "competitor-a.com":  { "platforms": ["chatgpt", "perplexity"], "count": 2 },
    "blog.example.org":  { "platforms": ["perplexity"], "count": 1 }
  },
  "platform_specific_sources": {
    "chatgpt":    ["news.example.com"],
    "perplexity": ["academic.example.edu"],
    "claude":     [],
    "gemini":     ["maps.google.com"]
  }
}
```

## 聚合指标

### cross_platform_visibility_score

品牌在 ≥ 2 个平台被提及的问题占比：

```text
cpv = 跨平台可见问题数 / 有效问题总数
```

### platform_parity_index

各平台提及率的标准差（越低 = 越一致）：

```text
parity = 1 - stddev(platform_mention_rates)
```

- 1.0 = 所有平台完全一致
- 0.0 = 极度不一致

### source_overlap_rate

跨平台引用的源域名占比：

```text
overlap = 被 ≥ 2 个平台引用的域名数 / 总引用域名数
```

### platform_advantage_map

标记每个平台的品牌提及率排名（哪个平台最有利于品牌）：

```json
{
  "best_platform": "perplexity",
  "worst_platform": "claude",
  "platform_ranking": [
    {"platform": "perplexity", "mention_rate": 0.85},
    {"platform": "chatgpt",    "mention_rate": 0.60},
    {"platform": "gemini",     "mention_rate": 0.45},
    {"platform": "claude",     "mention_rate": 0.20}
  ]
}
```

## Agent 使用指南

1. **标准模式**：每个问题搜索 2-4 个平台（perplexity + chatgpt 为最低要求）
2. **Quick 模式**：仅用默认平台（web_search 的默认引擎），不执行跨平台
3. **结果合并**：按 `question_id + canonical_url` 去重，保留最高 `citation_order`
4. **报告展示**：跨平台一致性差的问题标记为高优先级机会

## 与竞品的关系

| 竞品能力 | 本 Skill 对应 |
|----------|--------------|
| OneGlanse 跨 5 个 UI 界面采集 | 本 Skill 通过 API 层查询，不操作真实 UI |
| ai-brand-monitor-mcp 4 平台同步查询 | 本 Skill 分批查询，结果按平台标记 |
| GeoGryphon 平台特定评分 | 本 Skill 的 `platform_advantage_map` |

**关键区别**：本 Skill 不依赖平台 UI 自动化（如 Camoufox 浏览器），而是利用 Agent 的 `web_search` 工具，通过查询结果中的来源信息推断平台特征。这是有意的产品边界选择：保持零外部依赖、无浏览器、纯文本处理。