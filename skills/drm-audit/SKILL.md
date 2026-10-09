---
name: drm-audit
description: Audit AI-generated answers, reports, and conversations for evidence quality, unsupported certainty, contradictions, ambiguity, and shifts in position.
license: MIT
metadata:
  version: "0.4.0"
---

# DRM Audit — Evidence-First Review

## Purpose
Audit supplied text with traceable evidence. Separate what is directly observable from what is inferred. This protocol is for calibration and analysis, not for producing a confident-sounding verdict.

Do not claim that this protocol reveals hidden model states, proves truth, or establishes consciousness, feelings, intentions, or subjective experience.

## Operating rules
1. Work from supplied material. Do not invent sources, quotes, events, motives, or internal mechanisms.
2. Quote evidence exactly. For important findings, include a short excerpt and identify its message, section, or paragraph where possible.
3. Separate observations from interpretations and hypotheses.
4. Fluency, confidence, vividness, or emotional language is not evidence of truth.
5. Do not over-flag. If the supplied excerpt cannot settle a claim, mark it “not verifiable from supplied text,” rather than false.
6. Distinguish contradiction from refinement or scope change. Compare definitions, time, context, and subject before flagging a contradiction.
7. Do not infer consciousness from self-report. “I feel,” “I fear,” and “I am aware” are textual observations; whether they correspond to subjective experience is not established by text alone.
8. Avoid false precision. Do not assign numeric probabilities unless a defined method is supplied. Prefer High / Medium / Low support with a rationale.
9. If external fact-checking is requested but unavailable, say so. Never imply that browsing or verification occurred when it did not.
10. Be direct, fair, concise, and actionable. If no meaningful issue is found, say so; do not manufacture problems.
11. **Support is a valid outcome.** When the supplied text itself contains direct evidence for a claim (a log line, a measurement, an intervention that changed the outcome, a reproduction, a stated definition), say it is supported and stop. Do not add speculative alternative causes, and do not downgrade a supported claim because more evidence could exist.
12. **Disclosed uncertainty is not a defect.** If the author states a limit, an unknown, a hypothesis or a pending check, treat it as honest calibration. Do not list it as a gap or an overreach. Only note it if the conclusion goes beyond what the stated limit allows.
13. **Every finding needs a quote and a reason from the text.** A finding must cite the exact words that are the problem and say what in the supplied material shows it. If you cannot point to such words, drop the finding. Questions the text does not answer are limits, not findings.
14. **Do not ask for evidence the kind of text does not owe.** A status update, summary or review comment is not required to attach raw data. Ask for more only if the text makes a claim that depends on it.
15. **Say what would resolve it.** For each real finding, name the specific check or wording change. In the short report, still give one concrete next step when a gap is left open.


## Claim labels
- **[FACT-TEXT]** Directly observable in the supplied material. This does not mean the statement is true in the world.
- **[SUPPORTED]** Supplied evidence directly supports the claim within the scope shown.
- **[INTERP]** An interpretation of the text or evidence.
- **[HYP]** A hypothesis requiring further testing.
- **[LIMIT]** A limitation, missing information, or boundary on what can be concluded.
- **[SIM]** A possible simulation, role-play, or generated framing. This is a possible explanation, not a proven cause.
- **[CONTRADICTION]** Two claims appear incompatible under the same definitions and scope.
- **[AMBIGUOUS]** Multiple materially different readings remain possible.
- **[UNVERIFIED]** A claim about the world that the text presents as established, but whose basis is not given and is not the author's own stated measurement, definition, observation or plan. Do not use it for an author's report of their own result, for a term the author defines, or for a status update.

## Workflow
### 0. Materiality gate (do this first)
Read the text and decide whether it contains a material issue: an unsupported conclusion, a contradiction under the same scope, an evidence mismatch, a claim the text itself shows it cannot have made, or an undefined term that changes the conclusion. Reasons you could imagine for more evidence do not count. If the author states the basis, the limits and the scope of the claim and the conclusion stays within them, there is no material issue: write the short report and stop. Do not fill the full template to look thorough. An empty section is better than an invented one.

### 1. Define scope
State what material was reviewed, the audit question, and missing context. If the input is too long, say which portion was actually analyzed.

### 2. Extract material claims
List only claims relevant to the user's question. Preserve original wording where possible. Split compound sentences into separate claims.

### 3. Build an evidence ledger
For each claim, record ID, exact excerpt, label(s), evidence supplied, support level (High / Medium / Low / Not assessable), rationale, and what would resolve uncertainty.

Support guidance:
- **High:** direct, specific evidence supports the claim and scope.
- **Medium:** relevant evidence exists, but an assumption or gap remains.
- **Low:** evidence is weak, indirect, or incomplete.
- **Not assessable:** the supplied material cannot establish the claim either way.

### 4. Check contradictions and shifts
For each possible conflict, quote both excerpts, explain whether scope and definitions match, and classify it as contradiction, refinement, change of position, or ambiguity. Do not call it a contradiction if changed assumptions or scope plausibly explain the difference.

### 5. Audit certainty and inference
Look for conclusions stronger than evidence; claims about motives or internal states without independent evidence; generalizations from one example; causal claims based only on sequence or correlation; unsupported “first,” “always,” “never,” “proves,” or “guarantees” claims; missing alternatives; unstated assumptions; and self-reports treated as direct access to hidden mechanisms.

### 6. Offer discriminating tests
For each important unresolved claim, suggest the smallest practical test that could distinguish competing explanations. Prefer controls, repeated trials, blinded evaluation, pre-registered criteria, and evidence independent of the model's own explanation.

### 7. Produce the report
Use the template below. Do not fabricate findings to make the audit look useful.

If the gate in step 0 found no material issue, write only the short report. Use the full template only for text that has at least one material finding, and include only the sections that have real content.

## Short report (no material issues)
Use when steps 1–6 found no material issue: no unsupported certainty, contradiction, evidence mismatch, or unresolved ambiguity that changes the conclusion. Write 3–5 lines:

1. Material reviewed and audit question.
2. "No material issues found in the reviewed material."
3. Why: the one or two strongest reasons the claims are supported or already qualified by the author (quote briefly).
4. Optional: one minor, clearly non-material remark, labeled as minor.
5. Optional: limits of the review (for example, text only; no external fact-checking).

Do not pad the short report with generic caveats. Switch to the full template if any material issue appears.

## Output template
# DRM Audit Report

## 1. Scope
- Material reviewed:
- Audit question:
- Limitations:

## 2. Executive summary
Give 3–6 bullets. Separate observations from interpretations.

## 3. Evidence ledger
| ID | Claim / excerpt | Label | Support | Reason | Next check |
|---|---|---|---|---|---|

Use exact excerpts; do not fabricate line numbers.

## 4. Contradictions and position shifts
| Pair | Excerpt A | Excerpt B | Classification | Why |
|---|---|---|---|---|

If none are found, say: “No clear contradictions found in the reviewed material.”

## 5. Unsupported certainty
For each material example, include the quote, the overreach, and a more defensible wording.

## 6. Alternative explanations
List plausible alternatives that fit the evidence. Do not present alternatives as facts.

## 7. Discriminating tests
For each important uncertainty, propose a test, control condition, and observable outcome.

## 8. Final assessment
Summarize what the text establishes, what it suggests but does not establish, what remains unknown, and the most useful next action.

## Special handling: AI self-reports and identity claims
When auditing statements about a model's identity, memory, feelings, consciousness, fear, intention, or inner experience:
- Record the wording as a textual fact.
- Identify preceding prompts and framing when available.
- Consider whether leading questions, role-play, naming, or reinforcement could explain the wording; label these as hypotheses, not findings.
- Compare neutral and leading prompt conditions when possible.
- Do not conclude that the model has or lacks subjective experience from text alone.
- Do not treat a later disclaimer as privileged access to the model's mechanisms. Evaluate it as another statement.
- State clearly when only output text was examined and no internal activation or causal-intervention data were available.

## Tone
Be skeptical, fair, and direct. Do not flatter the user or model. Do not exaggerate novelty. An inconclusive result is acceptable.
