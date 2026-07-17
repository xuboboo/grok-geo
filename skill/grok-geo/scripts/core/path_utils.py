"""Path, directory, and run-lifecycle utilities."""
from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .constants import (
    HOSTED_RUNS_DIR, LOCAL_RUNS_DIR_NAME, SCHEMA_VERSION,
    SKILL_NAME, SKILL_VERSION,
)
from .io_utils import read_json, write_json
from .time_utils import utc_now_iso, utc_stamp


def default_runs_base_dir() -> Path:
    env = os.environ.get("GEO_AUDIT_RUNS_DIR")
    if env:
        return Path(env).expanduser().resolve()
    if Path("/mnt/data").exists():
        return HOSTED_RUNS_DIR
    return (Path.cwd() / LOCAL_RUNS_DIR_NAME).resolve()


def ensure_run_dirs(run_dir: Path) -> Dict[str, Path]:
    run_dir = Path(run_dir)
    paths = {
        "run": run_dir,
        "input": run_dir / "input",
        "raw": run_dir / "raw",
        "intermediate": run_dir / "intermediate",
        "output": run_dir / "output",
        "logs": run_dir / "logs",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def resolve_under(base: Path, candidate: Union[str, Path], *, allow_absolute_within: bool = False) -> Path:
    """Resolve path and ensure it stays under base (no escape)."""
    base_resolved = Path(base).resolve()
    cand = Path(candidate)
    if cand.is_absolute():
        resolved = cand.resolve()
    else:
        resolved = (base_resolved / cand).resolve()
    try:
        resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise PermissionError(f"Path escapes base directory: {candidate}") from exc
    return resolved


def assert_path_in_run(run_dir: Path, path: Union[str, Path]) -> Path:
    return resolve_under(run_dir, path if Path(path).is_absolute() else Path(run_dir) / path)


def generate_run_id() -> str:
    return f"geo_{utc_stamp()}_{secrets.token_hex(4)}"


def load_manifest(run_dir: Path) -> Dict[str, Any]:
    path = Path(run_dir) / "output" / "manifest.json"
    if not path.exists():
        alt = Path(run_dir) / "manifest.json"
        if alt.exists():
            return read_json(alt)
        raise FileNotFoundError(f"manifest not found: {path}")
    return read_json(path)


def save_manifest(run_dir: Path, manifest: Dict[str, Any]) -> None:
    manifest["updated_at"] = utc_now_iso()
    write_json(Path(run_dir) / "output" / "manifest.json", manifest)


def append_event(run_dir: Path, event_type: str, detail: Optional[Dict[str, Any]] = None) -> None:
    from .io_utils import append_jsonl
    event = {"ts": utc_now_iso(), "event": event_type, "detail": detail or {}}
    append_jsonl(Path(run_dir) / "logs" / "events.jsonl", event)


def new_manifest(run_id: str, mode: str, input_sha256: str, question_count: int = 0) -> Dict[str, Any]:
    now = utc_now_iso()
    return {
        "schema_version": SCHEMA_VERSION,
        "skill_name": SKILL_NAME,
        "skill_version": SKILL_VERSION,
        "run_id": run_id,
        "mode": mode,
        "status": "INITIALIZED",
        "started_at": now,
        "updated_at": now,
        "completed_at": None,
        "input_sha256": input_sha256,
        "question_count": question_count,
        "search_result_count": 0,
        "successful_result_count": 0,
        "failed_result_count": 0,
        "current_batch": 0,
        "warnings": [],
        "errors": [],
        "outputs": {},
    }


def load_skill_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def schema_path(name: str) -> Path:
    return load_skill_root() / "schemas" / name