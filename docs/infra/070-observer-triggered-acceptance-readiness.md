# Feature 070 — Observer-Triggered Acceptance Readiness

## Metadata

- **Feature ID**: `070-observer-triggered-acceptance-readiness`
- **Feature Name**: `Observer-Triggered Acceptance Readiness`
- **Feature Type**: `trigger logic / policy layer / acceptance foundation`
- **Priority**: `High`
- **Status**: `Implemented`
- **Owner`: `async-dev`
- **Roadmap**: docs/infra/async-dev-independent-acceptance-validation-roadmap.md (Stage B)
- **Related Features**:
  - `069-acceptance-artifact-model-foundation` (artifact contracts)
  - `067-execution-observer-foundation` (observer layer)
  - `061-external-execution-closeout` (closeout completion)
  - `020-low-interruption-execution-policy` (policy pattern)

---

## 1. Problem Statement

Feature 069 defined AcceptancePack and AcceptanceResult artifacts, but:
- async-dev cannot determine WHEN to trigger acceptance
- no logic exists to check "acceptance readiness" prerequisites
- acceptance might start too early (before verification/closeout complete)
- no structured decision model for trigger/no-trigger

Without this trigger layer, Feature 071 (acceptance runner) cannot be invoked automatically.

---

## 2. Goal

Define acceptance-readiness logic that determines when a feature or phase result is ready for independent acceptance:

1. AcceptanceReadinessState model — "ready" vs "not ready yet"
2. AcceptanceTriggerPolicy — configurable rules for trigger decision
3. Integration with Observer — detect acceptance trigger points
4. Structured trigger/no-trigger decision with reasons

---

## 3. Non-Goals

This feature does NOT:
- Implement acceptance runner (Feature 071)
- Wire acceptance findings to recovery (Feature 072)
- Add operator surfaces (Feature 074)

This feature is strictly about **trigger readiness detection**.

---

## 4. Core Design Principle

### 4.1 Acceptance Triggers After Execution Completes

Per user clarification, acceptance should trigger when ExecutionResult completes (not after review-night).

### 4.2 Readiness Prerequisites

Acceptance cannot start if:
- Closeout not complete (verification stall, closeout stall)
- Verification failed (browser tests failed)
- Blocked items present
- ExecutionResult.status is not success

### 4.3 Configurable Policy

Following Feature 020 pattern, acceptance trigger policy should be configurable:
- `always_trigger`: Trigger acceptance after every successful execution
- `feature_completion_only`: Only trigger when feature is completion candidate
- `manual_only`: Never auto-trigger, only on operator request

### 4.4 Observer Integration

Observer (Feature 067) can detect:
- ACCEPTANCE_READY condition
- ACCEPTANCE_BLOCKED condition

These findings flow to Recovery Console for operator visibility.

---

## 5. Target Outcomes

After this feature:
- `AcceptanceReadinessState` dataclass exists
- `AcceptanceTriggerPolicy` schema exists
- `check_acceptance_readiness()` function exists
- Observer can emit acceptance-readiness findings
- AcceptancePack generation can be triggered automatically or manually

---

## 6. Required Functional Changes

### 6.1 AcceptanceReadinessState Model

```python
class AcceptanceReadiness(str, Enum):
    READY = "ready"                   # All prerequisites satisfied
    NOT_READY = "not_ready"           # Prerequisites not met
    BLOCKED = "blocked"               # Explicit blocker present
    POLICY_SKIPPED = "policy_skipped" # Policy mode prevents auto-trigger

@dataclass
class AcceptanceReadinessResult:
    readiness: AcceptanceReadiness
    execution_result_id: str
    
    prerequisites_checked: list[str]
    prerequisites_satisfied: list[str]
    prerequisites_failed: list[str]
    
    blocking_reasons: list[str]
    
    trigger_allowed: bool
    trigger_recommended: bool
    
    policy_mode: str
    policy_decision: str
    
    checked_at: str
```

### 6.2 Acceptance Trigger Prerequisites

| Prerequisite | Condition | Failure Reason |
|--------------|-----------|----------------|
| execution_complete | ExecutionResult exists and status != blocked | No ExecutionResult found |
| closeout_success | closeout_terminal_state == success | Closeout failed or stalled |
| verification_pass | orchestration_terminal_state in [success, not_required, exception_accepted] | Verification failed |
| no_blockers | blocked_items empty | Execution blocked |
| no_pending_decisions | decisions_needed empty | Decisions pending |
| feature_spec_has_criteria | acceptance_criteria exists and non-empty | No acceptance criteria defined |

### 6.3 AcceptanceTriggerPolicy Schema

```yaml
schema_type: acceptance-trigger-policy
version: "1.0"

policy_modes:
  always_trigger:
    description: "Trigger acceptance after every successful execution"
    auto_trigger: true
    trigger_conditions:
      - execution_complete
      - closeout_success
      - verification_pass
    
  feature_completion_only:
    description: "Only trigger when feature is marked as completion candidate"
    auto_trigger: true
    trigger_conditions:
      - execution_complete
      - closeout_success
      - verification_pass
      - feature_completion_candidate  # Additional condition
    
  manual_only:
    description: "Never auto-trigger, require operator request"
    auto_trigger: false
    trigger_conditions: []  # Manual only

default_mode: "feature_completion_only"
```

### 6.4 Observer Finding Types Extension

Add new finding types to ObserverFindingType:

```python
class ObserverFindingType(str, Enum):
    # Existing types...
    
    # Acceptance readiness types (Feature 070)
    ACCEPTANCE_READY = "acceptance_ready"
    ACCEPTANCE_BLOCKED = "acceptance_blocked"
    ACCEPTANCE_OVERDUE = "acceptance_overdue"  # Feature not accepted after N days
```

---

## 7. Detailed Requirements

### 7.1 AcceptanceReadinessState Fields

| Field | Type | Description |
|-------|------|-------------|
| readiness | enum | READY/NOT_READY/BLOCKED/POLICY_SKIPPED |
| execution_result_id | string | ExecutionResult being evaluated |
| prerequisites_checked | array | All prerequisites that were checked |
| prerequisites_satisfied | array | Prerequisites that passed |
| prerequisites_failed | array | Prerequisites that failed |
| blocking_reasons | array | Why acceptance cannot proceed |
| trigger_allowed | boolean | Policy allows trigger |
| trigger_recommended | boolean | System recommends trigger |
| policy_mode | string | Current policy mode |
| policy_decision | string | Policy decision explanation |
| checked_at | datetime | When readiness was checked |

### 7.2 check_acceptance_readiness Function

Signature:

```python
def check_acceptance_readiness(
    project_path: Path,
    execution_result_id: str,
    policy_mode: str = "feature_completion_only"
) -> AcceptanceReadinessResult
```

Logic:
1. Load ExecutionResult
2. Check each prerequisite
3. Apply policy mode
4. Return structured result

### 7.3 Integration Points

- After `run-day` completion → call `check_acceptance_readiness`
- Observer periodic scan → detect ACCEPTANCE_READY/ACCEPTANCE_BLOCKED
- Recovery Console → show acceptance readiness status
- Feature 071 → consume readiness result to trigger runner

---

## 8. Expected File Changes

### 8.1 New Runtime Modules
- `runtime/acceptance_readiness.py` — AcceptanceReadinessState, check_acceptance_readiness

### 8.2 New Schema
- `schemas/acceptance-trigger-policy.schema.yaml`

### 8.3 Modified Files
- `runtime/execution_observer.py` — Add ACCEPTANCE_READY/ACCEPTANCE_BLOCKED finding types
- `runtime/state_store.py` — Add acceptance_readiness field to RunState
- `cli/commands/run_day.py` — Call check_acceptance_readiness after execution

### 8.4 Documentation
- `docs/infra/070-observer-triggered-acceptance-readiness.md`
- Update architecture.md with trigger semantics

---

## 9. Acceptance Criteria

## AC-001 AcceptanceReadinessState Model Exists
`runtime/acceptance_readiness.py` exists with AcceptanceReadiness enum and AcceptanceReadinessResult dataclass.

## AC-002 check_acceptance_readiness Function Exists
Function checks all 6 prerequisites and returns structured result.

## AC-003 AcceptanceTriggerPolicy Schema Exists
`schemas/acceptance-trigger-policy.schema.yaml` defines 3 policy modes with trigger conditions.

## AC-004 Observer Finding Types Extended
ObserverFindingType includes ACCEPTANCE_READY and ACCEPTANCE_BLOCKED.

## AC-005 Prerequisites Documented
All prerequisites clearly documented with failure reasons.

## AC-006 Policy Mode Default
Default policy mode is `feature_completion_only`.

## AC-007 Tests Added
Tests cover all prerequisites, all policy modes, and edge cases.

---

## 10. Test Requirements

- Prerequisite check tests (6 conditions)
- Policy mode tests (3 modes)
- Edge case: missing ExecutionResult
- Edge case: blocked_items present
- Edge case: policy_mode=manual_only
- Observer finding emission test

---

## 11. Implementation Guidance

### 11.1 Recommended Sequence

1. Create acceptance_readiness.py with state model
2. Create check_acceptance_readiness function
3. Create acceptance-trigger-policy.schema.yaml
4. Extend ObserverFindingType
5. Add tests
6. Update docs

### 11.2 Follow Feature 020 Pattern

AcceptanceTriggerPolicy should follow the same structure as ExecutionPolicy:
- policy_modes with trigger_conditions
- default_mode
- integration_points section

---

## 12. Risks and Mitigations

### Risk 1 — Acceptance triggers too early
**Mitigation:** Require closeout_success and verification_pass prerequisites.

### Risk 2 — Policy complexity grows
**Mitigation:** Start with 3 simple modes, extend later if needed.

### Risk 3 — Observer findings become noisy
**Mitigation:** Only emit ACCEPTANCE_READY/ACCEPTANCE_BLOCKED when relevant, not on every check.

---

## 13. Definition of Done

This feature is complete when:

1. AcceptanceReadinessState model exists and works
2. check_acceptance_readiness function returns structured results
3. AcceptanceTriggerPolicy schema validates
4. Observer can emit acceptance-readiness findings
5. All prerequisites are checked correctly
6. Tests pass for all scenarios
7. Docs reflect trigger semantics

---

## 14. Summary

Feature 070 builds the trigger layer for acceptance validation.

It answers: "When should acceptance start?"

The result is a structured readiness decision that Features 071-076 can consume.

In short:

> **070 makes async-dev smart about when to trigger acceptance.**