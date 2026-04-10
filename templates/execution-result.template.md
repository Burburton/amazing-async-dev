# ExecutionResult Template

> Structured outcome of daytime AI execution.

---

## Metadata

| Field | Value |
|-------|-------|
| Object Type | `ExecutionResult` |
| Purpose | Capture execution outcome for RunState and review |
| Update Frequency | Never (immutable) |
| Owner | Run-day workflow |

---

## Required Fields

### execution_id
Execution run identifier.

```
Example: exec-20240115-001
```

### status
Overall execution status.

```
Values: success, partial, blocked, failed, stopped
Example: success
```

### completed_items
Items successfully completed.

```
Example:
  - product-brief.schema.yaml
  - feature-spec.schema.yaml
```

### artifacts_created
Artifacts produced during execution.

```
Example:
  - name: product-brief.schema.yaml
    path: schemas/product-brief.schema.yaml
    type: file
```

### verification_result
Verification step results.

```
Example:
  passed: 3
  failed: 0
  skipped: 0
  details:
    - Required fields: passed
    - JSON Schema: passed
    - Terminology: passed
```

### issues_found
Issues discovered during execution.

```
Example:
  - type: warning
    description: Minor naming inconsistency
    severity: low
    resolution: fixed
```

### blocked_reasons
Reasons execution was blocked.

```
Example: [] (empty if not blocked)
```

### decisions_required
Decisions needing human input.

```
Example:
  - decision: schema-format-choice
    context: All schema files need format
    options: YAML, JSON
    recommendation: YAML
    urgency: high
```

### recommended_next_step
AI recommendation for continuation.

```
Example: Continue with RunState and ExecutionPack schemas
```

---

## Optional Fields

### metrics
Execution metrics.

```
Example:
  files_read: 5
  files_written: 2
  actions_taken: 12
  decisions_made: 0
```

### notes
Free-form execution notes.

### warnings
Non-blocking warnings.

### duration
Total execution time.

```
Example: 2h30m
```

---

## Template Instance

```yaml
execution_id: "exec-[YYYYMMDD]-[###]"
status: "[success|partial|blocked|failed|stopped]"
completed_items:
  - "[ITEM_1]"
  - "[ITEM_2]"
artifacts_created:
  - name: "[ARTIFACT_NAME]"
    path: "[FILE_PATH]"
    type: "[file|document|log|data]"
verification_result:
  passed: [COUNT]
  failed: [COUNT]
  skipped: [COUNT]
  details:
    - "[DETAIL_1]"
    - "[DETAIL_2]"
issues_found:
  - type: "[error|warning|note]"
    description: "[DESCRIPTION]"
    severity: "[high|medium|low]"
    resolution: "[fixed|pending|deferred]"
blocked_reasons:
  - reason: "[WHY_BLOCKED]"
    impact: "[IMPACT]"
    since: "[TIMESTAMP]"
decisions_required:
  - decision: "[DECISION_NAME]"
    context: "[CONTEXT]"
    options:
      - "[OPTION_1]"
      - "[OPTION_2]"
    recommendation: "[AI_RECOMMENDATION]"
    urgency: "[high|medium|low]"
recommended_next_step: "[NEXT_ACTION]"

# Optional
metrics:
  files_read: [COUNT]
  files_written: [COUNT]
  actions_taken: [COUNT]
  decisions_made: [COUNT]
notes: "[FREE_FORM]"
warnings:
  - "[WARNING_1]"
duration: "[DURATION]"
```

---

## Usage Rules

### For RunState Update
| ExecutionResult Field | RunState Field |
|----------------------|----------------|
| completed_items | completed_outputs |
| artifacts_created | artifacts |
| blocked_reasons | blocked_items |
| decisions_required | decisions_needed |
| recommended_next_step | next_recommended_action |

### For DailyReviewPack
| ExecutionResult Field | DailyReviewPack Field |
|----------------------|----------------------|
| completed_items | what_was_completed |
| artifacts_created | evidence |
| issues_found | problems_found |
| blocked_reasons | blocked_items |
| decisions_required | decisions_needed |
| recommended_next_step | tomorrow_plan |

---

## Validation Checklist

- [ ] execution_id matches ExecutionPack
- [ ] status is valid enum
- [ ] if blocked, blocked_reasons has items
- [ ] if partial, completed_items non-empty
- [ ] verification_result has counts

---

## Lifecycle Notes

| Aspect | Detail |
|--------|--------|
| Created by | run-day workflow |
| Updated | Never (immutable) |
| Consumed by | review-night, resume-next-day |
| Storage | `projects/{project_id}/execution-results/{execution_id}.md` |
| Format | Markdown with YAML block |

---

## Usage

### For RunState
- Update RunState based on completed_items
- Add blocked_reasons to blocked_items
- Add decisions_required to decisions_needed
- Set next_recommended_action

### For Review Pack
- Map to DailyReviewPack fields
- Include evidence for completed items
- List decisions with options

### For Next Day
- Use recommended_next_step for planning
- Resume from updated RunState