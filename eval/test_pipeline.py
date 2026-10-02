"""Tests for the case parser and the mock evaluation pipeline.

Run: python -m unittest discover -s eval -p "test_*.py" -v
"""

from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVAL_DIR.parent
sys.path.insert(0, str(EVAL_DIR))
sys.path.insert(0, str(REPO_ROOT / "build"))

import aggregate  # noqa: E402
import blind_pack  # noqa: E402
import pack  # noqa: E402
import run_cases  # noqa: E402
from cases import DEFAULT_CASES_PATH, parse_cases, validate_cases  # noqa: E402

# sha256 of tests/evaluation_cases.md at v0.1 without its title line.
V01_BODY_SHA256 = "9db11c6814ddea2ca02110dca2e5a308c3fc1ce89ec6d90d0e1763c1a3bc0370"
V02_MARKER = "\n---\n\n# v0.2 additions"
DIMENSIONS = aggregate.DIMENSIONS


def quiet(func, *args):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return func(*args)


class CaseSetTests(unittest.TestCase):
    def setUp(self):
        self.cases = parse_cases(DEFAULT_CASES_PATH)

    def test_v01_cases_unchanged(self):
        text = DEFAULT_CASES_PATH.read_text(encoding="utf-8")
        body = text.split("\n", 1)[1]
        body = body[: body.index(V02_MARKER)]
        self.assertEqual(hashlib.sha256(body.encode("utf-8")).hexdigest(), V01_BODY_SHA256)

    def test_composition(self):
        numbers = [c.number for c in self.cases]
        self.assertEqual(numbers, list(range(1, len(numbers) + 1)))
        new = [c for c in self.cases if c.number > 9]
        self.assertGreaterEqual(len(new), 12)
        self.assertLessEqual(len(new), 20)
        traps = [c for c in self.cases if c.type == "trap"]
        self.assertGreaterEqual(len(traps) * 3, len(self.cases))
        self.assertGreaterEqual(sum(c.type == "trap" for c in new) * 3, len(new))

    def test_every_case_complete(self):
        self.assertEqual(validate_cases(self.cases), [])

    def test_metadata_not_in_input(self):
        for case in self.cases:
            self.assertNotIn("Expected", case.input, case.id)
            self.assertNotIn("**Type:**", case.input, case.id)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.run_dir = self.root / "runs" / "test-mock"
        self.assertEqual(quiet(run_cases.main, ["--mock", "--run-dir", str(self.run_dir)]), 0)
        self.blind_root, self.key_root = self.root / "blind", self.root / "keys"
        self.assertEqual(
            quiet(
                blind_pack.main,
                [
                    "--run-dir", str(self.run_dir),
                    "--blind-root", str(self.blind_root),
                    "--key-root", str(self.key_root),
                    "--pack-id", "p1",
                ],
            ),
            0,
        )
        self.pack_dir = self.blind_root / "p1"
        self.key_path = self.key_root / "p1" / "key.json"
        self.key = json.loads(self.key_path.read_text(encoding="utf-8"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_run_outputs_and_manifest(self):
        n_cases = len(parse_cases(DEFAULT_CASES_PATH))
        for method in ("drm", "baseline"):
            self.assertEqual(len(list((self.run_dir / method).glob("case-*.md"))), n_cases)
        manifest = json.loads((self.run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["mode"], "mock")
        self.assertEqual(len(manifest["calls"]), 2 * n_cases)
        self.assertTrue(all("error" not in call for call in manifest["calls"]))
        # A second run skips everything already present.
        quiet(run_cases.main, ["--mock", "--run-dir", str(self.run_dir)])
        manifest = json.loads((self.run_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["calls"]), 2 * n_cases)

    def test_live_mode_requires_key(self):
        with self.assertRaises(SystemExit):
            quiet(run_cases.main, ["--live", "--run-dir", str(self.root / "live"), "--config", str(self._config_without_key())])

    def _config_without_key(self) -> Path:
        config = json.loads(run_cases.DEFAULT_CONFIG.read_text(encoding="utf-8"))
        config["api_key_env"] = "DRM_TEST_KEY_THAT_IS_NOT_SET"
        path = self.root / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        return path

    def test_key_separate_and_outputs_blinded(self):
        self.assertFalse(any(p.name == "key.json" for p in self.pack_dir.rglob("*")))
        self.assertNotIn(self.pack_dir.resolve(), self.key_path.resolve().parents)
        for path in self.pack_dir.rglob("*"):
            if path.name in ("A.md", "B.md", "score_sheet.csv", "INSTRUCTIONS.md"):
                text = path.read_text(encoding="utf-8").lower()
                self.assertNotIn("drm", text, path)
                self.assertNotIn("baseline", text, path)
        for mapping in self.key["mapping"].values():
            self.assertEqual(sorted(mapping.values()), ["baseline", "drm"])

    def test_key_inside_pack_rejected(self):
        with self.assertRaises(SystemExit):
            quiet(
                blind_pack.main,
                [
                    "--run-dir", str(self.run_dir),
                    "--blind-root", str(self.blind_root),
                    "--key-root", str(self.blind_root / "p2" / "secret"),
                    "--pack-id", "p2",
                ],
            )

    def _fill_sheet(self, reviewer: str, drm_score: int, baseline_score: int) -> Path:
        rows = list(csv.DictReader((self.pack_dir / "score_sheet.csv").read_text(encoding="utf-8").splitlines()))
        for row in rows:
            method = self.key["mapping"][row["case_id"]][row["label"]]
            row["reviewer"] = reviewer
            for dim in DIMENSIONS:
                row[dim] = str(drm_score if method == "drm" else baseline_score)
        path = self.root / f"{reviewer}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=blind_pack.SCORE_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_aggregate_unblinds_and_averages_reviewers(self):
        sheet1 = self._fill_sheet("R1", drm_score=2, baseline_score=0)
        sheet2 = self._fill_sheet("R2", drm_score=1, baseline_score=1)
        out, csv_out = self.root / "summary.md", self.root / "summary.csv"
        quiet(
            aggregate.main,
            ["--key", str(self.key_path), "--scores", str(sheet1), str(sheet2), "--out", str(out), "--csv-out", str(csv_out)],
        )
        report = out.read_text(encoding="utf-8")
        self.assertIn("| traps | 10 |", report)
        self.assertIn("| all cases | 26 | 2.50 | 7.50 |", report)  # columns: baseline, drm
        rows = list(csv.DictReader(csv_out.read_text(encoding="utf-8").splitlines()))
        self.assertEqual(len(rows), 52)
        drm_row = next(r for r in rows if r["method"] == "drm")
        self.assertEqual(float(drm_row["total"]), 7.5)
        self.assertEqual(drm_row["reviewers"], "2")

    def test_aggregate_rejects_bad_values(self):
        sheet = self._fill_sheet("R1", drm_score=2, baseline_score=0)
        text = sheet.read_text(encoding="utf-8").replace(",2,2,2,2,2,", ",3,2,2,2,2,", 1)
        sheet.write_text(text, encoding="utf-8")
        with self.assertRaises(SystemExit):
            quiet(aggregate.main, ["--key", str(self.key_path), "--scores", str(sheet)])

    def test_aggregate_rejects_blank_rows_unless_allowed(self):
        blank = self.pack_dir / "score_sheet.csv"
        with self.assertRaises(SystemExit):
            quiet(aggregate.main, ["--key", str(self.key_path), "--scores", str(blank)])
        quiet(aggregate.main, ["--key", str(self.key_path), "--scores", str(blank), "--allow-incomplete"])


class PackTests(unittest.TestCase):
    def test_zip_contents_and_reproducibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = pack.build(REPO_ROOT, Path(tmp) / "a.zip")
            second = pack.build(REPO_ROOT, Path(tmp) / "b.zip")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                names = archive.namelist()
        version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        prefix = f"drm-reliability-toolkit-{version}/"
        self.assertTrue(all(n.startswith(prefix) for n in names))
        for required in ("skills/drm-audit/SKILL.md", "skills/drm-contract/SKILL.md", "LICENSE", "eval/run_cases.py"):
            self.assertIn(prefix + required, names)
        for name in names:
            self.assertNotIn("/runs/", name)
            self.assertNotIn("/keys/", name)
            self.assertNotIn("TASK_FOR_CLOUD_AGENT", name)


if __name__ == "__main__":
    unittest.main()
