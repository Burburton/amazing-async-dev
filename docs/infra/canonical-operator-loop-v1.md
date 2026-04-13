# canonical-operator-loop-v1

## Title
Canonical Operator Loop Definition (Features 026-036)

## Purpose
Define one clear, repeatable daily loop for async-dev that can be explained in one page.

---

## The Canonical Daily Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                    OPERATOR DAILY LOOP                          │
│                                                                 │
│   EVENING (Day N)                                               │
│   ┌─────────────┐                                               │
│   │ review-night│  Generate nightly operator pack               │
│   └─────────────┘                                               │
│         ↓                                                       │
│   ┌─────────────────────┐                                       │
│   │ DailyReviewPack     │  Consolidated decision artifact       │
│   └─────────────────────┘                                       │
│         ↓                                                       │
│   Human reviews 20-30 min, makes decisions                      │
│         ↓                                                       │
│   MORNING (Day N+1)                                             │
│   ┌─────────────┐                                               │
│   │resume-next-day│  Carry forward prior night context          │
│   └─────────────┘                                               │
│         ↓                                                       │
│   ┌─────────────────────┐                                       │
│   │ Prior context shown │  Doctor status, recommended action    │
│   └─────────────────────┘                                       │
│         ↓                                                       │
│   ┌─────────────┐                                               │
│   │ plan-day    │  Shape today's bounded execution target       │
│   └─────────────┘                                               │
│         ↓                                                       │
│   ┌─────────────────────┐                                       │
│   │ ExecutionPack       │  Planning mode inferred, bounds set   │
│   └─────────────────────┘                                       │
│         ↓                                                       │
│   DAYTIME                                                       │
│   ┌─────────────┐                                               │
│   │ run-day     │  Execute aligned with planning intent         │
│   └─────────────┘                                               │
│         ↓                                                       │
│   ┌─────────────────────┐                                       │
│   │ ExecutionResult     │  Structured output with evidence      │
│   └─────────────────────┘                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Command Responsibilities (No Overlap)

| Command | Responsibility | Input | Output |
|---------|---------------|-------|--------|
| `review-night` | **Consolidate nightly signals** | ExecutionResult, Doctor assessment | DailyReviewPack |
| `resume-next-day` | **Carry forward prior night context** | DailyReviewPack, RunState | Continuation summary |
| `plan-day` | **Shape bounded execution target** | Resume context, FeatureSpec | ExecutionPack with planning mode |
| `run-day` | **Execute aligned with plan intent** | ExecutionPack | ExecutionResult |

**Clear separation**:
- `review-night` produces the decision artifact
- `resume-next-day` consumes it, does not plan
- `plan-day` shapes the execution target, does not execute
- `run-day` executes, does not replan

---

## Planning Modes (Feature 035)

`plan-day` infers the day's mode from resume context:

| Mode | Trigger | Execution Behavior |
|------|---------|-------------------|
| `continue_work` | HEALTHY doctor status | Normal bounded execution |
| `recover_and_continue` | ATTENTION_NEEDED with recovery hints | Prioritize recovery first |
| `verification_first` | Verification concerns present | Complete verification before expansion |
| `closeout_first` | COMPLETED_PENDING_CLOSEOUT | Archive/review before new work |
| `blocked_waiting_for_decision` | BLOCKED state | Decisions required before forward execution |

---

## Execution Intent Alignment (Feature 036)

`run-day` displays before execution:
- Planning mode
- Bounded target
- Prior doctor status
- Alignment status

Drift warnings:
- Blocked mode + forward execution → warns about decisions needed
- Closeout-first + expansion work → warns about premature expansion
- Verification-first + non-verification work → warns about missing verification

---

## Artifact Flow

```
Day N Evening:
  ExecutionResult → DailyReviewPack → Human Review

Day N+1 Morning:
  DailyReviewPack → resume-next-day → Prior Context Display
  Prior Context → plan-day → ExecutionPack (with planning_mode)
  
Day N+1 Daytime:
  ExecutionPack → run-day → ExecutionResult
  
Loop repeats.
```

---

## Key Principles

1. **`review-night` is the nightly decision artifact** - consolidates all signals (doctor, recovery, feedback, closeout) into one pack for human review.

2. **`resume-next-day` carries context forward** - does not replan, just shows prior night's signals and recommended action.

3. **`plan-day` shapes the bounded target** - uses resume context to infer planning mode, sets execution bounds.

4. **`run-day` executes aligned** - respects planning intent, warns on drift, stays inside bounds.

5. **Graceful fallback when context missing** - all commands work without prior artifacts.

---

## Terminal Commands (Canonical Loop)

```bash
# Evening - Day N
asyncdev review-night generate --product-id {id}

# Morning - Day N+1  
asyncdev resume-next-day continue-loop --product-id {id} --decision approve
asyncdev plan-day create --product-id {id} --feature-id {fid} --task "..."

# Daytime
asyncdev run-day --product-id {id} --mode external
```

---

## Validation Checklist

- [x] Loop can be explained in one page
- [x] Command responsibilities do not overlap
- [x] Each command has one clear input/output
- [x] Planning modes are well-defined
- [x] Drift warnings are rule-based and lightweight
- [x] Fallback behavior documented
- [x] Matches Features 033-036 implementation direction

---

## Status

This canonical loop definition is valid as of Features 026-036 consolidation phase.

Next step: Run real dogfooding to validate usability.