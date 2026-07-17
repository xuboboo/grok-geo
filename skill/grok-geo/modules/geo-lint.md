# Module: GEO Lint (v1.9)

> Extends Phase 2 â€?Brand Research with pre-publish compliance check.
> Script: `scripts/geo_lint.py`

## Usage

```bash
python <SKILL>/scripts/geo_lint.py \
  --input <RUN>/input/brand.json \
  --run-dir <RUN> \
  --output <RUN>/output/geo_lint_report.json
```

## Dimensions (6, 92 rules total)

| Dimension | Weight | Rules | Checks |
|-----------|--------|-------|--------|
| Schema | 25% | 22 | JSON-LD completeness, Organization/Product/FAQ schema, sameAs, speakable |
| Crawler | 20% | 18 | AI bot reachability (GPTBot/ClaudeBot/PerplexityBot), llms.txt, robots.txt |
| Citability | 25% | 20 | Factual claims, statistics, quotes, CTA ratio, keyword density, heading hierarchy |
| Entity | 15% | 14 | Brand name consistency, schema-brand match, contact info, sameAs links |
| Multimodal | 8% | 10 | Alt text, video captions, TOC, table headers, mobile |
| i18n | 7% | 8 | hreflang, lang attribute, multilingual URLs, date formats |

## Grading

- A (90+) / B (75-89) / C (60-74) / D (40-59) / F (<40)
- Severity deductions: ERROR -5, WARNING -2, INFO -0

## Output

- `output/geo_lint_report.json` â€?full lint report
- Embedded in report's "Site Readiness" section

Reference: `references/specification/geo-lint-rules.md` â€?92 rules full definition