# DRM Reliability Toolkit — v0.2

Skills for checking AI-generated reports, analyses, and research summaries for overreach: unsupported certainty, causal claims built on correlation or timing, and evidence that does not match the conclusion.

Status: prototype. Whether it finds more real problems than a plain "find the errors" prompt, without more false alarms, has **not** been measured yet. The evaluation set and scripts for that comparison are included.

## What is included

| Path | What it is |
|---|---|
| `skills/drm-audit/` | **Audit mode.** Reviews someone else's text (an AI answer, report, or conversation) and produces an evidence ledger with exact quotes, support levels, contradictions vs. scope changes, and discriminating tests. Has a short 3–5 line report when nothing material is found. |
| `skills/drm-contract/` | **Answer mode.** Structures the model's own answer: understanding → assumptions → plan → answer → alternatives → limits → next experiment. Uses `[LIMIT]`, `[SIM]`, `[PARADOX]`, `[PARTNER]` markers only when there is a basis for them. Has a short mode for simple questions. |
| `tests/evaluation_cases.md` | 26 synthetic cases with expected findings and expected absence of findings; 10 are false-positive traps. |
| `tests/scoring_rubric.md` | Five 0–2 dimensions: evidence fidelity, detection, false-positive restraint, calibration, actionability. |
| `eval/` | Scripts to run both methods, build a blinded review pack, and aggregate scores. See `eval/README.md`. |
| `examples/` | A synthetic self-report dialogue and a sample audit report. |

## What it looks for
- Conclusions stronger than the evidence ("proves", "will", "all users", "cures").
- Causal claims based only on sequence or correlation.
- Evidence that covers a different population, metric, or scope than the claim.
- Precise numbers without a source or method.
- Claims of verification that the context shows did not happen.
- Apparent contradictions, separated from changes in scope, time, or definition.
- Ambiguous key terms that change the conclusion.

It is also meant to leave sound text alone: when the author has already stated limits or the evidence supports the claim, the expected output is a short "no material issues" report.

## What it does not do
- It does not verify facts against the world unless sources or a separate research tool are supplied.
- It does not access model internals. Self-reports (including `[SIM]`) are treated as text, not as insight into mechanisms.
- It does not establish or rule out consciousness, feelings, or intentions from text.
- It does not guarantee fewer errors in any model's output.
- It has not been shown to outperform a baseline prompt.

## Install

### Claude Code
Copy one or both skill directories into your project's `.claude/skills/`:

```text
your-project/.claude/skills/drm-audit/SKILL.md
your-project/.claude/skills/drm-contract/SKILL.md
```

### Other agents
Skill discovery conventions vary by tool and version. Copy the `SKILL.md` files into the skill directory your agent documents and adapt the frontmatter if needed.

## Use
- **Audit:** ask the agent to audit a report or conversation with `drm-audit`, and state the question you want answered (for example, "Does this backtest memo support its conclusion?"). For long material, say which part to review.
- **Contract:** ask the agent to answer using `drm-contract`. Simple questions get the short mode automatically.

## Evaluation
The plan is to compare `drm-audit` with the plain prompt "Analyze this text for errors and unsupported claims." on the fixed case set, with blinded scoring and traps reported separately. See `eval/README.md` for the workflow. No results are reported here because none have been produced yet.

## Packaging
`python build/pack.py` writes a local ZIP to `dist/`. It does not publish anything.

## License
See `LICENSE`.
