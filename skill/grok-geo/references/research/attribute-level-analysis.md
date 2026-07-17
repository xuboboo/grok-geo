# Product Attribute-Level AI Analysis

## Goal

Understand which product attributes/features AI emphasizes or overlooks when discussing a brand, enabling targeted content strategy.

## Attribute Categories

| Category | Description | Example Keywords |
|----------|-------------|------------------|
| `core_features` | Main product capabilities | 功能, 特性, 能力, feature, capability, functionality |
| `pricing` | Price, plans, free tier | 价格, 定价, 收费, 免费, price, pricing, cost, free |
| `ease_of_use` | Usability, learning curve | 易用, 简单, 上手, 学习曲线, easy, simple, intuitive |
| `integrations` | API, plugins, connections | 集成, 对接, 插件, API, integration, plugin, connect |
| `support` | Customer service, docs | 支持, 客服, 服务, 文档, support, service, documentation |
| `scalability` | Enterprise, scale | 扩展, 规模化, 大规模, scalab, enterprise, scale |
| `security` | Privacy, compliance, encryption | 安全, 合规, 隐私, 加密, security, compliance, privacy |
| `performance` | Speed, reliability | 性能, 速度, 响应, 稳定, performance, speed, fast, reliable |

## Extraction Method

From each search result answer text:

1. Scan for attribute category keywords (Chinese + English)
2. Record which attributes are mentioned in the context of the brand
3. Count frequency across all search results
4. Compute emphasis score per attribute

## Emphasis Scoring

Per-attribute emphasis score (0-100):

```
emphasis = min(100, (mention_count / total_brand_mentions) × 100 × normalization_factor)
```

Where `normalization_factor` adjusts for category keyword count (categories with more keywords have a lower factor to prevent bias).

| Band | Score | Meaning |
|------|-------|---------|
| **primary focus** | ≥ 60 | AI heavily emphasizes this attribute |
| **secondary** | 30–59 | AI regularly mentions this attribute |
| **marginal** | 10–29 | AI occasionally mentions this attribute |
| **absent** | < 10 | AI rarely or never mentions this attribute |

## Gap Detection

Two types of gaps:

1. **Brand promotes, AI ignores**: Attribute is prominent on brand website/marketing but absent in AI answers
   - Action: Create more citable content for this attribute

2. **AI emphasizes, brand doesn't promote**: Attribute appears in AI answers but isn't a focus of brand marketing
   - Action: Either leverage this perception or correct it

## Output Structure

```json
{
  "attribute_analysis": {
    "per_question": {
      "q_001": {
        "attributes_detected": ["core_features", "pricing"],
        "raw_mentions": {"core_features": 3, "pricing": 1}
      }
    },
    "aggregate": {
      "core_features": {"count": 28, "emphasis_score": 85, "band": "primary focus"},
      "pricing": {"count": 22, "emphasis_score": 67, "band": "primary focus"},
      "security": {"count": 3, "emphasis_score": 9, "band": "absent"},
      "...": "..."
    },
    "gap_analysis": {
      "brand_promotes_ai_ignores": ["security", "scalability"],
      "ai_emphasizes_brand_quiet": ["ease_of_use"]
    }
  }
}
```

## Agent Usage Guide

### Phase 5 — Entity & Citation Analysis

After search results are collected, run `extract_attribute_analysis.py` to detect attribute mentions in each answer text. Results are written to `report.json` → `attribute_analysis`.

The attribute analysis feeds into:
- **Phase 7 (Opportunities)**: Gap detection identifies content creation targets
- **Phase 10 (Improvement Loop)**: Track whether attribute emphasis shifts after content changes