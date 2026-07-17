#!/usr/bin/env python3
"""URL normalization for citation processing (§11)."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import TRACKING_PARAMS, print_json, read_json, write_json  # noqa: E402


def normalize_url(url: str) -> Dict[str, Any]:
    original = url or ""
    if not original.strip():
        return {
            "original_url": original,
            "canonical_url": "",
            "domain": "",
            "url_sha256": hashlib.sha256(b"").hexdigest(),
            "error": "empty_url",
        }

    raw = original.strip()
    # ensure scheme for parse
    if "://" not in raw:
        raw = "https://" + raw

    try:
        parsed = urlparse(raw)
        scheme = (parsed.scheme or "https").lower()
        if scheme not in ("http", "https"):
            raise ValueError(f"unsupported scheme {scheme}")

        host = parsed.hostname or ""
        # IDNA
        try:
            host_idna = host.encode("idna").decode("ascii")
        except Exception:
            host_idna = host.lower()
        host_idna = host_idna.lower()
        if host_idna.startswith("www."):
            # keep www as-is for identity? doc says host lower; www often stripped for domain field
            pass

        port = parsed.port
        if port and (
            (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
        ):
            port = None

        netloc = host_idna
        if port:
            netloc = f"{host_idna}:{port}"
        if parsed.username:
            auth = parsed.username
            if parsed.password:
                auth = f"{auth}:{parsed.password}"
            netloc = f"{auth}@{netloc}"

        path = parsed.path or ""
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")

        # filter tracking query params; preserve order of remaining
        pairs = parse_qsl(parsed.query, keep_blank_values=True)
        filtered = [(k, v) for k, v in pairs if k.lower() not in TRACKING_PARAMS]
        query = urlencode(filtered, doseq=True)

        canonical = urlunparse((scheme, netloc, path, "", query, ""))  # no fragment
        domain = host_idna[4:] if host_idna.startswith("www.") else host_idna

        return {
            "original_url": original,
            "canonical_url": canonical,
            "domain": domain,
            "url_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "error": None,
        }
    except Exception as exc:
        return {
            "original_url": original,
            "canonical_url": "",
            "domain": "",
            "url_sha256": hashlib.sha256(original.encode("utf-8")).hexdigest(),
            "error": str(exc),
        }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize URLs for GEO citations")
    parser.add_argument("--url", default=None, help="Single URL")
    parser.add_argument("--input", default=None, help="JSON file: string, list, or {urls:[]}")
    parser.add_argument("--output", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    results: List[Dict[str, Any]] = []
    if args.url:
        results.append(normalize_url(args.url))
    elif args.input:
        data = read_json(args.input)
        if isinstance(data, str):
            results.append(normalize_url(data))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    results.append(normalize_url(item))
                elif isinstance(item, dict) and "url" in item:
                    results.append(normalize_url(item["url"]))
        elif isinstance(data, dict) and "urls" in data:
            for u in data["urls"]:
                results.append(normalize_url(u))
        else:
            print("unsupported input format", file=sys.stderr)
            return 2
    else:
        parser.error("provide --url or --input")

    out: Any = results[0] if len(results) == 1 else results
    if args.output:
        write_json(args.output, out)
    if args.json or not args.output:
        print_json(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())