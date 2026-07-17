# Module: Brand Depth Scoring (v1.1-v1.3)

> Extends Phase 2 â€?Brand Research with deep scoring capabilities.
> Scripts: computed by `calculate_metrics.py` (reads from `metrics.json`)

## v1.1 â€?Site Readiness Check

Run against `references/methodology/site-readiness-checklist.md`:

- Check robots.txt for AI bot access (18 pts)
- Check llms.txt presence and quality (18 pts)
- Check JSON-LD structured data (16 pts)
- Check meta tags completeness (14 pts)
- Check content citability signals (12 pts)
- Check brand entity consistency (10 pts)
- Check technical signals (6 pts)
- Check AI discovery endpoints (6 pts)

Write results to `report.json` â†?`site_readiness` and `metrics.json` â†?`site_readiness_score`.

Reference: `references/methodology/site-readiness-checklist.md`

## v1.2 â€?Content Freshness & RAG Readiness

Using search results from brand research:

1. **Freshness**: Detect content decay signals (temporal, statistical, version, event, price)
   - Compute freshness score (0-100, higher = fresher)
   - Write to `metrics.json` â†?`freshness`

2. **RAG Readiness**: Assess RAG chunk readiness from representative page structure
   - 6 dimensions: paragraph_structure, heading_hierarchy, definition_openings, self_containment, anchor_sentences, structured_data
   - Write to `metrics.json` â†?`rag_readiness`

References: `references/methodology/content-freshness.md`

## v1.3 â€?Citability & Trust Stack

Reusing search results from brand research:

1. **Citability**: Score content citability from 20 weighted methods (cite sources +115%, statistics +40%, quotation +41%)
   - Write to `metrics.json` â†?`citability`

2. **Negative Signals**: Detect 8 anti-citation signals (CTA overload, thin content, keyword stuffing, etc.)
   - Write to `metrics.json` â†?`negative_signals`

3. **Trust Stack**: Compute 5-layer trust score (technical/identity/social/academic/consistency)
   - Write to `metrics.json` â†?`trust_stack`

References: `references/methodology/citability-scoring.md`, `references/methodology/negative-signals.md`, `references/methodology/trust-stack.md`