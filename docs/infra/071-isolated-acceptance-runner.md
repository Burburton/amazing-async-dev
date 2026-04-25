# Feature 071 — Isolated Acceptance Runner

## Metadata

- **Feature ID**: `071-isolated-acceptance-runner`
- **Feature Name**: `Isolated Acceptance Runner`
- **Feature Type**: `execution layer / acceptance runner / isolated context`
- **Priority**: `High`
- **Status**: `Implemented`
- **Owner**: `async-dev`
- **Roadmap**: docs/infra/async-dev-independent-acceptance-validation-roadmap.md (Stage C)
- **Related Features**:
  - `069-acceptance-artifact-model-foundation` (artifact contracts)
  - `070-observer-triggered-acceptance-readiness` (trigger readiness)
  - `061-external-execution-closeout` (closeout completion)
  - `056-browser-verification` (verification layer)

---

## 1. Problem Statement

Feature 070 determines WHEN acceptance should trigger, but:
- async-dev has no mechanism to RUN acceptance validation
- no isolated execution context for validator
- no AcceptancePack builder from ExecutionResult
- no AcceptanceResult persistence path

Without an acceptance runner, trigger readiness produces no action.

---

## 2. Goal

Define and implement an isolated acceptance execution path that:
1. Builds AcceptancePack from ExecutionResult and FeatureSpec
2. Invokes validator in separate context
3. Persists AcceptanceResult with structured findings
4. Maintains clear separation from executor context

---

## 3. Acceptance Criteria

### AC-001: AcceptancePack Builder
- `build_acceptance_pack()` function exists
- AcceptancePack includes all required fields from schema
- AcceptancePack references ExecutionResult and FeatureSpec
- AcceptancePack includes verification_summary

### AC-002: Isolated Runner Interface
- `run_acceptance()` function exists
- Runner operates in separate context from executor
- Runner consumes AcceptancePack
- Runner produces AcceptanceResult

### AC-003: Validator Invocation
- Validator invocation interface defined
- Validator types: ai_session, human_review, automated_script
- Validator identity captured in AcceptanceResult
- Clear separation: validator ≠ executor

### AC-004: AcceptanceResult Persistence
- AcceptanceResult persisted to `acceptance-results/{acceptance_result_id}.md`
- YAML block format consistent with ExecutionResult
- Terminal state recorded
- Findings list captured

### AC-005: Attempt Tracking
- AcceptanceResult.attempt_number tracked
- History of previous attempts accessible
- Re-acceptance support built-in

### AC-006: Error Handling
- Runner handles validator failures gracefully
- Error states: validator_unavailable, validation_timeout
- Fallback to manual_review when automated fails

### AC-007: Tests
- Unit tests for AcceptancePack builder
- Unit tests for runner interface
- Integration tests for full acceptance flow

---

## 4. Design

### 4.1 AcceptancePack Builder

```python
def build_acceptance_pack(
    project_path: Path,
    execution_result_id: str,
) -> AcceptancePack:
```

Inputs:
- ExecutionResult (implementation outcome)
- FeatureSpec (acceptance_criteria)
- RunState (current phase, feature_id)

Outputs:
- AcceptancePack with all required fields

### 4.2 AcceptanceRunner

```python
class AcceptanceRunner:
    def __init__(self, project_path: Path, validator_type: ValidatorType):
        self.project_path = project_path
        self.validator_type = validator_type
    
    def run(self, acceptance_pack: AcceptancePack) -> AcceptanceResult:
        # Invoke validator
        # Collect findings
        # Return AcceptanceResult
```

### 4.3 Validator Types

```python
class ValidatorType(str, Enum):
    AI_SESSION = "ai_session"
    HUMAN_REVIEW = "human_review"
    AUTOMATED_SCRIPT = "automated_script"
```

### 4.4 Validator Interface

```python
@dataclass
class ValidatorIdentity:
    validator_type: ValidatorType
    validator_id: str  # session ID, person ID, or script name
    validator_context: str  # "independent" or "default"
    invoked_at: str
```

### 4.5 AcceptanceResult Persistence

Path: `projects/{project_id}/acceptance-results/{acceptance_result_id}.md`

Format:
```markdown
# AcceptanceResult

```yaml
acceptance_result_id: ar-20260425-001
terminal_state: accepted
acceptance_pack_id: ap-20260425-001
attempt_number: 1
validator_identity:
  validator_type: ai_session
  validator_id: ses-independent-001
  validator_context: independent
findings:
  - criterion_id: AC-001
    result: passed
    evidence_found: true
    notes: "..."
accepted_criteria: [AC-001]
failed_criteria: []
remediation_guidance: []
validated_at: 2026-04-25T12:00:00
```
```

---

## 5. Implementation Plan

### Step 1: Create Validator Models
- `runtime/validator_types.py` — ValidatorType, ValidatorIdentity

### Step 2: Create AcceptancePack Builder
- `runtime/acceptance_pack_builder.py` — build_acceptance_pack()

### Step 3: Create AcceptanceRunner
- `runtime/acceptance_runner.py` — AcceptanceRunner, run_acceptance()

### Step 4: Create AcceptanceResult Persistence
- Extend `runtime/state_store.py` — save_acceptance_result(), load_acceptance_result()

### Step 5: Add Tests
- `tests/test_acceptance_runner.py`

---

## 6. Dependencies

| Feature | Dependency |
|---------|------------|
| 069 | AcceptancePack, AcceptanceResult schemas |
| 070 | check_acceptance_readiness(), AcceptanceReadiness |
| 061 | ExecutionResult closeout fields |
| 056 | verification_summary extraction |

---

## 7. Out of Scope

- CLI command for acceptance trigger (deferred to Feature 074)
- Acceptance-to-recovery mapping (Feature 072)
- Re-acceptance loop orchestration (Feature 073)
- Completion gating (Feature 075)

---

## 8. Integration Points

- Observer (Feature 067) triggers acceptance via runner
- ExecutionResult provides implementation evidence
- FeatureSpec provides validation criteria
- AcceptanceResult feeds into completion gating (Feature 075)

---

## 9. Success Metrics

| Metric | Target |
|--------|--------|
| AcceptancePack completeness | 100% required fields |
| AcceptanceResult persistence | Successful write to acceptance-results/ |
| Validator isolation | validator_context = "independent" |
| Test coverage | All ACs covered |

---

## 10. Timeline

- Implementation: ~1 hour
- Tests: ~30 minutes
- Documentation: ~15 minutes
- Total: ~1.5 hours