# Daily Management Summary / Decision Inbox

Feature 015 strengthens the nightly review layer for the "day execution / night review" operating model.

---

## Overview

The system now aggregates daytime execution data into a management-friendly nightly view:
- Clear summary of what was accomplished
- Explicit distinction between resolved and unresolved issues
- Structured decision inbox with blocking status
- Actionable next-day recommendations

---

## CLI Commands

### Summary Commands

```bash
asyncdev summary today              # Full management summary
asyncdev summary decisions          # Focus on decision inbox
asyncdev summary issues             # Focus on issues summary
asyncdev summary next-day           # Focus on tomorrow's recommendation
```

### Review-Night Command

```bash
asyncdev review-night generate     # Generate DailyReviewPack
asyncdev review-night show          # Display latest review pack
```

---

## Structured Outputs

### Issues Summary

The `issues_summary` field provides explicit resolved/unresolved distinction:

```yaml
issues_summary:
  encountered:
    - description: "Test fixture path issue"
      severity: medium
      timestamp: "2026-04-11T10:30"
  resolved:
    - description: "Test fixture path issue"
      resolution: "Adjusted fixture setup"
      resolved_at: "2026-04-11T11:00"
  unresolved:
    - description: "LSP type errors in llm_adapter"
      severity: low
      blocking: false
      estimated_impact: "Pre-existing, not blocking"
```

### Decision Inbox

Each decision item now includes:

```yaml
decisions_needed:
  - decision_id: "dec-001"
    decision: "SQLite index vs file-based query"
    decision_type: technical
    options:
      - "SQLite primary"
      - "Files primary"
    recommendation: "Files primary"
    recommendation_reason: "Matches artifact-first philosophy"
    impact: "Archive query performance"
    blocking_tomorrow: false
    defer_impact: "Minor - current approach works"
    urgency: medium
```

### Next-Day Recommendation

Structured recommendation for tomorrow:

```yaml
next_day_recommendation:
  action: "Continue with Feature 016"
  preconditions:
    - "Feature 015 tests passing"
  safe_to_execute: true
  blocking_decisions: []
  estimated_scope: half-day
```

---

## Management View

### `asyncdev summary today`

Shows full management summary:

```
┌─ Daily Management Summary ──────────────────────────────┐
│ 2026-04-11 | demo-product | 014-archive-query           │
├──────────────────────────────────────────────────────────┤
│ Today's Goal: Implement archive query commands          │
│                                                          │
│ Completed (4):                                           │
│   - runtime/archive_query.py                             │
│   - cli/commands/archive.py                              │
│                                                          │
│ Issues:                                                  │
│   Encountered: 2                                         │
│   Resolved: 1                                            │
│   Unresolved: 1                                          │
│                                                          │
│ Decisions Needed: 1                                      │
│   [dec-001] SQLite vs Files                              │
│                                                          │
│ Tomorrow: Continue with Feature 016                      │
│   Safe to execute                                        │
└──────────────────────────────────────────────────────────┘
```

### `asyncdev summary decisions`

Decision inbox view:

```
┌─ Decision Inbox ────────────────────────────────────────┐
│ Decision 1: dec-001                                      │
│   Question: SQLite index vs file-based query?            │
│   Type: technical                                        │
│                                                          │
│   Options:                                               │
│     → Files primary (recommended)                        │
│       SQLite primary                                     │
│                                                          │
│   Recommendation: Files primary                          │
│     Matches artifact-first philosophy                    │
│                                                          │
│   Impact: Archive query performance                      │
│   Defer impact: Minor - current approach works           │
│                                                          │
│ Human Actions:                                           │
│   approve  - Accept AI recommendation                    │
│   revise   - Choose different option                     │
│   defer    - Postpone, work on alternative               │
│   redefine - Change question or scope                    │
└──────────────────────────────────────────────────────────┘
```

---

## Workflow

### Night Review (20-30 min target)

1. **Scan completion (3 min)**: `asyncdev summary today`
2. **Review issues (5 min)**: `asyncdev summary issues`
3. **Process decisions (10-15 min)**: `asyncdev summary decisions`
4. **Confirm tomorrow (2-3 min)**: `asyncdev summary next-day`

### Decision Processing

```bash
asyncdev resume-next-day continue-loop --decision approve
asyncdev resume-next-day continue-loop --decision revise --revise-choice "SQLite primary"
asyncdev resume-next-day continue-loop --decision defer
```

---

## Schema Updates

### New Required Fields

| Field | Description |
|-------|-------------|
| `issues_summary` | Structured issue breakdown |
| `next_day_recommendation` | Structured tomorrow's plan |

### New Decision Fields

| Field | Description |
|-------|-------------|
| `decision_id` | Unique identifier |
| `decision_type` | technical/scope/priority/design |
| `blocking_tomorrow` | Boolean - blocks next day |
| `defer_impact` | String - impact of deferring |

### ExecutionResult Addition

| Field | Description |
|-------|-------------|
| `issues_resolved` | Issues resolved during execution |

---

## Key Features

1. **Resolved/Unresolved Distinction**: Clear visibility into what's handled vs pending
2. **Blocking Status**: Know which decisions actually block progress
3. **Safe-to-Execute**: Know if tomorrow's plan is ready to run
4. **Decision Type Classification**: Categorize decisions for easier processing
5. **Risk Watch Items**: Surface potential risks before they become blockers

---

## Implementation Files

| File | Purpose |
|------|---------|
| `runtime/review_pack_builder.py` | Enhanced pack building |
| `cli/commands/summary.py` | Management view commands |
| `schemas/daily-review-pack.schema.yaml` | Updated schema (v2.0) |
| `schemas/execution-result.schema.yaml` | Added issues_resolved |
| `tests/test_daily_management.py` | Feature 015 tests |

---

## Acceptance Criteria

| Criteria | Status |
|----------|--------|
| nightly review easier to understand | ✅ |
| completed work summarized clearly | ✅ |
| unresolved issues surfaced clearly | ✅ |
| resolved vs unresolved distinguishable | ✅ |
| decision-needed items actionable | ✅ |
| next-day recommendations explicit | ✅ |
| nightly layer matches operating model | ✅ |

---

## Backward Compatibility

New fields added alongside existing fields:
- `issues_summary` + `problems_found` (legacy)
- `next_day_recommendation` + `tomorrow_plan` (legacy)
- All existing tests pass unchanged