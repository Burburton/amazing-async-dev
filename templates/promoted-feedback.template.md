# PromotedFeedback Template (Feature 019c)

> This template defines the structure of `PromotedFeedback` — a formalized follow-up record created from triaged workflow feedback.

---

## Metadata

| Field | Value |
|-------|-------|
| Object Type | `PromotedFeedback` |
| Purpose | Formal follow-up record from workflow feedback |
| Update Frequency | When followup_status changes |
| Owner | Operator |
| Feature | 019c - Feedback Promotion |
| Version | 1.0 |

---

## Required Fields

### promotion_id
- **Type**: string (pattern: `promo-YYYYMMDD-###`)
- **Description**: Unique identifier for this promoted follow-up
- **Example**: `promo-20260412-001`

### source_feedback_id
- **Type**: string (pattern: `wf-YYYYMMDD-###`)
- **Description**: ID of workflow feedback that was promoted
- **Example**: `wf-20260412-001`
- **Critical**: Links back to original feedback for full traceability

### summary
- **Type**: string
- **Description**: Concise summary of what this follow-up addresses
- **Example**: `CLI status command shows wrong phase after execution`
- **Notes**: Derived from source but can be refined during promotion

### promoted_at
- **Type**: datetime (ISO 8601)
- **Description**: When this feedback was promoted
- **Example**: `2026-04-12T10:00:00`

---

## Optional Fields

### promotion_reason
- **Type**: enum
- **Description**: Reason for promotion
- **Values**: `system_bug`, `ux_issue`, `workflow_improvement`, `documentation_gap`, `integration_issue`, `other`
- **Default**: `system_bug`

### promotion_note
- **Type**: string
- **Description**: Explanation of promotion decision
- **Example**: `This affects multiple users, should be prioritized`
- **Notes**: Optional but encouraged

### source_problem_domain
- **Type**: enum (`async_dev` | `product` | `uncertain`)
- **Description**: Preserved from source triage

### source_confidence
- **Type**: enum (`low` | `medium` | `high`)
- **Description**: Preserved from source triage

### source_escalation_recommendation
- **Type**: enum (`ignore` | `track_only` | `review_needed` | `candidate_issue`)
- **Description**: Preserved from source triage

### source_issue_type
- **Type**: enum
- **Description**: Issue type from source feedback

### source_description
- **Type**: string
- **Description**: Original description from source feedback

### followup_status
- **Type**: enum
- **Description**: Current status of follow-up work
- **Values**:
  | Status | Meaning |
  |--------|---------|
  | `open` | Promoted but not yet reviewed |
  | `reviewed` | Reviewed and confirmed |
  | `in_progress` | Work being done |
  | `addressed` | Fix implemented |
  | `closed` | Follow-up complete |
- **Default**: `open`

### candidate_feature_followup
- **Type**: string (pattern: `\d{3}-[a-z0-9-]+`)
- **Description**: Optional feature ID that could address this
- **Example**: `020-cli-phase-fix`

### artifact_reference
- **Type**: object
- **Description**: Reference to relevant artifact

### addressed_at
- **Type**: datetime
- **Description**: When follow-up was addressed

### addressed_note
- **Type**: string
- **Description**: How this was addressed

---

## Template Instances

```yaml
# PromotedFeedback Instance
promotion_id: "promo-YYYYMMDD-###"
source_feedback_id: "wf-YYYYMMDD-###"
summary: "CLI status command shows wrong phase after execution"
promotion_reason: "system_bug"
promotion_note: "Confirmed bug affecting day loop workflow"
source_problem_domain: "async_dev"
source_confidence: "high"
source_escalation_recommendation: "candidate_issue"
source_issue_type: "cli_behavior"
source_description: "asyncdev status showed wrong phase"
followup_status: "open"
promoted_at: "2026-04-12T10:00:00"
```

---

## Storage

- **Location**: `.runtime/feedback-promotions/{promotion_id}.yaml`
- **Format**: YAML
- **SQLite**: `promoted_feedback` table

---

## CLI Usage

```bash
# Promote triaged feedback
asyncdev feedback promote --feedback-id wf-001 --reason system_bug --note "Priority fix"

# List promotions
asyncdev feedback promotions list

# Show promotion details
asyncdev feedback promotions show --promotion-id promo-001
```

---

## Validation Checklist

Before promoting, verify:

- [ ] source feedback exists and is triaged
- [ ] source feedback has not been promoted already
- [ ] summary is non-empty
- [ ] promotion_id pattern matches

---

## See Also

- `schemas/promoted-feedback.schema.yaml` - Validation rules
- `schemas/workflow-feedback.schema.yaml` - Source feedback schema
- `docs/workflow-feedback.md` - Full documentation