# Funnel-Stage Visibility Analysis

## Goal

Track brand visibility at each stage of the buying funnel (awareness → consideration → conversion → retention) to identify where the brand gains or loses AI search visibility.

## Funnel Stage Definitions

| Stage | Intent | Example Questions |
|-------|--------|-------------------|
| **awareness** | category_knowledge, use_case | "最好的项目管理软件有哪些", "What tools help with team collaboration?" |
| **consideration** | recommendation, comparison | "Notion vs Obsidian 哪个好", "推荐一款适合小团队的 CRM" |
| **conversion** | purchase | "在哪里购买 Figma", "How to subscribe to ChatGPT Plus" |
| **retention** | brand_fact, usage_support | "Figma 怎么导出 PDF", "Is Salesforce SOC2 compliant?" |

## Per-Stage Visibility Scoring

For each funnel stage, compute:

| Metric | Definition |
|--------|------------|
| `mention_rate` | Proportion of questions at this stage where brand is mentioned |
| `recommendation_rate` | Proportion of questions at this stage where brand is recommended |
| `geo_score` | Composite GEO score (0-100) for questions at this stage only |

## Gap Detection

Compare per-stage metrics to identify:

1. **Weakest stage**: Stage with lowest `mention_rate` × `recommendation_rate`
2. **Stage gap**: Difference between best and worst stage for each metric
3. **Drop-off pattern**: Identify if visibility drops monotonically through the funnel

Common patterns:
- High awareness, low conversion → brand known but not trusted for purchase
- Low awareness, high retention → niche strength, poor discovery
- Uniform low → fundamental visibility problem

## Output Structure

```json
{
  "funnel_metrics": {
    "awareness": {
      "question_count": 8,
      "mention_rate": {"rate": 0.75, "numerator": 6, "denominator": 8},
      "recommendation_rate": {"rate": 0.50, "numerator": 4, "denominator": 8},
      "geo_score": 62.5
    },
    "consideration": { "..." },
    "conversion": { "..." },
    "retention": { "..." }
  },
  "gap_analysis": {
    "weakest_stage": "conversion",
    "strongest_stage": "awareness",
    "mention_rate_gap": 0.30,
    "recommendation_rate_gap": 0.25
  }
}
```

## Scoring Model and Bands

| Band | Composite Stage Score | Interpretation |
|------|----------------------|----------------|
| **strong** | ≥ 70 | Brand dominates this funnel stage |
| **moderate** | 40–69 | Brand present but not dominant |
| **weak** | 20–39 | Brand rarely appears at this stage |
| **absent** | < 20 | Brand effectively invisible |

Composite stage score = 0.4 × mention_rate + 0.4 × recommendation_rate + 0.2 × (geo_score / 100).

## Agent Usage Guide

### Phase 3 — Question Generation

After generating questions, each question is classified by funnel stage using `classify_funnel_stage.py`. This classification drives:

- Question distribution balancing: ensure all 4 stages are represented
- Intent-to-stage mapping: `INTENT_TO_FUNNEL` in `geo_common.py`

### Phase 6 — Metrics Computation

`calculate_metrics.py` computes per-stage metrics in addition to overall metrics. The `funnel_metrics` object is written to `metrics.json`.

Use per-stage metrics to:
- Identify which funnel stages need attention
- Prioritize opportunities by stage gap
- Track improvement across stages over time in the improvement loop (Phase 10)