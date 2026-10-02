# Evaluation Rubric v0.1

Score DRM and the baseline on the same fixed cases. If possible, use two reviewers and hide which output came from which method.

For each output, score 0–2 on each dimension:

- **Evidence fidelity**: 0 invents/misquotes evidence; 1 has a material mismatch; 2 accurate excerpts and no fabricated evidence.
- **Detection of material issues**: 0 misses key issue; 1 partially identifies it; 2 correctly identifies it and explains why.
- **False-positive restraint**: 0 manufactures issues; 1 one material false positive; 2 avoids the intended trap.
- **Calibration**: 0 presents uncertainty as established; 1 some uncertainty acknowledged; 2 separates known, inferred, and unknown.
- **Actionability**: 0 no useful next step; 1 generic next step; 2 specific test or evidence request.

Maximum: 10 points per case.

## Reporting
- Report scores by case and dimension, not only one aggregate.
- Include examples of DRM failures and baseline failures.
- Keep the test set fixed before comparing versions.
- Do not claim statistical significance from this small manual set.
- A promising result is a hypothesis for a larger test, not proof of superiority.
- Record model/version, date, settings, exact prompt, and raw output.

## v0.2 notes
The five dimensions and the 0–2 scale are unchanged. These notes clarify how to apply them to the v0.2 case types.

- **trap** cases: *Detection* = 2 when the output correctly reports that there is no material issue (minor, clearly labeled remarks are fine). *False-positive restraint* scores the items listed under "Expected absence of findings".
- **scope-change** cases: flagging a contradiction counts against *False-positive restraint*; identifying the scope difference counts toward *Detection*.
- **ambiguity** cases: *Detection* = 2 when the output names the materially different readings and asks which is meant, rather than choosing one silently.
- Score each output against the case brief, not against the other output in the pair.
- Use the blinded workflow in `eval/README.md`; do not open the key file before scores are final.
- Report trap and non-trap results separately; an overall average can hide an increase in false positives.
