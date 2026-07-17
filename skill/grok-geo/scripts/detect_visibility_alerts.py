#!/usr/bin/env python3
"""Detect visibility alerts by comparing current metrics with baseline.

v1.7 — Generates alerts for significant visibility drops with severity levels.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Allow import from scripts/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import ALERT_THRESHOLDS, read_json, write_json


def _get_nested(data: dict, *keys, default=None):
    """Get a nested value from a dict, e.g. _get_nested(d, 'a', 'b') → d['a']['b']."""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


def detect_alerts(current: dict, baseline: dict) -> List[Dict[str, Any]]:
    """Detect visibility alerts by comparing current metrics with baseline.

    Returns a list of alert dicts with type, severity, evidence, recommended_action.
    """
    alerts: List[Dict[str, Any]] = []

    # Rate-based metrics: mention_rate, recommendation_rate
    for metric_key in ("mention_rate", "recommendation_rate"):
        curr_rate = _get_nested(current, metric_key, "rate")
        base_rate = _get_nested(baseline, metric_key, "rate")

        if curr_rate is None or base_rate is None:
            continue

        drop = base_rate - curr_rate
        thresholds = ALERT_THRESHOLDS.get(metric_key, {})

        if drop >= thresholds.get("critical", 999):
            severity = "critical"
        elif drop >= thresholds.get("warning", 999):
            severity = "warning"
        else:
            continue

        alert_type = "mention_drop" if metric_key == "mention_rate" else "recommendation_drop"
        alerts.append({
            "alert_type": alert_type,
            "severity": severity,
            "metric": metric_key,
            "current_value": round(curr_rate, 4),
            "baseline_value": round(base_rate, 4),
            "delta": round(-drop, 4),
            "evidence": f"{metric_key} dropped from {base_rate:.2f} to {curr_rate:.2f} (Δ -{drop:.2f})",
            "recommended_action": _recommend_action(alert_type, severity),
        })

    # Score-based metrics: geo_score, visibility_score
    for metric_key in ("geo_score", "visibility_score"):
        curr_score = _get_nested(current, metric_key, "score")
        base_score = _get_nested(baseline, metric_key, "score")

        if curr_score is None or base_score is None:
            continue

        drop = base_score - curr_score
        thresholds = ALERT_THRESHOLDS.get(metric_key, {})

        if drop >= thresholds.get("critical", 999):
            severity = "critical"
        elif drop >= thresholds.get("warning", 999):
            severity = "warning"
        else:
            continue

        alert_type = f"{metric_key}_drop"
        alerts.append({
            "alert_type": alert_type,
            "severity": severity,
            "metric": metric_key,
            "current_value": round(curr_score, 1),
            "baseline_value": round(base_score, 1),
            "delta": round(-drop, 1),
            "evidence": f"{metric_key} dropped from {base_score:.1f} to {curr_score:.1f} (Δ -{drop:.1f})",
            "recommended_action": _recommend_action(alert_type, severity),
        })

    # Negative recommendation count increase
    curr_neg = _get_nested(current, "negative_recommendation_count", default=0)
    base_neg = _get_nested(baseline, "negative_recommendation_count", default=0)
    if curr_neg is not None and base_neg is not None and curr_neg > base_neg:
        alerts.append({
            "alert_type": "negative_recommendation_increase",
            "severity": "warning",
            "metric": "negative_recommendation_count",
            "current_value": curr_neg,
            "baseline_value": base_neg,
            "delta": curr_neg - base_neg,
            "evidence": f"Negative recommendation count increased from {base_neg} to {curr_neg}",
            "recommended_action": "Review negative recommendations for accuracy; address brand misperceptions",
        })

    return alerts


def _recommend_action(alert_type: str, severity: str) -> str:
    """Generate recommended action based on alert type and severity."""
    actions = {
        "mention_drop": "Investigate questions where brand mention was lost; check competitor content changes",
        "recommendation_drop": "Review top recommendation questions, update comparison content, verify brand claims accuracy",
        "geo_score_drop": "Comprehensive review needed: check visibility, mentions, recommendations, and citations",
        "visibility_score_drop": "Review brand presence across all platforms; check for new competitors or content gaps",
        "negative_recommendation_increase": "Review negative recommendations for accuracy; address brand misperceptions",
    }
    base = actions.get(alert_type, "Review recent changes and investigate root cause")
    if severity == "critical":
        return f"Priority: {base}"
    return base


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect visibility alerts from metric comparison (v1.7)"
    )
    parser.add_argument(
        "--current", required=True, help="Path to current metrics.json"
    )
    parser.add_argument(
        "--baseline", required=True, help="Path to baseline metrics.json"
    )
    parser.add_argument(
        "--output", required=True, help="Output path for alerts JSON"
    )
    args = parser.parse_args()

    current = read_json(args.current)
    baseline = read_json(args.baseline)

    alerts = detect_alerts(current, baseline)

    critical_count = sum(1 for a in alerts if a["severity"] == "critical")
    warning_count = sum(1 for a in alerts if a["severity"] == "warning")
    info_count = sum(1 for a in alerts if a["severity"] == "info")

    output = {
        "visibility_alerts": alerts,
        "alert_summary": {
            "total_alerts": len(alerts),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "info_count": info_count,
        },
    }

    write_json(args.output, output)
    print(json.dumps(output["alert_summary"], indent=2))


if __name__ == "__main__":
    main()