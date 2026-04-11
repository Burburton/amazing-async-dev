# Workflow Feedback Capture & Triage

Feature 019a: Lightweight mechanism to capture workflow/system issues during async-dev usage.
Feature 019b: Structured triage layer for workflow feedback classification.

---

## Why This Exists

When using `amazing-async-dev` in real scenarios, you may notice issues with the system itself:

- ExecutionPack points to wrong feature sequence
- Summary output misses important state
- CLI commands show inconsistent behavior
- Recovery guidance seems incorrect

These issues are often worked around manually, then forgotten. This feature ensures they are captured explicitly for future hardening, with a triage layer to classify them properly.

---

## Quick Start

### Record a workflow issue

```bash
# During execution, you notice an issue:
asyncdev feedback record \
  --domain product \
  --product my-app \
  --type execution_pack \
  --in "plan-day create" \
  --description "ExecutionPack referenced wrong feature"

# System-level issue (CLI bug) - domain auto-inferred:
asyncdev feedback record \
  --type cli_behavior \
  --in "status command" \
  --description "asyncdev status showed wrong phase"

# Record with immediate triage:
asyncdev feedback record \
  --type cli_behavior \
  --in "status" \
  --description "CLI bug" \
  --confidence high \
  --escalation candidate_issue
```

### Triage existing feedback

```bash
# Add triage classification after review:
asyncdev feedback triage \
  --feedback-id wf-20260411-001 \
  --domain async_dev \
  --confidence high \
  --escalation candidate_issue \
  --note "Confirmed async-dev CLI bug"
```

### List feedback

```bash
# All feedback
asyncdev feedback list

# Filter by domain
asyncdev feedback list --domain async_dev

# Filter by escalation level
asyncdev feedback list --escalation candidate_issue

# Only items needing follow-up
asyncdev feedback list --followup-needed

# Filter by product
asyncdev feedback list --product my-app
```

### View details

```bash
asyncdev feedback show --feedback-id wf-20260411-001
```

### Update status

```bash
asyncdev feedback update --feedback-id wf-20260411-001 --resolution fixed --status resolved
```

### View summary

```bash
asyncdev feedback summary
```

---

## Problem Domain Types (Feature 019b)

| Domain | Usage | Storage |
|--------|-------|---------|
| `async_dev` | Issue in amazing-async-dev system itself | `.runtime/workflow-feedback/` |
| `product` | Issue in specific product being built | `projects/{product}/workflow-feedback/` |
| `uncertain` | Needs operator review to determine | `projects/{product}/workflow-feedback/` |

### Auto-Inference (Feature 019b)

When `--domain` is not specified, problem_domain is auto-inferred from `issue_type`:

| Issue Type | Default Domain |
|------------|----------------|
| `cli_behavior` | `async_dev` |
| `persistence` | `async_dev` |
| `runtime` | `async_dev` |
| `recovery_logic` | `async_dev` |
| `planning` | `async_dev` |
| `execution_pack` | `async_dev` |
| `state_mismatch` | `async_dev` |
| `summary_review` | `async_dev` |
| `archive_history` | `async_dev` |
| `repo_integration` | `uncertain` |
| `sequencing` | `uncertain` |
| `other` | `uncertain` |

Operator can override during triage.

---

## Issue Types

| Type | Description |
|------|-------------|
| `sequencing` | Feature/task ordering inconsistencies |
| `planning` | Plan-day workflow issues |
| `execution_pack` | ExecutionPack content/structure problems |
| `state_mismatch` | RunState tracking inconsistencies |
| `summary_review` | DailyReviewPack issues |
| `archive_history` | Archive query/backfill problems |
| `repo_integration` | Git/repository issues |
| `recovery_logic` | Resume/recovery workflow bugs |
| `cli_behavior` | CLI command bugs |
| `persistence` | File/SQLite storage issues |
| `runtime` | Runtime engine problems |
| `other` | Uncategorized |

---

## Triage Model (Feature 019b)

### Confidence Levels

| Level | Meaning |
|-------|---------|
| `low` | Classification uncertain, needs review |
| `medium` | Reasonable confidence, may need verification |
| `high` | Confirmed classification |

### Escalation Recommendations

| Level | Meaning |
|-------|---------|
| `ignore` | Not worth tracking, minor issue |
| `track_only` | Keep recorded, no action needed |
| `review_needed` | Should appear in nightly review |
| `candidate_issue` | Candidate for formal async-dev issue |

---

## Key Concepts

### Self-corrected issues

Even if you fix an issue yourself during execution, record it:

```bash
asyncdev feedback record --self-corrected --description "Manually corrected sequence"
```

Self-corrected defects are still valuable for system hardening.

### Follow-up marking

Mark whether future attention is needed:

```bash
# Needs follow-up (default)
asyncdev feedback record --followup --description "Issue needs investigation"

# Minor issue, no follow-up needed
asyncdev feedback record --no-followup --description "Minor, handled"
```

### Uncertain classification

When you're unsure where the issue belongs:

```bash
asyncdev feedback record \
  --domain uncertain \
  --product my-app \
  --type repo_integration \
  --description "Unclear if git issue is system or product"
```

Mark as `uncertain` and triage during nightly review.

---

## Nightly Review Integration

Workflow feedback appears in DailyReviewPack under `workflow_feedback` section:

```yaml
workflow_feedback:
  encountered_today: 2
  items:
    - feedback_id: "wf-20260411-001"
      problem_domain: "async_dev"
      issue_type: "execution_pack"
      confidence: "high"
      escalation_recommendation: "candidate_issue"
      self_corrected: true
      requires_followup: true
      triaged: true
      summary: "ExecutionPack referenced wrong feature"
  followup_needed_count: 1
  self_corrected_count: 1
  async_dev_count: 1
  product_count: 0
  uncertain_count: 0
  candidate_issue_count: 1
  review_needed_count: 0
```

This ensures workflow issues are visible during nightly review with triage information.

---

## Storage

| Domain | Location |
|--------|----------|
| `async_dev` | `.runtime/workflow-feedback/{id}.yaml` |
| `product` | `projects/{product}/workflow-feedback/{id}.yaml` |
| `uncertain` | `projects/{product}/workflow-feedback/{id}.yaml` |

All feedback is also indexed in SQLite for quick queries.

---

## When to Record

| Scenario | Example |
|----------|---------|
| Unexpected behavior | "asyncdev status showed wrong phase" |
| Manual correction made | "Had to edit ExecutionPack manually" |
| Missing information | "Review pack missed blocking issue" |
| System bug | "CLI crashed on invalid input" |
| Uncertain source | "Git integration issue, unclear if system or product" |

---

## When NOT to Record

Do NOT record for:

- Product feature bugs (use product issue tracking)
- User learning curve mistakes
- Expected behavior that seems wrong (file a documentation issue)

---

## See Also

- `templates/workflow-feedback.template.md` - Full schema reference
- `schemas/workflow-feedback.schema.yaml` - Validation rules
- Feature spec: `docs/infra/amazing-async-dev-feature-019a-workflow-feedback-capture.md`
- Feature spec: `docs/infra/amazing-async-dev-feature-019b-workflow-feedback-triage.md`