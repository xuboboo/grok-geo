# GEO Brand Audit — Metric Definitions

> Version: 5.0.0
> All numeric metrics are produced by deterministic scripts. Do NOT hand-compute.

## Metric Tiering System

| Tier | Name | Confidence | Data Source | Report Treatment |
|------|------|-----------|-------------|-----------------|
| **T1** | Core | High | Pure algorithmic, search-result-derived | Display prominently, no caveat needed |
| **T2** | Extended | Medium | Deterministic but requires richer input data | Display with "data quality" note |
| **T3** | Experimental | Low | Heuristic / estimated / insufficient history | Display with explicit caveat, collapsible section |

### Tier Classification Rules

- **T1**: Score derived entirely from observed search results + deterministic formula. No estimation, no fallback defaults.
- **T2**: Score is deterministic, but input data may be partial (e.g., only some platforms queried, or site crawl data missing). Formula is sound, but coverage gaps affect accuracy.
- **T3**: Score uses heuristic constants, magic-number extrapolation, or falls back to estimated values when real data is absent. Must be labeled `⚠️ Experimental` in reports.

### Data Source Labels

| Label | Meaning |
|-------|---------|
| `measured` | Derived from actual search results or crawled data |
| `checklist` | Boolean evaluation of brand.json fields |
| `heuristic` | Uses hardcoded coefficients or extrapolation |
| `estimated` | Falls back to defaults when real data is missing |

---

## v1.1 New Metrics — **T1 Core**

| Metric | Source | Tier | Data | Description |
|--------|--------|------|------|-------------|
| `geo_score` | Composite | T1 | measured | 0-100 weighted composite: visibility(30%) + mention(25%) + recommendation(25%) + citation(20%) |
| `sentiment_index` | OneGlanse | T1 | measured | Average sentiment_score across all brand mentions (0-100 scale) |
| `recommendation_type_distribution` | OneGlanse | T1 | measured | Count per recommendation_type (top_pick / strong_alternative / conditional / mentioned_only / discouraged) |
| `citation_share_by_competitor` | ai-brand-monitor-mcp | T1 | measured | Per-competitor positive recommendation score and share of voice |
| `competitor_co_mentions` | ai-brand-monitor-mcp | T1 | measured | Which competitor entity_ids co-appear alongside brand in same answers |
| `site_readiness_score` | geo-optimizer-skill | T2 | measured | 0-100 technical readiness (robots.txt, llms.txt, schema, meta, content, entity, signals, AI endpoints) |
| `platform_citation_map` | OneGlanse + ai-brand-monitor-mcp | T1 | measured | Cross-platform visibility score, platform parity index, source overlap rate, platform advantage ranking |
| `freshness` | geo-optimizer-skill v4.7 | T1 | measured | Content freshness score (0-100), 5 decay pattern detection (temporal/statistical/version/event/price) |
| `rag_readiness` | geo-optimizer-skill v4.7 | T2 | measured | RAG chunk readiness (0-100), 6 dimensions (paragraph/heading/definition/self-contained/anchor/structured). Requires site crawl data. |
| `citability` | geo-optimizer-skill (KDD 2024) | T1 | measured | Content citability score (0-100), 20 weighted methods (cite_sources +115%, statistics +40%, quotation +41%) |
| `negative_signals` | geo-optimizer-skill | T1 | measured | Anti-citation signal score (0-100), 8 signal types (CTA overload, thin content, keyword stuffing, etc.) |
| `trust_stack` | geo-optimizer-skill | T2 | measured | 5-layer trust stack (A-F grade): technical, identity, social, academic, consistency. Some layers require site crawl. |
| `ai_perception` | OneGlanse + geo-optimizer-skill | T1 | measured | AI perception snapshot: positioning, price, claims, sentiment, competitor associations, misperceptions |

## v1.9 New Metrics — **T1 Core / T2 Extended**

| Metric | Source | Tier | Data | Description |
|--------|--------|------|------|-------------|
| `geo_lint_score` | geo-lint | T1 | measured | 0-100 GEO compliance score (6 dimensions: Schema 25% / Crawler 20% / Citability 25% / Entity 15% / Multimodal 8% / i18n 7%) |
| `geo_lint_grade` | geo-lint | T1 | measured | A-F grade (A=90+, B=75-89, C=60-74, D=40-59, F=<40) |
| `geo_lint_errors` | geo-lint | T1 | measured | ERROR-level issues count (each -5 points) |
| `geo_lint_warnings` | geo-lint | T1 | measured | WARNING-level issues count (each -2 points) |
| `schema_files_generated` | schema-automation | T1 | measured | Number of AI-readable files generated (5 types: llms.txt / llms-full.txt / entity.json / brand.json / aeo.json) |
| `schema_validation_passed` | schema-automation | T1 | measured | Cross-file validation all passed (boolean) |

## v2.0 New Metrics — **T1 Core**

| Metric | Source | Tier | Data | Description |
|--------|--------|------|------|-------------|
| `engines_used` | multi-engine | T1 | measured | List of AI engines used |
| `cross_engine_citation_consistency` | multi-engine | T1 | measured | Cross-engine citation consistency index (0-1, 1=all engines cite same sources) |
| `engine_success_rate` | multi-engine | T1 | measured | Per-engine query success rate |
| `engine_citation_rate` | multi-engine | T1 | measured | Per-engine citation rate (queries returning citations / total) |
| `engine_unique_domains` | multi-engine | T1 | measured | Per-engine unique cited domain count |

## v2.1 New Metrics — **T2 Extended**

| Metric | Source | Tier | Data | Description |
|--------|--------|------|------|-------------|
| `entity_kg_score` | entity-kg | T2 | measured | 0-100 entity completeness score (5 dimensions: basic 25 + KG 25 + relationships 20 + consistency 15 + authority 15). Requires rich brand.json input. |
| `entity_kg_grade` | entity-kg | T2 | measured | A-F grade (A=90+, B=75-89, C=60-74, D=40-59, F=<40) |
| `entity_action_items` | entity-kg | T2 | measured | Prioritized action list (P0/P1/P2), each with action + impact |

## v2.2 New Metrics — **T2 Extended**

| Metric | Source | Tier | Data | Description |
|--------|--------|------|------|-------------|
| `i18n_score` | i18n | T2 | measured | 0-100 internationalization score (tech 30 + content 30 + regional entity 20 + AI coverage 20). Requires multi-language search results. |
| `i18n_grade` | i18n | T2 | measured | A-F grade |
| `per_language_scores` | i18n | T2 | measured | Per-language individual scores |

## v2.3 New Metrics — **T2 Extended**

| Metric | Source | Tier | Data | Description |
|--------|--------|------|------|-------------|
| `closed_loop_actions` | closed-loop | T2 | measured | Prioritized action list (P0/P1/P2), with type/effort/deadline/validation |
| `citation_growth_rate` | closed-loop | T2 | measured | Citation growth rate (new_citations - baseline) / baseline. Requires baseline run. |
| `outreach_response_rate` | closed-loop | T2 | measured | Outreach response rate |

## v2.4 New Metrics — **T2 Extended**

| Metric | Source | Tier | Data | Description |
|--------|--------|------|------|-------------|
| `ai_traffic_sessions` | analytics | T2 | measured | AI referrer total sessions. Requires GA4 integration. |
| `ai_traffic_share` | analytics | T2 | measured | AI traffic share of total traffic |
| `ai_engagement_rate` | analytics | T2 | measured | AI user average engagement rate |
| `ai_conversion_rate` | analytics | T2 | measured | AI user conversion rate |
| `ai_top_landing_pages` | analytics | T2 | measured | AI traffic top landing pages |

## v2.5 New Metrics — **T2 Extended**

| Metric | Source | Tier | Data | Description |
|--------|--------|------|------|-------------|
| `academic_evidence_count` | academic | T2 | measured | Number of academic studies adopted |
| `optimization_methods_covered` | academic | T2 | measured | Number of academic optimization methods implemented (/9) |
| `research_freshness` | academic | T2 | measured | Year of most recent cited research |

## v3.0 New Metrics — **T1 Core / T2 Extended**

| Metric | Source | Tier | Data | Description |
|--------|--------|------|------|-------------|
| `chatgpt_shopping_rate` | Profound | T2 | measured | Brand product recommendation rate in shopping prompts. Requires ChatGPT Shopping API. |
| `chatgpt_product_rank` | Profound | T2 | measured | Average product ranking position |
| `prompt_discovery_count` | Otterly | T2 | measured | AI prompts discovered from seed keywords |
| `prompt_quality_avg` | Otterly | T2 | measured | Average quality score of discovered prompts |
| `ai_sov_overall` | Semrush | T1 | measured | AI Share of Voice overall (0-1) |
| `ai_sov_by_intent` | Semrush | T1 | measured | AI SOV by intent layer |
| `ai_sov_by_platform` | Semrush | T1 | measured | AI SOV by platform |
| `agentic_readiness_score` | Google I/O 2026 | T2 | checklist | Agentic Search readiness (0-100) |
| `ai_crawl_coverage` | Writesonic | T2 | measured | AI crawler coverage (crawled pages / total pages) |
| `persona_tracking_coverage` | Conductor | T2 | measured | Prompt coverage by user persona |

## v4.0 New Metrics — **T2 Extended / T3 Experimental**

| Metric | Source | Tier | Data | Description |
|--------|--------|------|------|-------------|
| `cross_engine_consistency_score` | Bluefish | T1 | measured | Cross-AI-engine brand narrative consistency (0-1) |
| `word_association_pos` | Evertune | T2 | measured | Positive word associations (count + frequency) |
| `word_association_neg` | Evertune | T2 | measured | Negative word associations (count + frequency) |
| `narrative_framing` | AthenaHQ | T2 | measured | Brand narrative frame (leader/challenger/specialist/niche) |
| `narrative_deviation_score` | AthenaHQ | T2 | measured | Narrative deviation (0-1, 0=fully consistent) |
| `platform_favorability` | Goodie AI | T2 | measured | Per-AI-engine brand favorability (0-100) |
| `ubs` | Conductor | T2 | measured | Unified Brand Score (0-100, GEO 40% + SEO 30% + Brand 30%) |
| `agentic_engine_status` | Whitebox | T3 | ⚠️ heuristic | Agentic GEO engine status (running/idle/error). No real engine integration. |
| `agentic_cycle_count` | AgenticGEO | T3 | ⚠️ heuristic | Autonomous optimization cycle count. No real cycle tracking. |

## v5.0 New Metrics — **T1 Core / T2 Extended / T3 Experimental**

| Metric | Source | Tier | Data | Description |
|--------|--------|------|------|-------------|
| `agentic_conversion_rate` | Bain/Amazon Rufus | T2 | checklist | Agent-Ready Hub readiness score (0-1). Boolean checklist against brand.json fields. |
| `agent_ready_score` | NetRanks | T2 | checklist | Agent-Ready Hub readiness (0-100). 7 boolean checks. |
| `hallucinations_detected` | NetRanks | T2 | measured | Brand hallucinations detected (4 severity levels). String matching against known_facts. |
| `defensive_geo_status` | NetRanks | T2 | measured | Defensive status (none/in_progress/verified). Derived from hallucination check. |
| `a2a_score` | NetRanks | T2 | checklist | Agent-to-Agent readiness (0-100). 7 boolean checks against brand.json. |
| `agent_manifest_exists` | NetRanks | T2 | checklist | Agent Manifest exists (boolean) |
| `multimodal_score` | GEOMOND | T3 | ⚠️ estimated | Multimodal GEO composite score (0-100). **Falls back to brand.json boolean estimation when site crawl data is absent.** Text/Image/Video/Voice scores use `has_blog? 40 : 0` style heuristics. |
| `predict_30d` | Trend Extrapolation | T3 | ⚠️ heuristic | 30-day trend extrapolation (0-100). **NOT a prediction model.** Uses `current_score × 1.09` with hardcoded momentum/velocity/seasonal constants. No historical data required. |
| `predict_90d` | Trend Extrapolation | T3 | ⚠️ heuristic | 90-day trend extrapolation (0-100). Same formula as 30d with ×3 multiplier. |
| `predict_confidence` | Trend Extrapolation | T3 | ⚠️ heuristic | Confidence interval. Width = `10 + (days/90) × 5`. No statistical basis. |

### v5.0 Experimental Metric Caveats

Reports MUST include the following caveat when displaying T3 metrics:

```
⚠️ Experimental Metrics Notice
The following metrics use heuristic estimation and should not be used for
decision-making without validation against real data:
- multimodal_score: estimated from brand.json fields when site data is unavailable
- predict_30d/90d: trend extrapolation using fixed coefficients, not a prediction model
- predict_confidence: arbitrary interval width, not statistically derived
```

---

## Version Mapping

| Feature Version | schema_version | Scripts |
|----------------|----------------|---------|
| v1.0-v1.8 | 1.0 | Core scripts, search enhancement, funnel/alert scripts |
| v1.9 | 1.9.0 | geo_lint.py, generate_schema_files.py |
| v2.0 | 2.0.0 | multi_engine_query.py |
| v2.1 | 2.1.0 | score_entity_kg.py |
| v2.2 | 2.2.0 | score_i18n.py |
| v2.3 | 2.3.0 | generate_closed_loop_actions.py |
| v2.4 | 2.4.0 | analyze_ai_referrers.py |
| v3.0 | 3.0.0 | cutting_edge_geo.py |
| v4.0 | 4.0.0 | ultimate_geo.py |
| v5.0 | 5.0.0 | ceiling_geo.py, calculate_metrics.py |

> Note: `core/constants.py` holds `SCHEMA_VERSION = "5.0.0"`. `calculate_metrics.py` references this constant.