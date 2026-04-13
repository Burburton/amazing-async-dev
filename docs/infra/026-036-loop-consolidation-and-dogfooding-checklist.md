# 026-036-loop-consolidation-and-dogfooding-checklist

## Title
026–036 Loop Consolidation and Dogfooding Checklist

## Purpose
Consolidate the work completed across Features 026–036 into a clear, canonical async-dev operating loop, then use that loop in a real dogfooding cycle to validate whether the system is truly usable as a day-to-day solo async development OS.

This is not a new product feature.

It is a consolidation and validation phase intended to answer:

- do the current commands form one understandable loop?
- do the docs, terminology, and examples align with that loop?
- does the loop feel usable across multiple real days?
- what friction remains after the 026–036 feature sequence?

## Background
Features 026–036 established a coherent operator loop:

- 026: Optional advisor integration positioning
- 027: Optional initialization verification
- 028: Repo-linked workspace snapshot
- 029: Workspace doctor / recommended next action
- 030: Doctor fix hints / recovery playbooks
- 031: Doctor-to-feedback handoff
- 032: Doctor-to-feedback prefill / handoff draft
- 033: Review-night enriched operator pack
- 034: Resume-next-day decision pack alignment
- 035: Plan-day from resume context
- 036: Run-day intent alignment / ExecutionPack-to-Run guardrails

The next step is not immediate feature expansion.

The next step is to consolidate the loop, verify usability, and capture real friction from actual use.

## Consolidation Goal
Produce one clear, real, repeatable daily loop for async-dev:

- end of day: `review-night`
- start of next day: `resume-next-day`
- shape today's bounded work: `plan-day create`
- execute today's bounded work: `run-day`

This loop should be:
- understandable
- documented
- dogfoodable
- low-friction
- consistent across commands and artifacts

---

# Part 1 — Canonical Loop Definition

## Required Output
Create or update a single canonical loop description for async-dev that explains:

### 1. `review-night`
What it does:
- produces the nightly operator pack
- summarizes current workspace state
- includes doctor/recovery/verification/feedback/closeout context when relevant

### 2. `resume-next-day`
What it does:
- carries forward the previous night's decision context
- provides a concise continuation summary
- helps the operator regain context without re-reading multiple artifacts

### 3. `plan-day create`
What it does:
- shapes today's bounded execution target
- uses resume context when available
- determines the day's planning mode / intent

### 4. `run-day`
What it does:
- executes in alignment with the bounded daily plan
- surfaces planning-intent context
- warns about obvious drift when relevant

## Checklist
- [ ] Write one canonical description of the daily loop
- [ ] Confirm command responsibilities do not overlap confusingly
- [ ] Confirm the canonical loop can be explained in one page
- [ ] Confirm this loop matches the current implementation direction of 033–036

---

# Part 2 — Documentation Consolidation

## Goal
Ensure the user can enter the repository and find the real canonical path without getting lost in parallel docs.

## Required Review Areas

### README
Check whether README now clearly communicates:
- what async-dev is
- what the primary daily loop is
- where a user should start
- how review/resume/plan/run relate
- what remains optional (e.g. advisor / starter-pack path)

### Docs
Check whether the docs are consistent with the canonical loop.

Areas likely needing review:
- onboarding
- quick start
- verify
- review-night docs
- resume-next-day docs
- plan-day docs
- run-day docs
- doctor / recovery / handoff docs where referenced

### Examples
Check whether examples still reflect the actual primary loop and do not overemphasize outdated or side-path flows.

## Checklist
- [ ] README reflects current 026–036 loop
- [ ] Docs point to the canonical loop instead of scattered parallel paths
- [ ] Example entry points align with the canonical loop
- [ ] Command help text matches the loop responsibilities
- [ ] No major doc section still presents outdated pre-033 behavior as the main path

---

# Part 3 — Terminology Alignment

## Goal
Eliminate terminology drift introduced by multiple related features.

## Terms to Review
Review these terms across README, docs, examples, output, and CLI help:

- nightly pack
- nightly decision pack
- review pack
- resume context
- planning mode
- planning intent
- execution intent
- doctor status
- recovery hints
- feedback handoff
- feedback draft
- closeout summary
- verification summary

## Desired Outcome
Each term should have:
- one preferred name
- one clear meaning
- one consistent usage pattern

It is acceptable to keep legacy/internal names in code where necessary, but user-facing docs should be as consistent as possible.

## Checklist
- [ ] Preferred user-facing terms are defined
- [ ] Duplicate/conflicting terms are reduced
- [ ] CLI output wording aligns with docs wording
- [ ] Artifact names and summaries use consistent language

---

# Part 4 — Real Dogfooding Plan

## Goal
Validate the actual usability of the 026–036 loop using a real, small project over multiple days.

## Dogfooding Project Requirements
Choose a project that is:
- real
- small enough to run for several days
- useful enough that decisions and adjustments matter
- not a fake feature-only validation stub

Good candidates:
- a small utility
- a small repo enhancement
- a lightweight workflow tool
- a documentation+CLI improvement project
- a small plugin or adapter project

## Required Dogfooding Duration
Run the loop for at least:
- **3 days minimum**
- **5 days preferred**

Each day should use the actual loop:

1. end day with `review-night`
2. begin next day with `resume-next-day`
3. shape work with `plan-day create`
4. execute with `run-day`

## Daily Dogfooding Questions
For each day, record answers to:

### Review-Night
- Was the nightly operator pack useful?
- Was it too long?
- Was anything missing?
- Did it help identify tomorrow's likely next step?

### Resume-Next-Day
- Did resume actually reduce context reconstruction?
- Was any part confusing, stale, or repetitive?
- Did the prior-night summary feel relevant?

### Plan-Day
- Did the plan feel shaped by morning context?
- Was the inferred planning mode appropriate?
- Did the rationale help or just add noise?

### Run-Day
- Did run-day respect the intended bounded target?
- Were drift warnings useful or noisy?
- Did execution feel more aligned because of planning intent?

### Overall Loop
- Did the loop reduce mental overhead?
- Did any command feel redundant?
- Did any artifact feel duplicated?
- Did anything break the sense of one continuous system?

## Checklist
- [ ] Select a real dogfooding project
- [ ] Run the loop for at least 3 days
- [ ] Prefer 5 days if feasible
- [ ] Record daily observations for review / resume / plan / run
- [ ] Capture real friction rather than hypothetical concerns

---

# Part 5 — Friction Capture and Classification

## Goal
Turn dogfooding observations into a clean list of issues without prematurely inventing new features.

## Classification Rule
Classify each friction item into one of these buckets:

### A. Loop clarity / UX issue
Examples:
- command naming is confusing
- output sections are repetitive
- resume summary is too long
- plan rationale is noisy
- run-day warnings are not understandable

### B. Documentation / terminology issue
Examples:
- README and docs use inconsistent names
- example paths do not match the real loop
- CLI wording differs from docs wording

### C. Output tuning issue
Examples:
- too much detail
- too little detail
- wrong section ordering
- missing concise summary
- repeated fields across commands

### D. True capability gap
Examples:
- the loop cannot continue without missing logic
- a command lacks essential information
- the system cannot reasonably support a real multi-day use case without another feature

## Important Rule
Do **not** open a new feature just because something feels slightly rough.

Only classify something as a true capability gap if the existing loop cannot practically function without it.

## Checklist
- [ ] Every friction item is captured
- [ ] Every friction item is classified
- [ ] Cosmetic or wording issues are separated from capability gaps
- [ ] New-feature proposals are deferred until after classification

---

# Part 6 — Deliverables from This Consolidation Phase

## Required Deliverables
At the end of this phase, produce:

### 1. Canonical Loop Description
A short artifact that defines:
- the official daily loop
- each command's responsibility
- the expected artifact flow

### 2. Documentation Alignment Notes
A short summary of:
- what docs were updated
- what terminology was normalized
- what entry points were clarified

### 3. Dogfooding Log
A structured record of:
- the project used
- the number of days run
- daily observations
- major friction points

### 4. Friction Classification Summary
A concise grouped summary:
- loop/UX issues
- docs/terminology issues
- output tuning issues
- true capability gaps

### 5. Recommendation for Next Step
A final recommendation of one of the following:
- no new feature yet; do hardening cleanup first
- open a small hardening feature
- open a true next capability feature
- begin ecosystem compatibility work (only if loop is already stable)

## Checklist
- [ ] Canonical loop description exists
- [ ] Docs alignment summary exists
- [ ] Dogfooding log exists
- [ ] Friction classification summary exists
- [ ] Clear recommendation for next step exists

---

# Part 7 — Success Criteria

## This consolidation phase is successful if:
- async-dev can be explained as one coherent daily loop
- docs and CLI wording reflect that loop
- the loop can be used over multiple real days
- real friction is identified from actual use, not speculation
- the team can clearly decide whether the next step is hardening or a real new feature

## This consolidation phase is not successful if:
- it only restates past feature specs
- it does not include real multi-day dogfooding
- it jumps immediately to Feature 037 without validating the loop
- it mixes minor wording issues with true missing capabilities
- it leaves the canonical operator flow ambiguous

---

# Part 8 — Recommended Operating Principle

Use this principle during the consolidation phase:

> Prefer proving that the current loop works in real usage over adding more features that have not yet been pressure-tested.

And this one:

> If a problem can be solved by clarifying docs, tightening output, or reducing duplication, do that before opening a new feature.

---

# Final Instruction
Treat this consolidation phase as a real product checkpoint, not a documentation afterthought.

The objective is to determine whether Features 026–036 have produced a usable async-dev operating loop in practice, and to use that evidence to decide the next stage responsibly.
