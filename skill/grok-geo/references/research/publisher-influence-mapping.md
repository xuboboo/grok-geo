# Publisher & Influencer Influence Mapping

## Goal

Map which publishers, media outlets, and influencers shape AI-generated answers
about a brand's category. Identify high-authority sources that AI models
frequently cite, enabling targeted outreach and content strategy.

## Publisher Categories

| Category | Description | Examples |
|---|---|---|
| `industry_media` | Trade publications and industry-specific media | Industry blogs, trade journals |
| `tech_blog` | Technology-focused blogs and publications | medium.com, dev.to, substack |
| `review_site` | Software/product review platforms | g2.com, capterra.com, trustpilot.com |
| `academic` | Academic institutions and research | .edu domains, arxiv.org, researchgate.net |
| `social_influencer` | Social media creators and influencers | Twitter/X creators, YouTube channels |
| `news_outlet` | Major news and business media | techcrunch.com, theverge.com, wired.com |
| `community_forum` | Community-driven Q&A and discussion | reddit.com, quora.com, stackoverflow.com |

## Influence Scoring

### Formula

```
influence_score = citation_count × support_ratio
```

Where:
- **citation_count**: Total number of times this publisher's content is cited across all questions
- **support_ratio**: Proportion of citations where the publisher supports (positively mentions) the target brand

### Authority Weight Sources

Authority weight can be derived from multiple signals:

1. **Domain age proxy** (from search results): Older, established domains carry more authority
2. **Citation count across questions**: Publishers cited in more questions have broader influence
3. **Cross-platform presence**: Publishers appearing across multiple AI platforms have wider reach

### Classification Rules

Publisher category is determined by domain pattern matching:

- Known review sites → `review_site`
- `.edu` / `arxiv.org` / `scholar.google` → `academic`
- Social platforms → `social_influencer`
- Known news domains → `news_outlet`
- Community forums → `community_forum`
- Known tech blogs → `tech_blog`
- Default → `industry_media`

## Output Structure

```json
{
  "publishers": [
    {
      "domain": "techcrunch.com",
      "publisher_type": "news_outlet",
      "citation_count": 5,
      "questions_cited_in": ["q-1", "q-3", "q-7"],
      "support_ratio": 0.6,
      "influence_score": 3.0,
      "brand_relationship": "neutral"
    }
  ],
  "summary": {
    "total_publishers": 15,
    "top_influencer": "techcrunch.com",
    "type_distribution": {
      "news_outlet": 4,
      "review_site": 3,
      "tech_blog": 5,
      "academic": 2,
      "community_forum": 1
    }
  }
}
```

### Brand Relationship Classification

Each publisher is classified by how it relates to the brand in citations:

| Relationship | Criteria |
|---|---|
| `supports` | >60% of citations positively mention the brand |
| `neutral` | 40-60% of citations are positive |
| `against` | <40% of citations are positive |

## Top Influencer Identification

For outreach prioritization, publishers are ranked by:

1. **influence_score** (primary): Higher score = higher priority
2. **citation_count** (secondary): More citations = broader reach
3. **support_ratio** (tertiary): Lower support = higher outreach opportunity

### Outreach Priority Matrix

| Influence | Current Support | Priority |
|---|---|---|
| High | Against/Neutral | 🔴 Critical — address misperceptions |
| High | Supports | 🟢 Maintain — strengthen relationship |
| Low | Against | 🟡 Monitor — watch for growth |
| Low | Neutral | ⚪ Low — not urgent |

## Agent Usage Guide

1. Run `map_publisher_influence.py` after citation classification (Phase 5)
2. Input: `citations.json` with domain, question_id, supports_target_brand fields
3. Output: Ranked publisher list saved to `publisher_influence.json`
4. Use top-5 influencers for Phase 7 outreach opportunity generation
5. Feed publisher data into `generate_optimization_actions.py` for actionable outreach plans