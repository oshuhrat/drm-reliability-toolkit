#!/usr/bin/env python3
"""Build a ZIP archive of the toolkit package.

The archive contains the skills, documentation, test set, and evaluation
scripts. It excludes run outputs, blinded packs, keys, results, and anything
not listed in INCLUDE. Entries are written in sorted order with a fixed
timestamp, so the same sources produce a byte-identical archive.

This only builds a local file. It does not upload or publish anything.

Example:
    python build/pack.py            # -> dist/drm-reliability-toolkit-<VERSION>.zip
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_NAME = "drm-reliability-toolkit"
FIXED_DATE = (2026, 1, 1, 0, 0, 0)

# Files and directories (recursively) shipped in the package, relative to the repo root.
INCLUDE = [
    "README.md",
    "CHANGELOG.md",
    "LICENSE",
    "VERSION",
    "skills/drm-audit/SKILL.md",
    "skills/drm-contract/SKILL.md",
    "examples",
    "tests/evaluation_cases.md",
    "tests/scoring_rubric.md",
    "eval/README.md",
    "eval/config.json",
    "eval/score_sheet.csv",
    "eval/cases.py",
    "eval/run_cases.py",
    "eval/blind_pack.py",
    "eval/aggregate.py",
]
EXCLUDE_PARTS = {"__pycache__", ".DS_Store"}


def collect_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    for entry in INCLUDE:
        path = root / entry
        if path.is_dir():
            files.update(p for p in path.rglob("*") if p.is_file())
        elif path.is_file():
            files.add(path)
        else:
            raise SystemExit(f"Missing file listed in INCLUDE: {entry}")
    return sorted(
        (p for p in files if not EXCLUDE_PARTS.intersection(p.relative_to(root).parts)),
        key=lambda p: p.relative_to(root).as_posix(),
    )


def build(root: Path, out: Path | None) -> Path:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    out = out or root / "dist" / f"{PACKAGE_NAME}-{version}.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    prefix = f"{PACKAGE_NAME}-{version}"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in collect_files(root):
            info = zipfile.ZipInfo(f"{prefix}/{path.relative_to(root).as_posix()}", date_time=FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, help="output ZIP path")
    args = parser.parse_args(argv)
    out = build(REPO_ROOT, args.out)
    with zipfile.ZipFile(out) as archive:
        names = archive.namelist()
    print(f"Wrote {out} ({len(names)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
