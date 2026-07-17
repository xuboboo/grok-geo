#!/usr/bin/env python3
"""Package skill/grok-geo into dist/grok-geo-v1.0.0.zip with single top-level dir."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill" / "grok-geo"
DIST = ROOT / "dist"
VERSION = (SKILL / "VERSION").read_text(encoding="utf-8").strip()
ZIP_NAME = f"grok-geo-v{VERSION}.zip"


def main() -> int:
    DIST.mkdir(parents=True, exist_ok=True)
    zip_path = DIST / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(SKILL.rglob("*")):
            if path.is_dir():
                continue
            if path.name == ".DS_Store" or "__pycache__" in path.parts:
                continue
            if path.suffix == ".pyc":
                continue
            rel = path.relative_to(SKILL)
            arc = Path("grok-geo") / rel
            zf.write(path, arcname=str(arc).replace("\\", "/"))

    h = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    sha_path = DIST / f"{ZIP_NAME}.sha256"
    sha_path.write_text(f"{h}  {ZIP_NAME}\n", encoding="utf-8")

    # verify single top-level
    with zipfile.ZipFile(zip_path, "r") as zf:
        tops = {name.split("/")[0] for name in zf.namelist() if name}
    assert tops == {"grok-geo"}, tops
    print(f"Wrote {zip_path}")
    print(f"SHA256 {h}")
    print(f"Top-level: {sorted(tops)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())