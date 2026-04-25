# AcceptancePack Template

> Structured input package for independent acceptance validation.

---

## Metadata

| Field | Value |
|-------|-------|
| Object Type | `AcceptancePack` |
| Purpose | Provide bounded input for acceptance validator |
| Update Frequency | Never (immutable per validation) |
| Owner | Acceptance trigger logic (Feature 070) |
| Schema | schemas/acceptance-pack.schema.yaml |

---

## Required Fields

### acceptance_pack_id

Unique identifier for this acceptance pack.

```
Pattern: ^ap-[0-9]{8}-[0-9]{3}$
Format: ap-YYYYMMDD-###
Example: ap-20260423-001
```

### feature_id

Feature being validated.

```
Pattern: ^\d{3}-[a-z0-9-]+$
Example: 069-acceptance-artifact-model-foundation
```

### product_id

Product context.

```
Example: amazing-async-dev
```

### execution_result_id

Reference to ExecutionResult being validated.

```
Pattern: ^exec-[0-9]{8}-[0-9]{3}$
Example: exec-20260423-001
```

### acceptance_criteria

Structured criteria to evaluate. Each criterion must have:

```yaml
criterion_id: "AC-001"  # Unique within this feature
description: "What must be satisfied"
evidence_type_hint: "file_existence | content_validation | behavior_verification | manual_review"
priority: "critical | required | optional"
```

Example:

```yaml
acceptance_criteria:
  - criterion_id: "AC-001"
    description: "AcceptancePack schema exists with all required fields"
    evidence_type_hint: "file_existence"
    priority: "critical"
  
  - criterion_id: "AC-002"
    description: "AcceptanceResult schema exists with terminal state enum"
    evidence_type_hint: "file_existence"
    priority: "critical"
  
  - criterion_id: "AC-003"
    description: "Templates exist for both artifacts"
    evidence_type_hint: "file_existence"
    priority: "required"
```

### implementation_summary

What was implemented (min 50 characters).

```
Example: Created AcceptancePack and AcceptanceResult schemas following existing patterns from execution-pack and execution-result. Added templates and examples demonstrating accepted, rejected, and conditional states.
```

### evidence_artifacts

Artifacts available for validation.

```yaml
evidence_artifacts:
  - name: "acceptance-pack.schema.yaml"
    path: "schemas/acceptance-pack.schema.yaml"
    type: "schema"
  - name: "acceptance-result.schema.yaml"
    path: "schemas/acceptance-result.schema.yaml"
    type: "schema"
```

### verification_summary

Summary of verification layer (execution correctness).

```yaml
verification_summary:
  verification_type: "backend_only"
  browser_verification_executed: false
  orchestration_terminal_state: "not_required"
  closeout_terminal_state: "success"
```

### triggered_at

When acceptance was triggered.

```
Format: ISO 8601 datetime
Example: 2026-04-23T14:30:00
```

### trigger_reason

Why acceptance started.

```
Values: execution_result_complete | operator_request | feature_complete_candidate | revalidation_after_fix
Example: execution_result_complete
```

---

## Optional Fields

### observer_findings_summary

Summary of observer findings if available.

```yaml
observer_findings_summary:
  total_findings: 3
  recovery_significant_count: 1
  critical_count: 0
  high_count: 1
```

### changed_files

Files changed in execution.

```yaml
changed_files:
  - "schemas/acceptance-pack.schema.yaml"
  - "schemas/acceptance-result.schema.yaml"
```

### notes_for_validator

Context for validator.

```
Example: Focus on schema completeness. Templates can be partial for v1.
```

### prior_attempt_reference

Reference to prior attempt if retry.

```
Pattern: ^ar-[0-9]{8}-[0-9]{3}$
Example: ar-20260422-001
```

---

## Usage

AcceptancePack is consumed by:
- Acceptance runner (Feature 071) to execute validation
- Validator session to understand what to check

AcceptancePack is created by:
- Acceptance trigger logic (Feature 070) after ExecutionResult completes

---

## Validation Rules

- `acceptance_pack_id` must match pattern
- `acceptance_criteria` must have at least 1 item
- Each criterion must have `criterion_id`, `description`, `priority`
- `implementation_summary` must be at least 50 characters
- `execution_result_id` must reference valid ExecutionResult

---

## Example Instance

See: examples/acceptance-pack.example.yaml