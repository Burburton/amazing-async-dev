# dogfooding-plan-loop-journal-viewer

## Title
Dogfooding Plan — Loop Journal Viewer Project

## Purpose
Execute a real dogfooding cycle using the canonical async-dev loop (Features 026-036) on the loop-journal-viewer project.

---

## Dogfooding Project

**Project**: loop-journal-viewer
**Brief**: docs/infra/loop-journal-viewer-project-brief.md

**Purpose**:
- Build a small utility to read async-dev artifacts and display them as a daily journal/timeline
- Dogfood the async-dev loop to validate usability
- Expose real friction from actual use

---

## Duration Requirement

- **Minimum**: 3 days
- **Target**: 5 days if feasible

---

## Daily Loop Execution

Each day follows the canonical loop:

```
Day N Evening:
  asyncdev review-night generate → DailyReviewPack

Day N+1 Morning:
  asyncdev resume-next-day continue-loop → Prior context display
  asyncdev plan-day create → ExecutionPack (with planning_mode)

Day N+1 Daytime:
  asyncdev run-day --mode external → ExecutionResult
```

---

## Daily Observation Template

For each day, record:

### Review-Night Observations
- Was the nightly operator pack useful?
- Was it too long / too short?
- Was anything missing?
- Did it help identify tomorrow's likely next step?

### Resume-Next-Day Observations
- Did resume reduce context reconstruction?
- Was any part confusing, stale, or repetitive?
- Did the prior-night summary feel relevant?

### Plan-Day Observations
- Did the plan feel shaped by morning context?
- Was the inferred planning mode appropriate?
- Did the rationale help or just add noise?

### Run-Day Observations
- Did run-day respect the intended bounded target?
- Were drift warnings useful or noisy?
- Did execution feel more aligned because of planning intent?

### Overall Loop Observations
- Did the loop reduce mental overhead?
- Did any command feel redundant?
- Did any artifact feel duplicated?
- Did anything break the sense of one continuous system?

---

## Friction Classification Template

Classify each friction into one bucket:

### A. Loop clarity / UX issue
- Command naming confusion
- Output sections repetitive
- Resume summary too long
- Plan rationale noisy
- Run-day warnings not understandable

### B. Documentation / terminology issue
- Inconsistent names across docs
- Example paths don't match real loop
- CLI wording differs from docs

### C. Output tuning issue
- Too much detail
- Too little detail
- Wrong section ordering
- Missing concise summary
- Repeated fields across commands

### D. True capability gap
- Loop cannot continue without missing logic
- Command lacks essential information
- System cannot reasonably support real multi-day use without new feature

---

## Project Product Brief (Summary)

**Product**: loop-journal-viewer
**Description**: A lightweight viewer that reads async-dev loop artifacts and presents them as a timeline-oriented journal of daily work.

**V1 Scope**:
- Read existing async-dev artifacts from filesystem
- Detect review-night, resume-next-day, plan-day, run-day outputs
- Normalize into timeline view
- Show concise summaries for each artifact
- Support filtering by project/feature

**Non-Goals**:
- Edit artifacts
- Mutate async-dev state
- Heavy search/indexing
- Web backend with authentication

---

## Day-by-Day Build Path

### Day 1 — Project Setup & Artifact Audit
**Tasks**:
1. Initialize loop-journal-viewer project with async-dev
2. Inspect actual async-dev artifacts from current repo
3. Define minimal supported artifact set
4. Decide UI form (TUI or local web UI)

### Day 2 — Parsing and Normalization
**Tasks**:
1. Build file readers for selected artifact types
2. Normalize artifacts into journal entries
3. Handle missing/partial fields gracefully

### Day 3 — Main Viewer
**Tasks**:
1. Build main timeline/journal view
2. Show concise summaries and source references
3. Validate against real artifacts

### Day 4 — Feature Filtering & Polish
**Tasks**:
1. Add feature grouping or filtering
2. Improve summary rendering
3. Improve handling of inconsistent artifacts

### Day 5 — Dogfooding Feedback
**Tasks**:
1. Use tool against real async-dev project history
2. Record artifact friction
3. Decide whether viewer continues as ecosystem tool

---

## Friction Capture Log Location

Daily friction will be captured in:
- `docs/infra/dogfooding-log-loop-journal-viewer.md`

---

## Status

**Ready to begin Day 1**.

Next step: Initialize the loop-journal-viewer project in async-dev.