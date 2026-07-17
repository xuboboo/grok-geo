# Module: Improvement Loop (v1.6-v1.8)

> Extends Phase 10 â€?Improvement Loop with continuous improvement capabilities.
> Scripts: `scripts/chain_runs.py`, `scripts/generate_improvement_plan.py`, `scripts/detect_visibility_alerts.py`, `scripts/generate_optimization_actions.py`

## v1.6 â€?Run Chaining & Improvement Plan

After report generation, if a baseline run exists:

### 1. Chain runs

```bash
python <SKILL>/scripts/chain_runs.py \
  --current-run-dir <RUN> \
  --baseline-run-dir <BASELINE_RUN> \
  --output <RUN>/intermediate/run_chain.json
```

### 2. Generate improvement plan

```bash
python <SKILL>/scripts/generate_improvement_plan.py \
  --drift <RUN>/intermediate/drift_analysis.json \
  --opportunities <RUN>/intermediate/opportunities.json \
  --metrics <RUN>/intermediate/metrics.json \
  --output <RUN>/output/improvement_plan.json
```

### 3. Re-test triggers

- Each action includes `deadline_days` and `validation_method`
- Manifest records `next_retest_date`

### 4. Loop status

- `loop_status`: first_run / improving / maintaining / regressing

Reference: `references/methodology/loop-engineering.md`

## v1.7 â€?Visibility Alerts

Compare current metrics with baseline to detect significant drops:

```bash
python <SKILL>/scripts/detect_visibility_alerts.py \
  --current-metrics <RUN>/intermediate/metrics.json \
  --baseline-metrics <BASELINE>/intermediate/metrics.json \
  --output <RUN>/output/visibility_alerts.json
```

Triggers on drops in: mention_rate, recommendation_rate, geo_score, visibility_score.
Severity levels: info / warning / critical.
Write to `report.json` â†?`visibility_alerts`.

Reference: `references/methodology/visibility-alerts.md`

## v1.8 â€?Optimization Action Engine

```bash
python <SKILL>/scripts/generate_optimization_actions.py \
  --run-dir <RUN> \
  --output <RUN>/output/optimization_actions.json
```

- Generate prioritized actions from all findings
- Deduplicate and sequence actions
- Include effort estimates and validation methods
- Write to `output/optimization_actions.json`

Reference: `references/methodology/optimization-action-engine.md`