# WorkflowFeedback Template (v2.2)

> This template defines the structure of `WorkflowFeedback` — a lightweight repairable record for workflow/system issues discovered during async-dev usage, with triage classification.

---

## Metadata

| Field | Value |
|-------|-------|
| Object Type | `WorkflowFeedback` |
| Purpose | Capture workflow/system issues with repair context and triage classification |
| Update Frequency | When resolution/triage changes |
| Owner | Operator / AI executor |
| Features | 019a - Capture + Repair Context, 019b - Triage, 019c - Promotion |
| Version | 2.2 |

---

## Required Fields

### feedback_id
- **Type**: string (pattern: `wf-YYYYMMDD-###`)
- **Description**: Unique identifier for this feedback record
- **Example**: `wf-20260411-001`

### problem_domain
- **Type**: enum (`async_dev` | `product` | `uncertain`)
- **Description**: Classification of where the issue originates
  - `async_dev`: amazing-async-dev system issues (CLI/runtime/persistence bugs)
  - `product`: Issues exposed during specific product/feature execution
  - `uncertain`: Needs operator review to determine classification
- **Auto-Inference**: If not specified, inferred from `issue_type`
- **Example**: `async_dev`

### issue_type
- **Type**: enum
- **Description**: Category of the workflow issue
- **Allowed values**:
  | Type | Description | Auto-Inferred Domain |
  |------|-------------|---------------------|
  | `sequencing` | Feature/task sequencing inconsistencies | `uncertain` |
  | `planning` | Plan-day workflow issues | `async_dev` |
  | `execution_pack` | ExecutionPack content or structure issues | `async_dev` |
  | `state_mismatch` | RunState or state tracking inconsistencies | `async_dev` |
  | `summary_review` | DailyReviewPack or nightly summary issues | `async_dev` |
  | `archive_history` | Archive or historical query issues | `async_dev` |
  | `repo_integration` | Repository or git integration issues | `uncertain` |
  | `recovery_logic` | Recovery or resume workflow issues | `async_dev` |
  | `cli_behavior` | CLI command behavior issues | `async_dev` |
  | `persistence` | File or SQLite persistence issues | `async_dev` |
  | `runtime` | Runtime engine issues | `async_dev` |
  | `other` | Uncategorized issues | `uncertain` |
- **Example**: `execution_pack`

### detected_by
- **Type**: enum (`operator` | `ai_executor` | `review_process` | `automated_check` | `post_analysis`)
- **Description**: Who/what detected this issue
- **Example**: `operator`

### detected_in
- **Type**: string
- **Description**: Context where issue was detected
- **Example**: `plan-day create command`

### description
- **Type**: string
- **Description**: Clear description of the workflow issue
- **Example**: `ExecutionPack referenced wrong feature sequence, pointing to feature 002 instead of 003`

### context_summary
- **Type**: string
- **Description**: What the system was doing when issue was detected - provides repair context
- **Example**: `Reviewing the generated ExecutionPack before starting real execution`
- **Critical**: Required for repair value - explains operational context at detection time

### self_corrected
- **Type**: boolean
- **Description**: Whether the issue was self-corrected during execution
- **Example**: `true`
- **Critical**: Captures issues that were worked around - still useful to track

### requires_followup
- **Type**: boolean
- **Description**: Whether this issue needs future attention/hardening
- **Example**: `true`

### detected_at
- **Type**: datetime (ISO 8601)
- **Description**: When this issue was detected
- **Example**: `2026-04-11T14:30:00`

---

## Strongly Recommended Fields (for Repair Value)

These fields are not strictly required but strongly recommended for debugging and repair.

### suspected_problem
- **Type**: string
- **Description**: What seems wrong - initial hypothesis about root cause
- **Example**: `Feature sequencing logic allowed task to be labeled as feature 003 while foundational work not created`
- **Recommendation**: Always provide when possible for repair value

### temporary_fix
- **Type**: string
- **Description**: How the issue was worked around - immediate response
- **Example**: `Operator manually stopped execution, reviewed ExecutionPack, corrected task flow`
- **Recommendation**: Always provide when a workaround was applied

### reproduction_hint
- **Type**: string
- **Description**: How to investigate or reproduce this issue later
- **Example**: `Initialize a new product, generate early execution planning, inspect ExecutionPack for feature numbering assumptions`
- **Recommendation**: Always provide to enable later investigation

---

## Optional Context Fields

### command_context
- **Type**: string
- **Description**: CLI command that triggered or was running when issue detected
- **Example**: `asyncdev run-day execute`

### expected_behavior
- **Type**: string
- **Description**: What should have happened according to design
- **Example**: `First executable feature in new product flow should be feature 001`

### actual_behavior
- **Type**: string
- **Description**: What actually happened - the observed deviation
- **Example**: `Generated ExecutionPack referenced feature 003 as current feature`

---

## Triage Fields (Feature 019b)

### confidence
- **Type**: enum (`low` | `medium` | `high`)
- **Description**: Confidence level of problem_domain classification
- **Example**: `high`

### escalation_recommendation
- **Type**: enum (`ignore` | `track_only` | `review_needed` | `candidate_issue`)
- **Description**: What should happen with this feedback
- **Allowed values**:
  | Level | Meaning |
  |-------|---------|
  | `ignore` | Not worth tracking |
  | `track_only` | Keep recorded, no action needed |
  | `review_needed` | Should appear in nightly review |
  | `candidate_issue` | Candidate for formal async-dev issue |
- **Example**: `candidate_issue`

### triaged_at
- **Type**: datetime (ISO 8601)
- **Description**: When triage classification was applied
- **Example**: `2026-04-11T15:00:00`

### triage_note
- **Type**: string
- **Description**: Optional explanation of triage decision
- **Example**: `Confirmed async-dev CLI bug after review`

---

## Optional Fields

### product_id
- **Type**: string
- **Description**: Product ID (required when problem_domain=product or uncertain)
- **Example**: `skill-pack-advisor`

### feature_id
- **Type**: string (pattern: `\d{3}-[a-z0-9-]+`)
- **Description**: Feature ID (for product-scoped issues)
- **Example**: `001-intake-schema`

### execution_id
- **Type**: string (pattern: `exec-YYYYMMDD-###`)
- **Description**: Execution ID if issue occurred during specific execution
- **Example**: `exec-20260411-001`

### impact
- **Type**: string
- **Description**: Impact of the issue on workflow
- **Example**: `Manual correction required, execution proceeded with correct feature`

### artifact_reference
- **Type**: object
- **Description**: Reference to relevant artifact(s)
- **Example**:
  ```yaml
  artifact_type: "execution-pack"
  artifact_path: "projects/skill-pack-advisor/execution-packs/exec-20260411-001.md"
  artifact_id: "exec-20260411-001"
  ```

### resolution
- **Type**: enum (`none` | `workaround` | `fixed` | `deferred` | `escalated`)
- **Description**: Resolution status
- **Example**: `workaround`

### resolution_note
- **Type**: string
- **Description**: Notes on how issue was handled
- **Example**: `Manually edited ExecutionPack to correct sequence`

### status
- **Type**: enum (`open` | `investigating` | `resolved` | `closed` | `archived`)
- **Description**: Current tracking status
- **Example**: `open`

### priority
- **Type**: enum (`high` | `medium` | `low`)
- **Description**: Priority for follow-up
- **Example**: `medium`

---

## Template Instances

```yaml
# WorkflowFeedback Instance - async_dev Domain (Full Repair Context)
feedback_id: "wf-20260411-001"
problem_domain: "async_dev"
issue_type: "execution_pack"
detected_by: "operator"
detected_in: "verification"
description: "ExecutionPack referenced a later feature before foundational feature sequencing was established."
context_summary: "Reviewing the generated ExecutionPack before starting real execution against the external repository."
suspected_problem: "Feature sequencing logic in async-dev allowed current task to be labeled as feature 003 while foundational work had not yet been created."
temporary_fix: "Operator manually stopped execution, reviewed the ExecutionPack, and corrected the task flow before continuing."
reproduction_hint: "Initialize a new product, generate early execution planning, and inspect the produced ExecutionPack for feature numbering/order assumptions."
command_context: "asyncdev run-day execute"
expected_behavior: "The first executable feature in a new product flow should be feature 001 or a clearly justified initial feature."
actual_behavior: "Generated ExecutionPack referenced feature 003 as the current feature."
self_corrected: true
requires_followup: true
detected_at: "2026-04-11T23:48:03"
```

```yaml
# WorkflowFeedback Instance - async_dev Domain (Triaged)
feedback_id: "wf-20260411-002"
problem_domain: "async_dev"
issue_type: "cli_behavior"
detected_by: "operator"
detected_in: "status command"
description: "asyncdev status showed wrong phase"
context_summary: "Running status check after execution completed."
suspected_problem: "Phase tracking not updated after execution."
self_corrected: true
requires_followup: true
confidence: "high"
escalation_recommendation: "candidate_issue"
triaged_at: "2026-04-11T15:00:00"
detected_at: "2026-04-11T14:30:00"
```

```yaml
# WorkflowFeedback Instance - product Domain
feedback_id: "wf-20260411-003"
problem_domain: "product"
issue_type: "execution_pack"
detected_by: "operator"
detected_in: "plan-day create"
product_id: "my-app"
feature_id: "001-core"
description: "ExecutionPack referenced wrong feature"
context_summary: "Creating execution plan for first feature."
self_corrected: true
requires_followup: true
detected_at: "2026-04-11T14:30:00"
```

```yaml
# WorkflowFeedback Instance - product Domain
feedback_id: "wf-YYYYMMDD-###"
problem_domain: "product"
issue_type: "execution_pack"
detected_by: "operator"
detected_in: "plan-day create"
product_id: "my-app"
feature_id: "001-core"
description: "ExecutionPack referenced wrong feature"
self_corrected: true
requires_followup: true
detected_at: "2026-04-11T14:30:00"
```

```yaml
# WorkflowFeedback Instance - uncertain Domain
feedback_id: "wf-YYYYMMDD-###"
problem_domain: "uncertain"
issue_type: "repo_integration"
detected_by: "operator"
detected_in: "git operations"
product_id: "my-app"
description: "Git integration issue, unclear source"
self_corrected: false
requires_followup: true
detected_at: "2026-04-11T14:30:00"
```

---

## Storage

### async_dev Domain
- **Location**: `.runtime/workflow-feedback/{feedback_id}.yaml`
- **Format**: YAML
- **SQLite**: `workflow_feedback` table

### product / uncertain Domain
- **Location**: `projects/{product_id}/workflow-feedback/{feedback_id}.yaml`
- **Format**: YAML
- **SQLite**: `workflow_feedback` table with product_id reference

---

## CLI Usage

```bash
# Record with required context_summary
asyncdev feedback record --type cli_behavior --in "status" --description "Wrong phase" --context "Running status check after execution"

# Record with strongly recommended repair fields
asyncdev feedback record --type execution_pack --in "plan-day" --description "Wrong sequence" --context "Reviewing ExecutionPack" --suspected "Feature numbering bug" --workaround "Manual edit" --reproduce "Generate new ExecutionPack and inspect numbering"

# Record with full context
asyncdev feedback record --type cli_behavior --in "status" --description "Wrong phase" --context "Running status check" --command "asyncdev status" --expected "show executing phase" --actual "showed planning phase" --suspected "Phase tracking not updated"

# Record product domain issue
asyncdev feedback record --domain product --product my-app --type execution_pack --description "Wrong sequence" --context "Plan-day workflow" --suspected "Product-specific sequencing issue"

# Triage existing feedback
asyncdev feedback triage --feedback-id wf-001 --domain async_dev --confidence high --escalation candidate_issue

# List feedback
asyncdev feedback list
asyncdev feedback list --domain async_dev
asyncdev feedback list --escalation candidate_issue

# Show details
asyncdev feedback show --feedback-id wf-001

# Summary with domain breakdown
asyncdev feedback summary
```

---

## Validation Checklist

Before saving WorkflowFeedback, verify:

- [ ] `feedback_id` matches pattern `wf-YYYYMMDD-###`
- [ ] `problem_domain` is valid enum (`async_dev`, `product`, `uncertain`)
- [ ] If `problem_domain` is `product` or `uncertain`, `product_id` is provided
- [ ] `issue_type` is valid enum
- [ ] `description` is non-empty
- [ ] `context_summary` is non-empty (required for repair value)
- [ ] `self_corrected` and `requires_followup` are boolean
- [ ] `detected_at` is valid datetime
- [ ] If triaged: `confidence` and `escalation_recommendation` are valid enums
- [ ] (Recommended) `suspected_problem`, `temporary_fix`, `reproduction_hint` provided

---

## Design Philosophy

From Feature 019a + 019b:

1. **Capture first, triage later** - Don't block capture on perfect classification
2. **Auto-inference helps** - Domain inferred from issue_type by default
3. **Keep the model lightweight** - This is not a full issue management system
4. **Record even self-corrected defects** - Hidden defects are still useful to track
5. **Preserve review value** - Feedback should help nightly review, not create noise
6. **Triage enables prioritization** - Confidence and escalation guide action
7. **Uncertain is explicit** - Don't guess when unsure, mark for review

---

## See Also

- `schemas/workflow-feedback.schema.yaml` - Validation rules
- `docs/workflow-feedback.md` - User documentation
- Feature specs: `docs/infra/amazing-async-dev-feature-019a*.md`, `docs/infra/amazing-async-dev-feature-019b*.md`