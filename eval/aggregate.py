#!/usr/bin/env python3
"""Unblind filled score sheets and summarize scores by case and dimension.

Scores from several reviewers are averaged per (case, method, dimension) first,
then across cases. Results are broken down by case type, with traps reported
separately. The script reports numbers only; it does not pick a winner, and
this small manual set does not support claims of statistical significance.

Example:
    python eval/aggregate.py \\
        --key eval/keys/<pack_id>/key.json \\
        --scores eval/blind/<pack_id>/score_sheet.csv \\
        --out eval/results/<pack_id>.md --csv-out eval/results/<pack_id>.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cases import CASE_TYPES, DEFAULT_CASES_PATH, cases_by_id  # noqa: E402

DIMENSIONS = [
    "evidence_fidelity",
    "detection",
    "false_positive_restraint",
    "calibration",
    "actionability",
]
MAX_PER_DIMENSION = 2


def load_scores(paths: list[Path], key: dict, allow_incomplete: bool):
    """Return {(case_id, method): {dimension: [scores...]}} and reviewer counts."""
    errors: list[str] = []
    scores: dict[tuple[str, str], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    reviewers: dict[tuple[str, str], set[str]] = defaultdict(set)
    skipped = 0
    for path in paths:
        with path.open(newline="", encoding="utf-8") as handle:
            for line_no, row in enumerate(csv.DictReader(handle), start=2):
                where = f"{path}:{line_no}"
                if row.get("pack_id") != key["pack_id"]:
                    errors.append(f"{where}: pack_id {row.get('pack_id')!r} does not match key {key['pack_id']!r}")
                    continue
                case_id, label = row.get("case_id"), row.get("label")
                if case_id not in key["mapping"] or label not in key["mapping"][case_id]:
                    errors.append(f"{where}: unknown case/label {case_id!r}/{label!r}")
                    continue
                raw = [(row.get(d) or "").strip() for d in DIMENSIONS]
                if not any(raw):
                    skipped += 1
                    if not allow_incomplete:
                        errors.append(f"{where}: no scores filled in")
                    continue
                values = {}
                for dim, value in zip(DIMENSIONS, raw):
                    if value not in ("0", "1", "2"):
                        errors.append(f"{where}: {dim} must be 0, 1 or 2, got {value!r}")
                    else:
                        values[dim] = int(value)
                if len(values) != len(DIMENSIONS):
                    continue
                method = key["mapping"][case_id][label]
                reviewer = (row.get("reviewer") or "").strip() or "(unnamed)"
                if reviewer in reviewers[(case_id, method)]:
                    errors.append(f"{where}: duplicate score from reviewer {reviewer!r} for {case_id}/{label}")
                    continue
                reviewers[(case_id, method)].add(reviewer)
                for dim, value in values.items():
                    scores[(case_id, method)][dim].append(value)
    if errors:
        raise SystemExit("Score sheet problems:\n  " + "\n  ".join(errors))
    return scores, reviewers, skipped


def fmt(value: float | None) -> str:
    return "–" if value is None else f"{value:.2f}"


def build_report(key: dict, cases: dict, scores, reviewers, skipped: int) -> tuple[str, list[dict]]:
    methods = key["methods"]
    per_case: dict[tuple[str, str], dict[str, float]] = {}
    for (case_id, method), dims in scores.items():
        per_case[(case_id, method)] = {d: mean(dims[d]) for d in DIMENSIONS}

    # Only cases scored for every method enter the summaries, so groups compare like with like.
    scored_cases = sorted(c for c in key["mapping"] if all((c, m) in per_case for m in methods))
    partial = sorted(c for c in key["mapping"] if c not in scored_cases and any((c, m) in per_case for m in methods))

    def group_mean(case_ids, method, dim=None):
        vals = [
            per_case[(c, method)][dim] if dim else sum(per_case[(c, method)].values())
            for c in case_ids
        ]
        return mean(vals) if vals else None

    groups = [("all cases", scored_cases)]
    groups.append(("traps", [c for c in scored_cases if cases[c].type == "trap"]))
    groups.append(("non-traps", [c for c in scored_cases if cases[c].type != "trap"]))
    for case_type in CASE_TYPES:
        if case_type != "trap":
            groups.append((f"type: {case_type}", [c for c in scored_cases if cases[c].type == case_type]))

    lines = [
        f"# Score summary — pack `{key['pack_id']}`",
        "",
        "Numbers only. This is a small manual set: differences are not evidence of",
        "statistical significance, and no method is declared better here.",
        "",
        f"- Cases with scores for every method: {len(scored_cases)} of {len(key['mapping'])}",
    ]
    if partial:
        lines.append(f"- Cases scored for only some methods (excluded from summaries): {', '.join(partial)}")
    if skipped:
        lines.append(f"- Blank rows skipped: {skipped}")
    all_reviewers = sorted({r for rs in reviewers.values() for r in rs})
    lines.append(f"- Reviewers: {', '.join(all_reviewers) if all_reviewers else 'none'}")
    lines.append(f"- Maximum: {MAX_PER_DIMENSION} per dimension, {MAX_PER_DIMENSION * len(DIMENSIONS)} per case")
    lines.append("")

    lines += ["## Mean total per case, by group", ""]
    lines.append("| Group | n | " + " | ".join(methods) + " |")
    lines.append("|---|---|" + "---|" * len(methods))
    for name, ids in groups:
        lines.append(f"| {name} | {len(ids)} | " + " | ".join(fmt(group_mean(ids, m)) for m in methods) + " |")
    lines.append("")

    for name, ids in groups[:3]:
        lines += [f"## Mean score by dimension — {name} (n={len(ids)})", ""]
        lines.append("| Dimension | " + " | ".join(methods) + " |")
        lines.append("|---|" + "---|" * len(methods))
        for dim in DIMENSIONS:
            lines.append(f"| {dim} | " + " | ".join(fmt(group_mean(ids, m, dim)) for m in methods) + " |")
        lines.append("")

    lines += ["## Per case", ""]
    header = "| Case | Type | Reviewers | " + " | ".join(f"{m} total" for m in methods) + " |"
    lines += [header, "|---|---|---|" + "---|" * len(methods)]
    long_rows: list[dict] = []
    for case_id in sorted(key["mapping"]):
        n_rev = max((len(reviewers.get((case_id, m), ())) for m in methods), default=0)
        totals = []
        for m in methods:
            dims = per_case.get((case_id, m))
            totals.append(fmt(sum(dims.values()) if dims else None))
            if dims:
                long_rows.append(
                    {
                        "case_id": case_id,
                        "type": cases[case_id].type,
                        "method": m,
                        "reviewers": len(reviewers[(case_id, m)]),
                        **{d: round(dims[d], 3) for d in DIMENSIONS},
                        "total": round(sum(dims.values()), 3),
                    }
                )
        lines.append(f"| {case_id} | {cases[case_id].type} | {n_rev} | " + " | ".join(totals) + " |")
    lines.append("")
    return "\n".join(lines), long_rows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--scores", type=Path, nargs="+", required=True, help="one or more filled score sheets")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--out", type=Path, help="write the Markdown summary here (default: stdout)")
    parser.add_argument("--csv-out", type=Path, help="write unblinded per-case, per-method scores here")
    parser.add_argument("--allow-incomplete", action="store_true", help="skip rows with no scores instead of failing")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    key = json.loads(args.key.read_text(encoding="utf-8"))
    cases = cases_by_id(args.cases)
    missing = [c for c in key["mapping"] if c not in cases]
    if missing:
        raise SystemExit(f"Key references cases not in {args.cases}: {missing}")
    scores, reviewers, skipped = load_scores(args.scores, key, args.allow_incomplete)
    report, long_rows = build_report(key, cases, scores, reviewers, skipped)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
        print(f"Summary written to {args.out}")
    else:
        print(report)
    if args.csv_out:
        args.csv_out.parent.mkdir(parents=True, exist_ok=True)
        fields = ["case_id", "type", "method", "reviewers", *DIMENSIONS, "total"]
        with args.csv_out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(long_rows)
        print(f"Per-case scores written to {args.csv_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
