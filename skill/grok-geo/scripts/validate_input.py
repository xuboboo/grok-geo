#!/usr/bin/env python3
"""Validate and normalize GEO brand audit input."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse

# Allow running as script from scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (  # noqa: E402
    domain_from_url,
    load_schema,
    names_conflict,
    normalize_entity_name,
    print_json,
    sha256_json,
    validate_against_schema,
    write_json,
)

EXIT_OK = 0
EXIT_NOT_FOUND = 10
EXIT_JSON = 11
EXIT_SCHEMA = 12
EXIT_URL = 13
EXIT_CONFLICT = 14
EXIT_SENSITIVE = 15
EXIT_UNKNOWN = 19

SENSITIVE_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "api_key_like"),
    (re.compile(r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*\S+"), "credential_assignment"),
    (re.compile(r"(?i)password\s*[:=]\s*\S+"), "password"),
    (re.compile(r"\b\d{17}[\dXx]\b"), "id_card_like"),
]


def strip_fragment_and_lower_host(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Only http/https allowed: {url}")
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError(f"Invalid host: {url}")
    # rebuild without fragment; keep path/query/userinfo carefully
    netloc = host
    if parsed.port and not (
        (parsed.scheme == "http" and parsed.port == 80)
        or (parsed.scheme == "https" and parsed.port == 443)
    ):
        netloc = f"{host}:{parsed.port}"
    if parsed.username:
        user = parsed.username
        if parsed.password:
            user = f"{user}:{parsed.password}"
        netloc = f"{user}@{netloc}"
    return urlunparse((parsed.scheme.lower(), netloc, parsed.path or "", "", parsed.query, ""))


def scan_sensitive(obj: Any, path: str = "$") -> List[str]:
    hits: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            hits.extend(scan_sensitive(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(scan_sensitive(v, f"{path}[{i}]"))
    elif isinstance(obj, str):
        for pat, label in SENSITIVE_PATTERNS:
            if pat.search(obj):
                hits.append(f"{path}: {label}")
    return hits


def normalize_input(data: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(data)
    out.setdefault("schema_version", "1.0")
    mode = out.get("mode") or "standard"
    out["mode"] = mode
    out.setdefault("language", "zh-CN")
    out.setdefault("brand_aliases", [])
    out.setdefault("target_region", [])
    out.setdefault("competitors", [])
    out.setdefault("products", [])
    out.setdefault("business_goals", [])
    out.setdefault("known_facts", [])
    out.setdefault("forbidden_claims", [])
    options = dict(out.get("options") or {})

    try:
        out["website"] = strip_fragment_and_lower_host(out["website"])
    except ValueError as exc:
        raise ValueError(f"INVALID_URL:{exc}") from exc

    brand_norm = normalize_entity_name(out["brand_name"])
    brand_domain = domain_from_url(out["website"])

    # competitors: dedupe by normalized name, normalize websites
    seen_names = set()
    cleaned_comps = []
    for comp in out.get("competitors") or []:
        name = (comp.get("name") or "").strip()
        if not name:
            continue
        nn = normalize_entity_name(name)
        if nn in seen_names:
            continue
        seen_names.add(nn)
        if names_conflict(name, out["brand_name"]):
            raise ValueError("BRAND_COMPETITOR_CONFLICT: competitor name equals brand")
        website = comp.get("website")
        if website:
            try:
                website = strip_fragment_and_lower_host(website)
            except ValueError as exc:
                raise ValueError(f"INVALID_URL:{exc}") from exc
            if domain_from_url(website) == brand_domain and brand_domain:
                raise ValueError("BRAND_COMPETITOR_CONFLICT: competitor website equals brand")
        cleaned_comps.append({"name": name, "website": website})
    out["competitors"] = cleaned_comps

    # known_facts urls
    facts = []
    for fact in out.get("known_facts") or []:
        f = dict(fact)
        if f.get("source_url"):
            try:
                f["source_url"] = strip_fragment_and_lower_host(f["source_url"])
            except ValueError as exc:
                raise ValueError(f"INVALID_URL:{exc}") from exc
        facts.append(f)
    out["known_facts"] = facts

    # question_count rules
    if mode == "quick":
        options["question_count"] = 10
    elif mode == "standard":
        qc = int(options.get("question_count") or 30)
        if qc > 40:
            raise ValueError("INPUT_SCHEMA_INVALID: question_count max 40 for standard")
        options["question_count"] = qc
    elif mode == "offline_import":
        options.setdefault("question_count", 10)
    else:
        raise ValueError(f"INPUT_SCHEMA_INVALID: unknown mode {mode}")

    qv = int(options.get("query_variants") or 1)
    if qv > 2:
        raise ValueError("INPUT_SCHEMA_INVALID: query_variants max 2")
    options["query_variants"] = qv
    options.setdefault("max_opportunities", 10)
    options.setdefault("max_content_briefs", 5)
    out["options"] = options

    # no file paths from user
    for key in ("path", "file", "file_path", "run_dir", "script"):
        if key in data:
            raise ValueError("INPUT_SCHEMA_INVALID: file paths not allowed in input")

    out["_meta"] = {
        "brand_normalized": brand_norm,
        "brand_domain": brand_domain,
        "input_sha256": sha256_json({k: v for k, v in out.items() if k != "_meta"}),
    }
    return out


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate GEO brand audit input")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", required=True, help="Normalized output JSON path")
    parser.add_argument("--json", action="store_true", help="Print result JSON to stdout")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        print("INPUT_FILE_NOT_FOUND", file=sys.stderr)
        return EXIT_NOT_FOUND

    try:
        with input_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        print(f"INVALID_JSON: {exc}", file=sys.stderr)
        return EXIT_JSON
    except OSError as exc:
        print(f"INPUT_FILE_NOT_FOUND: {exc}", file=sys.stderr)
        return EXIT_NOT_FOUND

    if not isinstance(data, dict):
        print("INPUT_SCHEMA_INVALID: root must be object", file=sys.stderr)
        return EXIT_SCHEMA

    sensitive = scan_sensitive(data)
    if sensitive:
        print("SENSITIVE_INPUT_DETECTED: " + "; ".join(sensitive), file=sys.stderr)
        return EXIT_SENSITIVE

    schema = load_schema("input.schema.json")
    schema_errors = validate_against_schema(data, schema)
    if schema_errors:
        print("INPUT_SCHEMA_INVALID:\n" + "\n".join(schema_errors), file=sys.stderr)
        return EXIT_SCHEMA

    try:
        normalized = normalize_input(data)
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("INVALID_URL"):
            print(msg, file=sys.stderr)
            return EXIT_URL
        if msg.startswith("BRAND_COMPETITOR_CONFLICT") or "DUPLICATE" in msg:
            print(msg, file=sys.stderr)
            return EXIT_CONFLICT
        print(msg, file=sys.stderr)
        return EXIT_SCHEMA
    except Exception as exc:  # pragma: no cover
        print(f"UNKNOWN: {exc}", file=sys.stderr)
        return EXIT_UNKNOWN

    write_json(args.output, normalized)
    if args.json:
        print_json({"ok": True, "output": str(args.output), "mode": normalized["mode"]})
    else:
        print(str(Path(args.output).resolve()))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())