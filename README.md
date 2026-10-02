# DRM Reliability Toolkit — v0.1

An evidence-first skill for auditing AI-generated answers and long conversations.

## What it does
- Separates textual observations from interpretations and hypotheses.
- Flags unsupported certainty, contradictions, missing evidence, and shifts in position.
- Produces a structured report with evidence excerpts and limitations.
- Avoids claiming that text alone proves consciousness, emotion, intent, or hidden internal states.

## What it does not do
- It does not access model internals.
- It does not independently verify facts unless sources or a separate research tool are available.
- It does not guarantee fewer hallucinations.
- It does not diagnose consciousness or subjective experience.

## Install

### Claude Code
Copy `skills/drm-audit/` into your project's `.claude/skills/` directory:

```text
your-project/.claude/skills/drm-audit/SKILL.md
```

### Codex and other agents
Skill discovery conventions vary by tool and version. Copy `skills/drm-audit/SKILL.md` into the skill directory documented by your agent. Adapt metadata if required by that tool.

## Use
Ask the agent to audit a conversation or document using the DRM evidence protocol. Provide the text and the question you want answered. For long conversations, specify the relevant time range.

## Evaluation before selling
Run DRM and a plain baseline prompt on the same fixed test set. Compare correctly identified issues, false positives, evidence accuracy, contradiction detection, and calibration. Do not market numerical improvement until measured on a fixed test set.

This is a prototype starter package, not a validated benchmark or a guarantee of improved model reliability.
