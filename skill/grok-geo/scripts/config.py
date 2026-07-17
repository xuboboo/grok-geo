#!/usr/bin/env python3
"""Configuration management for grok-geo API integrations."""

from __future__ import annotations

import json
import logging
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("grok-geo.config")


@dataclass
class APIConfig:
    """API configuration for AI engines."""
    
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    perplexity_api_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "APIConfig":
        """Load configuration from environment variables."""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            perplexity_api_key=os.getenv("PERPLEXITY_API_KEY"),
        )
    
    @classmethod
    def from_file(cls, config_path: Path) -> "APIConfig":
        """Load configuration from JSON file.
        
        Warns if the config file has overly permissive permissions (world-readable).
        """
        if not config_path.exists():
            return cls()
        
        # Check file permissions (Unix-like systems)
        try:
            mode = config_path.stat().st_mode
            if mode & stat.S_IROTH:
                logger.warning(
                    "Config file %s is world-readable. Consider: chmod 600 %s",
                    config_path, config_path
                )
        except (OSError, AttributeError):
            pass  # Windows or permission check not supported
        
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Warn if API keys are found in file
        key_fields = ["openai_api_key", "anthropic_api_key", "google_api_key", "perplexity_api_key"]
        found_keys = [k for k in key_fields if data.get(k)]
        if found_keys:
            logger.warning(
                "API keys found in config file (%s). Prefer environment variables for production use.",
                ", ".join(found_keys)
            )
        
        return cls(
            openai_api_key=data.get("openai_api_key"),
            anthropic_api_key=data.get("anthropic_api_key"),
            google_api_key=data.get("google_api_key"),
            perplexity_api_key=data.get("perplexity_api_key"),
        )
    
    def available_engines(self) -> List[str]:
        """Get list of engines with valid API keys."""
        engines = []
        if self.openai_api_key:
            engines.append("openai")
        if self.anthropic_api_key:
            engines.append("anthropic")
        if self.google_api_key:
            engines.append("google")
        if self.perplexity_api_key:
            engines.append("perplexity")
        return engines
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (masking API keys)."""
        return {
            "openai_configured": bool(self.openai_api_key),
            "anthropic_configured": bool(self.anthropic_api_key),
            "google_configured": bool(self.google_api_key),
            "perplexity_configured": bool(self.perplexity_api_key),
            "available_engines": self.available_engines(),
        }


@dataclass
class RunConfig:
    """Run configuration for audit execution."""
    
    base_dir: Path = field(default_factory=lambda: Path("./geo-audit-runs"))
    mode: str = "standard"  # quick, standard, offline_import
    engines: List[str] = field(default_factory=list)
    max_questions: int = 30
    timeout: int = 60
    
    @classmethod
    def from_env(cls) -> "RunConfig":
        """Load run configuration from environment variables."""
        base_dir = os.getenv("GEO_AUDIT_RUNS_DIR", "./geo-audit-runs")
        mode = os.getenv("GEO_AUDIT_MODE", "standard")
        engines_str = os.getenv("GEO_AUDIT_ENGINES", "")
        engines = [e.strip() for e in engines_str.split(",") if e.strip()]
        
        return cls(
            base_dir=Path(base_dir),
            mode=mode,
            engines=engines,
            max_questions=int(os.getenv("GEO_AUDIT_MAX_QUESTIONS", "30")),
            timeout=int(os.getenv("GEO_AUDIT_TIMEOUT", "60")),
        )


# Global configuration instances
_api_config: Optional[APIConfig] = None
_run_config: Optional[RunConfig] = None


def get_api_config() -> APIConfig:
    """Get global API configuration."""
    global _api_config
    if _api_config is None:
        _api_config = APIConfig.from_env()
    return _api_config


def get_run_config() -> RunConfig:
    """Get global run configuration."""
    global _run_config
    if _run_config is None:
        _run_config = RunConfig.from_env()
    return _run_config


def set_api_config(config: APIConfig):
    """Set global API configuration."""
    global _api_config
    _api_config = config


def set_run_config(config: RunConfig):
    """Set global run configuration."""
    global _run_config
    _run_config = config


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Quick test
    api_config = get_api_config()
    run_config = get_run_config()
    
    logger.info("API Config: %s", api_config.to_dict())
    logger.info("Run Config: %s", {
        "base_dir": str(run_config.base_dir),
        "mode": run_config.mode,
        "engines": run_config.engines,
    })