#!/usr/bin/env python3
"""Extract deterministic signals from a single search result.

Extracts A-class (brand visibility) and D-class (citation) signals
deterministically. B-class (recommendation) and F-class (quality)
signals are left for Agent semantic judgment in Phase 5.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import normalize_entity_name, read_json  # noqa: E402


def extract_domain(url: str) -> str:
    """Extract domain from URL, normalized to lowercase."""
    try:
        parsed = urlparse(url)
        return (parsed.netloc or "").lower().lstrip("www.")
    except Exception:
        return ""


def contains_brand(
    text: str,
    brand_name: str,
    aliases: Optional[Sequence[str]] = None,
    products: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Check if brand is mentioned in text. Returns match details."""
    text_lower = text.lower()
    norm_brand = normalize_entity_name(brand_name, strip_company_suffix=False)

    matches = []

    # Check brand name
    if norm_brand and norm_brand in text_lower:
        matches.append({"type": "brand_name", "value": norm_brand})

    # Check aliases
    for alias in aliases or []:
        norm_alias = normalize_entity_name(alias, strip_company_suffix=False)
        if norm_alias and norm_alias in text_lower:
            matches.append({"type": "alias", "value": norm_alias})

    # Check product names
    for product in products or []:
        norm_product = normalize_entity_name(product, strip_company_suffix=False)
        if norm_product and norm_product in text_lower:
            matches.append({"type": "product", "value": norm_product})

    return {
        "mentioned": len(matches) > 0,
        "matches": matches,
        "match_count": len(matches),
    }


def find_brand_position(text: str, brand_name: str, aliases: Optional[Sequence[str]] = None) -> Optional[int]:
    """Find the position of brand first mention (by paragraph index)."""
    paragraphs = re.split(r"\n\s*\n", text)
    needles = [normalize_entity_name(brand_name, strip_company_suffix=False)]
    for a in aliases or []:
        needles.append(normalize_entity_name(a, strip_company_suffix=False))

    for i, para in enumerate(paragraphs):
        para_lower = para.lower()
        for needle in needles:
            if needle and needle in para_lower:
                return i
    return None


def detect_list_structure(text: str) -> bool:
    """Detect if text contains list structures."""
    # Numbered lists: 1. 2. 3. or 1) 2) 3)
    if re.search(r"(?:^|\n)\s*(?:\d+[\.\)]\s)", text):
        return True
    # Bullet lists: - * •
    if re.search(r"(?:^|\n)\s*[\-\*•]\s", text):
        return True
    return False


def detect_table_structure(text: str) -> bool:
    """Detect if text contains table-like structures."""
    # Pipe-separated tables
    if re.search(r"\|.*\|.*\|", text):
        return True
    # Tab-separated or multi-space aligned columns
    if re.search(r"(?:^|\n)\s*\S+\s{3,}\S+\s{3,}\S+", text):
        return True
    return False


def classify_citation_source(
    domain: str,
    brand_domain: str,
    competitor_domains: Sequence[str],
) -> str:
    """Classify a citation domain into a source type."""
    domain_lower = domain.lower()
    brand_d = brand_domain.lower().lstrip("www.")

    if brand_d and (domain_lower == brand_d or domain_lower.endswith("." + brand_d)):
        return "owned"

    for comp_d in competitor_domains:
        comp_d = comp_d.lower().lstrip("www.")
        if comp_d and (domain_lower == comp_d or domain_lower.endswith("." + comp_d)):
            return "competitor_owned"

    # Known social platforms
    social_domains = {"twitter.com", "x.com", "facebook.com", "linkedin.com", "instagram.com",
                      "youtube.com", "reddit.com", "weibo.com", "zhihu.com", "xiaohongshu.com"}
    if domain_lower in social_domains or any(domain_lower.endswith("." + s) for s in social_domains):
        return "social"

    # Known commerce
    commerce_domains = {"amazon.com", "taobao.com", "jd.com", "tmall.com"}
    if domain_lower in commerce_domains:
        return "commerce"

    return "earned_media"


def extract_signals(
    search_result: Dict[str, Any],
    brand_name: str,
    brand_domain: str,
    competitors: Optional[Sequence[str]] = None,
    aliases: Optional[Sequence[str]] = None,
    products: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Extract all deterministic signals from a search result.

    Returns a dict with A-class, D-class, and E-class signals.
    """
    answer_text = search_result.get("answer_text", "")
    citations = search_result.get("citations") or []
    sources = search_result.get("sources") or []

    # ── A-class: Brand visibility signals ──
    brand_check = contains_brand(answer_text, brand_name, aliases, products)
    brand_position = find_brand_position(answer_text, brand_name, aliases)

    brand_domain_lower = brand_domain.lower().lstrip("www.")
    competitor_domains = []
    competitor_names_norm = []
    for c in (competitors or []):
        if isinstance(c, dict):
            competitor_domains.append(c.get("website", ""))
            competitor_names_norm.append(normalize_entity_name(c.get("name", ""), strip_company_suffix=False))
        else:
            competitor_names_norm.append(normalize_entity_name(str(c), strip_company_suffix=False))

    # Check citations for brand domain
    brand_cited = False
    brand_domain_cited = False
    for cit in citations:
        cit_url = cit.get("url", "")
        cit_domain = extract_domain(cit_url)
        if brand_domain_lower and cit_domain == brand_domain_lower:
            brand_cited = True
            brand_domain_cited = True

    # Check answer text for brand domain URL
    if brand_domain_lower and brand_domain_lower in answer_text.lower():
        brand_domain_cited = True

    # Check if brand appears in heading-like context
    brand_in_heading = False
    lines = answer_text.split("\n")
    for line in lines:
        if re.match(r"^#{1,3}\s|^\*\*.*\*\*$|^\d+[\.\)]\s.*\*\*", line):
            if any(m["value"] in line.lower() for m in brand_check.get("matches", [])):
                brand_in_heading = True
                break

    # ── A-class: Competitor signals ──
    competitor_mentioned = []
    competitor_cited = []
    for comp_name in competitor_names_norm:
        if comp_name and comp_name in answer_text.lower():
            competitor_mentioned.append(comp_name)

    for cit in citations:
        cit_domain = extract_domain(cit.get("url", ""))
        for comp_d in competitor_domains:
            comp_d_norm = comp_d.lower().lstrip("www.")
            if comp_d_norm and cit_domain == comp_d_norm:
                competitor_cited.append(comp_d_norm)

    # ── D-class: Citation signals ──
    citation_domains = []
    citation_types = {}
    for cit in citations:
        domain = extract_domain(cit.get("url", ""))
        if domain and domain not in citation_domains:
            citation_domains.append(domain)
            source_type = classify_citation_source(domain, brand_domain, competitor_domains)
            citation_types[source_type] = citation_types.get(source_type, 0) + 1

    # Also extract from sources
    for src in sources:
        domain = extract_domain(src.get("url", ""))
        if domain and domain not in citation_domains:
            citation_domains.append(domain)

    # ── E-class: Platform signals ──
    response_length = len(answer_text)
    has_list = detect_list_structure(answer_text)
    has_table = detect_table_structure(answer_text)

    # Detect inline citation patterns
    has_inline_citations = bool(re.search(r"\[\d+\]|\(\d{4}\)|\[(?:source|来源)\s*\d*\]", answer_text))

    # Estimate factual specificity
    number_count = len(re.findall(r"\b\d+(?:\.\d+)?%?\b", answer_text))
    if number_count >= 5:
        factual_specificity = "high"
    elif number_count >= 2:
        factual_specificity = "medium"
    else:
        factual_specificity = "low"

    # Check for refusal
    refusal_patterns = ["无法回答", "无法提供", "I cannot", "I'm unable", "没有相关信息", "我不确定"]
    is_refusal = any(p in answer_text for p in refusal_patterns)

    return {
        # A-class
        "brand_mentioned": brand_check["mentioned"],
        "brand_match_details": brand_check["matches"],
        "brand_cited": brand_cited,
        "brand_domain_cited": brand_domain_cited,
        "brand_position_in_answer": brand_position,
        "brand_in_heading": brand_in_heading,
        # C-class
        "competitor_mentioned": competitor_mentioned,
        "competitor_cited": list(set(competitor_cited)),
        # D-class
        "citation_domains": citation_domains,
        "citation_count": len(citations),
        "citation_types": citation_types,
        "brand_domain_in_citations": brand_domain_cited,
        # E-class
        "platform_hints": {
            "response_length": response_length,
            "has_inline_citations": has_inline_citations,
            "has_list_structure": has_list,
            "has_table_structure": has_table,
        },
        # F-class (partial, deterministic part)
        "response_quality": {
            "citation_density": round(len(citations) / max(response_length, 1) * 1000, 2),
            "factual_specificity": factual_specificity,
            "is_refusal": is_refusal,
        },
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract deterministic signals from a search result"
    )
    parser.add_argument("--search-result", required=True, help="Path to search result JSON")
    parser.add_argument("--brand-name", required=True, help="Target brand name")
    parser.add_argument("--brand-domain", required=True, help="Target brand domain")
    parser.add_argument("--competitors", default="[]", help="JSON array of competitor names or objects")
    parser.add_argument("--aliases", default="[]", help="JSON array of brand aliases")
    parser.add_argument("--products", default="[]", help="JSON array of product names")
    parser.add_argument("--output", default=None, help="Output file path")
    args = parser.parse_args(argv)

    search_result = read_json(args.search_result)
    competitors = json.loads(args.competitors)
    aliases = json.loads(args.aliases)
    products = json.loads(args.products)

    signals = extract_signals(
        search_result,
        args.brand_name,
        args.brand_domain,
        competitors=competitors,
        aliases=aliases,
        products=products,
    )

    output = json.dumps(signals, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())