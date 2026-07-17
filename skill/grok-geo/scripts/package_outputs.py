#!/usr/bin/env python3
"""Package run outputs and refresh manifest.outputs paths."""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from geo_common import (  # noqa: E402
    append_event,
    load_manifest,
    print_json,
    save_manifest,
    sha256_file,
)


OUTPUT_FILES = [
    "report.md",
    "report.json",
    "questions.csv",
    "evidence.csv",
    "opportunities.csv",
    "manifest.json",
]


def package_outputs(run_dir: Path, zip_path: Optional[Path] = None) -> Dict[str, object]:
    run_dir = Path(run_dir)
    out_dir = run_dir / "output"
    outputs: Dict[str, str] = {}
    missing: List[str] = []
    for name in OUTPUT_FILES:
        p = out_dir / name
        if p.exists():
            outputs[name.replace(".", "_")] = str(p.resolve())
        else:
            missing.append(name)

    try:
        manifest = load_manifest(run_dir)
        manifest["outputs"] = {**(manifest.get("outputs") or {}), **outputs}
        save_manifest(run_dir, manifest)
        # re-resolve after save
        outputs["manifest_json"] = str((out_dir / "manifest.json").resolve())
    except FileNotFoundError:
        print("warn: manifest not found, output paths not recorded", file=sys.stderr)

    archive = None
    archive_sha = None
    if zip_path is None:
        zip_path = out_dir / f"{run_dir.name}-outputs.zip"
    zip_path = Path(zip_path)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in OUTPUT_FILES:
            p = out_dir / name
            if p.exists():
                zf.write(p, arcname=f"{run_dir.name}/{name}")
    archive = str(zip_path.resolve())
    archive_sha = sha256_file(zip_path)

    append_event(
        run_dir,
        "outputs_packaged",
        {"zip": archive, "sha256": archive_sha, "missing": missing},
    )
    return {
        "outputs": outputs,
        "missing": missing,
        "zip": archive,
        "zip_sha256": archive_sha,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Package GEO audit outputs")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--zip", default=None, help="optional zip output path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = package_outputs(Path(args.run_dir), Path(args.zip) if args.zip else None)
    print_json(result)
    return 1 if result["missing"] else 0


if __name__ == "__main__":
    raise SystemExit(main())