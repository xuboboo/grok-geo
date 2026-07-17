# Visibility Alert Triggers

## Goal

Detect significant visibility changes that warrant attention, enabling proactive response to AI search visibility shifts.

## Alert Types

| Type | Description | Example Trigger |
|------|-------------|-----------------|
| `position_drop` | Brand dropped in recommendation position | Was #1, now #3 |
| `mention_lost` | Brand no longer mentioned in answers | Previously mentioned in 80% of questions, now 50% |
| `citation_lost` | Brand website no longer cited as source | Domain citations dropped significantly |
| `sentiment_drop` | Sentiment toward brand shifted negative | Average sentiment dropped from 70 to 45 |
| `new_competitor` | New competitor appearing in answers | Previously unknown entity now recommended |
| `recommendation_downgrade` | Recommendation strength decreased | From `top_pick` to `conditional` |

## Severity Levels

| Level | Response Required | Notification |
|-------|------------------|--------------|
| **info** | Monitor only | Logged, no action required |
| **warning** | Review within 1 week | Flag in report, suggested investigation |
| **critical** | Immediate attention | Top of report, action required |

## Threshold Definitions

### Rate-based metrics (mention_rate, recommendation_rate)

| Drop Amount | Severity |
|-------------|----------|
| ≥ 0.15 | warning |
| ≥ 0.30 | critical |

### Score-based metrics (geo_score, visibility_score)

| Drop Amount | Severity |
|-------------|----------|
| ≥ 10 | warning |
| ≥ 25 | critical |

### Other signals

| Condition | Severity |
|-----------|----------|
| negative_recommendation_count increased | warning |
| New competitor entity not in baseline | info |

## Alert Output Structure

```json
{
  "visibility_alerts": [
    {
      "question_id": "q_007",
      "alert_type": "mention_drop",
      "severity": "warning",
      "evidence": "mention_rate dropped from 0.75 to 0.55 (Δ -0.20)",
      "metric": "mention_rate",
      "current_value": 0.55,
      "baseline_value": 0.75,
      "delta": -0.20,
      "recommended_action": "Investigate questions where brand mention was lost; check competitor content changes"
    },
    {
      "alert_type": "recommendation_downgrade",
      "severity": "critical",
      "evidence": "recommendation_rate dropped from 0.60 to 0.25 (Δ -0.35)",
      "metric": "recommendation_rate",
      "current_value": 0.25,
      "baseline_value": 0.60,
      "delta": -0.35,
      "recommended_action": "Priority: review top recommendation questions, update comparison content, verify brand claims accuracy"
    }
  ],
  "alert_summary": {
    "total_alerts": 2,
    "critical_count": 1,
    "warning_count": 1,
    "info_count": 0
  }
}
```

## Integration with Improvement Loop (Phase 10)

Visibility alerts feed directly into the improvement loop:

1. **Baseline comparison**: Current run metrics are compared against the most recent baseline run
2. **Alert generation**: `detect_visibility_alerts.py` produces alerts with severity and recommended actions
3. **Priority ranking**: Critical alerts are surfaced at the top of the improvement plan
4. **Action mapping**: Each alert type maps to specific improvement action types:
   - `mention_lost` → `expand_coverage`, `build_backlinks`
   - `recommendation_downgrade` → `update_content`, `fix_misperception`
   - `citation_lost` → `fix_technical`, `build_backlinks`
   - `sentiment_drop` → `fix_misperception`, `update_content`
5. **Re-test scheduling**: Alert severity influences re-test urgency (critical: 3 days, warning: 7 days)

## Agent Usage Guide

### Phase 10 — Improvement Loop

When a baseline run exists:

1. Load baseline `metrics.json` and current `metrics.json`
2. Run `detect_visibility_alerts.py` to generate alerts
3. Include alerts in `report.json` → `visibility_alerts`
4. Use alert severity to prioritize improvement actions
5. Critical alerts should be addressed before other opportunities