# Buying Journey Metrics

## Goal

Measure brand visibility effectiveness at each buying journey stage, identify
drop-off points, and compute cross-stage conversion rates to optimize the
customer acquisition funnel in AI search.

## Journey Stages

| Stage | Description | Example Questions |
|---|---|---|
| `problem_awareness` | User recognizes a problem | "Why is my team's productivity low?" |
| `solution_awareness` | User explores solution categories | "What tools improve team productivity?" |
| `vendor_comparison` | User compares specific vendors | "Asana vs Monday vs Trello" |
| `purchase_decision` | User ready to buy | "Asana pricing plans for 50 users" |
| `post_purchase` | Existing user seeking support | "Asana API integration guide" |

### Funnel-to-Journey Mapping

| Funnel Stage | Journey Stages |
|---|---|
| `awareness` | `problem_awareness` |
| `consideration` | `vendor_comparison` |
| `conversion` | `purchase_decision` |
| `retention` | `post_purchase` |

Note: `solution_awareness` is a sub-stage derived from `awareness` funnel questions
with `use_case` intent.

## Per-Stage Metrics

Each journey stage computes:

| Metric | Formula | Range |
|---|---|---|
| `visibility_rate` | questions_with_mention / total_questions | 0.0–1.0 |
| `recommendation_rate` | questions_with_recommendation / total_questions | 0.0–1.0 |
| `sentiment_score` | avg(sentiment_scores) | 0–100 |
| `citation_rate` | questions_with_citation / total_questions | 0.0–1.0 |
| `competitor_dominance` | competitor_mentions / total_mentions | 0.0–1.0 |

## Journey Conversion Funnel

Measures what percentage of questions where brand is visible at stage N
are also visible at stage N+1:

```
conversion_rate(N→N+1) = visible_at_both_stages / visible_at_stage_N
```

### Transition Metrics

```json
{
  "transitions": [
    {
      "from_stage": "problem_awareness",
      "to_stage": "solution_awareness",
      "brand_visible_from": 8,
      "brand_visible_to": 5,
      "brand_visible_both": 4,
      "conversion_rate": 0.5,
      "drop_off_rate": 0.5
    }
  ]
}
```

## Journey Gap Analysis

Identify stages where brand visibility drops significantly:

| Drop-off Severity | Threshold | Action |
|---|---|---|
| `severe` | ≥40% visibility drop | Immediate content creation |
| `moderate` | 20-40% drop | Content update within 14 days |
| `minor` | <20% drop | Monitor quarterly |

### Gap Detection Logic

```python
for i in range(len(stages) - 1):
    change = visibility[stages[i+1]] - visibility[stages[i]]
    if change <= -0.4:
        severity = "severe"
    elif change <= -0.2:
        severity = "moderate"
    elif change < 0:
        severity = "minor"
```

## Cross-Persona Analysis

Compare the same journey stage across different personas:

| Persona | Problem Awareness | Solution Awareness | Comparison |
|---|---|---|---|
| SMB Owner | 0.8 | 0.6 | 0.3 |
| Enterprise | 0.5 | 0.7 | 0.8 |
| Developer | 0.9 | 0.4 | 0.6 |

Cross-persona gaps reveal which audiences are underserved at each stage.

## Output Structure

```json
{
  "stage_metrics": {
    "problem_awareness": {
      "total_questions": 5,
      "mention_rate": 0.6,
      "recommendation_rate": 0.4,
      "sentiment_score": 72.5,
      "citation_rate": 0.2
    }
  },
  "journey_coverage": 0.8,
  "journey_progression": -0.05,
  "progression_direction": "negative",
  "drop_offs": [
    {
      "from_stage": "solution_awareness",
      "to_stage": "vendor_comparison",
      "visibility_change": -0.3,
      "severity": "moderate"
    }
  ],
  "weakest_stage": "vendor_comparison",
  "strongest_stage": "problem_awareness",
  "critical_transitions": ["solution_awareness → vendor_comparison"]
}
```

## Agent Usage Guide

1. Run `compute_journey_metrics.py` after metric calculation (Phase 6)
2. Input: `questions.json` (with funnel_stage), `entity_analysis.jsonl`, `citations.json`
3. Output: `journey_metrics.json` with per-stage and transition metrics
4. Feed journey gaps into `generate_optimization_actions.py` for stage-specific content plans
5. Compare across audit runs to track journey improvement over time