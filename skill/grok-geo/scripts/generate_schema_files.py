#!/usr/bin/env python3
"""Schema Automation — AI 可读文件自动生成器。

从品牌输入自动生成 5 种 AI 可读文件：
  - llms.txt / llms-full.txt / entity.json / brand.json / aeo.json

用法:
  python generate_schema_files.py --input <run_dir>/input/brand.json \
    --output-dir <run_dir>/output [--search-results <run_dir>/raw/search_results.jsonl]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (
    read_json,
    read_jsonl,
    write_json,
    utc_now_iso,
    print_json,
)


# ─── llms.txt generation ────────────────────────────────────────────────

def generate_llms_txt(brand: Dict[str, Any]) -> str:
    """Generate llms.txt content following the llms.txt specification."""
    name = brand.get("brand_name", "Brand")
    description = brand.get("description", "")
    if len(description) > 160:
        description = description[:157] + "..."

    products = brand.get("products", [])
    website = brand.get("website", "").rstrip("/")
    industry = brand.get("industry", "")

    lines = [
        f"# {name}",
        f"> {description}" if description else f"> {industry} solution",
        "",
    ]

    # Products section
    if products:
        lines.append("## Products")
        for p in products:
            if isinstance(p, dict):
                pname = p.get("name", "")
                pdesc = p.get("description", "")
                purl = p.get("url", "")
                lines.append(f"- [{pname}]({purl}): {pdesc}" if purl else f"- {pname}: {pdesc}")
            else:
                lines.append(f"- {p}")
        lines.append("")

    # Key Pages
    key_pages = [
        ("About", f"{website}/about"),
        ("Pricing", f"{website}/pricing"),
        ("Documentation", f"{website}/docs"),
        ("Blog", f"{website}/blog"),
    ]
    lines.append("## Key Pages")
    for label, url in key_pages:
        lines.append(f"- [{label}]({url})")
    lines.append("")

    # Contact
    contact_email = brand.get("contact_email", "")
    social = brand.get("social_links", {})
    if contact_email or social:
        lines.append("## Contact")
        if contact_email:
            lines.append(f"- Email: {contact_email}")
        for platform, handle in social.items():
            lines.append(f"- {platform.title()}: {handle}")
        lines.append("")

    # FAQ
    faq = brand.get("faq", [])
    if faq:
        lines.append("## Frequently Asked Questions")
        for item in faq[:10]:
            q = item.get("question", "") if isinstance(item, dict) else ""
            a = item.get("answer", "") if isinstance(item, dict) else ""
            if q:
                lines.append(f"- {q}")
                if a:
                    lines.append(f"  {a}")
        lines.append("")

    lines.append(f"## Last Updated")
    lines.append(utc_now_iso()[:10])

    return "\n".join(lines) + "\n"


def generate_llms_full_txt(brand: Dict[str, Any]) -> str:
    """Generate llms-full.txt — extended version with complete info."""
    base = generate_llms_txt(brand)
    name = brand.get("brand_name", "Brand")
    website = brand.get("website", "").rstrip("/")

    extra_sections = []

    # Team
    founders = brand.get("founders", [])
    if founders:
        extra_sections.append("## Team")
        for f in founders:
            if isinstance(f, dict):
                extra_sections.append(f"- {f.get('name', '')} — {f.get('role', 'Founder')}")
            else:
                extra_sections.append(f"- {f}")
        extra_sections.append("")

    # Competitors (for AI context)
    competitors = brand.get("competitors", [])
    if competitors:
        extra_sections.append("## Category Context")
        extra_sections.append(f"This product competes in the {brand.get('industry', '')} space.")
        extra_sections.append("Notable alternatives include:")
        for c in competitors[:5]:
            extra_sections.append(f"- {c}")
        extra_sections.append("")

    # Key facts
    known_facts = brand.get("known_facts", [])
    if known_facts:
        extra_sections.append("## Key Facts")
        for fact in known_facts:
            if isinstance(fact, dict):
                extra_sections.append(f"- {fact.get('claim', '')}")
            else:
                extra_sections.append(f"- {fact}")
        extra_sections.append("")

    # Supported languages
    languages = brand.get("supported_languages", [])
    if languages:
        extra_sections.append("## Supported Languages")
        extra_sections.append(", ".join(languages))
        extra_sections.append("")

    if extra_sections:
        base = base.rstrip() + "\n\n" + "\n".join(extra_sections) + "\n"

    return base


# ─── entity.json generation ─────────────────────────────────────────────

def generate_entity_json(brand: Dict[str, Any]) -> Dict[str, Any]:
    """Generate entity.json (schema.org Organization)."""
    website = brand.get("website", "").rstrip("/")
    entity: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": brand.get("brand_name", ""),
        "url": website,
        "description": brand.get("description", ""),
    }

    logo = brand.get("logo_url")
    if logo:
        entity["logo"] = logo

    founding = brand.get("founding_year") or brand.get("founded")
    if founding:
        entity["foundingDate"] = str(founding)

    founders = brand.get("founders", [])
    if founders:
        entity["founders"] = []
        for f in founders:
            if isinstance(f, dict):
                entity["founders"].append({"@type": "Person", "name": f.get("name", "")})
            else:
                entity["founders"].append({"@type": "Person", "name": str(f)})

    # sameAs
    same_as: List[str] = []
    social = brand.get("social_links", {})
    social_url_map = {
        "twitter": "https://twitter.com/{}",
        "linkedin": "https://linkedin.com/company/{}",
        "github": "https://github.com/{}",
        "facebook": "https://facebook.com/{}",
        "youtube": "https://youtube.com/{}",
    }
    for platform, handle in social.items():
        template = social_url_map.get(platform.lower())
        if template:
            if handle.startswith("http"):
                same_as.append(handle)
            else:
                same_as.append(template.format(handle.lstrip("@")))
    if same_as:
        entity["sameAs"] = same_as

    # Contact
    contact_email = brand.get("contact_email", "")
    contact_phone = brand.get("contact_phone", "")
    if contact_email or contact_phone:
        cp: Dict[str, Any] = {"@type": "ContactPoint", "contactType": "customer service"}
        if contact_email:
            cp["email"] = contact_email
        if contact_phone:
            cp["telephone"] = contact_phone
        entity["contactPoint"] = cp

    # Address
    address = brand.get("address", {})
    if address:
        addr: Dict[str, Any] = {"@type": "PostalAddress"}
        for key in ("streetAddress", "addressLocality", "addressRegion", "postalCode", "addressCountry"):
            if address.get(key):
                addr[key] = address[key]
        if len(addr) > 1:
            entity["address"] = addr

    # Certifications
    certs = brand.get("certifications", [])
    if certs:
        entity["hasCredential"] = [
            {"@type": "EducationalOccupationalCredential", "name": c}
            for c in certs
        ]

    return entity


# ─── brand.json generation ──────────────────────────────────────────────

def generate_brand_json(brand: Dict[str, Any]) -> Dict[str, Any]:
    """Generate brand.json — AI-optimized brand context file."""
    result: Dict[str, Any] = {
        "name": brand.get("brand_name", ""),
        "industry": brand.get("industry", ""),
        "target_customer": brand.get("target_customer", ""),
        "website": brand.get("website", ""),
    }

    # Optional fields
    optional_mappings = {
        "tagline": "tagline",
        "founded": "founding_year",
        "hq": "headquarters",
        "employees": "employee_count",
        "pricing_model": "pricing_model",
    }
    for out_key, in_key in optional_mappings.items():
        val = brand.get(in_key)
        if val:
            result[out_key] = val

    # Description (concise)
    desc = brand.get("description", "")
    if desc:
        result["description"] = desc[:160]

    # Value props
    value_props = brand.get("value_props", brand.get("core_value_props", []))
    if value_props:
        result["core_value_props"] = value_props[:5]

    # Competitors
    competitors = brand.get("competitors", [])
    if competitors:
        result["competitors"] = competitors[:5]

    # Key differentiators
    differentiators = brand.get("differentiators", brand.get("key_differentiators", []))
    if differentiators:
        result["key_differentiators"] = differentiators[:5]

    # Social proof
    social_proof: Dict[str, Any] = {}
    customers = brand.get("key_customers", brand.get("customers", []))
    if customers:
        social_proof["customers"] = customers[:5]
    awards = brand.get("awards", [])
    if awards:
        social_proof["awards"] = awards[:3]
    metrics = brand.get("metrics", {})
    if metrics:
        social_proof["metrics"] = metrics
    if social_proof:
        result["social_proof"] = social_proof

    # Certifications
    certs = brand.get("certifications", [])
    if certs:
        result["certifications"] = certs

    return result


# ─── aeo.json generation ────────────────────────────────────────────────

def generate_aeo_json(brand: Dict[str, Any]) -> Dict[str, Any]:
    """Generate aeo.json — AI Engine Optimization config."""
    name = brand.get("brand_name", "")
    website = brand.get("website", "").rstrip("/")

    # Build key facts from known_facts
    known_facts: List[str] = []
    for fact in brand.get("known_facts", []):
        if isinstance(fact, dict):
            claim = fact.get("claim", "")
            if claim:
                known_facts.append(claim)
        elif isinstance(fact, str):
            known_facts.append(fact)

    # Auto-generate basic facts if empty
    if not known_facts:
        if brand.get("founding_year"):
            known_facts.append(f"Founded in {brand['founding_year']}")
        if brand.get("industry"):
            known_facts.append(f"Operating in the {brand['industry']} industry")
        if brand.get("target_customer"):
            known_facts.append(f"Serving {brand['target_customer']}")

    # Build FAQ from products
    faq_entries: List[Dict[str, str]] = []
    manual_faq = brand.get("faq", [])
    for item in manual_faq:
        if isinstance(item, dict) and item.get("question") and item.get("answer"):
            faq_entries.append({"q": item["question"], "a": item["answer"]})

    # Auto-generate basic FAQ
    if not faq_entries:
        faq_entries.append({"q": f"What is {name}?", "a": f"{name} is a {brand.get('industry', 'solution')} for {brand.get('target_customer', 'businesses')}."})
        if brand.get("pricing_model"):
            faq_entries.append({"q": f"How much does {name} cost?", "a": f"{name} uses a {brand['pricing_model']} pricing model."})

    # Content priorities
    content_priorities: List[Dict[str, str]] = []
    products = brand.get("products", [])
    for p in products[:5]:
        if isinstance(p, dict):
            pname = p.get("name", "")
            purl = p.get("url", f"{website}/products/{pname.lower().replace(' ', '-')}")
            content_priorities.append({"topic": pname, "url": purl})
    if not content_priorities:
        content_priorities.append({"topic": name, "url": website})

    return {
        "schema_version": "1.9.0",
        "brand": name,
        "preferred_citation_name": name,
        "preferred_citation_source": f"{website}/about",
        "faq_entries": faq_entries[:10],
        "key_facts": known_facts[:10],
        "content_priorities": content_priorities,
        "supported_languages": brand.get("supported_languages", ["en"]),
        "last_updated": utc_now_iso()[:10],
    }


# ─── Validation ─────────────────────────────────────────────────────────

def validate_generated_files(
    llms_txt: str,
    entity: Dict[str, Any],
    brand: Dict[str, Any],
    aeo: Dict[str, Any],
    brand_name: str,
) -> List[str]:
    """Validate generated files against quality constraints."""
    errors: List[str] = []

    # llms.txt
    if brand_name.lower() not in llms_txt.lower():
        errors.append("llms.txt: 缺少品牌名称")
    if llms_txt.count("http") < 3:
        errors.append("llms.txt: 关键 URL 不足 3 个")

    # entity.json
    if not entity.get("name"):
        errors.append("entity.json: 缺少 name 字段")
    if not entity.get("url"):
        errors.append("entity.json: 缺少 url 字段")
    if entity.get("@context") != "https://schema.org":
        errors.append("entity.json: @context 不正确")

    # brand.json
    if not brand.get("name"):
        errors.append("brand.json: 缺少 name 字段")
    if not brand.get("industry"):
        errors.append("brand.json: 缺少 industry 字段")

    # aeo.json
    if not aeo.get("preferred_citation_name"):
        errors.append("aeo.json: 缺少 preferred_citation_name")
    if len(aeo.get("key_facts", [])) < 2:
        errors.append("aeo.json: key_facts 不足 2 条")

    # Cross-file consistency
    entity_name = entity.get("name", "").lower()
    brand_json_name = brand.get("name", "").lower()
    if entity_name and brand_json_name and entity_name != brand_json_name:
        errors.append(f"品牌名不一致: entity.json='{entity.get('name')}' vs brand.json='{brand.get('name')}'")

    return errors


# ─── CLI ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Schema Automation — AI 可读文件生成")
    parser.add_argument("--input", required=True, help="品牌输入 JSON 文件路径")
    parser.add_argument("--output-dir", required=True, help="输出目录")
    parser.add_argument("--search-results", help="搜索结果 JSONL（可选，用于丰富内容）")
    args = parser.parse_args()

    brand_input = read_json(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate all files
    llms_txt = generate_llms_txt(brand_input)
    llms_full_txt = generate_llms_full_txt(brand_input)
    entity_json = generate_entity_json(brand_input)
    brand_json = generate_brand_json(brand_input)
    aeo_json = generate_aeo_json(brand_input)

    # Validate
    validation_errors = validate_generated_files(
        llms_txt, entity_json, brand_json, aeo_json,
        brand_input.get("brand_name", ""),
    )

    # Write files
    from geo_common import atomic_write_text

    atomic_write_text(output_dir / "llms.txt", llms_txt)
    atomic_write_text(output_dir / "llms-full.txt", llms_full_txt)
    write_json(output_dir / "entity.json", entity_json)
    write_json(output_dir / "brand.json", brand_json)
    write_json(output_dir / "aeo.json", aeo_json)

    # Summary
    summary = {
        "generated_at": utc_now_iso(),
        "files": ["llms.txt", "llms-full.txt", "entity.json", "brand.json", "aeo.json"],
        "output_dir": str(output_dir),
        "validation_errors": validation_errors,
        "validation_passed": len(validation_errors) == 0,
    }
    write_json(output_dir / "schema_files_manifest.json", summary)

    print(f"Generated 5 schema files in {output_dir}/")
    if validation_errors:
        print(f"Validation warnings ({len(validation_errors)}):")
        for err in validation_errors:
            print(f"  - {err}")
    else:
        print("All validation checks passed.")


if __name__ == "__main__":
    main()