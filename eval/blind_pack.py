#!/usr/bin/env python3
"""Build a blinded review pack from a run directory.

For every case that has output from both methods, the two outputs are assigned
the labels A and B in random order. The reviewer sees only A/B; the mapping is
written to a separate key file that the reviewer must not open.

    eval/blind/<pack_id>/              # give this directory to the reviewer
        INSTRUCTIONS.md
        score_sheet.csv                # rows in random case order, scores blank
        cases/<case_id>/brief.md       # input, type, expected / not-expected findings
        cases/<case_id>/A.md
        cases/<case_id>/B.md
    eval/keys/<pack_id>/key.json       # A/B -> method mapping; NOT for the reviewer

Literal method names ("DRM", "drm-audit") are removed from outputs before
packing. Output structure can still reveal the method; see eval/README.md.

Example:
    python eval/blind_pack.py --run-dir eval/runs/2026-10-02-mock
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import random
import re
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cases import DEFAULT_CASES_PATH, Case, cases_by_id  # noqa: E402

EVAL_DIR = Path(__file__).resolve().parent
LABELS = ("A", "B")
SCORE_COLUMNS = [
    "pack_id",
    "case_id",
    "label",
    "reviewer",
    "evidence_fidelity",
    "detection",
    "false_positive_restraint",
    "calibration",
    "actionability",
    "notes",
]
# Remove literal method identifiers. "DRM Audit Report" -> "Audit Report".
_REDACTIONS = [
    (re.compile(r"\bdrm-audit\b", re.IGNORECASE), "audit"),
    (re.compile(r"\bDRM\b[ -]?", re.IGNORECASE), ""),
]


def redact(text: str) -> tuple[str, int]:
    total = 0
    for pattern, replacement in _REDACTIONS:
        text, n = pattern.subn(replacement, text)
        total += n
    return text, total


def brief_markdown(case: Case) -> str:
    quoted = "\n".join("> " + line if line else ">" for line in case.input.splitlines())
    findings = "\n".join(f"- {item}" for item in case.expected_findings)
    absence = "\n".join(f"- {item}" for item in case.expected_absence)
    return (
        f"# {case.id} — {case.title}\n\n"
        f"- **Type:** {case.type}\n\n"
        f"## Input given to the model\n{quoted}\n\n"
        f"## Expected findings\n{findings}\n\n"
        f"## Expected absence of findings\n{absence}\n"
    )


INSTRUCTIONS = """# Review instructions

You are scoring two anonymous outputs (A and B) per case. Do not try to work out
which method produced which output, and do not open any key file.

For each case:
1. Read `cases/<case_id>/brief.md` (input, case type, expected findings,
   expected absence of findings).
2. Read `A.md` and `B.md`.
3. Fill one row per output in `score_sheet.csv`: put your name or initials in
   `reviewer` and a score of 0, 1 or 2 in each of the five dimensions
   (see tests/scoring_rubric.md). Use `notes` for short justifications.

For `trap` cases, "detection" means correctly reporting that there is no
material issue; "false_positive_restraint" scores whether the output avoided
the traps listed under "Expected absence of findings".

Score each output against the brief, not against the other output.
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--pack-id", help="default: <run dir name>-<random suffix>")
    parser.add_argument("--blind-root", type=Path, default=EVAL_DIR / "blind")
    parser.add_argument("--key-root", type=Path, default=EVAL_DIR / "keys")
    parser.add_argument("--seed", type=int, help="fix the shuffle (stored only in the key file)")
    parser.add_argument("--no-redact", action="store_true", help="do not strip method names from outputs")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_dir: Path = args.run_dir
    method_dirs = sorted(p for p in run_dir.iterdir() if p.is_dir() and p.name != "prompts")
    if len(method_dirs) != 2:
        raise SystemExit(f"Expected exactly 2 method directories in {run_dir}, found {[p.name for p in method_dirs]}")
    methods = [p.name for p in method_dirs]

    outputs = {m: {p.stem: p for p in (run_dir / m).glob("*.md")} for m in methods}
    common = sorted(set(outputs[methods[0]]) & set(outputs[methods[1]]))
    missing = sorted(set(outputs[methods[0]]) ^ set(outputs[methods[1]]))
    if missing:
        print(f"[warn] skipping cases without output from both methods: {missing}", file=sys.stderr)
    if not common:
        raise SystemExit("No cases with output from both methods")

    all_cases = cases_by_id(args.cases)
    unknown = [c for c in common if c not in all_cases]
    if unknown:
        raise SystemExit(f"Outputs for case ids not in {args.cases}: {unknown}")

    seed = args.seed if args.seed is not None else secrets.randbits(64)
    rng = random.Random(seed)
    pack_id = args.pack_id or f"{run_dir.name}-{secrets.token_hex(3)}"
    pack_dir = args.blind_root / pack_id
    key_dir = args.key_root / pack_id

    pack_resolved, key_resolved = pack_dir.resolve(), key_dir.resolve()
    if key_resolved == pack_resolved or pack_resolved in key_resolved.parents:
        raise SystemExit("The key directory must not be inside the review pack")
    if pack_dir.exists() or key_dir.exists():
        raise SystemExit(f"Pack '{pack_id}' already exists; choose another --pack-id")

    mapping: dict[str, dict[str, str]] = {}
    redaction_counts: dict[str, dict[str, int]] = {}
    for case_id in common:
        order = methods[:]
        rng.shuffle(order)
        mapping[case_id] = dict(zip(LABELS, order))
        case_dir = pack_dir / "cases" / case_id
        case_dir.mkdir(parents=True)
        (case_dir / "brief.md").write_text(brief_markdown(all_cases[case_id]), encoding="utf-8")
        redaction_counts[case_id] = {}
        for label, method in mapping[case_id].items():
            text = outputs[method][case_id].read_text(encoding="utf-8")
            count = 0
            if not args.no_redact:
                text, count = redact(text)
            redaction_counts[case_id][label] = count
            (case_dir / f"{label}.md").write_text(text, encoding="utf-8")

    sheet_order = common[:]
    rng.shuffle(sheet_order)
    with (pack_dir / "score_sheet.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(SCORE_COLUMNS)
        for case_id in sheet_order:
            for label in LABELS:
                writer.writerow([pack_id, case_id, label] + [""] * (len(SCORE_COLUMNS) - 3))
    (pack_dir / "INSTRUCTIONS.md").write_text(INSTRUCTIONS, encoding="utf-8")

    key_dir.mkdir(parents=True)
    key = {
        "pack_id": pack_id,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "methods": methods,
        "seed": seed,
        "redacted": not args.no_redact,
        "redaction_counts": redaction_counts,
        "mapping": mapping,
    }
    (key_dir / "key.json").write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")

    print(f"Review pack: {pack_dir}  ({len(common)} cases)")
    print(f"Key file:    {key_dir / 'key.json'}  -- keep this away from the reviewer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
