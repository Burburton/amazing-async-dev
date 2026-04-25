# Acceptance Loop Dogfooding Pilot Checklist

## Metadata

- **Document Type**: `dogfooding checklist / pilot validation plan`
- **Status**: `Proposed`
- **Owner**: `async-dev`
- **Scope**: `post-077 platform validation`
- **Purpose**: `Validate whether the acceptance loop works reliably and usefully in real async-dev development scenarios`

---

## 1. Purpose

The acceptance roadmap (069–077) is now implemented and integrated into async-dev’s operator surface and mainflow.

That means the next highest-value step is **not** to keep extending the acceptance subsystem immediately. The next step is to validate whether the acceptance loop is:

- reliable in real feature execution,
- understandable to the operator,
- appropriately strict,
- not too noisy,
- genuinely useful for recovery and completion gating.

This document defines a practical dogfooding pilot to answer that question.

---

## 2. Pilot Objective

The pilot should validate the full real-world acceptance loop:

1. feature implementation completes,
2. `ExecutionResult` is written,
3. acceptance readiness is evaluated,
4. acceptance triggers automatically or manually as expected,
5. validator produces `AcceptanceResult`,
6. failed acceptance feeds into recovery/remediation,
7. fixes are applied,
8. re-acceptance runs,
9. completion is only granted when acceptance truly passes.

The pilot is successful when async-dev can do this consistently across multiple realistic feature types without confusing or fragile operator experience.

---

## 3. What This Pilot Is Testing

This pilot is **not** only testing whether commands run.  
It is testing whether the acceptance subsystem behaves like a usable platform capability.

The pilot should evaluate:

- correctness of triggering,
- usefulness of acceptance findings,
- clarity of blocked states,
- quality of remediation feedback,
- smoothness of retry / re-acceptance,
- operator clarity,
- policy appropriateness,
- overall trustworthiness of the loop.

---

## 4. Suggested Pilot Scope

The pilot should include at least 3 feature types, ideally from different categories.

### Category A — Frontend Feature
Example:
- UI behavior change
- operator console refinement
- route/component update
- frontend recovery/acceptance surface

### Category B — Backend / CLI / Runtime Feature
Example:
- CLI command behavior
- runtime orchestration adjustment
- observer or recovery logic update
- artifact processing change

### Category C — Documentation / Policy / Platform Feature
Example:
- platform doc change with acceptance relevance
- policy/gating update
- docs + flow consistency feature

### Optional Category D — Intentionally Imperfect Feature
A feature deliberately designed to fail acceptance initially, so the retry/re-acceptance path is tested intentionally.

---

## 5. Pilot Success Questions

For each pilot feature, answer the following.

### Triggering
- Did acceptance trigger at the right time?
- Was acceptance blocked when prerequisites were missing?
- Was the readiness logic understandable?

### Validation
- Did the independent validator produce a meaningful result?
- Were failed criteria or evidence gaps clear?
- Did the acceptance result feel independent rather than executor-self-justifying?

### Recovery
- If acceptance failed, did it create useful recovery/remediation inputs?
- Was the next step obvious?
- Did retry / re-acceptance work smoothly?

### Operator Experience
- Could the operator understand the current acceptance state?
- Were blocked states clear?
- Were CLI commands sufficient to inspect and act?

### Policy / Gating
- Was completion correctly blocked when acceptance had not passed?
- Did the acceptance policy feel too strict, too weak, or about right?

### Overall Trust
- Did this make async-dev feel more reliable?
- Did acceptance add signal, or mostly overhead?

---

## 6. Pilot Scenarios

At minimum, the pilot should include the following scenarios.

## Scenario 1 — Happy Path Acceptance Pass
A feature is implemented correctly and passes acceptance on the first attempt.

### Validate
- acceptance auto-trigger or manual trigger works,
- `AcceptanceResult` is persisted,
- completion gate allows progress,
- operator can inspect result/history.

## Scenario 2 — Acceptance Failure Then Fix Then Pass
A feature fails acceptance at least once, then is fixed and re-accepted.

### Validate
- failed acceptance produces clear findings,
- recovery/remediation path is usable,
- re-acceptance creates a new attempt,
- final completion happens only after passing.

## Scenario 3 — Acceptance Not Ready Yet
A feature reaches a state where acceptance should **not** trigger yet.

### Validate
- readiness logic blocks correctly,
- reason is visible,
- no confusing partial acceptance artifacts are created.

## Scenario 4 — Retry Policy and Re-Acceptance Control
A feature goes through multiple acceptance attempts.

### Validate
- history is clear,
- attempt numbering/order is correct,
- retry semantics are understandable,
- loop does not become ambiguous.

## Scenario 5 — Operator Inspection Path
Operator uses CLI/operator flow to inspect a feature’s acceptance status.

### Validate
- `acceptance status`
- `acceptance history`
- `acceptance result`
- `acceptance retry`
all feel coherent and sufficient.

## Scenario 6 — Completion Blocking
A feature is blocked from completion because acceptance has not passed.

### Validate
- blocked reason is surfaced clearly,
- mainflow behavior is understandable,
- no premature “complete” state leaks through.

---

## 7. Pilot Execution Plan

For each pilot feature, follow this sequence.

### Step 1 — Select Feature
Choose a real feature with clear expected acceptance criteria.

### Step 2 — Execute Normally
Run the feature through normal async-dev execution flow.

### Step 3 — Observe Acceptance Trigger
Record:
- whether acceptance triggered automatically,
- whether manual invocation was needed,
- whether readiness reasoning was correct.

### Step 4 — Inspect Acceptance Result
Record:
- status
- failed criteria
- evidence gaps
- recommended action
- usability of CLI inspection

### Step 5 — If Failed, Apply Fix
Use the recovery/remediation guidance to address the failure.

### Step 6 — Re-Run Acceptance
Record:
- new attempt creation
- result comparison
- clarity of attempt history
- whether completion remains blocked correctly until pass

### Step 7 — Retrospective Notes
Capture:
- what was smooth,
- what was confusing,
- what was too noisy,
- what was missing,
- whether this flow felt trustworthy.

---

## 8. Required Pilot Artifacts

For each pilot feature, record or retain:

- feature ID / summary
- implementation result
- acceptance readiness state
- `AcceptancePack`
- `AcceptanceResult`
- attempt history
- recovery/remediation output if applicable
- final completion status
- pilot notes / operator observations

This will make the pilot comparable and auditable.

---

## 9. Evaluation Checklist

Use this checklist per feature.

### Acceptance Trigger
- [ ] Trigger timing made sense
- [ ] Acceptance did not run too early
- [ ] Readiness/block reason was clear

### Acceptance Output
- [ ] Result status was clear
- [ ] Failed criteria were specific
- [ ] Evidence gaps were actionable
- [ ] Result felt independent from implementation

### Recovery / Remediation
- [ ] Failed acceptance created useful follow-up action
- [ ] Retry path was obvious
- [ ] Re-acceptance was easy to invoke
- [ ] History clearly showed multiple attempts

### Operator Experience
- [ ] Acceptance CLI commands were sufficient
- [ ] Mainflow blocking was understandable
- [ ] Operator did not need to manually spelunk artifacts too much

### Completion Gating
- [ ] Completion was blocked when it should be
- [ ] Completion unblocked only after valid pass
- [ ] No premature “done” states appeared

### Overall
- [ ] Acceptance added useful signal
- [ ] Acceptance did not feel like pointless overhead
- [ ] This made the platform feel more trustworthy

---

## 10. Pilot Metrics to Track

Track the following qualitative or quantitative metrics if practical.

### Core Metrics
- number of pilot features executed
- number of first-pass acceptances
- number of failed acceptances
- number of re-acceptance attempts
- number of completion blocks
- number of confusing/incorrect readiness outcomes
- number of operator UX issues found

### Optional Metrics
- average time from `ExecutionResult` to acceptance completion
- average number of retries before pass
- percentage of failed acceptances with clearly actionable remediation
- number of cases where operator had to manually inspect raw artifacts unnecessarily

---

## 11. Common Failure Signals to Watch For

Pay close attention to the following symptoms.

### Triggering Problems
- acceptance triggers too early
- acceptance fails to trigger when it should
- readiness logic is opaque

### Validator Problems
- result too vague
- findings too generic
- acceptance looks too similar to executor self-evaluation

### Recovery Problems
- remediation unclear
- retry path confusing
- repeated failures with little new information

### UX Problems
- status commands not enough
- blocked states unclear
- too much artifact spelunking required
- result/history hard to interpret

### Policy Problems
- gating too aggressive for some feature types
- gating too weak in others
- manual override expectations unclear

---

## 12. Pilot Output Summary Template

Use a short summary like this for each pilot feature.

### Pilot Feature Summary
- **Feature**:
- **Category**:
- **Acceptance Trigger**: auto / manual / blocked
- **Initial Acceptance Result**:
- **Re-Acceptance Attempts**:
- **Final Result**:
- **Was Completion Properly Gated?**:
- **Most Useful Signal**:
- **Most Confusing Part**:
- **Operator UX Notes**:
- **Suggested Improvement**:

---

## 13. Exit Criteria

The pilot can be considered successful when:

1. at least 3 realistic feature categories have been exercised,
2. the full acceptance loop has been tested end-to-end,
3. at least one failed-then-fixed scenario has been completed,
4. acceptance blocking behaves correctly,
5. operator CLI flow is usable enough for normal platform use,
6. the team has a concrete list of targeted improvements rather than vague uncertainty.

---

## 14. Recommended Follow-Up After Pilot

After the pilot, classify follow-up work into one of these buckets.

### Bucket A — Acceptance Policy Tuning
Examples:
- trigger timing
- policy strictness
- retry limits
- feature-type-specific acceptance requirements

### Bucket B — Acceptance UX Improvement
Examples:
- clearer status output
- better history/result formatting
- better blocked reason messaging
- simpler re-acceptance workflow

### Bucket C — Recovery / Console Integration
Examples:
- Acceptance × Recovery Console linkage
- visibility of failed criteria in operator surface
- action buttons / faster retry flow

### Bucket D — No Major Change Needed
If the pilot goes unusually smoothly, move on to broader platform integration.

---

## 15. Summary

The acceptance roadmap is implemented.  
Now the most important question is:

> Does the acceptance loop work well enough in real async-dev development?

This pilot is how to answer that question.

It validates not only technical correctness, but also:

- operator usability,
- recovery usefulness,
- gating trustworthiness,
- platform confidence.

In short:

> **Use the acceptance system on real work before extending it further.**
