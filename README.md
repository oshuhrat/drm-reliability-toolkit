# DRM Reliability Toolkit

Two free skills (MIT) for AI agents.

| Skill | What it does |
|---|---|
| `skills/drm-audit/` | Audit mode. Reviews someone else's text (an AI answer, report, conversation): checks materiality first, then builds an evidence ledger with exact quotes, or a short "no material issues" report. Helps reduce false alarms and unsupported certainty. |
| `skills/drm-contract/` | Answer mode. Structures the model's own answer: understanding, assumptions, plan, answer, alternatives, limits, next experiment. Markers are used only when there is a basis for them. |

## Install (Claude Code)
Copy the skill folders into `.claude/skills/`:

```text
your-project/.claude/skills/drm-audit/SKILL.md
your-project/.claude/skills/drm-contract/SKILL.md
```

Other agents: copy the `SKILL.md` files into the skill directory your agent documents.

## Use
Ask the agent to audit a report with `drm-audit`, or to answer using `drm-contract`.

## Limits
Does not verify facts against the world, does not access model internals, does not guarantee fewer errors.

## License
MIT. See `LICENSE`.
