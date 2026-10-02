#!/usr/bin/env python3
"""LLM judge for a blinded review pack (OpenCode backend).

Reads eval/blind/<pack_id>/, scores every anonymous output (A / B) against the
case brief using the rubric in tests/scoring_rubric.md, and writes a filled
score sheet that eval/aggregate.py can read. The judge never sees the key file
or the other output, and each output is scored in a separate call, so there is
no position bias from showing A next to B.

An LLM judge is a noisy instrument. Use at least two different judge models
from different families, check agreement between them, and calibrate each on a
few cases with known answers before trusting its scores. Use a judge that is not
the model that produced the outputs.

Examples:
    python eval/judge.py --pack eval/blind/<pack_id> --mock --out eval/scores/<pack_id>-mock.csv
    python eval/judge.py --pack eval/blind/<pack_id> --model opencode/big-pickle --out eval/scores/<pack_id>-bigpickle.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blind_pack import SCORE_COLUMNS  # noqa: E402
from cases import REPO_ROOT  # noqa: E402

DIMENSIONS = ["evidence_fidelity", "detection", "false_positive_restraint", "calibration", "actionability"]
RUBRIC_PATH = REPO_ROOT / "tests" / "scoring_rubric.md"

JUDGE_TEMPLATE = """You are a strict, fair evaluator of text-analysis outputs.

Below are a case brief (the input text that was analyzed, the findings an
ideal analysis should contain, and findings it should NOT contain) and one
anonymous analysis of that input. Score the analysis against the brief using
the rubric. Judge substance, not style or length. Do not reward formatting.
Quote-check: if the analysis quotes text, it must match the input.

# Rubric
{rubric}

# Case brief
{brief}

# Analysis to score
<analysis>
{output}
</analysis>

Reply with ONLY a JSON object, no other text, in this exact form:
{{"evidence_fidelity": 0, "detection": 0, "false_positive_restraint": 0, "calibration": 0, "actionability": 0, "notes": "one short sentence"}}
Each score is an integer 0, 1 or 2.
"""


def parse_scores(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    scores = {}
    for dim in DIMENSIONS:
        value = data.get(dim)
        if value not in (0, 1, 2):
            return None
        scores[dim] = value
    scores["notes"] = str(data.get("notes", ""))[:300]
    return scores


def mock_judge(prompt: str) -> str:
    return json.dumps({d: 1 for d in DIMENSIONS} | {"notes": "mock score"})


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pack", type=Path, required=True, help="blind pack directory (not the key directory)")
    parser.add_argument("--out", type=Path, required=True, help="filled score sheet CSV to write")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--mock", action="store_true", help="constant scores, no network")
    group.add_argument("--model", help="judge model as provider/model, e.g. opencode/big-pickle")
    parser.add_argument("--opencode-bin", help="path to opencode.exe (default: auto)")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between calls")
    parser.add_argument("--attempts", type=int, default=2, help="tries per output when the reply is not valid JSON")
    parser.add_argument("--only", nargs="+", metavar="CASE_ID")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    pack: Path = args.pack
    if (pack / "key.json").exists() or "keys" in {p.name for p in pack.parents}:
        raise SystemExit("Refusing to run: the judge must be given the blind pack, never a key directory")
    sheet = pack / "score_sheet.csv"
    if not sheet.exists():
        raise SystemExit(f"{sheet} not found; is this a blind pack?")

    rubric = RUBRIC_PATH.read_text(encoding="utf-8")
    judge_name = "mock-judge" if args.mock else f"judge:{args.model}"
    if not args.mock:
        from opencode_client import run_opencode

    with sheet.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if args.only:
        rows = [r for r in rows if r["case_id"] in set(args.only)]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    filled, failed, first = [], 0, True
    for row in rows:
        case_dir = pack / "cases" / row["case_id"]
        prompt = JUDGE_TEMPLATE.format(
            rubric=rubric,
            brief=(case_dir / "brief.md").read_text(encoding="utf-8"),
            output=(case_dir / f"{row['label']}.md").read_text(encoding="utf-8"),
        )
        scores = None
        for attempt in range(1, args.attempts + 1):
            if not first and args.delay and not args.mock:
                time.sleep(args.delay)
            first = False
            try:
                reply = mock_judge(prompt) if args.mock else run_opencode(args.model, prompt, binary=args.opencode_bin)["text"]
            except Exception as exc:  # recorded, run continues
                print(f"[error] {row['case_id']} {row['label']} attempt {attempt}: {exc}", file=sys.stderr)
                continue
            scores = parse_scores(reply)
            if scores:
                break
            print(f"[warn] {row['case_id']} {row['label']} attempt {attempt}: reply was not valid score JSON", file=sys.stderr)
        out_row = {col: row.get(col, "") for col in SCORE_COLUMNS}
        out_row["reviewer"] = judge_name
        if scores:
            out_row.update(scores)
            print(f"[ok] {row['case_id']} {row['label']}")
        else:
            failed += 1
        filled.append(out_row)

    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCORE_COLUMNS)
        writer.writeheader()
        writer.writerows(filled)
    print(f"\nScore sheet: {args.out}  ({len(filled) - failed} scored, {failed} unscored; use aggregate.py --allow-incomplete if any are unscored)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
