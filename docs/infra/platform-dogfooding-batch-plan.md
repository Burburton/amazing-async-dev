# Platform Dogfooding Batch Plan

## Metadata

- **Document Type**: `dogfooding plan / platform validation batch / execution program`
- **Status**: `Proposed`
- **Owner**: `async-dev`
- **Scope**: `post-078 platform validation`
- **Purpose**: `Validate the integrated async-dev platform across real feature work before expanding major new capabilities`

---

## 1. Purpose

The platform now includes a substantial integrated chain:

- execution kernel
- verification / closeout / recovery
- observer foundation
- Recovery Console
- acceptance subsystem
- acceptance CLI/mainflow
- acceptance × Recovery Console integration

At this stage, the highest-value next step is **not** immediate expansion into many new features.  
The highest-value step is to validate whether the platform behaves well as a whole when used on real work.

This document defines a **Platform Dogfooding Batch Plan** to run a focused set of real features through the platform and evaluate whether the platform is:

- usable,
- trustworthy,
- coherent,
- appropriately strict,
- low-friction for the operator,
- ready for the next productization step.

---

## 2. Objective

Use async-dev itself to execute a batch of realistic features and evaluate the entire platform chain end-to-end.

The batch should validate:

1. normal execution flow,
2. verification and closeout behavior,
3. observer usefulness,
4. recovery usefulness,
5. acceptance trigger and loop behavior,
6. acceptance × Recovery Console integration,
7. artifact/evidence usability,
8. overall operator clarity.

The goal is to answer:

> Does async-dev now work like a real integrated execution platform in practice, not just in feature specs and isolated tests?

---

## 3. What This Batch Is Testing

This batch is not just testing whether one subsystem works. It is testing whether the **whole platform feels operationally coherent**.

Specifically, the batch should test:

- execution reliability
- state truthfulness
- operator experience
- recovery ergonomics
- acceptance value
- evidence discoverability
- system coherence across multiple feature types

---

## 4. Batch Design Principles

### 4.1 Use Real Features, Not Synthetic Toy Tasks

The batch should use realistic platform-relevant work so that problems surface naturally.

### 4.2 Cover Different Feature Categories

Different feature types stress different platform layers.

### 4.3 Include At Least One Failure/Recovery Case

A batch that only uses happy-path work does not validate the platform deeply enough.

### 4.4 Focus on Platform Learning, Not Just Task Completion

The main output is insight into where the platform is strong and where it still feels awkward.

### 4.5 Keep the Batch Finite

This should be a bounded pilot batch, not an open-ended forever test.

---

## 5. Recommended Batch Composition

Run a batch of **4 to 6 real features** across the following categories.

## Category A — Frontend / Operator Surface Feature
Examples:
- Recovery Console refinement
- operator layout improvement
- acceptance state display improvement
- status visualization change

### Why Include It
This stresses:
- frontend verification
- operator-facing UX
- closeout and acceptance UI paths

## Category B — CLI / Runtime / Orchestration Feature
Examples:
- CLI behavior adjustment
- runtime policy update
- observer logic refinement
- command target resolution enhancement

### Why Include It
This stresses:
- execution kernel
- artifact truth
- non-UI verification
- completion gating logic

## Category C — Acceptance / Recovery / Cross-Layer Feature
Examples:
- acceptance artifact placement hardening
- recovery item classification refinement
- observer-to-console mapping improvement

### Why Include It
This stresses:
- cross-layer coherence
- operator surface + kernel integration
- evidence and state consistency

## Category D — Documentation / Policy / Platform Feature
Examples:
- platform docs/status rollup
- policy wording clarification
- canonical object/flow model cleanup

### Why Include It
This stresses:
- non-code features
- acceptance policy realism
- documentation/operator coherence

## Category E — Deliberately Imperfect Feature
This feature should be chosen or executed in a way that intentionally causes:
- acceptance failure,
- recovery path use,
- or observer/re-acceptance behavior.

### Why Include It
This validates:
- non-happy paths
- recovery loop
- operator usability under failure

---

## 6. Suggested Batch Size

Recommended batch size:

- **minimum**: 4 features
- **preferred**: 5 features
- **maximum for one round**: 6 features

This is enough coverage to reveal recurring platform issues without making the batch too diffuse.

---

## 7. Required Scenarios Across the Batch

Across the whole batch, the platform must encounter and be evaluated against these scenarios.

### Scenario 1 — Normal Happy Path
Execution completes, acceptance passes, and completion proceeds cleanly.

### Scenario 2 — Verification / Closeout Sensitivity
A feature stresses verification, closeout, or state timing.

### Scenario 3 — Observer-Relevant Condition
A feature produces state the observer should detect or classify meaningfully.

### Scenario 4 — Recovery Needed
At least one feature should enter a meaningful recovery state.

### Scenario 5 — Acceptance Failure Then Re-Acceptance
At least one feature should fail acceptance first, then be fixed and re-accepted.

### Scenario 6 — Operator Inspection Path
At least one feature should require the operator to use CLI and/or Recovery Console to inspect and act.

### Scenario 7 — Evidence / Artifact Navigation
At least one feature should force inspection of generated artifacts to evaluate whether evidence is easy to find and understand.

---

## 8. Per-Feature Execution Checklist

For each feature in the batch, record the following.

### A. Feature Setup
- feature ID / title
- category
- expected platform layer stressed
- expected acceptance policy relevance

### B. Execution
- did execution start cleanly?
- did it produce expected `ExecutionResult`?
- did verification/closeout behave correctly?

### C. Observer
- did the observer produce anything useful?
- if yes, was it timely and relevant?
- if no, should it have?

### D. Recovery
- did the feature require recovery?
- if yes, was the recovery path understandable?
- was the Recovery Console helpful?

### E. Acceptance
- did acceptance trigger correctly?
- was acceptance result useful?
- did it block completion correctly?
- did retry/re-acceptance work if needed?

### F. Artifacts / Evidence
- were relevant artifacts easy to find?
- did the evidence feel coherent?
- was artifact placement intuitive?

### G. Operator Experience
- did the operator understand what was happening?
- what required too much manual investigation?
- what felt smooth?
- what felt awkward?

### H. Outcome
- pass cleanly
- pass after recovery
- pass after re-acceptance
- blocked / confusing / failed
- suggested improvements

---

## 9. Batch Evaluation Dimensions

For each feature and for the batch overall, score or qualitatively assess the platform on these dimensions.

### 9.1 Execution Reliability
- did the system reliably execute and close out work?

### 9.2 Verification / Closeout Trust
- did state truth align with actual behavior?

### 9.3 Observer Usefulness
- did the observer add signal rather than noise?

### 9.4 Recovery Usability
- was it easy to understand and act on recovery situations?

### 9.5 Acceptance Value
- did acceptance improve trust?
- did it generate useful remediation?

### 9.6 Operator Clarity
- did the platform make current state and next action clear?

### 9.7 Artifact / Evidence Coherence
- were outputs placed and linked in a way that supports practical use?

### 9.8 Platform Cohesion
- did the system feel like one platform or several adjacent subsystems?

---

## 10. Issues to Explicitly Watch For

The batch should actively watch for these recurring platform issues.

### Execution-Level Issues
- feature appears complete but state is ambiguous
- closeout stalls or looks complete when it is not
- verification output does not match platform state

### Observer-Level Issues
- observer misses meaningful problems
- observer produces noisy or unhelpful findings
- observer and console tell conflicting stories

### Recovery-Level Issues
- recovery classification unclear
- remediation guidance weak
- too much context switching to act

### Acceptance-Level Issues
- acceptance triggers too early or too late
- failed criteria too vague
- retry/re-acceptance path awkward
- completion blocking feels confusing

### Artifact-Level Issues
- relevant artifacts too hard to find
- evidence spread across too many locations
- latest truth not obvious

### Operator-Level Issues
- too many commands or unclear entrypoints
- Recovery Console missing crucial context
- platform still requires too much manual spelunking

---

## 11. Required Batch Outputs

At the end of the batch, produce the following outputs.

### 11.1 Per-Feature Summary
For each feature:
- category
- final outcome
- key platform observations
- issues found
- suggested follow-up

### 11.2 Cross-Batch Issue Summary
Group issues into buckets such as:
- execution kernel
- observer
- recovery console
- acceptance
- artifacts/evidence
- docs/operator flow

### 11.3 Platform Readiness Assessment
A concise assessment of:
- what feels stable enough now
- what still feels alpha/rough
- what should be improved next
- whether the platform is ready for broader dogfooding or external demonstration

### 11.4 Recommended Next Feature Bucket
At the end of the batch, classify the next highest-value work as one of:

- **A. Artifact/Evidence Rollup**
- **B. Operator Home / Platform Overview**
- **C. Docs / Platform Rollup**
- **D. Recovery / Acceptance UX refinement**
- **E. No major new feature needed yet**

---

## 12. Suggested Reporting Template

Use a short summary like this for each feature.

### Batch Feature Report
- **Feature**:
- **Category**:
- **Execution Outcome**:
- **Verification / Closeout Notes**:
- **Observer Notes**:
- **Recovery Notes**:
- **Acceptance Notes**:
- **Artifacts / Evidence Notes**:
- **Operator UX Notes**:
- **Final Assessment**:
- **Suggested Improvement**:

---

## 13. Exit Criteria

The batch can be considered complete when:

1. at least 4 real features have been run,
2. all key platform categories have been exercised,
3. at least one recovery path and one failed acceptance path have been exercised,
4. operator flow has been used in practice,
5. artifact/evidence discoverability has been evaluated,
6. a prioritized next-step decision can be made based on real platform use rather than speculation.

---

## 14. Interpreting the Batch Result

### If the Batch Goes Smoothly
Then the next step should likely be:
- project artifacts and evidence rollup,
- or a small operator overview surface,
- or platform docs/status rollup.

### If the Batch Reveals Mostly UX Friction
Then the next step should likely be:
- Recovery Console refinement,
- acceptance/recovery operator flow refinement,
- CLI/help clarity improvements.

### If the Batch Reveals Mostly Artifact Confusion
Then the next step should likely be:
- canonical project artifacts directory rollup,
- evidence placement unification,
- artifact linking improvements.

### If the Batch Reveals Deeper Kernel Problems
Then the next step should likely be:
- targeted execution/closeout/observer hardening,
- not new operator surfaces.

---

## 15. Summary

The platform now has enough integrated capability that the most valuable next step is practical dogfooding across a bounded batch of real features.

This batch should answer whether async-dev is now:

- operationally coherent,
- trustable,
- operator-friendly,
- evidence-driven,
- and ready for the next productization step.

In short:

> **Use the platform as a platform before expanding it further.**
