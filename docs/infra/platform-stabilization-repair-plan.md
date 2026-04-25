# Platform Stabilization Repair Plan

## Metadata

- **Document Type**: `stabilization repair plan`
- **Status**: `Active`
- **Owner**: `async-dev`
- **Scope**: `platform-level`
- **Based On**: `docs/infra/platform-stabilization-window-freeze-plan.md`
- **Started**: `2026-04-25`
- **Branch**: `platform/foundation`

---

## 1. Purpose

Per the Platform Stabilization Window Freeze Plan, this document tracks:
- Pre-existing issues requiring repair during stabilization
- Evidence truth gaps to be hardened
- Operator friction points discovered through dogfooding
- Deferred ideas for post-stabilization consideration

The stabilization window shifts from **building new mechanisms** to **repairing and hardening existing ones**.

---

## 2. Issue Categories

Per freeze plan Section 12, repair work falls into these buckets:

| Bucket | Description | Allowed During Freeze? |
|--------|-------------|------------------------|
| A | Real Feature Delivery | Yes |
| B | Platform Blocker Fix | Yes |
| C | Evidence/Artifact Truth Fix | Yes |
| D | Narrow Operator UX Fix | Yes |
| E | Minimal Documentation Clarification | Yes |
| F | New Major Mechanism | **NO** - Deferred |

---

## 3. Bucket B - Platform Blocker Fixes

### B-001: Pre-existing Test Failures (CLI new-feature)

| Field | Value |
|-------|-------|
| Issue ID | B-001 |
| Severity | Medium |
| Affected Tests | `test_cli_new_feature.py::TestNewFeatureCreate::test_creates_feature_directory`, `test_creates_feature_spec_yaml`, `TestNewFeatureList::test_lists_features` |
| Root Cause | Feature spec path routing change (docs/features/{id}/) not reflected in CLI |
| Evidence | Tests fail on directory existence check |
| Fix Scope | Update CLI to use correct feature spec path via artifact_router |
| Status | Pending |

### B-002: Pre-existing Test Failures (Reacceptance Trigger)

| Field | Value |
|-------|-------|
| Issue ID | B-002 |
| Severity | Low |
| Affected Tests | `test_reacceptance_loop.py::TestTriggerReacceptance::test_trigger_reacceptance_creates_result`, `test_trigger_reacceptance_updates_history` |
| Root Cause | `trigger_reacceptance()` returns None instead of creating result |
| Evidence | `assert result is not None` fails |
| Fix Scope | Debug trigger_reacceptance function, fix result creation |
| Status | Pending |

---

## 4. Bucket C - Evidence/Artifact Truth Fixes

### C-001: Observer Findings Not Persisted

| Field | Value |
|-------|-------|
| Issue ID | C-001 |
| Severity | High |
| Component | `runtime/execution_observer.py` |
| Root Cause | ObserverFinding objects are ephemeral, never written to disk |
| Spec Violation | Feature 067 Section 6.7: "Observer findings must be persisted" |
| Impact | Findings disappear after each run, Recovery Console re-runs observer every time |
| Fix Scope | Add `save_observer_findings()` function, create `observer-findings/` directory |
| Status | Pending |

### C-002: Scattered Latest-Truth Resolution (Partially Fixed)

| Field | Value |
|-------|-------|
| Issue ID | C-002 |
| Severity | Medium |
| Original Pattern | Latest resolution scattered across ~10 files with different methods |
| Fix Applied | Feature 079 created `LatestTruthResolver` consolidating patterns |
| Remaining | CLI consumers still use old patterns (workspace_snapshot, summary, recovery_data_adapter) |
| Fix Scope | Update CLI consumers to use `LatestTruthResolver` |
| Status | Partial - Need consumer updates |

### C-003: Acceptance Artifact Types Missing from ArtifactType (Fixed)

| Field | Value |
|-------|-------|
| Issue ID | C-003 |
| Severity | Medium |
| Original State | ArtifactType enum lacked ACCEPTANCE_PACK, ACCEPTANCE_RESULT, etc. |
| Fix Applied | Feature 079 added 6 new types |
| Status | Fixed |

### C-004: Acceptance-Recovery Directory Inconsistency (Fixed)

| Field | Value |
|-------|-------|
| Issue ID | C-004 |
| Severity | High |
| Original State | `acceptance_recovery_adapter.py` used `acceptance-recovery-packs` but `acceptance_recovery.py` creates `acceptance-recovery` |
| Fix Applied | Feature 079 changed adapter to use correct directory |
| Status | Fixed |

### C-005: Observer Findings Not Discoverable (Persistence Gap)

| Field | Value |
|-------|-------|
| Issue ID | C-005 |
| Severity | High |
| Component | `runtime/execution_observer.py`, artifact hierarchy |
| Root Cause | Observer findings are ephemeral - no artifact to find, no directory placement |
| Evidence | recovery_data_adapter.py consumes findings directly from function call, not from persisted file |
| Impact | Evidence disappears; no audit trail; cannot query past findings |
| Fix Scope | Create `observer-findings/{observation_id}.md` persistence; add cumulative findings tracking |
| Status | Pending |

### C-006: Missing Latest Pointer Files

| Field | Value |
|-------|-------|
| Issue ID | C-006 |
| Severity | Medium |
| Issue | No canonical pointer files exist to identify latest truth without glob/scanning |
| Evidence | Feature 079 Section 6.2 specifies latest-pointers; current requires glob + mtime every time |
| Fix Scope | Create `latest-*.md` or symlink pointer files after each execution/acceptance result |
| Status | Pending |

### C-007: Artifact Router Missing Observer Path Function

| Field | Value |
|-------|-------|
| Issue ID | C-007 |
| Severity | Medium |
| Issue | OBSERVER_FINDINGS type defined but no path routing function exists |
| Evidence | Line 43 defines type, but no `get_observer_findings_path()` like other artifacts |
| Fix Scope | Add observer path functions to artifact_router.py |
| Status | Pending |

### C-008: Evidence Summary Not Auto-Updated

| Field | Value |
|-------|-------|
| Issue ID | C-008 |
| Severity | Medium |
| Issue | Evidence summary can become stale - not auto-generated after key events |
| Evidence | Save functions exist but no hook in execution/acceptance completion |
| Fix Scope | Auto-update evidence summary after: execution result, acceptance result, observer run |
| Status | Pending |

### C-009: Scattered Latest-Truth Resolution (Legacy Patterns)

| Field | Value |
|-------|-------|
| Issue ID | C-009 |
| Severity | Medium |
| Original State | Multiple inconsistent approaches to finding "latest" artifacts |
| Fix Applied | Feature 079 LatestTruthResolver consolidates patterns |
| Remaining | Legacy patterns still in workspace_snapshot, recovery_data_adapter, decision_sync |
| Fix Scope | Deprecate scattered patterns, route all through LatestTruthResolver |
| Status | Partial - Need consumer migration |

---

## 5. Bucket D - Operator UX Fixes

### D-001: Recovery Show Execution ID Parsing (Fixed)

| Field | Value |
|-------|-------|
| Issue ID | D-001 |
| Severity | High |
| Original State | Naive hyphen-splitting failed for IDs like `exec-acceptance-pilot-001-001-backend-cli-test` |
| Fix Applied | Changed parsing to match against existing project directories |
| Discovered By | DOG-001 dogfooding |
| Status | Fixed |

### D-002: Feature 078 Documentation Gap (Fixed)

| Field | Value |
|-------|-------|
| Issue ID | D-002 |
| Severity | Low |
| Original State | Feature 078 not documented in README Implementation Status |
| Fix Applied | Added Features 078, 079 to README |
| Status | Fixed |

### D-003: run-day --project Parameter (Already Fixed in Hardening)

| Field | Value |
|-------|-------|
| Issue ID | D-003 |
| Severity | Medium |
| Original State | run-day lacked --project parameter, defaulted to demo-product causing confusion |
| Fix Applied | UX hardening applied during 026-036 milestone |
| Discovered By | Dogfooding Days 1-3 recurring issue |
| Status | Fixed (prior to stabilization) |

### D-004: Completion Blocking Messages Generic

| Field | Value |
|-------|-------|
| Issue ID | D-004 |
| Severity | Medium |
| Issue | "blocked_acceptance_failed" lacks specific failed criteria |
| Affected Flow | `asyncdev acceptance gate` |
| Fix Scope | Add criterion-specific blocking reasons to gate output |
| Status | Pending |

### D-005: Evidence Console Requires Explicit --project

| Field | Value |
|-------|-------|
| Issue ID | D-005 |
| Severity | Low |
| Issue | No auto-detection of single project like other consoles |
| Affected Command | `asyncdev evidence summary` |
| Fix Scope | Add single-project auto-detection when only one project exists |
| Status | Pending |

### D-006: Remediation Guidance Truncated

| Field | Value |
|-------|-------|
| Issue ID | D-006 |
| Severity | Low |
| Issue | Remediation guidance truncated to 50 chars in Recovery Console detail view |
| Fix Scope | Expand remediation detail display |
| Status | Pending |

### D-007: Manual Artifact Spelunking (Fixed via Feature 079)

| Field | Value |
|-------|-------|
| Issue ID | D-007 |
| Severity | Medium |
| Original State | Operator needed manual directory navigation for latest truth |
| Fix Applied | Feature 079 `asyncdev evidence latest` and `asyncdev evidence questions` |
| Status | Fixed |

### D-008: CLI Parameter Naming Inconsistency

| Field | Value |
|-------|-------|
| Issue ID | D-008 |
| Severity | Low |
| Issue | `--project` vs `--product-id` across different commands |
| Fix Scope | Documentation alignment, standardize on `--project` |
| Status | Pending (docs only) |

---

## 6. Bucket E - Documentation Clarifications

### E-001: Evidence Summary CLI Documentation

| Field | Value |
|-------|-------|
| Issue ID | E-001 |
| Severity | Low |
| Gap | Evidence Console (Feature 079) not documented in docs/architecture.md |
| Fix Scope | Add evidence-summary to artifact catalog and platform layers |
| Status | Pending |

---

## 7. Bucket F - Deferred Ideas (Post-Stabilization)

Per freeze plan Rule 6, these ideas are recorded but not implemented:

| ID | Idea | Category | Priority |
|----|------|----------|----------|
| F-001 | Observer findings persistence implementation | Evidence Truth | High |
| F-002 | Acceptance history visualization (timeline view) | Operator UX | Low |
| F-003 | Acceptance retry with remediation execution | Acceptance Flow | Medium |
| F-004 | Project-level evidence rollup enhancement | Evidence Truth | Medium |
| F-005 | Platform overview dashboard | Operator UX | Low |
| F-006 | CLI consumer migration to LatestTruthResolver | Evidence Truth | Medium |

---

## 8. Repair Priority Order

Recommended fix sequence during stabilization:

| Priority | Issue ID | Bucket | Description | Estimated Effort |
|----------|----------|--------|-------------|------------------|
| 1 | C-005 | Evidence Truth | Observer findings persistence | Medium |
| 2 | C-006 | Evidence Truth | Latest pointer files | Low |
| 3 | C-007 | Evidence Truth | Artifact router observer paths | Low |
| 4 | C-009 | Evidence Truth | LatestTruthResolver consumer migration | Low |
| 5 | B-001 | Blocker | CLI new-feature tests | Low |
| 6 | B-002 | Blocker | Reacceptance trigger tests | Low |
| 7 | D-004 | Operator UX | Completion blocking messages | Low |
| 8 | D-005 | Operator UX | Evidence console auto-detection | Low |
| 9 | E-001 | Documentation | Evidence summary docs | Low |
| 10 | C-008 | Evidence Truth | Evidence auto-update | Medium |

---

## 9. Tracking Template

Per freeze plan Section 13, track:

### Week 1 (2026-04-25)

| Metric | Count |
|--------|-------|
| Real features executed | 5 (DOG-001 to DOG-005) |
| Blockers found | 2 (B-001, B-002 pre-existing) |
| Blockers fixed | 0 |
| Evidence truth issues found | 4 |
| Evidence truth issues fixed | 3 (C-003, C-004, C-002 partial) |
| Operator friction issues found | 2 |
| Operator friction issues fixed | 2 (D-001, D-002) |
| Deferred ideas added | 6 |
| Platform confidence | Improved |

---

## 10. Success Criteria

Per freeze plan Section 14, stabilization is successful when:

- [ ] Pre-existing test failures resolved (B-001, B-002)
- [ ] Observer findings persistence implemented (C-001)
- [ ] CLI consumers migrated to LatestTruthResolver (C-002)
- [ ] All evidence truth gaps hardened
- [ ] Platform feels stable for continued use

---

## 11. Exit Criteria

Per freeze plan Section 15, freeze can end when:

- [ ] All bucket B (blocker) items resolved
- [ ] All bucket C (evidence truth) items resolved
- [ ] Blocker rate dropped to zero for 1 week
- [ ] Team can identify next post-freeze investment

---

## 12. Summary

This repair plan tracks stabilization work following the freeze policy:
- **Fix blockers** (pre-existing test failures)
- **Harden evidence truth** (observer persistence, latest-truth consolidation)
- **Reduce operator friction** (already largely done via dogfooding)
- **Defer new mechanisms** (record ideas, don't implement)

Current status: **Evidence truth mostly hardened** via Feature 079, **operator friction reduced** via dogfooding fixes. Remaining: test failures and observer persistence.