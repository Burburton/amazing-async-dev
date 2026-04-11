# Archive-aware Planning

Feature 017: Archive-aware Plan Agent

---

## What is Archive-aware Planning?

Archive-aware planning enhances `plan-day` to use historical context from archived features when generating next-day recommendations.

Instead of planning purely from current state, the system now:
- Uses lessons learned from similar completed features
- Applies reusable patterns from prior work
- Accounts for unresolved decisions and blockers
- Provides explainable rationale for recommendations

---

## Why This Matters

`amazing-async-dev` accumulated valuable historical data:
- ArchivePack with lessons_learned and reusable_patterns
- Decision template outcomes
- Blocker and recovery context
- Execution history

This data should inform future planning, not just sit in storage.

---

## How It Works

### 1. Archive-aware Context

When planning, the system:

1. Loads recent archives from `projects/{product}/archive/`
2. Extracts lessons and patterns from ArchivePacks
3. Matches them against the current task keywords
4. Returns applicable lessons/patterns

Example:
```yaml
archive_references:
  - feature_id: "001-core-objects"
    lessons_count: 3
    patterns_count: 2
```

### 2. Decision-aware Constraints

The system checks:
- Pending decisions in `decisions_needed`
- Which decisions block tomorrow (`blocking_tomorrow: true`)
- High urgency decisions requiring immediate attention

If blocking decisions exist:
- `safe_to_execute: false`
- Preconditions include "Resolve decision: ..."

### 3. Blocker-aware Constraints

The system checks:
- Active blockers in `blocked_items`
- Recovery classification (blocked, failed, awaiting_decision)
- Safe alternatives that can proceed despite blockers

If blocked:
- Main task may be deferred
- Alternative tasks are suggested

---

## Planning Output

Enhanced ExecutionPack now includes:

```yaml
execution_id: "exec-20260411-001"
task_id: "Implement archive query"
goal: "Execute: Implement archive query"

safe_to_execute: true
estimated_scope: "half-day"

preconditions:
  - "Resolve decision: schema format"

rationale:
  primary_reason: "Task recommended based on historical patterns"
  confidence: "high"
  lessons_applied:
    - lesson: "Small tasks work better"
      source: "001-core-objects"
  patterns_applied:
    - pattern: "Schema + Template structure"
      source: "001-core-objects"
  warnings: []

archive_references:
  - feature_id: "001-core-objects"
    lessons_count: 3
    patterns_count: 2

planning_context:
  archive_summary:
    total_archives: 5
    lessons_available: 12
  decision_summary:
    blocking_count: 0
  blocker_summary:
    classification: "ready_to_resume"
```

---

## CLI Usage

### plan-day create

```bash
asyncdev plan-day create --project demo --task "Add CLI commands"
```

Output shows:
- ExecutionPack preview
- Rationale panel
- Warnings if any
- Lessons/patterns applied

### --show-context

```bash
asyncdev plan-day create --show-context
```

Shows full planning context including:
- Archives considered
- Lessons/patterns available
- Decision/blocker state

### plan-day context

```bash
asyncdev plan-day context --project demo
```

Shows planning context without creating ExecutionPack.

---

## Design Principles

### 1. Planning remains bounded
Archive awareness improves recommendations, not replaces bounded execution.

### 2. Reuse history where it matters
Only use archive data when it can materially improve planning quality.

### 3. Respect current execution reality
Current blockers and decisions always take precedence over historical patterns.

### 4. Explain why
Every recommendation has rationale explaining the decision factors.

### 5. Improve trust, not complexity
The system feels smarter without becoming opaque.

---

## Implementation Files

| File | Purpose |
|------|---------|
| `runtime/plan_aware_agent.py` | Archive/decision/blocker-aware planning logic |
| `cli/commands/plan_day.py` | Enhanced plan-day with awareness |
| `schemas/execution-pack.schema.yaml` | New fields for planning context |
| `tests/test_plan_aware_agent.py` | Tests for awareness functions |

---

## Validation Questions

This feature should help answer:

- What should tomorrow's day-run do?
- Why is that the best next step?
- What prior lesson or pattern supports this choice?
- Is a pending decision blocking this plan?
- Is a blocker still preventing this plan?
- Is the proposed next step safe and bounded?

---

## Success Criteria

1. `plan-day` produces better next-day recommendations
2. Planning uses archive lessons/patterns
3. Planning accounts for unresolved decisions
4. Planning accounts for blocker context
5. Planning output is explainable
6. Operator needs less manual reasoning

---

## Related Features

- Feature 014: Archive Query / History Inspection
- Feature 015: Daily Management Summary / Decision Inbox
- Feature 016: Decision Template System
- Feature 008: Completion & Archive Flow