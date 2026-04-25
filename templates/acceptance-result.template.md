# AcceptanceResult Template

> Structured output from independent acceptance validation.

---

## Metadata

| Field | Value |
|-------|-------|
| Object Type | `AcceptanceResult` |
| Purpose | Record acceptance validation outcome with detailed findings |
| Update Frequency | Never (immutable per validation) |
| Owner | Acceptance runner (Feature 071) |
| Schema | schemas/acceptance-result.schema.yaml |

---

## Required Fields

### acceptance_result_id

Unique identifier for this result.

```
Pattern: ^ar-[0-9]{8}-[0-9]{3}$
Format: ar-YYYYMMDD-###
Example: ar-20260423-001
```

### acceptance_pack_id

Reference to input pack.

```
Pattern: ^ap-[0-9]{8}-[0-9]{3}$
Example: ap-20260423-001
```

### terminal_state

Final acceptance status.

```
Values:
  - accepted      ✅ Valid for completion
  - rejected      ❌ NOT valid, needs rework
  - conditional   ✅ Valid with caveats
  - manual_review ❌ NOT valid, needs human
  - escalated     ❌ NOT valid, needs escalation
```

### findings

Per-criterion evaluation results.

```yaml
findings:
  - criterion_id: "AC-001"
    criterion_description: "AcceptancePack schema exists"
    status: "satisfied | failed | partial | needs_evidence"
    evidence_links: ["schemas/acceptance-pack.schema.yaml"]
    gap_description: "What's missing if failed/partial"
    verification_method: "How it was checked"
```

### accepted_criteria

List of satisfied criterion_ids.

```yaml
accepted_criteria: ["AC-001", "AC-002", "AC-003"]
```

### failed_criteria

List of failed criterion_ids.

```yaml
failed_criteria: []  # Empty if accepted
```

### missing_evidence

Evidence gaps.

```yaml
missing_evidence:
  - criterion_id: "AC-005"
    required_evidence_type: "file_existence"
    suggested_artifact: "examples/acceptance-result-rejected.example.yaml"
```

### validator_identity

Who performed validation.

```yaml
validator_identity:
  validator_type: "ai_session | human_review | automated_script"
  validator_name: "acceptance-validator-v1"
  validator_session: "ses_abc123"  # If AI
```

### validated_at

When validation completed.

```
Format: ISO 8601 datetime
Example: 2026-04-23T15:00:00
```

### attempt_number

Which attempt (1-N).

```
Example: 1
```

---

## Optional Fields

### remediation_guidance

How to fix rejected criteria.

```yaml
remediation_guidance:
  must_fix:
    - criterion_id: "AC-004"
      action: "Create acceptance-pack.template.md"
      priority: "critical"
  suggested_actions:
    - "Copy template structure from execution-pack.template.md"
  estimated_effort: "30 minutes"
```

### conditional_notes

Caveats for conditional acceptance.

```
Example: Accepted with note: examples demonstrate accepted state only, rejected examples pending
```

### escalate_reason

Why escalated.

```yaml
escalate_reason:
  escalation_type: "criterion_ambiguity | evidence_insufficient | policy_conflict | unknown_blocker"
  description: "AC-007 interpretation unclear"
  suggested_resolution: "Clarify with feature owner"
```

### next_recommended_action

What to do next.

```
Example: Proceed to feature completion
```

### validation_duration

Time spent.

```
Example: 15m
```

---

## Terminal State Validity

| State | Valid for Completion? | Action |
|-------|------------------------|--------|
| accepted | ✅ Yes | Proceed to completion |
| conditional | ✅ Yes | Proceed with documented notes |
| rejected | ❌ No | Trigger rework/recovery |
| manual_review | ❌ No | Wait for human decision |
| escalated | ❌ No | Resolve escalation first |

---

## Usage

AcceptanceResult is consumed by:
- Completion gating (Feature 075) — block completion if not accepted/conditional
- Recovery integration (Feature 072) — feed failed_criteria into rework
- Operator surfaces (Feature 074) — display acceptance status
- ArchivePack creation — populate acceptance_result summary

AcceptanceResult is created by:
- Acceptance runner (Feature 071)

---

## Validation Rules

- `acceptance_result_id` must match pattern
- `terminal_state` must be valid enum
- `findings` must have at least 1 item
- If `terminal_state` is rejected, `failed_criteria` must have items
- If `terminal_state` is conditional, `conditional_notes` must be present
- If `terminal_state` is escalated, `escalate_reason` must be present
- `attempt_number` must be >= 1

---

## Integration with ArchivePack

AcceptanceResult maps to ArchivePack.acceptance_result:

```yaml
# AcceptanceResult (detailed)
accepted_criteria: ["AC-001", "AC-002"]
failed_criteria: ["AC-003"]
terminal_state: "conditional"

# Maps to ArchivePack.acceptance_result (summary)
acceptance_result:
  satisfied: ["AC-001", "AC-002"]
  unsatisfied: ["AC-003"]
  overall: "mostly-satisfied"
```

---

## Example Instances

See:
- examples/acceptance-result.example.yaml (accepted state)
- examples/acceptance-result-rejected.example.yaml (rejected state)
- examples/acceptance-result-conditional.example.yaml (conditional state)