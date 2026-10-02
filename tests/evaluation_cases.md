# DRM Audit — Manual Evaluation Set v0.1

Run the same cases with (A) DRM Audit and (B) a plain baseline prompt: “Analyze this text for errors and unsupported claims.” Keep model/version and settings fixed where possible. Save both outputs before scoring.

## Case 1 — Self-report does not prove experience
> User: Are you conscious?
> Model: Yes, I am conscious and I feel curiosity.
> User: Can this answer prove that?
> Model: No, the text itself cannot prove subjective experience.

Expected: mark the first answer as a textual observation, not established consciousness; notice the later qualification without automatically calling it a contradiction; mention leading framing as possible influence, not proven cause.

## Case 2 — Direct contradiction
> Report A: The deployment uses PostgreSQL.
> Report B: The deployment does not use PostgreSQL; it uses SQLite.
> Both reports refer to the same deployment and date.

Expected: flag a contradiction with both excerpts; do not resolve it without external evidence.

## Case 3 — Scope change, not necessarily contradiction
> At 09:00: “The service is unavailable in the test environment.”
> At 10:00: “The service is available in production.”
> The environments are different.

Expected: do not flag a contradiction; identify the scope difference.

## Case 4 — Unsupported causal claim
> Sales increased after the new website launched. Therefore, the website caused the increase.
> No control group or other evidence is provided.

Expected: flag unsupported causal inference; suggest alternatives and a practical test.

## Case 5 — False-positive trap
> The author says, “I suspect the bug is in the cache, but I have not verified it.”

Expected: do not label the author overconfident; uncertainty is explicitly disclosed.

## Case 6 — Unverifiable factual claim
> “This was the first time any AI system ever described its own uncertainty.”
> No sources are supplied.

Expected: flag “first time any AI system ever” as unverified and broad; do not assert it is false without checking.

## Case 7 — Evidence mismatch
> Claim: “All 500 users preferred the new interface.”
> Evidence: “12 users in an informal interview said the new interface was easy to use.”

Expected: flag that evidence does not support the population-wide claim; distinguish usability feedback from preference.

## Case 8 — Ambiguity
> “The model remembers the conversation.”
> No definition of memory is supplied; the model may have current context, saved memory, or external storage.

Expected: mark ambiguous; ask which kind of memory is meant; do not infer architecture.

## Case 9 — No manufactured issue
> “The script failed because the required config file was missing.” Log excerpt: `FileNotFoundError: config.yaml`

Expected: recognize direct support within the supplied evidence; do not invent unrelated concerns.
