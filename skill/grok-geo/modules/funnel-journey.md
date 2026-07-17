# Module: Funnel & Journey Metrics (v1.7-v1.8)

> Extends Phase 3, 6, 7 with funnel-stage and buying-journey analysis.
> Scripts: `scripts/classify_funnel_stage.py`, `scripts/compute_journey_metrics.py`

## v1.7 �?Funnel Stage Classification

After generating questions (Phase 3), classify each by funnel stage:

```bash
python <SKILL>/scripts/classify_funnel_stage.py \
  --questions <RUN>/intermediate/questions.json \
  --output <RUN>/intermediate/questions.json
```

Adds `funnel_stage` field: awareness / consideration / conversion / retention.

### Funnel-Stage Metrics (Phase 6)

Metrics are computed per funnel stage in addition to overall.
Per-stage metrics include: mention_rate, recommendation_rate, geo_score.
Write to `metrics.json` �?`funnel_metrics`.

## v1.8 �?Buying Journey Metrics

Compute visibility effectiveness at each buying journey stage:

```bash
python <SKILL>/scripts/compute_journey_metrics.py \
  --questions <RUN>/intermediate/questions.json \
  --entities <RUN>/intermediate/entity_analysis.jsonl \
  --citations <RUN>/intermediate/citations.json \
  --output <RUN>/intermediate/journey_metrics.json
```

Write per-stage and transition metrics to `metrics.json` �?`journey_metrics`.

### Attribute-Level Analysis (Phase 5)

Detect which product attributes are discussed (core_features/pricing/ease_of_use/integrations/support/scalability/security/performance).
- Compute per-attribute emphasis score
- Detect attribute gaps (brand promotes but AI ignores)
- Write to `report.json` �?`attribute_analysis`

### Publisher Influence Mapping (Phase 5)

Map which publishers/media shape AI answers about the brand's category.
- Compute per-publisher influence score (citation_count x support_ratio)
- Identify top influencers for outreach prioritization
- Write to `report.json` �?`publisher_influence`

References: `references/methodology/funnel-stage-analysis.md`, `references/research/attribute-level-analysis.md`, `references/research/publisher-influence-mapping.md`, `references/methodology/buying-journey-metrics.md`