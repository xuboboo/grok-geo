#!/usr/bin/env python3
"""Real-time monitoring and alerting for GEO brand visibility."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AlertRule:
    """Alert rule definition."""
    metric: str          # e.g., "geo_score", "mention_rate"
    condition: str       # "below", "above", "change"
    threshold: float     # Threshold value
    severity: str        # "critical", "warning", "info"
    message: str         # Alert message template


@dataclass
class Alert:
    """Triggered alert."""
    rule: AlertRule
    current_value: float
    previous_value: Optional[float]
    triggered_at: str
    brand_name: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metric": self.rule.metric,
            "condition": self.rule.condition,
            "threshold": self.rule.threshold,
            "severity": self.rule.severity,
            "message": self.rule.message.format(threshold=self.rule.threshold),
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "triggered_at": self.triggered_at,
            "brand_name": self.brand_name
        }


class Monitor:
    """Real-time monitoring engine."""
    
    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self.alerts_file = self.run_dir / "alerts.json"
        self.metrics_history_file = self.run_dir / "metrics_history.jsonl"
        self.rules: List[AlertRule] = self._load_default_rules()
        
        # Ensure directory exists
        self.run_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_default_rules(self) -> List[AlertRule]:
        """Load default alert rules."""
        return [
            AlertRule("geo_score", "below", 40, "critical", "GEO Score dropped below {threshold}"),
            AlertRule("geo_score", "below", 60, "warning", "GEO Score is below {threshold}"),
            AlertRule("mention_rate", "below", 0.3, "critical", "Mention rate dropped below {threshold:.0%}"),
            AlertRule("mention_rate", "below", 0.5, "warning", "Mention rate is below {threshold:.0%}"),
            AlertRule("recommendation_rate", "below", 0.2, "warning", "Recommendation rate is low"),
            AlertRule("sentiment_index", "below", 40, "warning", "Sentiment index is negative"),
            AlertRule("sentiment_index", "below", 20, "critical", "Sentiment index is critically low"),
        ]
    
    def _extract_metric(self, metrics: Dict[str, Any], metric_name: str) -> Optional[float]:
        """Extract metric value from metrics dict."""
        if metric_name == "geo_score":
            return metrics.get("geo_score", {}).get("score")
        elif metric_name == "mention_rate":
            return metrics.get("mention_rate", {}).get("rate")
        elif metric_name == "recommendation_rate":
            return metrics.get("recommendation_rate", {}).get("rate")
        elif metric_name == "sentiment_index":
            return metrics.get("sentiment_index", {}).get("score")
        return None
    
    def _get_previous_value(self, metric_name: str) -> Optional[float]:
        """Get previous metric value from history."""
        history = self.get_history(days=7)
        if not history:
            return None
        
        # Get the most recent entry before current
        for entry in reversed(history[:-1] if len(history) > 1 else []):
            value = self._extract_metric(entry.get("metrics", {}), metric_name)
            if value is not None:
                return value
        return None
    
    def check_alerts(self, current_metrics: Dict[str, Any]) -> List[Alert]:
        """Check current metrics against alert rules."""
        alerts = []
        
        for rule in self.rules:
            value = self._extract_metric(current_metrics, rule.metric)
            if value is None:
                continue
            
            triggered = False
            if rule.condition == "below" and value < rule.threshold:
                triggered = True
            elif rule.condition == "above" and value > rule.threshold:
                triggered = True
            elif rule.condition == "change":
                prev_value = self._get_previous_value(rule.metric)
                if prev_value is not None:
                    change = abs(value - prev_value) / prev_value if prev_value != 0 else 0
                    if change > rule.threshold:
                        triggered = True
            
            if triggered:
                alert = Alert(
                    rule=rule,
                    current_value=value,
                    previous_value=self._get_previous_value(rule.metric),
                    triggered_at=datetime.now().isoformat(),
                    brand_name=current_metrics.get("brand_name", "Unknown")
                )
                alerts.append(alert)
        
        # Save alerts
        if alerts:
            self._save_alerts(alerts)
        
        return alerts
    
    def _save_alerts(self, alerts: List[Alert]):
        """Save alerts to file."""
        existing = []
        if self.alerts_file.exists():
            with open(self.alerts_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
        
        existing.extend([alert.to_dict() for alert in alerts])
        
        with open(self.alerts_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
    
    def get_alerts(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        if not self.alerts_file.exists():
            return []
        
        with open(self.alerts_file, "r", encoding="utf-8") as f:
            alerts = json.load(f)
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        return [a for a in alerts if a.get("triggered_at", "") >= cutoff]
    
    def save_metrics(self, metrics: Dict[str, Any]):
        """Save metrics to history file."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }
        
        with open(self.metrics_history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get metrics history for specified days."""
        if not self.metrics_history_file.exists():
            return []
        
        cutoff = datetime.now() - timedelta(days=days)
        history = []
        
        with open(self.metrics_history_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    timestamp = datetime.fromisoformat(entry["timestamp"])
                    if timestamp >= cutoff:
                        history.append(entry)
                except (json.JSONDecodeError, KeyError):
                    continue
        
        return history
    
    def add_rule(self, rule: AlertRule):
        """Add a custom alert rule."""
        self.rules.append(rule)
    
    def remove_rule(self, metric: str, condition: str, threshold: float):
        """Remove an alert rule."""
        self.rules = [
            r for r in self.rules
            if not (r.metric == metric and r.condition == condition and r.threshold == threshold)
        ]


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        run_dir = Path(sys.argv[1])
    else:
        run_dir = Path("./geo-audit-runs/test")
    
    monitor = Monitor(run_dir)
    
    # Test metrics
    test_metrics = {
        "brand_name": "TestBrand",
        "geo_score": {"score": 35},
        "mention_rate": {"rate": 0.25},
        "recommendation_rate": {"rate": 0.15},
        "sentiment_index": {"score": 30}
    }
    
    # Check alerts
    alerts = monitor.check_alerts(test_metrics)
    print(f"Triggered {len(alerts)} alerts:")
    for alert in alerts:
        print(f"  [{alert.rule.severity}] {alert.rule.message.format(threshold=alert.rule.threshold)}")
    
    # Save metrics
    monitor.save_metrics(test_metrics)
    print(f"Saved metrics to {monitor.metrics_history_file}")