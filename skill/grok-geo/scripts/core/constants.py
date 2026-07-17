"""Core constants and configuration for grok-geo."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

SKILL_NAME = "grok-geo"
SKILL_VERSION = "5.0.0"
SCHEMA_VERSION = "5.0.0"

# Hosted default; local override via GEO_AUDIT_RUNS_DIR or --base-dir
HOSTED_RUNS_DIR = Path("/mnt/data/geo-audit-runs")
LOCAL_RUNS_DIR_NAME = "geo-audit-runs"

RUN_STATUSES = (
    "INITIALIZED",
    "VALIDATING_INPUT",
    "RESEARCHING_BRAND",
    "GENERATING_QUESTIONS",
    "WAITING_FOR_SEARCH",
    "SEARCHING",
    "ANALYZING_ENTITIES",
    "ANALYZING_CITATIONS",
    "VERIFYING_CLAIMS",
    "CALCULATING_METRICS",
    "GENERATING_OPPORTUNITIES",
    "RENDERING_REPORT",
    "VALIDATING_REPORT",
    "COMPLETED",
    "PARTIAL",
    "FAILED",
)

RECOMMENDATION_INTENTS = frozenset({"recommendation", "comparison", "purchase"})

RECOMMENDATION_MENTION_TYPES = frozenset({
    "strongly_recommended",
    "recommended",
    "weakly_recommended",
})

POSITIVE_RECOMMENDATION_TYPES = frozenset({
    "strongly_recommended",
    "recommended",
    "weakly_recommended",
})

RECOMMENDATION_TYPE_SCORES: Dict[str, float] = {
    "top_pick": 1.00,
    "strong_alternative": 0.75,
    "conditional": 0.45,
    "mentioned_only": 0.15,
    "discouraged": 0.00,
    "not_mentioned": 0.00,
}

# v1.1 — Composite GEO score weights
GEO_SCORE_WEIGHTS = {
    "visibility": 0.30,
    "mention": 0.25,
    "recommendation": 0.25,
    "citation": 0.20,
}

TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "yclid", "mc_cid", "mc_eid",
})

COMPANY_SUFFIXES = (
    "有限公司", "股份有限公司", "集团", "公司",
    "inc", "inc.", "ltd", "ltd.", "llc", "co", "co.",
    "corp", "corp.", "corporation", "limited",
)

LIMITATION_TEXT = (
    "本次结果基于指定时间、问题样本、地区和当前搜索运行环境。"
    "AI 搜索回答可能随时间、模型、平台、用户上下文和搜索索引变化。"
    "本报告不代表所有 AI 产品、所有账号或全部用户的绝对排名，"
    "也不保证采取建议后能进入 AI 推荐结果。"
)

FORBIDDEN_PROMISE_PATTERNS = (
    r"保证排名",
    r"(?<![不否])一定进入",
    r"绝对第一",
    r"保证进入",
    r"保证.*前三",
    r"100%提升",
)

# v1.2 — Content Freshness decay caps
FRESHNESS_DECAY_CAPS: Dict[str, int] = {
    "temporal": 30, "statistical": 25, "version": 20, "event": 15, "price": 10,
}

# v1.2 — RAG chunk readiness weights
RAG_CHUNK_WEIGHTS: Dict[str, float] = {
    "paragraph_structure": 0.25, "heading_hierarchy": 0.20,
    "definition_openings": 0.15, "self_containment": 0.20,
    "anchor_sentences": 0.10, "structured_data": 0.10,
}

PLATFORMS = ("chatgpt", "perplexity", "claude", "gemini", "ai_overview")

# v1.4 — Search Query Templates
SEARCH_TEMPLATE_TYPES = ("best_tools", "alternatives", "recommendations", "reviews", "comparisons")

STANDARD_TEMPLATE_DISTRIBUTION = {
    "best_tools": 6, "alternatives": 5, "recommendations": 8, "reviews": 6, "comparisons": 5,
}

QUICK_TEMPLATE_DISTRIBUTION = {
    "best_tools": 2, "alternatives": 2, "recommendations": 3, "reviews": 2, "comparisons": 1,
}

PLATFORM_FEATURES = {
    "chatgpt": {"inline_citations": "occasional", "source_cards": True, "style": "narrative", "list_common": True},
    "perplexity": {"inline_citations": "always", "source_cards": True, "style": "citation_dense", "list_common": True},
    "claude": {"inline_citations": "occasional", "source_cards": False, "style": "analytical", "list_common": False},
    "gemini": {"inline_citations": "occasional", "source_cards": True, "style": "list_oriented", "list_common": True},
}

# v1.6 — Loop Engineering
IMPROVEMENT_ACTION_TYPES = (
    "create_content", "update_content", "fix_misperception",
    "build_backlinks", "fix_technical", "expand_coverage",
)

RETEST_INTERVALS = {
    "create_content": 14, "update_content": 7, "fix_misperception": 7,
    "build_backlinks": 30, "fix_technical": 3, "expand_coverage": 14,
}

# v1.7 — Funnel Stage / Attribute Analysis / Alerts
FUNNEL_STAGES = ("awareness", "consideration", "conversion", "retention")

INTENT_TO_FUNNEL = {
    "category_knowledge": "awareness", "use_case": "awareness",
    "recommendation": "consideration", "comparison": "consideration",
    "purchase": "conversion", "brand_fact": "retention", "usage_support": "retention",
}

ATTRIBUTE_CATEGORIES = (
    "core_features", "pricing", "ease_of_use", "integrations",
    "support", "scalability", "security", "performance",
)

ATTRIBUTE_KEYWORDS = {
    "core_features": ["功能", "特性", "能力", "feature", "capability", "functionality"],
    "pricing": ["价格", "定价", "收费", "免费", "费用", "price", "pricing", "cost", "free"],
    "ease_of_use": ["易用", "简单", "上手", "学习曲线", "easy", "simple", "intuitive", "learning curve"],
    "integrations": ["集成", "对接", "插件", "API", "integration", "plugin", "connect"],
    "support": ["支持", "客服", "服务", "文档", "support", "service", "documentation"],
    "scalability": ["扩展", "规模化", "大规模", "scalab", "enterprise", "scale"],
    "security": ["安全", "合规", "隐私", "加密", "security", "compliance", "privacy", "encrypt"],
    "performance": ["性能", "速度", "响应", "稳定", "performance", "speed", "fast", "reliable"],
}

ALERT_THRESHOLDS = {
    "mention_rate": {"warning": 0.15, "critical": 0.30},
    "recommendation_rate": {"warning": 0.15, "critical": 0.30},
    "geo_score": {"warning": 10, "critical": 25},
    "visibility_score": {"warning": 10, "critical": 25},
}

# v1.8 — Publisher / Journey / Optimization
PUBLISHER_CATEGORIES = (
    "industry_media", "tech_blog", "review_site", "academic",
    "social_influencer", "news_outlet", "community_forum", "unknown",
)

JOURNEY_STAGES = (
    "problem_awareness", "solution_awareness", "vendor_comparison",
    "purchase_decision", "post_purchase",
)

FUNNEL_TO_JOURNEY = {
    "awareness": "problem_awareness", "consideration": "vendor_comparison",
    "conversion": "purchase_decision", "retention": "post_purchase",
}

OPTIMIZATION_ACTION_CATEGORIES = (
    "content_creation", "content_update", "technical_fix",
    "backlink_building", "misperception_correction", "schema_optimization", "faq_creation",
)

PUBLISHER_DOMAIN_PATTERNS = {
    "tech_blog": ["medium.com", "dev.to", "hashnode", "substack", "wordpress.com"],
    "review_site": ["g2.com", "capterra.com", "trustpilot.com", "getapp.com", "trustadius.com"],
    "academic": [".edu", "arxiv.org", "scholar.google", "researchgate.net"],
    "news_outlet": ["techcrunch.com", "theverge.com", "wired.com", "zdnet.com", "thenextweb.com"],
    "community_forum": ["reddit.com", "quora.com", "stackoverflow.com", "github.com"],
}

NEGATIVE_SIGNAL_DEDUCTIONS: Dict[str, int] = {
    "critical": 15, "high": 10, "medium": 5, "low": 2,
}

TRUST_STACK_WEIGHTS: Dict[str, float] = {
    "technical": 0.25, "identity": 0.20, "social": 0.20,
    "academic": 0.15, "consistency": 0.20,
}

PERCEPTION_WEIGHTS: Dict[str, float] = {
    "positioning_clarity": 0.25, "price_transparency": 0.15,
    "claim_consistency": 0.20, "sentiment_strength": 0.25,
    "competitor_framing": 0.15,
}