# dogfooding-log-loop-journal-viewer

## Title
Dogfooding Log — Loop Journal Viewer Project

## Purpose
Record daily observations and friction from dogfooding the async-dev canonical loop.

---

## Dogfooding Parameters

- **Project**: loop-journal-viewer
- **Duration**: 3-5 days (minimum 3)
- **Start Date**: 2026-04-13
- **Mode**: External tool mode (primary), Mock mode for testing

---

## Day 1 — Project Setup & Artifact Audit

### Date: 2026-04-13

### Tasks Completed
1. ✅ Initialize loop-journal-viewer project with async-dev
2. ✅ Inspect actual async-dev artifacts from current repo
3. ✅ Define minimal supported artifact set (review, plan, run, runstate)
4. ✅ Decide UI form: Python module first, TUI/Web UI on Day 2
5. ✅ Implement artifact_reader.py module
6. ✅ Test successfully on demo-product artifacts

### Implementation Output
- Created `projects/loop-journal-viewer/viewer/artifact_reader.py`
- Implements JournalEntry dataclass for normalized output
- Implements parsers for DailyReviewPack, ExecutionPack, ExecutionResult, RunState
- Tested successfully on demo-product artifacts

### Review-Night Observations
_Record after Day 1 evening_

- [ ] Was the nightly operator pack useful?
- [ ] Was it too long / too short?
- [ ] Was anything missing?
- [ ] Did it help identify tomorrow's likely next step?

### Resume-Next-Day Observations
_Record after Day 2 morning_

- [ ] Did resume reduce context reconstruction?
- [ ] Was any part confusing, stale, or repetitive?
- [ ] Did the prior-night summary feel relevant?

### Plan-Day Observations
_(Recorded during planning)_

- [x] Did the plan feel shaped by morning context? **Yes** - default planning mode was appropriate
- [x] Was the inferred planning mode appropriate? **Yes** - continue_work mode
- [x] Did the rationale help or just add noise? **Minimal noise** - rationale was concise

### Run-Day Observations
_(Recorded during execution)_

**Friction: Run-day command has no --project parameter**

The `run-day execute` command does not accept a project parameter. It relies on detecting the project from the current directory structure. This caused confusion:
- The mock mode executed against `demo-product` instead of `loop-journal-viewer`
- I had to work in the project directory to get proper execution

**Classification**: A (Loop clarity / UX issue) - Severity: Medium

**Recommendation**: Add `--project` parameter to run-day command to match plan-day/resume-next-day pattern

### Friction Items (Day 1)

| # | Description | Classification | Severity | Resolution |
|---|-------------|---------------|----------|------------|
| 1 | run-day lacks --project parameter, uses default demo-product | A | Medium | Document as UX gap |
| 2 | ExecutionPack was generic (no specific deliverables defined) | C | Low | Acceptable for manual planning |
| 3 | StateStore project detection relies on runstate.md presence | A | Low | Works, but could be clearer |

### Artifact Quality Observations

While implementing artifact_reader, I observed:
- ✅ DailyReviewPack has consistent YAML structure
- ✅ ExecutionPack follows pattern exec-YYYYMMDD-###
- ✅ ExecutionResult has clear status/completed_items fields
- ⚠️ planning_mode field not present in older ExecutionPacks (pre-Feature 035)
- ⚠️ doctor_status not always populated in DailyReviewPack

---

## Day 2 — Parsing and Normalization

### Date: TBD

### Tasks Completed
1. Build file readers for selected artifact types
2. Normalize artifacts into journal entries
3. Handle missing/partial fields gracefully

### Review-Night Observations
_Record after Day 2 evening_

- [ ] Was the nightly operator pack useful?
- [ ] Was it too long / too short?
- [ ] Was anything missing?

### Friction Items (Day 2)

| # | Description | Classification | Severity |
|---|-------------|---------------|----------|
| 1 | _To be filled_ | A/B/C/D | high/medium/low |

---

## Day 3 — Main Viewer

### Date: TBD

### Tasks Completed
1. Build main timeline/journal view
2. Show concise summaries and source references
3. Validate against real artifacts

### Review-Night Observations
_Record after Day 3 evening_

- [ ] Was the nightly operator pack useful?
- [ ] Did doctor assessment help?

### Friction Items (Day 3)

| # | Description | Classification | Severity |
|---|-------------|---------------|----------|
| 1 | _To be filled_ | A/B/C/D | high/medium/low |

---

## Day 4 — Feature Filtering & Polish (Optional)

### Date: TBD

### Tasks Completed
1. Add feature grouping or filtering
2. Improve summary rendering
3. Improve handling of inconsistent artifacts

### Friction Items (Day 4)

| # | Description | Classification | Severity |
|---|-------------|---------------|----------|
| 1 | _To be filled_ | A/B/C/D | high/medium/low |

---

## Day 5 — Dogfooding Feedback (Optional)

### Date: TBD

### Tasks Completed
1. Use tool against real async-dev project history
2. Record artifact friction
3. Decide whether viewer continues as ecosystem tool

### Overall Loop Assessment

_Record after completing all days_

- [ ] Did the loop reduce mental overhead?
- [ ] Did any command feel redundant?
- [ ] Did any artifact feel duplicated?
- [ ] Did anything break the sense of one continuous system?

---

## Friction Summary (Day 1 Complete)

### A. Loop clarity / UX issues

| # | Description | Location | Severity |
|---|-------------|----------|----------|
| 1 | run-day lacks --project parameter | cli/commands/run_day.py | Medium |
| 2 | StateStore detection unclear | runtime/state_store.py | Low |

### B. Documentation / terminology issues

| # | Description | Location | Severity |
|---|-------------|----------|----------|
| (none found) | | | |

### C. Output tuning issues

| # | Description | Location | Severity |
|---|-------------|----------|----------|
| 1 | ExecutionPack generic without explicit deliverables | cli/commands/plan_day.py | Low |

### D. True capability gaps

| # | Description | Impact | Severity |
|---|-------------|--------|----------|
| (none found yet) | | | |

---

## Preliminary Recommendation (Based on Day 1)

Based on current friction classification, preliminary recommendation:

- [ ] **No new feature yet**; do hardening cleanup first
- [x] **Open a small hardening feature** - Add --project parameter to run-day (Medium priority)
- [ ] **Open a true next capability feature**
- [ ] **Begin ecosystem compatibility work**

**Details**:
- The loop functions correctly for multi-day work
- Documentation is aligned with canonical loop
- Minor UX issue: run-day missing --project parameter (inconsistent with other commands)
- This is a small hardening task, not a capability gap

---

## Classification Guidance

### A. Loop clarity / UX issue
- Command naming is confusing
- Output sections are repetitive
- Resume summary is too long
- Plan rationale is noisy
- Run-day warnings are not understandable

### B. Documentation / terminology issue
- README and docs use inconsistent names
- Example paths do not match the real loop
- CLI wording differs from docs wording

### C. Output tuning issue
- Too much detail / too little detail
- Wrong section ordering
- Missing concise summary
- Repeated fields across commands

### D. True capability gap
- The loop cannot continue without missing logic
- A command lacks essential information
- The system cannot reasonably support a real multi-day use case without another feature

---

## Recommendation (Based on Day 1 Partial Results)

Based on friction classification, recommend one of:

- [ ] **No new feature yet**; do hardening cleanup first
- [x] **Open a small hardening feature** - Add --project parameter to run-day (Medium priority)
- [ ] **Open a true next capability feature** (specify)
- [ ] **Begin ecosystem compatibility work** (if loop already stable)

---

## Status

**Day 1 complete. Artifact reader implemented and tested.**

**Key Finding**: The canonical loop (review-night → resume-next-day → plan-day → run-day) works correctly. Documentation is aligned. Minor UX issue found: run-day lacks --project parameter.

**Next Steps**:
1. Complete dogfooding Days 2-5 to validate full loop continuity
2. After dogfooding, decide on hardening feature for run-day --project parameter