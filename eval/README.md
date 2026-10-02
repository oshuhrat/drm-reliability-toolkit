# Evaluation workflow

Compares two methods on the fixed case set in `tests/evaluation_cases.md`:

- `drm` — system prompt = `skills/drm-audit/SKILL.md` (frontmatter stripped); user message "Audit the following text." + the case input.
- `baseline` — no system prompt; user message "Analyze this text for errors and unsupported claims." + the case input.

Both use the same model and settings from `config.json`. Only the case input (the blockquote) is sent; titles, types, and expectations are never sent to the model.

Requirements: Python 3.10+. Mock runs need nothing else. Live runs need `pip install anthropic` and an API key in an environment variable.

## 1. Check the case set

```bash
python eval/cases.py
```

Lists every case with its type and fails if any case lacks an input, a type, expected findings, or expected absence of findings.

## 2. Run the cases

Mock (no network, canned responses — for testing the pipeline only):

```bash
python eval/run_cases.py --mock
# -> eval/runs/<YYYY-MM-DD>-mock/
```

Live (calls the API, costs money; run only when you intend to):

```bash
export ANTHROPIC_API_KEY=...        # never commit the key
python eval/run_cases.py --live
# -> eval/runs/<YYYY-MM-DD>/
```

Useful flags: `--only case-01 case-10`, `--methods drm`, `--run-dir PATH`, `--overwrite`. Calls run one at a time with `delay_seconds` between them. Existing outputs are skipped, so an interrupted run can be resumed by running the same command again.

Each run directory contains:

```text
manifest.json            model, temperature, effort, max_tokens, prompt hashes,
                         per-call timestamps, returned model id, stop_reason, token usage, errors
prompts/<method>.json    exact system prompt and user template
<method>/<case_id>.md    raw response text, nothing added
```

### Config (`config.json`)
| Key | Meaning |
|---|---|
| `model` | Model id sent to the API. The returned model id is recorded per call in the manifest. |
| `temperature` | `null` = not sent. Current Claude Opus/Sonnet/Fable models reject non-default sampling parameters; set a number only for models that accept it. |
| `effort` | Sent as `output_config.effort`; `null` to omit. |
| `max_tokens`, `max_retries`, `delay_seconds` | Request limits, SDK retries, pause between calls. |
| `api_key_env` | Name of the environment variable holding the key. |
| `methods.<name>` | `system` or `system_file`, and `user_template` containing `{input}`. |

Refusal fallbacks to another model are deliberately not enabled, so every output comes from the configured model. A refusal or truncated response is written as-is and flagged in the manifest (`stop_reason`); empty responses are written as a neutral placeholder comment.

## 3. Build a blinded review pack

```bash
python eval/blind_pack.py --run-dir eval/runs/<run>
```

Creates:

```text
eval/blind/<pack_id>/      give this whole directory to the reviewer
    INSTRUCTIONS.md
    score_sheet.csv        rows in random case order, scores blank
    cases/<case_id>/brief.md, A.md, B.md
eval/keys/<pack_id>/key.json   A/B -> method mapping. Do not give this to the reviewer.
```

The A/B assignment is random per case. The key is written to a separate directory tree, and the script refuses to place it inside the pack. Pass `--seed` only if you need a reproducible shuffle; the seed is stored in the key file only.

**Limits of blinding.** Literal method names ("DRM", "drm-audit") are removed from outputs, but the `drm` output usually follows the audit template (evidence ledger, `[FACT-TEXT]`-style labels), so a reviewer may still recognize it. Mitigations: score each output against the brief rather than against the other output; use more than one reviewer; have reviewers note when they believe they recognized the method.

## 4. Score

Reviewers fill `score_sheet.csv` in the pack (one copy per reviewer, each with their name in `reviewer`). Each dimension is 0, 1, or 2 per `tests/scoring_rubric.md`. `eval/score_sheet.csv` is the empty template with the same columns:

```text
pack_id,case_id,label,reviewer,evidence_fidelity,detection,false_positive_restraint,calibration,actionability,notes
```

## 5. Aggregate

Only after all scores are final:

```bash
python eval/aggregate.py \
    --key eval/keys/<pack_id>/key.json \
    --scores reviewer1.csv reviewer2.csv \
    --out eval/results/<pack_id>.md --csv-out eval/results/<pack_id>.csv
```

Output: mean total per case for all cases, traps, non-traps, and each case type; mean per dimension for all / traps / non-traps; a per-case table. Multiple reviewers are averaged per case first. Invalid values (anything other than 0, 1, 2), mismatched pack ids, unknown cases, and duplicate reviewer rows are errors. Blank rows are errors unless `--allow-incomplete` is passed.

The script reports numbers only. It does not pick a better method, and 26 cases do not support claims of statistical significance.

## Tests

```bash
python -m unittest discover -s eval -p "test_*.py" -v
```

Covers: the case parser and set composition (including that cases 1–9 are unchanged from v0.1), the full mock pipeline (run → blind → score → aggregate), that the key stays outside the pack and method names do not appear in packed outputs, score validation, and the ZIP build.

## Where outputs go
`eval/runs/`, `eval/blind/`, `eval/keys/`, and `eval/results/` are git-ignored by default. Commit a run deliberately if you want it in the repository, and never commit a key file next to an unfinished review.
