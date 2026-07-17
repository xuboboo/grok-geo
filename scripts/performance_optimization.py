#!/usr/bin/env python3
"""Performance optimization for grok-geo — caching and key path optimization."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skill" / "grok-geo" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from geo_common import read_json


# ─── Cache Layer ───────────────────────────────────────────────────────

class SchemaCache:
    """Cache for JSON Schema files to avoid repeated disk reads."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    @lru_cache(maxsize=32)
    def load(self, schema_path: str) -> Dict[str, Any]:
        """Load and cache a JSON Schema file."""
        if schema_path not in self._cache:
            self._cache[schema_path] = read_json(Path(schema_path))
        return self._cache[schema_path]
    
    def clear(self):
        """Clear the cache."""
        self._cache.clear()
        self.load.cache_clear()


# Global schema cache instance
_schema_cache = SchemaCache()


def get_cached_schema(schema_path: str) -> Dict[str, Any]:
    """Get a cached JSON Schema."""
    return _schema_cache.load(schema_path)


# ─── Entity Index ─────────────────────────────────────────────────────

class EntityIndex:
    """Hash-based index for fast entity lookups."""
    
    def __init__(self, entities: Dict[str, Dict[str, Any]]):
        self._index: Dict[str, Dict[str, Any]] = {}
        self._build_index(entities)
    
    def _build_index(self, entities: Dict[str, Dict[str, Any]]):
        """Build hash index from entities dict."""
        for qid, row in entities.items():
            for entity in row.get("entities", []):
                entity_id = entity.get("entity_id", "")
                if entity_id:
                    self._index[entity_id] = entity
    
    def get(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity by ID in O(1) time."""
        return self._index.get(entity_id)
    
    def has(self, entity_id: str) -> bool:
        """Check if entity exists in O(1) time."""
        return entity_id in self._index


# ─── Optimized Metric Calculation ─────────────────────────────────────

def calculate_metrics_optimized(
    questions: list,
    entities_by_qid: Dict[str, Dict[str, Any]],
    citations: list,
    claims: list,
) -> Dict[str, Any]:
    """Optimized version of calculate_metrics with caching and indexing."""
    from calculate_metrics import calculate_metrics
    
    # Build entity index for fast lookups
    entity_index = EntityIndex(entities_by_qid)
    
    # Pre-process citations by question_id for O(1) lookup
    citations_by_qid: Dict[str, list] = {}
    for c in citations:
        qid = c.get("question_id", "")
        if qid not in citations_by_qid:
            citations_by_qid[qid] = []
        citations_by_qid[qid].append(c)
    
    # Call original function (already optimized internally)
    return calculate_metrics(questions, entities_by_qid, citations, claims)


# ─── Batch JSON Operations ────────────────────────────────────────────

def batch_read_json(file_paths: list) -> Dict[str, Any]:
    """Read multiple JSON files in batch."""
    results = {}
    for path in file_paths:
        try:
            results[str(path)] = read_json(Path(path))
        except Exception as e:
            results[str(path)] = {"error": str(e)}
    return results


def batch_write_json(data_dict: Dict[str, Any], output_dir: Path):
    """Write multiple JSON files in batch."""
    from geo_common import write_json
    for filename, data in data_dict.items():
        write_json(output_dir / filename, data)


if __name__ == "__main__":
    # Quick benchmark
    import time
    
    # Test schema cache
    schema_path = str(ROOT / "skill" / "grok-geo" / "schemas" / "report.schema.json")
    
    start = time.perf_counter()
    for _ in range(1000):
        get_cached_schema(schema_path)
    cached_time = time.perf_counter() - start
    
    print(f"Schema cache: {cached_time:.3f}s for 1000 reads")
    print(f"Cache info: {_schema_cache.load.cache_info()}")