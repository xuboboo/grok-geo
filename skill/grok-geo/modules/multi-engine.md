# Module: Multi-Engine Query (v2.0)

> Extends Phase 4 �?Search Execution with real AI engine API queries.
> Script: `scripts/multi_engine_query.py`

## Usage

```bash
# Check available engines
python <SKILL>/scripts/multi_engine_query.py health-check

# Batch query (auto-distribute)
python <SKILL>/scripts/multi_engine_query.py batch \
  --run-dir <RUN> --mode standard

# Specify engines
python <SKILL>/scripts/multi_engine_query.py batch \
  --run-dir <RUN> --engines chatgpt,perplexity,claude
```

## Supported Engines (6)

| Engine | Env Variable | Citations | Standard Share |
|--------|-------------|-----------|----------------|
| ChatGPT Search | `OPENAI_API_KEY` | Yes | 30% |
| Perplexity | `PERPLEXITY_API_KEY` | Yes | 25% |
| Claude Search | `ANTHROPIC_API_KEY` | Yes | 20% |
| Gemini | `GOOGLE_API_KEY` | Yes | 15% |
| Grok | `XAI_API_KEY` | No | 5% |
| DeepSeek | `DEEPSEEK_API_KEY` | No | 5% |

## Fallback

When API is unavailable, auto-degrades to `web_search` simulation. Response is tagged with `"fallback": "web_search"`.

## Cross-Engine Analysis (auto-computed)

- Citation Consistency Index (CEC): 0-1, measures overlap of cited sources across engines
- Per-engine stats: mention_rate / recommendation_rate / citation_rate / unique_domains
- Response format detection: narrative / list / table, inline citation detection

## Output

- `<RUN>/raw/engine_responses.jsonl` �?raw query results
- `<RUN>/intermediate/cross_engine_metrics.json` �?cross-engine metrics

Reference: `references/research/multi-engine-query.md`