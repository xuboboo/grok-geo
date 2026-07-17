# Module: Search Pipeline (v1.4-v1.5)

> Extends Phase 4 �?Search Execution with enhanced pipeline.
> Scripts: `scripts/execute_search_batch.py`, `scripts/extract_search_signals.py`, `scripts/score_search_result.py`

## v1.4 �?Enhanced Search Pipeline

### 1. Generate search queue

```bash
python <SKILL>/scripts/execute_search_batch.py \
  --run-dir <RUN> --action queue --batch-size 5
```

### 2. For each question (original + variants)

a. Call `web_search` with the question text
b. Immediately extract deterministic signals:

```bash
python <SKILL>/scripts/extract_search_signals.py \
  --search-result /tmp/search_result_<qid>.json \
  --brand-name "<brand>" --brand-domain "<domain>" \
  --competitors '<competitor_json>' --aliases '<alias_json>' \
  --output /tmp/signals_<qid>.json
```

c. Merge signals into search result as `extracted_signals` field
d. Persist immediately:

```bash
python <SKILL>/scripts/append_search_result.py \
  --run-dir <RUN> --input /tmp/search_result_<qid>.json
```

### 3. Update batch statistics

```bash
python <SKILL>/scripts/execute_search_batch.py \
  --run-dir <RUN> --action stats
```

### Query Templates

| Template | Standard (30q) | Quick (10q) | Purpose |
|----------|---------------|-------------|---------|
| best_tools | 6 | 2 | Category discovery |
| alternatives | 5 | 2 | Competitor alternatives |
| recommendations | 8 | 3 | Scenario-specific (highest value) |
| reviews | 6 | 2 | Brand evaluation |
| comparisons | 5 | 1 | Feature comparison |

### Signal Extraction (6 classes)

- **A-class**: Brand visibility (mentioned/cited/position/heading)
- **B-class**: Recommendation (extracted by Agent in Phase 5)
- **C-class**: Competitor signals (mentioned/cited)
- **D-class**: Citation sources (domains/types/count)
- **E-class**: Platform hints (response length/list/table/inline citations)
- **F-class**: Response quality (citation density/specificity/refusal)

References: `references/research/realtime-citation-check.md`, `references/specification/search-query-templates.md`, `references/methodology/search-signal-extraction.md`

## v1.5 �?Snapshot, Quality Scoring & Retry

### 1. Score result quality

```bash
python <SKILL>/scripts/score_search_result.py \
  --search-result /tmp/search_result_<qid>.json \
  --brand-name "<brand>" --business-value <bv> \
  --output /tmp/scored_<qid>.json \
  --snapshot-output <RUN>/snapshots/<qid>/snap_<ts>.json
```

### 2. Retry if needed (score < 60 or soft failure)

- Apply recommended strategy (A-G) from `references/methodology/adaptive-retry-strategy.md`
- Max 1 retry per question

### 3. Drift detection (if historical run exists)

```bash
python <SKILL>/scripts/detect_drift.py \
  --baseline <HISTORICAL_RUN>/snapshots_index.json \
  --current <RUN>/snapshots_index.json \
  --output <RUN>/intermediate/drift_analysis.json
```

References: `references/research/search-snapshot-archiving.md`, `references/methodology/semantic-drift-detection.md`, `references/methodology/adaptive-retry-strategy.md`