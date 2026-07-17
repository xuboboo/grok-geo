#!/usr/bin/env python3
"""Link a current audit run to a baseline run and compute run-level metric deltas.

Usage:
    python chain_runs.py --current-run-dir <dir> --baseline-run-dir <dir> --output <path>

Outputs run_chain.json with baseline_id, current_id, deltas, improvement_direction.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from geo_common import SKILL_NAME, SKILL_VERSION, load_manifest, read_json, utc_now_iso, write_json  # noqa: E402

# ─── Metric extraction helpers ─────────────────────────────────────────────

# Keys in metrics.json to track.  Each tuple is (top_key, sub_key, label).
_METRIC_KEYS = [
    ("mention_rate", "rate", "mention_rate"),
    ("recommendation_rate", "rate", "recommendation_rate"),
    ("geo_score", "score", "geo_score"),
    ("visibility_score", "score", "visibility_score"),
]


def _extract_metric_value(metrics: dict, top_key: str, sub_key: str) -> float | None:
    """Pull a numeric value from a metrics dict.  Returns None if absent."""
    top = metrics.get(top_key)
    if top is None:
        return None
    if isinstance(top, (int, float)):
        return float(top)
    if isinstance(top, dict):
        val = top.get(sub_key)
        if val is not None:
            return float(val)
    return None


# ─── Public API (imported by tests) ────────────────────────────────────────


def compute_run_deltas(baseline_metrics: dict, current_metrics: dict) -> dict:
    """Compute per-metric deltas and overall improvement direction.

    Parameters
    ----------
    baseline_metrics : dict
        Metrics dict from the baseline run (metrics.json content).
    current_metrics : dict
        Metrics dict from the current run.

    Returns
    -------
    dict
        For each tracked metric: ``{"baseline": float|None, "current": float|None, "delta": float|None}``.
        Plus ``"improvement_direction"``: ``"improving"`` | ``"maintaining"`` | ``"regressing"``.
    """
    deltas: dict = {}
    positive = 0
    negative = 0
    total_compared = 0

    for top_key, sub_key, label in _METRIC_KEYS:
        base_val = _extract_metric_value(baseline_metrics, top_key, sub_key)
        curr_val = _extract_metric_value(current_metrics, top_key, sub_key)

        if base_val is not None and curr_val is not None:
            delta = round(curr_val - base_val, 6)
            total_compared += 1
            # Treat changes within 1% of baseline as neutral
            threshold = max(abs(base_val) * 0.01, 0.001)
            if delta > threshold:
                positive += 1
            elif delta < -threshold:
                negative += 1
        else:
            delta = None

        deltas[label] = {
            "baseline": base_val,
            "current": curr_val,
            "delta": delta,
        }

    # Determine improvement direction
    if total_compared == 0:
        direction = "maintaining"
    elif positive > negative:
        direction = "improving"
    elif negative > positive:
        direction = "regressing"
    else:
        direction = "maintaining"

    deltas["improvement_direction"] = direction
    return deltas


# ─── CLI ────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Chain current run to baseline and compute metric deltas."
    )
    parser.add_argument("--current-run-dir", required=True, help="Path to current run directory")
    parser.add_argument("--baseline-run-dir", required=True, help="Path to baseline run directory")
    parser.add_argument("--output", required=True, help="Output path for run_chain.json")
    args = parser.parse_args()

    current_dir = Path(args.current_run_dir)
    baseline_dir = Path(args.baseline_run_dir)
    output_path = Path(args.output)

    # Load manifests
    current_manifest = load_manifest(current_dir)
    baseline_manifest = load_manifest(baseline_dir)

    # Load metrics from intermediate/
    current_metrics_path = current_dir / "intermediate" / "metrics.json"
    baseline_metrics_path = baseline_dir / "intermediate" / "metrics.json"

    current_metrics: dict = {}
    baseline_metrics: dict = {}

    if current_metrics_path.exists():
        current_metrics = read_json(current_metrics_path)
    if baseline_metrics_path.exists():
        baseline_metrics = read_json(baseline_metrics_path)

    # Compute deltas
    deltas = compute_run_deltas(baseline_metrics, current_metrics)

    # Build chain record
    chain = {
        "schema_version": "1.0",
        "skill_name": SKILL_NAME,
        "skill_version": SKILL_VERSION,
        "baseline_id": baseline_manifest.get("run_id", ""),
        "current_id": current_manifest.get("run_id", ""),
        "chained_at": utc_now_iso(),
        "deltas": deltas,
        "improvement_direction": deltas.get("improvement_direction", "maintaining"),
    }

    write_json(output_path, chain)
    print(f"Run chain written to {output_path}")


if __name__ == "__main__":
    main()