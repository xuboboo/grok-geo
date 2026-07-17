"""URL and domain utilities."""
from __future__ import annotations


def domain_from_url(url: str) -> str:
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def is_same_or_subdomain(domain: str, root: str) -> bool:
    domain = (domain or "").lower().lstrip(".")
    root = (root or "").lower().lstrip(".")
    if not domain or not root:
        return False
    return domain == root or domain.endswith("." + root)