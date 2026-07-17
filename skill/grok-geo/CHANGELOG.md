# Changelog

## 5.0.0 — 2026-07-18

### Architecture Refactoring + Metric Tiering + MCP Server

**Architecture:**
- Split `geo_common.py` (1201 lines) into `core/` (9 modules) + `scoring/` (1 module) sub-packages
- Backward-compatible shim: existing `from geo_common import ...` unchanged, 94 tests pass
- New import paths: `core.constants`, `core.io_utils`, `core.path_utils`, `core.hashing`, `core.time_utils`, `core.validation`, `core.locking`, `core.text_utils`, `core.url_utils`, `core.cli_utils`

**Metric Tiering (T1/T2/T3):**
- T1 Core: Pure algorithmic, search-result-derived (no caveats needed)
- T2 Extended: Deterministic but requires richer input data (data quality note)
- T3 Experimental: Heuristic/estimated/insufficient history (explicit caveats required)
- `predict_30d/90d` renamed to "Trend Extrapolation" — honest about being `current_score × 1.09`, not a prediction model
- `multimodal_score` labeled T3 when estimated from brand.json fallbacks
- All T3 metrics include `⚠️_notice` field in output JSON

**MCP Server:**
- New `mcp/` directory with `manifest.json` + `mcp_server.py`
- 7 tools: `geo_audit_run`, `geo_audit_status`, `geo_audit_report`, `geo_audit_metrics`, `geo_schedule_add`, `geo_schedule_list`, `geo_schedule_run`
- Stdio JSON-RPC transport, compatible with Cursor MCP integration

**SKILL.md Updates:**
- Phase 10 fully integrated: scheduler setup, monitor alert checks, drift detection, closed-loop optimization
- References section updated with new `specification/`, `methodology/`, `research/` structure

**Documentation:**
- `references/` reorganized: 43 files → 3 subdirectories (10 specification + 20 methodology + 13 research)
- `references/INDEX.md` created with full catalog
- `METRICS.md` rewritten with T1/T2/T3 tiering, data source labels, and experimental caveats
- `CHANGELOG.md` restructured: last 3 versions detailed, older versions collapsed

## 5.0.0 — 2026-07-17

### Ceiling: Agentic Commerce + Defensive GEO + A2A + Multimodal GEO + Predictive

- `scripts/ceiling_geo.py` — 5 subcommands: agentic-commerce, defensive, a2a, multimodal, predict, full-check
- Agentic Commerce: Agent Conversion Rate, Agent-Ready Hub (7 boolean checks)
- Defensive GEO: Hallucination detection (4 severity levels), auto-correction chain
- A2A: Agent Manifest generation (capabilities + API endpoints + verification)
- Multimodal GEO: Text/Image/Video/Voice 4-dimension scoring, cross-modal consistency
- Predictive: 30/90-day trend extrapolation (T3 Experimental — heuristic coefficients, not ML)

## 4.0.0 — 2026-07-17

### Agentic Brand Vault + Narrative Analysis + Multi-Model Heatmap + Agentic GEO Engine

- `scripts/ultimate_geo.py` — 6 subcommands: brand-vault, narrative, heatmap, agentic, hybrid, full-audit
- Brand Vault: Word association graphs, cross-engine consistency scoring (CECS), narrative deviation
- Narrative Analysis: Brand framing detection (leader/challenger/specialist/niche), tone scoring
- Multi-Model Heatmap: Per-engine favorability, platform advantage ranking
- Agentic GEO Engine: 5 autonomous agents (monitor/diagnose/optimize/verify/report)
- Unified Brand Score (UBS): 40% GEO + 30% SEO + 30% Brand

## 3.0.0 — 2026-07-17

### 2026 Cutting-Edge: ChatGPT Shopping + Prompt Discovery + AI SOV + Agentic Search

- `scripts/cutting_edge_geo.py` — Prompt Discovery generator, AI SOV calculator, Agentic Readiness check, ChatGPT Shopping analysis
- ChatGPT Shopping: Product appearance rate, avg rank, competitor comparison
- AI Prompt Discovery: Auto-discover prompts from seed keywords, 4 intent × multi-template generation
- AI Share of Voice (SOV): Overall / by-intent / by-funnel-stage / by-competitor
- Agentic Readiness: Google I/O 2026 checklist (Product Schema, real-time data, API accessibility)
- Persona-Based Tracking: 5 user personas (Technical/Business/EndUser/ITAdmin/Developer)

---

<details>
<summary>v2.5 and earlier (collapsed)</summary>

## 2.5.0 — 2026-07-17
i18n scoring (4 dimensions), closed-loop optimization actions, GA4/GSC AI referrer analysis, academic frontiers (Princeton KDD 2024 9 methods). New: `score_i18n.py`, `generate_closed_loop_actions.py`, `analyze_ai_referrers.py`.

## 2.1.0 — 2026-07-17
Entity SEO + Knowledge Graph: 5-dimension entity completeness scoring (basic/KG/relationships/consistency/authority). New: `score_entity_kg.py`.

## 2.0.0 — 2026-07-17
Multi-engine real API queries: 6 AI engine adapters (ChatGPT/Perplexity/Claude/Gemini/Grok/DeepSeek), unified response format, auto-fallback to web_search. New: `multi_engine_query.py`.

## 1.9.0 — 2026-07-17
Schema automation + GEO Lint: 92-rule compliance check (6 dimensions), auto-generate llms.txt/entity.json/brand.json/aeo.json. New: `geo_lint.py`, `generate_schema_files.py`.

## 1.8.0 — 2026-07-17
Publisher influence mapping, buying journey metrics (5 stages), optimization action engine (7 types). New: `map_publisher_influence.py`, `compute_journey_metrics.py`, `generate_optimization_actions.py`.

## 1.7.0 — 2026-07-17
Funnel stage classification, attribute-level analysis (8 categories), visibility alerts (6 types). New: `classify_funnel_stage.py`, `extract_attribute_analysis.py`, `detect_visibility_alerts.py`.

## 1.6.0 — 2026-07-17
Continuous improvement loop: run chaining, drift-driven improvement plans, retest triggers. New: `chain_runs.py`, `generate_improvement_plan.py`.

## 1.5.0 — 2026-07-17
Search time dimensions: snapshot archiving, semantic drift detection (6 drift types), adaptive retry (7 strategies). New: `score_search_result.py`, `detect_drift.py`.

## 1.4.0 — 2026-07-17
Search pipeline: 5 query templates, batch execution, signal extraction (6 signal types). New: `execute_search_batch.py`, `extract_search_signals.py`.

## 1.3.0 — 2026-07-17
Content quality: citability scoring (20 methods), negative signals (8 types), trust stack (5 layers A-F), AI perception snapshot.

## 1.2.0 — 2026-07-17
Content freshness (5 decay patterns), RAG readiness (6 dimensions), cross-platform citation map, topic authority scoring.

## 1.1.0 — 2026-07-17
GEO composite score, sentiment index, recommendation type classification, competitor co-mention tracking, site readiness checklist.

## 1.0.0 — 2026-07-17
Initial release: input protocol, run state machine, search persistence, citation classification, deterministic metrics, opportunity ranking, report rendering & validation.

</details>