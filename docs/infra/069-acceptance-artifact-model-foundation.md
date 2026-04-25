# Feature 069 — Acceptance Artifact Model Foundation

## Metadata

- **Feature ID**: `069-acceptance-artifact-model-foundation`
- **Feature Name**: `Acceptance Artifact Model Foundation`
- **Feature Type**: `artifact schema / platform foundation / acceptance layer`
- **Priority**: `High`
- **Status**: `Implemented`
- **Owner**: `async-dev`
- **Roadmap**: docs/infra/async-dev-independent-acceptance-validation-roadmap.md (Stage A)
- **Related Features**:
  - `067-execution-observer-foundation` (trigger integration)
  - `068-platform-foundation-rollup` (platform layer model)
  - `Future: 070-076` (acceptance loop features)

---

## 1. Problem Statement

async-dev currently has:
- `FeatureSpec.acceptance_criteria` — unstructured text array listing criteria
- `ArchivePack.acceptance_result` — lightweight snapshot with satisfied/unsatisfied/overall

But no formal artifact contracts for:
- Structured input package for an independent validator
- Structured output capturing detailed findings per criterion
- Evidence linking and verification method documentation
- Attempt tracking and validator identity

Without these contracts, the acceptance layer (Features 069-076) cannot be wired properly.

---

## 2. Goal

Define the canonical artifact and schema foundation for independent acceptance validation:

1. `AcceptancePack` — structured input for validator
2. `AcceptanceResult` — structured output from validator
3. `AcceptanceTerminalState` — terminal status enum
4. `AcceptanceFinding` — per-criterion evaluation model

These artifacts provide stable contracts that Features 070-076 can trigger, run, and consume.

---

## 3. Non-Goals

This feature does NOT:
- Implement acceptance trigger logic (Feature 070)
- Implement acceptance runner (Feature 071)
- Wire acceptance findings to recovery (Feature 072)
- Add operator surfaces for acceptance (Feature 074)

This feature is strictly about **artifact contracts**.

---

## 4. Core Design Principle

### 4.1 Acceptance ≠ Verification

| Layer | Purpose | Question |
|-------|---------|----------|
| Verification | Execution correctness | "Did it run correctly?" |
| Acceptance | Requirement fulfillment | "Does it meet the criteria?" |

### 4.2 Separate Actor Principle

The validator must be separate from the executor:
- Different AI session (default validator)
- Human review (alternative validator)
- Automated scripts (alternative validator)

AcceptancePack and AcceptanceResult must support this separation.

### 4.3 Structured Criteria

Each acceptance criterion must be identifiable:
- criterion_id for tracking
- description for clarity
- evidence_type hint for verification method

### 4.4 Evidence Linking

Findings must reference evidence artifacts, not just describe gaps.

---

## 5. Target Outcomes

After this feature:
- `AcceptancePack.schema.yaml` exists with required fields
- `AcceptanceResult.schema.yaml` exists with terminal states
- Templates exist for both artifacts
- Examples demonstrate realistic content
- Docs reflect acceptance model in platform layer

---

## 6. Required Functional Changes

### 6.1 AcceptancePack Schema

Defines the input package for validator:

```yaml
schema_type: acceptance-pack
version: "1.0"

required:
  - acceptance_pack_id
  - feature_id
  - product_id
  - execution_result_id
  - acceptance_criteria   # structured from FeatureSpec
  - implementation_summary
  - evidence_artifacts
  - verification_status
  - triggered_at
  - trigger_reason

optional:
  - observer_findings
  - changed_files
  - notes_for_validator
```

### 6.2 AcceptanceResult Schema

Defines the output from validator:

```yaml
schema_type: acceptance-result
version: "1.0"

required:
  - acceptance_result_id
  - acceptance_pack_id
  - terminal_state       # ACCEPTED/REJECTED/CONDITIONAL/MANUAL_REVIEW/ESCALATED
  - findings             # per-criterion evaluation
  - accepted_criteria
  - failed_criteria
  - missing_evidence
  - validator_identity
  - validated_at
  - attempt_number

optional:
  - remediation_guidance
  - conditional_notes
  - escalate_reason
```

### 6.3 AcceptanceTerminalState Enum

Terminal states for acceptance result:

| State | Valid for Completion? | Meaning |
|-------|------------------------|---------|
| ACCEPTED | ✅ Yes | All criteria satisfied |
| REJECTED | ❌ No | Criteria not met, needs rework |
| CONDITIONAL | ✅ Yes | Accepted with documented caveats |
| MANUAL_REVIEW | ❌ No | Needs human judgment |
| ESCALATED | ❌ No | Cannot proceed without escalation |

### 6.4 AcceptanceFinding Model

Per-criterion evaluation:

```yaml
criterion_id: "AC-001"
criterion_description: "All six object schemas exist"
status: "satisfied" | "failed" | "partial" | "needs_evidence"
evidence_links: ["schemas/product-brief.schema.yaml", ...]
gap_description: "Missing feature-spec.template.md"  # if failed/partial
verification_method: "file_existence_check"
```

---

## 7. Detailed Requirements

### 7.1 AcceptancePack Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| acceptance_pack_id | string | Yes | Format: `ap-YYYYMMDD-###` |
| feature_id | string | Yes | Reference to FeatureSpec |
| product_id | string | Yes | Product context |
| execution_result_id | string | Yes | Reference to ExecutionResult being validated |
| acceptance_criteria | array | Yes | Structured criteria from FeatureSpec |
| implementation_summary | string | Yes | What was implemented |
| evidence_artifacts | array | Yes | Paths to artifacts for validation |
| verification_status | object | Yes | Verification layer result summary |
| triggered_at | datetime | Yes | When acceptance was triggered |
| trigger_reason | string | Yes | Why acceptance started |

### 7.2 AcceptanceResult Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| acceptance_result_id | string | Yes | Format: `ar-YYYYMMDD-###` |
| acceptance_pack_id | string | Yes | Links to input pack |
| terminal_state | enum | Yes | ACCEPTED/REJECTED/CONDITIONAL/MANUAL_REVIEW/ESCALATED |
| findings | array | Yes | AcceptanceFinding per criterion |
| accepted_criteria | array | Yes | List of satisfied criterion_ids |
| failed_criteria | array | Yes | List of failed criterion_ids |
| missing_evidence | array | Yes | Evidence gaps preventing acceptance |
| validator_identity | string | Yes | AI system, human, or script name |
| validated_at | datetime | Yes | When validation completed |
| attempt_number | integer | Yes | 1-N for retry tracking |

### 7.3 AcceptanceCriteriaItem Structure

Upgrade from unstructured text to structured object:

```yaml
criterion_id: "AC-001"
description: "All six object schemas exist"
evidence_type_hint: "file_existence" | "behavior_verification" | "manual_review"
priority: "critical" | "required" | "optional"
```

---

## 8. Expected File Changes

### 8.1 New Schemas
- `schemas/acceptance-pack.schema.yaml`
- `schemas/acceptance-result.schema.yaml`

### 8.2 New Templates
- `templates/acceptance-pack.template.md`
- `templates/acceptance-result.template.md`

### 8.3 New Examples
- `examples/acceptance-pack.example.yaml`
- `examples/acceptance-result.example.yaml`

### 8.4 Documentation Updates
- `docs/architecture.md` — Add AcceptancePack/AcceptanceResult to object model
- `docs/platform/platform-readiness.md` — Add acceptance layer status

---

## 9. Acceptance Criteria

## AC-001 AcceptancePack Schema Exists
A valid `schemas/acceptance-pack.schema.yaml` file exists with all required fields defined.

## AC-002 AcceptanceResult Schema Exists
A valid `schemas/acceptance-result.schema.yaml` file exists with terminal state enum and findings structure.

## AC-003 Templates Exist
Both `templates/acceptance-pack.template.md` and `templates/acceptance-result.template.md` exist.

## AC-004 Examples Exist
Both example files exist with realistic content demonstrating proper usage.

## AC-005 Terminal States Documented
AcceptanceTerminalState enum values are documented with "valid for completion" semantics.

## AC-006 Architecture Updated
docs/architecture.md references AcceptancePack and AcceptanceResult in the object model.

## AC-007 Relationship to Verification Clear
Documentation clearly distinguishes verification (execution correctness) from acceptance (requirement fulfillment).

---

## 10. Test Requirements

At minimum:
- YAML schema validation passes for both new schemas
- Template renders correctly with placeholder values
- Examples validate against schemas
- No conflicts with existing archive-pack.acceptance_result

---

## 11. Implementation Guidance

### 11.1 Recommended Sequence

1. Create acceptance-pack.schema.yaml
2. Create acceptance-result.schema.yaml
3. Create templates for both
4. Create examples demonstrating accepted/rejected/conditional states
5. Update architecture.md
6. Verify schema validation

### 11.2 Avoid These Patterns

- Making AcceptanceResult replace ArchivePack.acceptance_result (they serve different purposes)
- Adding trigger logic to AcceptancePack (trigger is Feature 070)
- Adding recovery wiring to AcceptanceResult (recovery is Feature 072)

---

## 12. Risks and Mitigations

### Risk 1 — Acceptance and verification get confused
**Mitigation:** Explicit documentation section distinguishing purposes.

### Risk 2 — AcceptanceResult too vague to drive remediation
**Mitigation:** Require gap_description and evidence_links in each finding.

### Risk 3 — Conflicts with existing archive-pack.acceptance_result
**Mitigation:** Keep ArchivePack.acceptance_result as summary, AcceptanceResult as detailed artifact.

---

## 13. Definition of Done

This feature is complete when:

1. Both schemas exist and validate
2. Both templates exist and render
3. Examples demonstrate realistic states
4. Architecture docs reflect acceptance model
5. No contradictions with existing acceptance_result pattern
6. The artifact contracts are stable for Features 070-076 to build on

---

## 14. Summary

Feature 069 defines the artifact contracts for independent acceptance validation.

Without AcceptancePack and AcceptanceResult, Features 070-076 cannot reliably:
- Trigger acceptance
- Run validation
- Store findings
- Feed results into recovery

In short:

> **069 builds the artifact foundation for the acceptance loop.**