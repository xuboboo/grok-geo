#!/usr/bin/env python3
"""Classify citation URLs (§11)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (  # noqa: E402
    domain_from_url,
    is_same_or_subdomain,
    print_json,
    read_json,
    read_jsonl,
    write_json,
)
from normalize_urls import normalize_url  # noqa: E402

# Predefined institutional / community / social / commerce domains (partial)
INSTITUTIONAL_DOMAINS = {
    "gov.cn",
    "edu.cn",
    "wikipedia.org",
    "zh.wikipedia.org",
    "who.int",
    "nih.gov",
    "europa.eu",
}
SOCIAL_DOMAINS = {
    "weibo.com",
    "twitter.com",
    "x.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "douyin.com",
    "xiaohongshu.com",
    "xhslink.com",
    "linkedin.com",
}
COMMUNITY_DOMAINS = {
    "zhihu.com",
    "reddit.com",
    "stackoverflow.com",
    "v2ex.com",
    "tieba.baidu.com",
    "quora.com",
    "github.com",
    "juejin.cn",
    "csdn.net",
}
COMMERCE_DOMAINS = {
    "tmall.com",
    "taobao.com",
    "jd.com",
    "amazon.com",
    "amazon.cn",
    "pinduoduo.com",
    "suning.com",
}
DIRECTORY_DOMAINS = {
    "crunchbase.com",
    "tianyancha.com",
    "qichacha.com",
    "bloomberg.com",
    "g2.com",
    "capterra.com",
    "producthunt.com",
}
MEDIA_HINTS = (
    "news",
    "media",
    "press",
    "blog",
    "report",
    "review",
    "article",
)


def classify_domain(
    domain: str,
    *,
    brand_domain: str = "",
    competitor_domains: Optional[Sequence[str]] = None,
    title: str = "",
) -> str:
    domain = (domain or "").lower()
    if brand_domain and is_same_or_subdomain(domain, brand_domain):
        return "owned"
    for cd in competitor_domains or []:
        if cd and is_same_or_subdomain(domain, cd):
            return "competitor_owned"
    for root in INSTITUTIONAL_DOMAINS:
        if is_same_or_subdomain(domain, root):
            return "institutional"
    for root in SOCIAL_DOMAINS:
        if is_same_or_subdomain(domain, root):
            return "social"
    for root in COMMUNITY_DOMAINS:
        if is_same_or_subdomain(domain, root):
            return "community"
    for root in COMMERCE_DOMAINS:
        if is_same_or_subdomain(domain, root):
            return "commerce"
    for root in DIRECTORY_DOMAINS:
        if is_same_or_subdomain(domain, root):
            return "directory"
    blob = f"{domain} {title}".lower()
    if any(h in blob for h in MEDIA_HINTS):
        return "earned_media"
    # common news TLDs / media sites heuristics
    if any(x in domain for x in (".news", "36kr", "techcrunch", "forbes", "huxiu", "ifanr")):
        return "earned_media"
    return "unknown"


def classify_citation(
    citation: Dict[str, Any],
    *,
    brand_domain: str,
    competitor_domains: Sequence[str],
    question_id: str = "",
    order: int = 1,
) -> Dict[str, Any]:
    url = citation.get("url") or citation.get("original_url") or ""
    norm = normalize_url(url)
    source_type = classify_domain(
        norm["domain"],
        brand_domain=brand_domain,
        competitor_domains=competitor_domains,
        title=citation.get("title") or "",
    )
    return {
        "question_id": question_id or citation.get("question_id") or "",
        "original_url": norm["original_url"] or url,
        "canonical_url": norm["canonical_url"],
        "domain": norm["domain"],
        "title": citation.get("title") or "",
        "source_type": source_type,
        "citation_order": citation.get("citation_order") or order,
        "supports_target_brand": bool(citation.get("supports_target_brand", False)),
        "supports_competitor": bool(citation.get("supports_competitor", False)),
        "support_description": citation.get("support_description") or "",
        "confidence": citation.get("confidence"),
        "url_sha256": norm["url_sha256"],
    }


def classify_from_search_results(
    search_rows: Sequence[Dict[str, Any]],
    brand: Dict[str, Any],
    preclassified: Optional[Sequence[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    brand_domain = domain_from_url(brand.get("website") or "")
    competitor_domains = [
        domain_from_url(c.get("website") or "")
        for c in (brand.get("competitors") or [])
        if c.get("website")
    ]
    # index preclassified by original/canonical url
    pre_by_url: Dict[str, Dict[str, Any]] = {}
    for item in preclassified or []:
        for key in ("original_url", "canonical_url", "url"):
            if item.get(key):
                pre_by_url[item[key]] = item

    out: List[Dict[str, Any]] = []
    for row in search_rows:
        qid = row.get("question_id") or ""
        citations = row.get("citations") or []
        for i, cit in enumerate(citations, 1):
            base = dict(cit)
            url = base.get("url") or ""
            if url in pre_by_url:
                base.update({k: v for k, v in pre_by_url[url].items() if k not in ("url",)})
            out.append(
                classify_citation(
                    base,
                    brand_domain=brand_domain,
                    competitor_domains=competitor_domains,
                    question_id=qid,
                    order=i,
                )
            )
    return out


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Classify citation URLs")
    parser.add_argument("--run-dir", default=None)
    parser.add_argument("--brand", default=None, help="brand.json path")
    parser.add_argument("--search-results", default=None)
    parser.add_argument("--input", default=None, help="optional pre-annotated citations JSON")
    parser.add_argument("--output", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir) if args.run_dir else None
    brand_path = Path(args.brand) if args.brand else (run_dir / "input" / "brand.json" if run_dir else None)
    if not brand_path or not brand_path.exists():
        print("brand input required", file=sys.stderr)
        return 1
    brand = read_json(brand_path)

    sr_path = (
        Path(args.search_results)
        if args.search_results
        else (run_dir / "raw" / "search_results.jsonl" if run_dir else None)
    )
    if not sr_path or not sr_path.exists():
        print("search results required", file=sys.stderr)
        return 1
    rows = read_jsonl(sr_path)

    pre = None
    if args.input:
        data = read_json(args.input)
        if isinstance(data, dict) and "citations" in data:
            pre = data["citations"]
        elif isinstance(data, list):
            pre = data

    citations = classify_from_search_results(rows, brand, pre)
    payload = {"schema_version": "1.0", "citations": citations}
    write_json(args.output, payload)
    if args.json:
        print_json({"count": len(citations), "output": args.output})
    else:
        print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())