# DRM Reliability Toolkit — v0.4

Skills that make an AI reviewer check a text for overreach without raising false alarms: unsupported certainty, causal claims built on correlation or timing, evidence that does not match the conclusion, and verification that never happened.

**Free. MIT license. Early version: see "What was measured" before relying on it.**

## What it does best
In our tests the main effect was **fewer false alarms**. A plain "find the errors" prompt tends to criticise correct, well-qualified text. `drm-audit` first decides whether there is a material issue and, if there is none, writes a 3–5 line "no material issues" report. It also separates what the text shows from what is only inferred, and cites exact quotes.

It did **not** find noticeably more real problems than a strong model already finds with a plain prompt.

## What is included

| Path | What it is |
|---|---|
| `skills/drm-audit/` | **Audit mode.** Reviews someone else's text (an AI answer, report, conversation). Starts with a materiality check; produces an evidence ledger with exact quotes, support levels, contradictions vs. scope changes, and discriminating tests, or a short report when nothing material is found. |
| `skills/drm-contract/` | **Answer mode.** Structures the model's own answer: understanding → assumptions → plan → answer → alternatives → limits → next experiment, with `[LIMIT]`, `[SIM]`, `[PARADOX]`, `[PARTNER]` markers used only when there is a basis for them. **Not evaluated in the tests below.** |
| `tests/evaluation_cases.md` | 57 synthetic cases with expected findings and expected absence of findings (about 40% are false-positive traps). |
| `tests/scoring_rubric.md` | Five 0–2 dimensions: evidence fidelity, detection, false-positive restraint, calibration, actionability. |
| `eval/` | Scripts to run methods, build a blinded review pack, score with LLM judges, and aggregate. Raw judge score sheets and earlier skill versions are included. |
| `examples/` | A synthetic self-report dialogue and a sample audit report. |

## What was measured
Same cases, same user message; only the system prompt differed (skill vs. none). Outputs were scored 0–10 by two LLM judges (different model families) that saw anonymised A/B outputs; judge agreement was high (correlation 0.87–0.92).

| Subject model | Skill version | Cases | Plain prompt | With skill | Traps only (plain → skill) |
|---|---|---|---|---|---|
| Claude Opus 5.5 | 0.4 | 12 fresh | 8.0 | 9.7 | 6.25 → 9.5 |
| Cohere north-mini-code (free) | 0.4 | 12 fresh | 5.5 | 7.7 | 1.9 → 5.6 |
| Qwen3.8-27B (free) | 0.3 | 17 fresh | 6.3 | 8.7 | 3.4 → 7.0 |
| Muse Spark 1.3 (free) | 0.2 | 26 | 8.4 / 8.0 | 9.2 / 9.0 | 7.9 / 6.9 → 8.3 / 7.6 |

On the cases where the text really contains an error, Claude Opus 5.5 scored about the same with and without the skill (9.75 vs 9.8). The gain came from the traps.

## Limits of these results
- Small, synthetic, author-written case set; one run per model; no statistical significance claimed.
- Judges are LLMs, mostly free models. The skill's output is recognisable by its structure, so blinding is partial and judges may favour structured reports.
- The skill was revised after seeing failures on earlier cases (0.2 → 0.3 → 0.4). Fresh cases were written for each check, but the later cases were written by someone who knew the skill's weak spots.
- Version 0.4 vs 0.3 was not shown to be better (interval includes zero).
- `drm-contract` has no measurements yet.

## What it does not do
- It does not verify facts against the world unless sources or a separate research tool are supplied.
- It does not access model internals. Self-reports (including `[SIM]`) are treated as text, not as insight into mechanisms.
- It does not establish or rule out consciousness, feelings, or intentions from text.
- It does not guarantee fewer errors in any model's output.

## Install

### Claude Code
Copy one or both skill directories into your project's `.claude/skills/` (or your user-level skills directory):

```text
your-project/.claude/skills/drm-audit/SKILL.md
your-project/.claude/skills/drm-contract/SKILL.md
```

### Other agents
Skill discovery conventions vary by tool and version. Copy the `SKILL.md` files into the skill directory your agent documents and adapt the frontmatter if needed.

## Use
- **Audit:** ask the agent to audit a report or conversation with `drm-audit`, and state the question you want answered (for example, "Does this backtest memo support its conclusion?"). For long material, say which part to review.
- **Contract:** ask the agent to answer using `drm-contract`.

## Reproduce or extend the evaluation
See `eval/README.md`. You need a model API key or the `opencode` CLI; run on synthetic cases only if you use free models that may log requests.

## License
MIT. See `LICENSE`.
