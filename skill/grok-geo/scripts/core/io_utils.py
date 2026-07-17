"""IO utilities — JSON, JSONL, CSV, atomic write."""
from __future__ import annotations

import csv
import json
import os
import tempfile
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Sequence, Union


def read_json(path: Union[str, Path]) -> Any:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Union[str, Path], data: Any, indent: int = 2) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=indent) + "\n"
    atomic_write_text(p, text)


def atomic_write_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass


def read_jsonl(path: Union[str, Path]) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {p}:{line_no}: {exc}") from exc
            if not isinstance(obj, dict):
                raise ValueError(f"JSONL row must be object at {p}:{line_no}")
            rows.append(obj)
    return rows


def append_jsonl(path: Union[str, Path], obj: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"
    with p.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


def write_csv(path: Union[str, Path], rows: Sequence[Dict[str, Any]], fieldnames: Sequence[str]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    sio = StringIO()
    writer = csv.DictWriter(sio, fieldnames=list(fieldnames), extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: _csv_cell(row.get(k)) for k in fieldnames})
    atomic_write_text(p, sio.getvalue())


def _csv_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)