#!/usr/bin/env python3
"""Entity name normalization and matching helpers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (  # noqa: E402
    domain_from_url,
    normalize_entity_name,
    print_json,
    read_json,
    write_json,
)


def build_alias_map(brand: Dict[str, Any]) -> Dict[str, str]:
    """Map normalized alias/product -> canonical entity id."""
    mapping: Dict[str, str] = {}
    brand_name = brand.get("brand_name") or ""
    mapping[normalize_entity_name(brand_name)] = "target-brand"
    for a in brand.get("brand_aliases") or []:
        mapping[normalize_entity_name(a)] = "target-brand"
    for p in brand.get("products") or []:
        mapping[normalize_entity_name(p.get("name") or "")] = "target-brand"
        for a in p.get("aliases") or []:
            mapping[normalize_entity_name(a)] = "target-brand"
    for i, c in enumerate(brand.get("competitors") or []):
        cid = f"competitor-{i+1}"
        mapping[normalize_entity_name(c.get("name") or "")] = cid
    return {k: v for k, v in mapping.items() if k}


def match_entity(text: str, brand: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return best matching entity descriptor if text matches known names."""
    norm = normalize_entity_name(text)
    if not norm:
        return None
    amap = build_alias_map(brand)
    if norm in amap:
        eid = amap[norm]
        if eid == "target-brand":
            return {
                "entity_id": "target-brand",
                "canonical_name": brand.get("brand_name"),
                "entity_type": "target_brand",
            }
        # competitor
        idx = int(eid.split("-")[1]) - 1
        comps = brand.get("competitors") or []
        name = comps[idx]["name"] if idx < len(comps) else text
        return {
            "entity_id": eid,
            "canonical_name": name,
            "entity_type": "competitor",
        }
    # fuzzy: containment for longer names
    for alias, eid in sorted(amap.items(), key=lambda x: -len(x[0])):
        if len(alias) >= 2 and (alias in norm or norm in alias):
            if eid == "target-brand":
                return {
                    "entity_id": "target-brand",
                    "canonical_name": brand.get("brand_name"),
                    "entity_type": "target_brand",
                }
            idx = int(eid.split("-")[1]) - 1
            comps = brand.get("competitors") or []
            name = comps[idx]["name"] if idx < len(comps) else text
            return {
                "entity_id": eid,
                "canonical_name": name,
                "entity_type": "competitor",
            }
    return None


def scan_text_for_entities(text: str, brand: Dict[str, Any]) -> List[Dict[str, Any]]:
    found: List[Dict[str, Any]] = []
    seen = set()
    amap = build_alias_map(brand)
    hay = normalize_entity_name(text, strip_company_suffix=False)
    for alias, eid in sorted(amap.items(), key=lambda x: -len(x[0])):
        if not alias or alias not in hay:
            continue
        if eid in seen:
            continue
        seen.add(eid)
        if eid == "target-brand":
            found.append(
                {
                    "entity_id": "target-brand",
                    "canonical_name": brand.get("brand_name"),
                    "entity_type": "target_brand",
                    "matched_alias": alias,
                }
            )
        else:
            idx = int(eid.split("-")[1]) - 1
            comps = brand.get("competitors") or []
            name = comps[idx]["name"] if idx < len(comps) else alias
            found.append(
                {
                    "entity_id": eid,
                    "canonical_name": name,
                    "entity_type": "competitor",
                    "matched_alias": alias,
                }
            )
    return found


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize entity names / match helpers")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_norm = sub.add_parser("normalize", help="Normalize a name")
    p_norm.add_argument("--name", required=True)
    p_norm.add_argument("--keep-suffix", action="store_true")

    p_map = sub.add_parser("alias-map", help="Build alias map from brand input")
    p_map.add_argument("--input", required=True)
    p_map.add_argument("--output", default=None)

    p_match = sub.add_parser("match", help="Match text against brand entities")
    p_match.add_argument("--input", required=True, help="brand.json")
    p_match.add_argument("--text", required=True)
    p_match.add_argument("--scan", action="store_true", help="scan full text for all entities")

    args = parser.parse_args(argv)

    if args.cmd == "normalize":
        print(
            normalize_entity_name(
                args.name, strip_company_suffix=not args.keep_suffix
            )
        )
        return 0

    brand = read_json(args.input)
    if args.cmd == "alias-map":
        amap = build_alias_map(brand)
        if args.output:
            write_json(args.output, amap)
        print_json(amap)
        return 0

    if args.cmd == "match":
        if args.scan:
            print_json(scan_text_for_entities(args.text, brand))
        else:
            print_json(match_entity(args.text, brand))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())