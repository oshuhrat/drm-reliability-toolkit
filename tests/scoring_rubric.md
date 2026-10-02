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
