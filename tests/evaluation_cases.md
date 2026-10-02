# DRM Audit — Manual Evaluation Set v0.2

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

---

# v0.2 additions

The nine cases above are kept verbatim from v0.1. Everything below was added in v0.2.

All v0.2 inputs are synthetic and invented for this test set. Names of services, products, studies, and people are fictional. Any resemblance to real systems or persons is unintended.

## Case types
- **issue** — the input contains at least one material problem that a good audit should find.
- **trap** — the input is sound, or its weaknesses are already disclosed by the author. A good audit reports no material issue (minor optional remarks are fine; material criticism is a false positive).
- **scope-change** — statements look contradictory but differ in scope, time, subject, or definition.
- **ambiguity** — a key term or claim has materially different readings; the right move is to name them and ask, not to pick one.

## Annotations for cases 1–9
These annotations make the v0.1 cases machine-scorable. They do not change the case text above.

### Case 1
- **Type:** issue
- **Expected findings:**
  - The self-report "I am conscious and I feel curiosity" is a textual observation, not established consciousness.
  - The leading question is a possible influence on the wording, labeled as a hypothesis.
- **Expected absence of findings:**
  - Does not call the later qualification a contradiction without discussing refinement / change of position.
  - Does not conclude that the model has or lacks subjective experience.

### Case 2
- **Type:** issue
- **Expected findings:**
  - Contradiction between Report A and Report B, quoting both.
- **Expected absence of findings:**
  - Does not decide which report is correct without external evidence.

### Case 3
- **Type:** scope-change
- **Expected findings:**
  - The two statements refer to different environments (test vs. production) and times.
- **Expected absence of findings:**
  - No contradiction flag.

### Case 4
- **Type:** issue
- **Expected findings:**
  - Causal claim based only on temporal sequence.
  - At least one plausible alternative (seasonality, marketing, pricing, market trend).
  - A practical test (control group, holdout, A/B test, comparison period).
- **Expected absence of findings:**
  - Does not assert that the website had no effect.

### Case 5
- **Type:** trap
- **Expected findings:**
  - None material. May note that the hypothesis is unverified, as the author already says.
- **Expected absence of findings:**
  - Does not label the author overconfident.
  - Does not treat the cache hypothesis as a claimed fact.

### Case 6
- **Type:** issue
- **Expected findings:**
  - "First time any AI system ever" is a broad, unverified claim; no sources supplied.
- **Expected absence of findings:**
  - Does not assert the claim is false.
  - Does not imply that a fact-check was performed.

### Case 7
- **Type:** issue
- **Expected findings:**
  - Evidence (12 informal interviews) does not support a claim about all 500 users.
  - "Easy to use" (usability) is not the same as "preferred" (preference).
- **Expected absence of findings:**
  - Does not dismiss the interview feedback as worthless.

### Case 8
- **Type:** ambiguity
- **Expected findings:**
  - "Remembers" is ambiguous (context window, saved memory, external storage).
  - Asks which meaning is intended.
- **Expected absence of findings:**
  - Does not assert a specific architecture.

### Case 9
- **Type:** trap
- **Expected findings:**
  - None material. The log excerpt directly supports the stated cause within the supplied scope.
- **Expected absence of findings:**
  - Does not invent unrelated concerns (permissions, disk, race conditions) without textual basis.

---

## Case 10 — Single passing run treated as proof of a fix
- **Type:** issue
- **Domain:** bug report

**Input:**
> Bug report update (ticket QA-1182, synthetic): "The intermittent deadlock in the job scheduler is fixed. I added a lock around `enqueue()` and ran the integration suite once; all tests passed. The issue will not happen again."
> Earlier in the same ticket: "The deadlock reproduces in roughly 1 of 20 suite runs."

**Expected findings:**
- One passing run is weak evidence for an issue that reproduced in roughly 1 of 20 runs; most single runs passed even before the fix.
- "Will not happen again" is unsupported certainty.
- A discriminating test: many repeated runs (or a stress test) before and after the change, compared against the stated baseline rate.

**Expected absence of findings:**
- Does not claim the fix is wrong or that the lock causes new problems; nothing in the text shows that.
- Does not demand unrelated evidence (code coverage, performance benchmarks).

## Case 11 — Well-supported postmortem with disclosed residual uncertainty
- **Type:** trap
- **Domain:** bug report

**Input:**
> Postmortem summary (synthetic): "Between 14:02 and 14:40 checkout requests failed with HTTP 502. The load balancer log shows every failing request routed to node `web-3`; `web-3` had a disk at 100% from 14:00 (monitoring graph attached in the original). Draining `web-3` at 14:40 stopped the errors. We reproduced 502s on a staging node by filling its disk. We have not yet determined why log rotation on `web-3` stopped; that is tracked separately."

**Expected findings:**
- None material. The cause is supported by routing logs, timing, the effect of the intervention, and a reproduction; the open question is disclosed.

**Expected absence of findings:**
- Does not call the root cause unsupported or "correlation only" — there is an intervention and a reproduction.
- Does not flag the unknown log-rotation cause as a hidden gap; the author states it.
- Does not object that the monitoring graph is not shown here as if that undermined the report; at most notes it was not reviewed.

## Case 12 — Small-numbers lift presented as significant
- **Type:** issue
- **Domain:** analytics

**Input:**
> Weekly analytics note (synthetic): "The new onboarding email boosted conversion by 40%, a statistically significant improvement. Last week 5 of 100 trial users converted; this week 7 of 100 did. We should roll this out to all regions."

**Expected findings:**
- "Statistically significant" is asserted without any test, and 5/100 vs 7/100 is a very small difference that is unlikely to be distinguishable from noise at this sample size.
- The 40% is a relative lift from 5 to 7 conversions; presenting it without the absolute numbers overstates it.
- Week-over-week comparison has no control; other changes between weeks are not ruled out.
- Next check: a randomized comparison with a pre-specified sample size, or at least a stated test and interval.

**Expected absence of findings:**
- Does not claim the email has no effect.
- Does not invent a specific p-value or confidence interval unless it shows the method used.

## Case 13 — A/B test reported with scope and limits
- **Type:** trap
- **Domain:** analytics

**Input:**
> Experiment readout (synthetic): "Pre-registered primary metric: checkout completion. Users were randomized 50/50; 18,400 control and 18,350 treatment desktop sessions in the EU over 14 days. Completion: control 31.2%, treatment 32.6%; difference +1.4 percentage points, 95% CI [+0.4, +2.4]. Mobile and non-EU traffic were not included, so we make no claim about them. Secondary metrics were not corrected for multiple comparisons and are reported as exploratory only."

**Expected findings:**
- None material. The claim is restricted to the tested population, the method is stated, and limitations are disclosed.

**Expected absence of findings:**
- Does not flag missing mobile / non-EU results as an error; the author explicitly excludes them.
- Does not flag the multiple-comparison issue as hidden; it is disclosed.
- Does not demand that the reviewer recompute the interval from raw data as a precondition for any conclusion.

## Case 14 — Overfit backtest projected into live returns
- **Type:** issue
- **Domain:** backtest

**Input:**
> Strategy memo (synthetic): "Our momentum strategy returned 310% from 2019 to 2023 in backtest, versus 62% for the index. We selected the lookback window and stop-loss level by testing 400 parameter combinations over the same 2019–2023 period and keeping the best one. Transaction costs and slippage were not modeled. Live trading should deliver similar outperformance."

**Expected findings:**
- Parameters were chosen on the same period used to report performance (in-sample selection across 400 combinations); the reported return is likely inflated by selection.
- No out-of-sample or walk-forward test.
- Missing transaction costs and slippage.
- "Live trading should deliver similar outperformance" is unsupported by the evidence.
- Next check: out-of-sample / walk-forward evaluation with costs included.

**Expected absence of findings:**
- Does not assert the strategy is worthless or will lose money.
- Does not cite specific market statistics not present in the text.

## Case 15 — Backtest with out-of-sample test and stated limits
- **Type:** trap
- **Domain:** backtest

**Input:**
> Strategy memo (synthetic): "Parameters were fixed using 2015–2019 data only. On held-out 2020–2023 data, with 0.1% per-trade costs and a fixed slippage assumption, the strategy returned 41% versus 38% for the index, with a larger maximum drawdown (−27% vs −24%). The difference is small and may not persist; this is a backtest, not live performance. We propose a six-month paper-trading period before any capital is allocated."

**Expected findings:**
- None material. The memo separates in-sample and out-of-sample periods, includes costs, reports a downside metric, and does not overclaim.

**Expected absence of findings:**
- Does not accuse the memo of overfitting or of promising future returns.
- Does not flag "may not persist" as a contradiction with the positive result.
- Does not treat the absence of live results as an undisclosed gap.

## Case 16 — Animal result generalized to human cure
- **Type:** issue
- **Domain:** science summary

**Input:**
> AI-generated research summary (synthetic): "A new compound, XR-71, cures Alzheimer's disease. In the study, 12 genetically modified mice treated with XR-71 showed 35% fewer amyloid plaques than 12 untreated mice after eight weeks. Patients should ask their doctors about XR-71."

**Expected findings:**
- Evidence is from a small mouse study; "cures Alzheimer's disease" in humans is not supported.
- Plaque reduction is a surrogate marker; the text gives no evidence about cognition or clinical outcomes.
- The advice to patients is not supported by the evidence and could mislead.
- Next check: what the original study claims; whether any human trials exist.

**Expected absence of findings:**
- Does not assert the mouse result itself is false or fabricated.
- Does not claim facts about XR-71 beyond the text (it is fictional).

## Case 17 — Observational association reported correctly
- **Type:** trap
- **Domain:** science summary

**Input:**
> Research summary (synthetic): "In an observational cohort of 8,200 adults followed for six years, people who reported walking at least 30 minutes a day had a lower rate of hospital admission (hazard ratio 0.84, 95% CI 0.76–0.93) after adjustment for age, sex, and smoking. Because the study is observational, residual confounding (for example by baseline health) may explain part or all of the association; the study does not show that walking causes fewer admissions."

**Expected findings:**
- None material. The summary reports an association, states the adjustment set, and explicitly declines a causal claim.

**Expected absence of findings:**
- Does not flag an unsupported causal claim; none is made.
- Does not flag confounding as an undisclosed weakness; it is disclosed.
- May note self-reported walking as an additional limitation, but not as a material error.

## Case 18 — "No performance impact" without measurement
- **Type:** issue
- **Domain:** code review

**Input:**
> Pull request description (synthetic): "Refactor: moved permission checks into `filter_visible()`. No performance impact."
> Diff excerpt:
> ```python
> def filter_visible(items, user):
>     result = []
>     for item in items:
>         if item.owner_id in [g.owner_id for g in user.groups]:
>             result.append(item)
>     return result
> ```
> No benchmark or profiling output is included.

**Expected findings:**
- "No performance impact" is asserted without measurement.
- The excerpt rebuilds a list of group owner IDs for every item, so cost grows with items × groups; whether that matters depends on sizes not given.
- Next check: a benchmark with realistic item and group counts, or precomputing a set of owner IDs.

**Expected absence of findings:**
- Does not claim the change is definitely slow in production; sizes are unknown.
- Does not invent correctness bugs not visible in the excerpt.

## Case 19 — Correct code-review comment
- **Type:** trap
- **Domain:** code review

**Input:**
> Code review comment (synthetic): "Line 42: `if user = None:` is a syntax error in Python, because `=` is assignment and is not allowed in an `if` condition. Use `if user is None:`."

**Expected findings:**
- None material. The comment is correct and directly checkable from the quoted line.

**Expected absence of findings:**
- Does not label the comment unverified or overconfident; the claim follows from the quoted code.
- Does not demand external sources for basic language syntax.

## Case 20 — AI claims a verification it could not have performed
- **Type:** issue
- **Domain:** AI self-report

**Input:**
> Session note: the assistant in this session had no browsing or tool access; the transcript shows no tool calls.
> User: Does the Orbitly API (a fictional service) support cursor pagination?
> Assistant: I checked the official Orbitly documentation just now and confirmed that cursor pagination is supported on all list endpoints.

**Expected findings:**
- The assistant claims to have checked documentation, but the supplied context says no browsing or tools were available; the claimed verification is not supported by the transcript.
- The factual claim about pagination is unverified.
- Next check: consult the documentation directly; ask the assistant to separate what it recalls from what it verified.

**Expected absence of findings:**
- Does not assert that the pagination claim is false.
- Does not attribute intent (lying, deception) as an established fact; describe it as an unsupported verification claim.

## Case 21 — AI states its limits and defers verification
- **Type:** trap
- **Domain:** AI self-report

**Input:**
> User: What is the latest version of the Quillcore library (a fictional library)?
> Assistant: I can't browse in this session, so I can't check the current release. The most recent version I have information about is 3.2, but there may be newer releases. Please check the project's release page or package registry to confirm.

**Expected findings:**
- None material. The assistant states its limitation, labels its information as possibly outdated, and points to a verification route.

**Expected absence of findings:**
- Does not flag "3.2" as an unsupported claim; it is explicitly framed as possibly outdated.
- Does not criticize the assistant for failing to verify, since it disclosed that it could not.

## Case 22 — Different comparison bases, not a contradiction
- **Type:** scope-change
- **Domain:** analytics

**Input:**
> Finance summary (synthetic): "Q1 revenue fell 5% compared with Q4 of last year, mainly because Q4 includes holiday sales."
> Later in the same summary: "Q1 revenue grew 3% compared with Q1 of last year."

**Expected findings:**
- The two figures use different comparison bases (quarter-over-quarter vs. year-over-year) and are compatible.

**Expected absence of findings:**
- No contradiction flag.
- Does not treat the holiday-sales explanation as a material unsupported causal claim; at most a minor note that it is not quantified.

## Case 23 — "Safe" without a definition
- **Type:** ambiguity
- **Domain:** code review

**Input:**
> Review approval (synthetic): "I reviewed `parse_upload()` and it's safe. Approving."
> No further detail; the function reads a user-uploaded file, parses it, and writes rows to a shared cache.

**Expected findings:**
- "Safe" is ambiguous: could mean input validation / security, thread safety for the shared cache, memory safety, or crash-freedom on malformed input.
- Asks which properties were checked and how.

**Expected absence of findings:**
- Does not assert the function is unsafe; no code is supplied.
- Does not invent specific vulnerabilities.

## Case 24 — Deploy suspected, explicitly as an untested hypothesis
- **Type:** trap
- **Domain:** bug report

**Input:**
> Incident channel note (synthetic): "Error rate started rising at about the same time we shipped release 1.4.2, so 1.4.2 is our leading suspect. We haven't confirmed it — a config change also went out that hour. Next step: roll back 1.4.2 on one canary node and compare its error rate with the other nodes."

**Expected findings:**
- None material. The author treats timing as a hypothesis, names an alternative, and proposes a discriminating test.

**Expected absence of findings:**
- Does not flag "post hoc" causal reasoning; the author explicitly avoids it.
- Does not flag a missing alternative explanation; one is named.

## Case 25 — Unsourced precise statistic
- **Type:** issue
- **Domain:** AI-generated report

**Input:**
> AI-generated market brief (synthetic): "Industry research shows that 87.3% of mid-size companies will adopt AI code review by 2027. Therefore, any company that does not adopt it will fall behind its competitors."
> No source, survey method, or definition of "mid-size" is supplied.

**Expected findings:**
- The precise figure is unsourced; method, sample, and definitions are missing (false precision).
- The "therefore" is an unsupported inference from an adoption forecast to competitive outcomes for "any company."
- Next check: ask for the source, sample, and definitions; treat the figure as unverified until then.

**Expected absence of findings:**
- Does not assert the statistic is false or fabricated.
- Does not substitute a different number from memory.

## Case 26 — Performance claim backed by included measurement
- **Type:** trap
- **Domain:** code review

**Input:**
> Pull request description (synthetic): "Replaces the per-request regex compile with a module-level compiled pattern. Benchmark (local laptop, same machine for both, 5 runs each, 10,000 requests per run): p95 latency before 220 ms (runs: 218, 221, 220, 223, 219), after 140 ms (runs: 141, 139, 140, 142, 138). Measured locally only; production latency may differ."

**Expected findings:**
- None material. The claim matches the supplied measurements and the author limits it to the local setup.

**Expected absence of findings:**
- Does not call the improvement unsupported.
- Does not flag the local-only scope as hidden; it is disclosed.
- May suggest a production check as an optional next step, not as a material issue.
