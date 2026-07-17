#!/usr/bin/env python3
"""Entity SEO & Knowledge Graph Scorer — 实体完整性与知识图谱评分。

评估品牌实体在知识图谱中的完整性和权威性。

用法:
  python score_entity_kg.py --input <run_dir>/input/brand.json \
    --run-dir <RUN> --output <RUN>/intermediate/entity_kg_score.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (
    read_json,
    write_json,
    utc_now_iso,
    clamp,
    domain_from_url,
    normalize_entity_name,
)


# ─── Dimension definitions ──────────────────────────────────────────────

def score_basic_declaration(brand: Dict[str, Any], site_data: Dict[str, Any]) -> Dict[str, Any]:
    """Score basic entity declaration completeness (0-25)."""
    items: List[Dict[str, Any]] = []
    total = 0

    # 1. Organization schema complete (5 pts)
    org_schema = site_data.get("org_schema", {})
    org_fields = ["name", "url", "logo", "description"]
    present = [f for f in org_fields if org_schema.get(f)]
    score = round(5 * len(present) / len(org_fields))
    items.append({"check": "org_schema_complete", "score": score, "max": 5,
                  "detail": f"{len(present)}/{len(org_fields)} fields present"})
    total += score

    # 2. sameAs links >= 3 (5 pts)
    same_as = brand.get("social_links", {})
    same_as_count = len(same_as)
    # Check for knowledge base links
    known_kb = brand.get("knowledge_base_links", [])
    same_as_count += len(known_kb)
    score = min(5, round(5 * same_as_count / 3))
    items.append({"check": "sameas_links", "score": score, "max": 5,
                  "detail": f"{same_as_count} sameAs links found"})
    total += score

    # 3. entity.json exists (3 pts)
    has_entity = site_data.get("has_entity_json", False)
    score = 3 if has_entity else 0
    items.append({"check": "entity_json", "score": score, "max": 3,
                  "detail": "exists" if has_entity else "missing"})
    total += score

    # 4. brand.json exists (3 pts)
    has_brand = site_data.get("has_brand_json", False)
    score = 3 if has_brand else 0
    items.append({"check": "brand_json", "score": score, "max": 3,
                  "detail": "exists" if has_brand else "missing"})
    total += score

    # 5. aeo.json exists (3 pts)
    has_aeo = site_data.get("has_aeo_json", False)
    score = 3 if has_aeo else 0
    items.append({"check": "aeo_json", "score": score, "max": 3,
                  "detail": "exists" if has_aeo else "missing"})
    total += score

    # 6. llms.txt brand info (3 pts)
    llms = site_data.get("llms_txt", {})
    llms_score = 0
    if llms.get("exists"):
        if llms.get("has_brand_name"):
            llms_score += 1
        if llms.get("has_description"):
            llms_score += 1
        if llms.get("has_key_pages"):
            llms_score += 1
    items.append({"check": "llms_txt_info", "score": llms_score, "max": 3,
                  "detail": f"{llms_score}/3 llms.txt fields"})
    total += llms_score

    # 7. Contact info verifiable (3 pts)
    contact_score = 0
    if brand.get("contact_email"):
        contact_score += 1
    if brand.get("contact_phone"):
        contact_score += 1
    if brand.get("address"):
        contact_score += 1
    items.append({"check": "contact_info", "score": contact_score, "max": 3,
                  "detail": f"{contact_score}/3 contact fields"})
    total += contact_score

    return {"score": total, "max": 25, "items": items}


def score_knowledge_graph(brand: Dict[str, Any], search_data: Dict[str, Any]) -> Dict[str, Any]:
    """Score knowledge graph presence (0-25)."""
    items: List[Dict[str, Any]] = []
    total = 0

    # 1. Wikidata entry (8 pts)
    wikidata = search_data.get("wikidata", {})
    wikidata_score = 0
    if wikidata.get("has_entry"):
        wikidata_score += 4
        if wikidata.get("has_qid"):
            wikidata_score += 2
        if wikidata.get("properties_filled", 0) >= 5:
            wikidata_score += 2
    items.append({"check": "wikidata", "score": wikidata_score, "max": 8,
                  "detail": f"Q-ID: {wikidata.get('qid', 'none')}, properties: {wikidata.get('properties_filled', 0)}"})
    total += wikidata_score

    # 2. Wikipedia page (6 pts)
    wikipedia = search_data.get("wikipedia", {})
    wiki_score = 0
    if wikipedia.get("has_page"):
        wiki_score += 4
        if not wikipedia.get("is_redirect", True):
            wiki_score += 2
    items.append({"check": "wikipedia", "score": wiki_score, "max": 6,
                  "detail": f"page: {wikipedia.get('page_title', 'none')}"})
    total += wiki_score

    # 3. Google Knowledge Panel (4 pts)
    gkp = search_data.get("google_knowledge_panel", {})
    gkp_score = 4 if gkp.get("exists") else 0
    items.append({"check": "gkp", "score": gkp_score, "max": 4,
                  "detail": "exists" if gkp.get("exists") else "not found"})
    total += gkp_score

    # 4. Crunchbase/PitchBook (3 pts)
    biz_db = search_data.get("business_databases", {})
    biz_score = 3 if biz_db.get("crunchbase") or biz_db.get("pitchbook") else 0
    items.append({"check": "business_db", "score": biz_score, "max": 3,
                  "detail": f"crunchbase={biz_db.get('crunchbase', False)}, pitchbook={biz_db.get('pitchbook', False)}"})
    total += biz_score

    # 5. Industry directories (2 pts)
    directories = search_data.get("industry_directories", [])
    dir_score = min(2, len(directories))
    items.append({"check": "directories", "score": dir_score, "max": 2,
                  "detail": f"{len(directories)} directories found"})
    total += dir_score

    # 6. Vertical knowledge bases (2 pts)
    vertical = search_data.get("vertical_kb", [])
    vert_score = min(2, len(vertical))
    items.append({"check": "vertical_kb", "score": vert_score, "max": 2,
                  "detail": f"{len(vertical)} vertical KB entries"})
    total += vert_score

    return {"score": total, "max": 25, "items": items}


def score_entity_relationships(brand: Dict[str, Any]) -> Dict[str, Any]:
    """Score entity relationship graph completeness (0-20)."""
    items: List[Dict[str, Any]] = []
    total = 0

    # 1. founder → Person (4 pts)
    founders = brand.get("founders", [])
    founder_score = min(4, len(founders) * 2)
    items.append({"check": "founder_link", "score": founder_score, "max": 4,
                  "detail": f"{len(founders)} founders"})
    total += founder_score

    # 2. product → Organization (4 pts)
    products = brand.get("products", [])
    product_score = min(4, len(products))
    items.append({"check": "product_link", "score": product_score, "max": 4,
                  "detail": f"{len(products)} products"})
    total += product_score

    # 3. competitor → Organization (3 pts)
    competitors = brand.get("competitors", [])
    comp_score = min(3, len(competitors))
    items.append({"check": "competitor_link", "score": comp_score, "max": 3,
                  "detail": f"{len(competitors)} competitors"})
    total += comp_score

    # 4. parentOrg / subsidiary (3 pts)
    parent = brand.get("parent_company")
    subsidiaries = brand.get("subsidiaries", [])
    parent_score = 0
    if parent:
        parent_score += 2
    if subsidiaries:
        parent_score += 1
    items.append({"check": "org_hierarchy", "score": parent_score, "max": 3,
                  "detail": f"parent={parent}, subsidiaries={len(subsidiaries)}"})
    total += parent_score

    # 5. awards (2 pts)
    awards = brand.get("awards", [])
    award_score = min(2, len(awards))
    items.append({"check": "awards", "score": award_score, "max": 2,
                  "detail": f"{len(awards)} awards"})
    total += award_score

    # 6. knowsAbout topics (2 pts)
    topics = brand.get("expertise_topics", brand.get("knows_about", []))
    topic_score = min(2, len(topics))
    items.append({"check": "knows_about", "score": topic_score, "max": 2,
                  "detail": f"{len(topics)} topics"})
    total += topic_score

    # 7. memberOf (2 pts)
    memberships = brand.get("memberships", brand.get("memberOf", []))
    member_score = min(2, len(memberships))
    items.append({"check": "member_of", "score": member_score, "max": 2,
                  "detail": f"{len(memberships)} memberships"})
    total += member_score

    return {"score": total, "max": 20, "items": items}


def score_entity_consistency(brand: Dict[str, Any], search_data: Dict[str, Any]) -> Dict[str, Any]:
    """Score entity consistency across platforms (0-15)."""
    items: List[Dict[str, Any]] = []
    total = 0

    brand_name = brand.get("brand_name", "")
    consistency = search_data.get("name_consistency", {})

    # 1. Brand name consistent across platforms (5 pts)
    variants = consistency.get("variants_found", [])
    if len(variants) <= 1:
        name_score = 5
    elif len(variants) <= 2:
        name_score = 3
    else:
        name_score = 1
    items.append({"check": "name_consistency", "score": name_score, "max": 5,
                  "detail": f"{len(variants)} name variants found"})
    total += name_score

    # 2. Description semantic consistency (4 pts)
    desc_consistency = consistency.get("description_alignment", 0)
    desc_score = round(4 * clamp(desc_consistency, 0, 1))
    items.append({"check": "description_consistency", "score": desc_score, "max": 4,
                  "detail": f"alignment: {desc_consistency:.2f}"})
    total += desc_score

    # 3. Category/industry consistency (3 pts)
    cat_consistency = consistency.get("category_alignment", 0)
    cat_score = round(3 * clamp(cat_consistency, 0, 1))
    items.append({"check": "category_consistency", "score": cat_score, "max": 3,
                  "detail": f"alignment: {cat_consistency:.2f}"})
    total += cat_score

    # 4. Key facts consistency (3 pts)
    facts_consistency = consistency.get("facts_alignment", 0)
    facts_score = round(3 * clamp(facts_consistency, 0, 1))
    items.append({"check": "facts_consistency", "score": facts_score, "max": 3,
                  "detail": f"alignment: {facts_consistency:.2f}"})
    total += facts_score

    return {"score": total, "max": 15, "items": items}


def score_entity_authority(brand: Dict[str, Any], search_data: Dict[str, Any]) -> Dict[str, Any]:
    """Score entity authority signals (0-15)."""
    items: List[Dict[str, Any]] = []
    total = 0

    authority = search_data.get("authority_signals", {})

    # 1. External citations >= 10 domains (5 pts)
    citing_domains = authority.get("citing_domains", [])
    cite_score = min(5, round(5 * len(citing_domains) / 10))
    items.append({"check": "external_citations", "score": cite_score, "max": 5,
                  "detail": f"{len(citing_domains)} citing domains"})
    total += cite_score

    # 2. Media coverage >= 3 (4 pts)
    media = authority.get("media_mentions", [])
    media_score = min(4, round(4 * len(media) / 3))
    items.append({"check": "media_coverage", "score": media_score, "max": 4,
                  "detail": f"{len(media)} media mentions"})
    total += media_score

    # 3. Academic citations (3 pts)
    academic = authority.get("academic_citations", 0)
    acad_score = min(3, academic)
    items.append({"check": "academic", "score": acad_score, "max": 3,
                  "detail": f"{academic} academic citations"})
    total += acad_score

    # 4. Government/standards body (3 pts)
    gov = authority.get("government_references", 0)
    gov_score = min(3, gov)
    items.append({"check": "government", "score": gov_score, "max": 3,
                  "detail": f"{gov} government references"})
    total += gov_score

    return {"score": total, "max": 15, "items": items}


# ─── Action item generator ──────────────────────────────────────────────

def generate_action_items(
    basic: Dict[str, Any],
    kg: Dict[str, Any],
    rels: Dict[str, Any],
    consistency: Dict[str, Any],
    authority: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate prioritized action items from scores."""
    actions: List[Dict[str, Any]] = []

    # P0: Critical missing items
    for item in basic["items"]:
        if item["score"] == 0 and item["max"] >= 3:
            actions.append({"priority": "P0", "action": f"Create {item['check']}", "impact": "Basic entity declaration"})

    for item in kg["items"]:
        if item["score"] == 0 and item["max"] >= 4:
            actions.append({"priority": "P0", "action": f"Establish {item['check']}", "impact": "Knowledge graph presence"})

    # P1: Partial items
    for item in kg["items"]:
        if 0 < item["score"] < item["max"] and item["max"] >= 3:
            actions.append({"priority": "P1", "action": f"Improve {item['check']}", "impact": "Knowledge graph completeness"})

    for item in rels["items"]:
        if item["score"] == 0:
            actions.append({"priority": "P1", "action": f"Add {item['check']} relationship", "impact": "Entity relationship graph"})

    # P2: Enhancement
    for item in authority["items"]:
        if item["score"] < item["max"]:
            actions.append({"priority": "P2", "action": f"Build {item['check']}", "impact": "Entity authority"})

    return actions


# ─── Main scorer ────────────────────────────────────────────────────────

def score_entity_kg(
    brand: Dict[str, Any],
    site_data: Optional[Dict[str, Any]] = None,
    search_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compute full entity KG score."""
    site_data = site_data or {}
    search_data = search_data or {}

    basic = score_basic_declaration(brand, site_data)
    kg = score_knowledge_graph(brand, search_data)
    rels = score_entity_relationships(brand)
    cons = score_entity_consistency(brand, search_data)
    auth = score_entity_authority(brand, search_data)

    total = basic["score"] + kg["score"] + rels["score"] + cons["score"] + auth["score"]

    if total >= 90:
        grade = "A"
    elif total >= 75:
        grade = "B"
    elif total >= 60:
        grade = "C"
    elif total >= 40:
        grade = "D"
    else:
        grade = "F"

    actions = generate_action_items(basic, kg, rels, cons, auth)

    return {
        "schema_version": "2.1.0",
        "scored_at": utc_now_iso(),
        "entity_score": total,
        "grade": grade,
        "dimensions": {
            "basic_declaration": basic,
            "knowledge_graph": kg,
            "entity_relationships": rels,
            "entity_consistency": cons,
            "entity_authority": auth,
        },
        "action_items": actions,
    }


# ─── CLI ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Entity KG Scorer")
    parser.add_argument("--input", required=True, help="Brand input JSON")
    parser.add_argument("--run-dir", help="Run directory (for loading metrics)")
    parser.add_argument("--output", help="Output path")
    args = parser.parse_args()

    brand = read_json(args.input)

    site_data: Dict[str, Any] = {}
    search_data: Dict[str, Any] = {}

    if args.run_dir:
        run_dir = Path(args.run_dir)
        metrics_path = run_dir / "intermediate" / "metrics.json"
        if metrics_path.exists():
            metrics = read_json(metrics_path)
            site_data = metrics.get("site_readiness", {})

        # Populate search_data from entity_analysis.jsonl (real search results)
        from geo_common import read_jsonl as _read_jsonl
        entity_path = run_dir / "intermediate" / "entity_analysis.jsonl"
        citations_path = run_dir / "intermediate" / "citations.json"

        citing_domains: set = set()
        media_mentions: list = []
        name_variants: set = set()
        engines_with_mention: set = set()

        if entity_path.exists():
            entities = _read_jsonl(entity_path)
            brand_norm = normalize_entity_name(brand.get("brand_name", ""))
            for entry in entities:
                answer = entry.get("answer_text", entry.get("search_answer", ""))
                engine = entry.get("engine", "unknown")
                # Check if brand is mentioned
                if brand_norm and brand_norm in normalize_entity_name(answer):
                    engines_with_mention.add(engine)
                # Extract name variants
                for entity in entry.get("entities", []):
                    if entity.get("entity_type") == "target_brand":
                        name_variants.add(entity.get("canonical_name", ""))
                        name_variants.discard("")

        if citations_path.exists():
            citations = read_json(citations_path) if citations_path.suffix == ".json" else _read_jsonl(citations_path)
            cit_list = citations if isinstance(citations, list) else citations.get("citations", [])
            for cit in cit_list:
                domain = cit.get("domain", "")
                if domain:
                    citing_domains.add(domain)
                source_type = cit.get("source_type", "")
                if source_type in ("earned_media", "news"):
                    media_mentions.append(domain)

        # Determine KG presence from search results
        has_wikipedia = any("wikipedia" in d for d in citing_domains)
        has_crunchbase = any("crunchbase" in d for d in citing_domains)

        search_data = {
            "wikidata": {"has_entry": has_wikipedia, "has_qid": False, "properties_filled": 0},
            "wikipedia": {"has_page": has_wikipedia, "is_redirect": False},
            "google_knowledge_panel": {"exists": len(engines_with_mention) >= 3},
            "business_databases": {"crunchbase": has_crunchbase, "pitchbook": False},
            "industry_directories": [d for d in citing_domains if d not in citing_domains - {"g2.com", "capterra.com", "trustpilot.com"}],
            "vertical_kb": [],
            "name_consistency": {
                "variants_found": list(name_variants),
                "description_alignment": 0.0,
                "category_alignment": 0.0,
                "facts_alignment": 0.0,
            },
            "authority_signals": {
                "citing_domains": list(citing_domains),
                "media_mentions": media_mentions,
                "academic_citations": 0,
                "government_references": 0,
            },
        }

    report = score_entity_kg(brand, site_data, search_data)

    if args.output:
        write_json(args.output, report)
        print(f"Entity KG score: {report['entity_score']}/100 (Grade: {report['grade']})")
        print(f"Action items: {len(report['action_items'])}")
    else:
        from geo_common import print_json
        print_json(report)


if __name__ == "__main__":
    main()