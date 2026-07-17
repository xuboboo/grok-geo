# Module: Schema Automation (v1.9)

> Extends Phase 9 �?Report Rendering with AI-readable file generation.
> Script: `scripts/generate_schema_files.py`

## Usage

```bash
python <SKILL>/scripts/generate_schema_files.py \
  --input <RUN>/input/brand.json \
  --output-dir <RUN>/output
```

## Generated Files (5)

| File | Purpose | Source |
|------|---------|--------|
| `llms.txt` | AI-era robots.txt, tells AI crawlers what the site is | [llms.txt spec](https://llmstxt.org/) |
| `llms-full.txt` | Full version with sitemap and product details | [llms.txt spec](https://llmstxt.org/) |
| `entity.json` | schema.org Organization machine-readable entity | [aio-surfaces](https://github.com/Janady/aio-surfaces) |
| `brand.json` | AI-optimized brand context file | [geo-checklist](https://github.com/alexandrebrt14/geo-checklist) |
| `aeo.json` | AI Engine Optimization config (FAQ, key facts) | [aio-surfaces](https://github.com/Janady/aio-surfaces) |

## Auto-Validation

After generation, automatically validates:
- llms.txt contains brand name and >= 3 key URLs
- entity.json passes JSON-LD validation (name, url, @type)
- brand.json contains name, industry, target_customer
- aeo.json contains preferred_citation_name and >= 2 key_facts
- Cross-file brand name consistency

Validation manifest written to `output/schema_files_manifest.json`.

Reference: `references/research/schema-automation.md`