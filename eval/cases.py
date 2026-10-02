"""Parse tests/evaluation_cases.md into structured cases.

The Markdown file is the single source of truth. Two layouts are supported:

* v0.1 cases (1-9): ``## Case N — Title`` with a blockquote input and a free-text
  ``Expected:`` line. Their type and expected / not-expected findings live in a
  separate ``### Case N`` block under "Annotations for cases 1–9", so the
  original case text stays unchanged.
* v0.2 cases (10+): ``## Case N — Title`` followed by ``- **Type:**``,
  ``**Input:**`` (blockquote), ``**Expected findings:**`` and
  ``**Expected absence of findings:**`` lists.

Only the blockquote input is sent to the model. Titles, types and expectations
are for reviewers and for aggregation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CASES_PATH = REPO_ROOT / "tests" / "evaluation_cases.md"

CASE_TYPES = ("issue", "trap", "scope-change", "ambiguity")

_CASE_HEADING = re.compile(r"^## Case (\d+) — (.+?)\s*$")
_ANNOTATION_HEADING = re.compile(r"^### Case (\d+)\s*$")
_ANY_HEADING = re.compile(r"^#{1,6} ")
_TYPE_LINE = re.compile(r"^\s*-\s*\*\*Type:\*\*\s*(\S+)\s*$")
_DOMAIN_LINE = re.compile(r"^\s*-\s*\*\*Domain:\*\*\s*(.+?)\s*$")
_LIST_HEADER = re.compile(
    r"^\s*(?:-\s*)?\*\*(Expected findings|Expected absence of findings):\*\*\s*$"
)
_LIST_ITEM = re.compile(r"^\s*-\s+(.+?)\s*$")
_LEGACY_EXPECTED = re.compile(r"^Expected:\s*(.+?)\s*$")


@dataclass
class Case:
    number: int
    title: str
    input: str = ""
    type: str = ""
    domain: str = ""
    expected_findings: list[str] = field(default_factory=list)
    expected_absence: list[str] = field(default_factory=list)
    legacy_expected: str = ""

    @property
    def id(self) -> str:
        return f"case-{self.number:02d}"


def _sections(lines: list[str]):
    """Yield (kind, number, title, body_lines) for case and annotation sections."""
    current = None
    for line in lines:
        case_match = _CASE_HEADING.match(line)
        ann_match = _ANNOTATION_HEADING.match(line)
        if case_match or ann_match or _ANY_HEADING.match(line):
            if current:
                yield current
            current = None
            if case_match:
                current = ("case", int(case_match.group(1)), case_match.group(2), [])
            elif ann_match:
                current = ("annotation", int(ann_match.group(1)), "", [])
            continue
        if current:
            current[3].append(line)
    if current:
        yield current


def _parse_fields(body: list[str], case: Case, *, read_input: bool) -> None:
    input_lines: list[str] = []
    active_list: list[str] | None = None
    seen_expectations = False
    for line in body:
        if read_input and not seen_expectations and line.startswith(">"):
            input_lines.append(line[2:] if line.startswith("> ") else line[1:])
            continue
        if m := _TYPE_LINE.match(line):
            case.type = m.group(1)
            active_list = None
            continue
        if m := _DOMAIN_LINE.match(line):
            case.domain = m.group(1)
            active_list = None
            continue
        if m := _LIST_HEADER.match(line):
            seen_expectations = True
            active_list = (
                case.expected_findings
                if m.group(1) == "Expected findings"
                else case.expected_absence
            )
            continue
        if m := _LEGACY_EXPECTED.match(line):
            seen_expectations = True
            case.legacy_expected = m.group(1)
            active_list = None
            continue
        if active_list is not None:
            if m := _LIST_ITEM.match(line):
                active_list.append(m.group(1))
                continue
            if line.strip():
                active_list = None
    if read_input:
        case.input = "\n".join(input_lines).strip("\n")


def parse_cases(path: Path | str = DEFAULT_CASES_PATH) -> list[Case]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    cases: dict[int, Case] = {}
    annotations: list[tuple[int, list[str]]] = []
    for kind, number, title, body in _sections(lines):
        if kind == "case":
            if number in cases:
                raise ValueError(f"Duplicate case number {number}")
            case = Case(number=number, title=title)
            _parse_fields(body, case, read_input=True)
            cases[number] = case
        else:
            annotations.append((number, body))
    for number, body in annotations:
        if number not in cases:
            raise ValueError(f"Annotation for unknown case {number}")
        _parse_fields(body, cases[number], read_input=False)
    return [cases[n] for n in sorted(cases)]


def validate_cases(cases: list[Case]) -> list[str]:
    """Return a list of problems; empty means every case is complete."""
    problems = []
    for case in cases:
        if not case.input:
            problems.append(f"{case.id}: empty input")
        if case.type not in CASE_TYPES:
            problems.append(f"{case.id}: type {case.type!r} not in {CASE_TYPES}")
        if not case.expected_findings:
            problems.append(f"{case.id}: no expected findings")
        if not case.expected_absence:
            problems.append(f"{case.id}: no expected absence of findings")
    return problems


def cases_by_id(path: Path | str = DEFAULT_CASES_PATH) -> dict[str, Case]:
    return {case.id: case for case in parse_cases(path)}


if __name__ == "__main__":
    parsed = parse_cases()
    for c in parsed:
        print(f"{c.id}  {c.type:<12} {c.title}")
    issues = validate_cases(parsed)
    traps = sum(c.type == "trap" for c in parsed)
    print(f"\n{len(parsed)} cases, {traps} traps ({traps / len(parsed):.0%})")
    if issues:
        print("Problems:\n  " + "\n  ".join(issues))
        raise SystemExit(1)
