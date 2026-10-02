# Changelog

## 0.2.0
### Evaluation set
- `tests/evaluation_cases.md` is now v0.2. The nine v0.1 cases are unchanged in text.
- Added structured annotations for cases 1–9 (type, expected findings, expected absence of findings) in a separate section.
- Added 17 synthetic cases (10–26) covering bug reports, analytics, backtests, science summaries, code review, and AI self-reports. Totals: 26 cases — 12 issue, 10 trap, 2 scope-change, 2 ambiguity. Traps are 10/26 overall and 8/17 of the new cases.
- `tests/scoring_rubric.md`: added v0.2 notes on applying the existing dimensions to trap, scope-change, and ambiguity cases. Dimensions and scale unchanged.

### Evaluation tooling (`eval/`)
- `run_cases.py`: runs each case through each method sequentially and saves raw responses to `eval/runs/<date>/<method>/<case_id>.md`, with a manifest of model, settings, and prompt hashes. Requires `--mock` or `--live`; the API key is read from an environment variable.
- `blind_pack.py`: builds an A/B-labeled review pack with a separate key file.
- `aggregate.py`: unblinds filled score sheets and reports scores by case, dimension, and case type, with traps separately. Reports numbers only.
- `score_sheet.csv`: empty template matching the rubric.
- `test_pipeline.py`: tests the case parser and the full pipeline on mock responses.
- No real model runs have been made; no comparison results exist yet.

### Skills
- New `skills/drm-contract/SKILL.md`: answer-time contract with `[LIMIT]`, `[SIM]`, `[PARADOX]`, `[PARTNER]` markers, full and short modes. Markers are conditional (no quotas); `[SIM]` is documented as a self-report, not access to mechanisms; recaps of earlier sessions only when supplied by the user.
- `drm-audit`: added `license` and `metadata.version` to the frontmatter; added a short report (3–5 lines) for material with no material issues. Operating rules 1–10, labels, and the full template are unchanged.

### Packaging and docs
- README rewritten around reviewing AI-generated reports and research for overreach; limitations kept; no effectiveness claims.
- Added `VERSION`, `build/pack.py` (local, reproducible ZIP), `.gitignore` for run outputs, packs, keys, and build output.
- `LICENSE` unchanged; the license decision remains with the owner.

## 0.1.0 — initial prototype
- Added evidence-first DRM Audit skill.
- Added illustrative AI self-report example and sample report.
- Added nine manual evaluation cases and a scoring rubric.
- Explicitly documented that text-only analysis does not establish consciousness or hidden internal states.
