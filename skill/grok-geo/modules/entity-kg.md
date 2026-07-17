# Module: Entity KG Scoring (v2.1)

> Extends Phase 2 �?Brand Research with entity completeness scoring.
> Script: `scripts/score_entity_kg.py`

## Usage

```bash
python <SKILL>/scripts/score_entity_kg.py \
  --input <RUN>/input/brand.json \
  --run-dir <RUN> \
  --output <RUN>/intermediate/entity_kg_score.json
```

## Dimensions (5, total 100)

| Dimension | Score | Checks |
|-----------|-------|--------|
| Basic Entity Declaration | 25 | Organization schema / sameAs / entity.json / brand.json / aeo.json / llms.txt / contact info |
| Knowledge Graph Registration | 25 | Wikidata Q-ID / Wikipedia page / Google Knowledge Panel / Crunchbase / industry directories |
| Entity Relationship Graph | 20 | founder / product / competitor / parentOrg / award / knowsAbout / memberOf |
| Entity Consistency | 15 | Brand name cross-platform consistency / description semantic consistency / category consistency / key facts consistency |
| Entity Authority Signals | 15 | External citing domain count / media coverage / academic citations / government citations |

## Output

- Auto-generates prioritized action list (P0/P1/P2)
- Each action item includes: dimension, action description, estimated impact

Reference: `references/research/entity-knowledge-graph.md` �?three-layer entity model, scoring details, optimization action list