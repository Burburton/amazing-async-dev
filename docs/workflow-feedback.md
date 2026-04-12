# Workflow Feedback Capture, Triage & Promotion

Feature 019a: Lightweight mechanism to capture workflow/system issues during async-dev usage.
Feature 019b: Structured triage layer for workflow feedback classification.
Feature 019c: Feedback promotion to formal follow-up records.

---

## Why This Exists

When using `amazing-async-dev` in real scenarios, you may notice issues with the system itself:

- ExecutionPack points to wrong feature sequence
- Summary output misses important state
- CLI commands show inconsistent behavior
- Recovery guidance seems incorrect

These issues are often worked around manually, then forgotten. This feature ensures they are captured explicitly for future hardening, with a triage layer to classify them properly, and a promotion mechanism to turn them into formal follow-up work.

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

### Promote to formal follow-up (Feature 019c)

```bash
# Promote triaged feedback to formal follow-up record:
asyncdev feedback promote \
  --feedback-id wf-20260411-001 \
  --reason system_bug \
  --note "Priority fix needed for CLI stability"
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

## Promotion Model (Feature 019c)

### What is Promotion?

Promotion creates a **formal follow-up record** from triaged workflow feedback. It's the explicit step between triage and external issue creation.

**Key boundaries:**
- Promotion creates internal follow-up records, NOT external GitHub issues
- Promotion requires triage first (confidence + escalation set)
- Each feedback can only be promoted once (no duplicates)
- Source feedback gets `promotion_status=promoted` after promotion

### Promotion Reasons

| Reason | When to use |
|--------|-------------|
| `system_bug` | Confirmed bug in async-dev system |
| `ux_issue` | User experience problem |
| `workflow_improvement` | Workflow enhancement opportunity |
| `documentation_gap` | Missing or unclear documentation |
| `integration_issue` | Integration problem |
| `other` | Uncategorized |

### Follow-up Status

| Status | Meaning |
|--------|---------|
| `open` | Promoted but not yet reviewed |
| `reviewed` | Reviewed and confirmed |
| `in_progress` | Work being done |
| `addressed` | Fix implemented |
| `closed` | Follow-up complete |

### Promotion Commands

```bash
# Promote triaged feedback
asyncdev feedback promote --feedback-id wf-001 --reason system_bug --note "Priority fix"

# List promotions
asyncdev feedback promotions list

# Filter by status
asyncdev feedback promotions list --status open

# Show promotion details
asyncdev feedback promotions show --promotion-id promo-001

# Update promotion status
asyncdev feedback promotions update --promotion-id promo-001 --status addressed --note "Fixed"
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

Promotions appear in `promotions` section:

```yaml
promotions:
  promoted_count: 3
  open_count: 2
  promotion_ids:
    - "promo-20260412-001"
    - "promo-20260412-002"
  summaries:
    - "CLI status command shows wrong phase"
    - "Persistence layer needs optimization"
```

---

## Storage

| Domain | Location |
|--------|----------|
| `async_dev` | `.runtime/workflow-feedback/{id}.yaml` |
| `product` | `projects/{product}/workflow-feedback/{id}.yaml` |
| `uncertain` | `projects/{product}/workflow-feedback/{id}.yaml` |
| **promotions** | `.runtime/feedback-promotions/{id}.yaml` |

All feedback and promotions are indexed in SQLite for quick queries.

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

## Workflow Stages

```
capture → triage → promotion → follow-up → external
```

1. **capture**: Record the workflow issue with basic details
2. **triage**: Add classification (domain, confidence, escalation)
3. **promotion**: Create formal follow-up record (internal)
4. **follow-up**: Track until addressed
5. **external**: (future) Optional GitHub issue creation

---

## See Also

- `templates/workflow-feedback.template.md` - Feedback schema reference
- `templates/promoted-feedback.template.md` - Promotion schema reference
- `schemas/workflow-feedback.schema.yaml` - Feedback validation rules
- `schemas/promoted-feedback.schema.yaml` - Promotion validation rules
- Feature specs: `docs/infra/amazing-async-dev-feature-019a*.md`, `docs/infra/amazing-async-dev-feature-019b*.md`, `docs/infra/amazing-async-dev-feature-019c*.md`