# Optimization Action Engine

## Goal

Generate specific, prioritized, executable optimization actions from audit
findings. Transform raw metrics, gaps, and signals into an actionable plan
with clear ownership, deadlines, and validation methods.

## Action Categories

| Category | Description | Typical Effort |
|---|---|---|
| `content_creation` | Create new content to fill AI visibility gaps | 8–16 hours |
| `content_update` | Update existing content for accuracy and freshness | 4–8 hours |
| `technical_fix` | Fix technical SEO issues affecting citability | 2–4 hours |
| `backlink_building` | Build backlinks from high-authority publishers | 20–40 hours |
| `misperception_correction` | Correct factual errors in AI-generated answers | 8–16 hours |
| `schema_optimization` | Add or improve structured data markup | 2–4 hours |
| `faq_creation` | Create FAQ content for common AI queries | 4–8 hours |

## Action Generation Inputs

The engine synthesizes findings from multiple sources:

| Input Source | Key Signals | Action Types Generated |
|---|---|---|
| `opportunities.json` | High-score opportunity gaps | `content_creation`, `faq_creation` |
| `drift_analysis.json` | Position/recommendation drops | `content_update`, `misperception_correction` |
| `attribute_analysis.json` | Attribute coverage gaps | `content_creation`, `content_update` |
| `metrics.json` | Low visibility/recommendation rates | `content_creation`, `backlink_building` |
| `negative_signals` | Trust/citability issues | `technical_fix`, `schema_optimization` |
| `publisher_influence` | High-influence publishers | `backlink_building` |

## Priority Scoring

### Formula

```
priority_score = impact × urgency × feasibility
```

Where each factor is 1–10:

| Factor | Source | Low (1–3) | Medium (4–6) | High (7–10) |
|---|---|---|---|---|
| **Impact** | Opportunity score or drift severity | Minor gap | Moderate gap | Critical gap |
| **Urgency** | Time-sensitivity of the issue | Quarterly fix | Monthly fix | Immediate fix |
| **Feasibility** | Inverse of effort estimate | Major project | Medium effort | Quick win |

### Priority Levels

| Score Range | Priority Level | Timeline |
|---|---|---|
| 500+ | 🔴 Critical | Within 7 days |
| 200–499 | 🟠 High | Within 14 days |
| 50–199 | 🟡 Medium | Within 30 days |
| <50 | 🟢 Low | Next quarter |

## Action Schema

Each action in the optimization plan:

```json
{
  "title": "Create vendor comparison page for top 5 project management tools",
  "description": "Address gap in vendor_comparison stage where brand has 0% visibility",
  "category": "content_creation",
  "priority_score": 720,
  "priority_level": "critical",
  "target_questions": ["q-003", "q-007", "q-012"],
  "expected_impact": "Increase vendor_comparison visibility from 0% to 40%+",
  "effort_estimate": "8–12 hours",
  "validation_method": "Re-run audit after 14 days; check visibility_rate at vendor_comparison stage",
  "deadline_days": 14,
  "source": "journey_gap_analysis"
}
```

## Action Deduplication and Grouping

Before output, the engine:

1. **Deduplicates** actions targeting the same content with the same category
2. **Groups** related actions (e.g., multiple FAQ items → single FAQ creation project)
3. **Resolves conflicts** by keeping higher-priority action when two overlap
4. **Limits output** to max 15 actions to maintain executability

### Deduplication Rules

```
Two actions are duplicates if:
  - Same category AND
  - Overlapping target_questions (>50% overlap)
  
Merge strategy:
  - Keep higher priority_score
  - Union target_questions
  - Take max effort_estimate
```

## Output Structure

```json
{
  "generated_at": "2026-07-17T10:30:00Z",
  "total_actions": 12,
  "actions": [...],
  "category_summary": {
    "content_creation": 4,
    "content_update": 3,
    "technical_fix": 2,
    "backlink_building": 1,
    "misperception_correction": 1,
    "schema_optimization": 1,
    "faq_creation": 0
  },
  "total_effort_hours": 85,
  "critical_count": 2,
  "high_count": 4
}
```

## Agent Usage Guide

1. Run `generate_optimization_actions.py` in Phase 10 (improvement loop)
2. Required input: `opportunities.json`, `metrics.json`
3. Optional inputs: `drift_analysis.json`, `attribute_analysis.json`
4. Output: `optimization_plan.json` with max 15 prioritized actions
5. Present top-5 actions in report; full list in output file
6. Each action includes `deadline_days` and `validation_method` for re-test scheduling