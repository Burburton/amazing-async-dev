# AGENTS.md

AI Agent behavior rules for `amazing-async-dev` repository.

---

## 1. Mission

This repository serves **day-sized async development loops**.

The goal: AI makes bounded progress during the day, human reviews at night in 20-30 minutes, work resumes the next day from explicit state.

---

## 2. Required Objects

Before any action, read these artifacts:

1. **ProductBrief** (`projects/{product_id}/product-brief.md`)
   - Product scope and constraints

2. **FeatureSpec** (`projects/{product_id}/features/{feature_id}/feature-spec.md`)
   - Feature boundaries and acceptance criteria

3. **RunState** (`projects/{product_id}/runstate.md`)
   - Current execution state

4. **ExecutionPack** (`projects/{product_id}/execution-packs/{execution_id}.md`)
   - Bounded task for today

If any required object is missing or invalid, **STOP** and report the issue.

---

## 3. Hard Rules

### 3.1 Scope Boundary
- **Never** exceed `task_scope` from ExecutionPack
- **Never** expand goals without human approval
- **Stop** at any `stop_condition`

### 3.2 Decision Handling
- When encountering a decision point: **STOP**, record in `decisions_needed`, wait for human
- **Never** make architectural decisions autonomously
- **Always** provide options with recommendations

### 3.3 State Management
- **Always** update RunState after each action
- **Always** set `last_action` and `updated_at`
- **Always** update `current_phase` when phase changes

### 3.4 Output Requirements
- **Always** produce deliverables listed in ExecutionPack
- **Always** leave evidence (files, logs, artifacts)
- **Always** run verification steps
- **Always** generate DailyReviewPack at end of execution

### 3.5 Blocking Behavior
- If blocked: set `current_phase` to `blocked`, add to `blocked_items`
- If decision needed: add to `decisions_needed` with options
- **Never** proceed when blocked or awaiting decision

---

## 4. End-of-run Checklist

Before ending execution, verify:

- [ ] All `deliverables` from ExecutionPack completed?
- [ ] Evidence left in `artifacts_created`?
- [ ] RunState updated with `last_action`?
- [ ] Blocked items recorded if any?
- [ ] Decisions needed recorded if any?
- [ ] `next_recommended_action` written?
- [ ] DailyReviewPack generated?

If any item fails, **complete it before stopping**.

---

## 5. Reference Files

| File | Purpose |
|------|---------|
| `docs/terminology.md` | Consistent naming across artifacts |
| `docs/architecture.md` | Object relationships and flow |
| `docs/operating-model.md` | Day loop phases and responsibilities |
| `schemas/*.schema.yaml` | Field definitions and validation |
| `templates/*.template.md` | Human-readable formats |

---

## 6. Quick Reference

### Phase Transitions
```
planning → executing (task started)
executing → reviewing (task completed)
executing → blocked (blocker encountered)
blocked → executing (blocker resolved)
reviewing → planning (next day resume)
```

### Status Codes
| Status | Meaning |
|--------|---------|
| `success` | All deliverables completed |
| `partial` | Some completed, some skipped |
| `blocked` | Cannot proceed |
| `failed` | Execution error |
| `stopped` | Stop condition met |

### Human Actions
| Action | When to use |
|--------|-------------|
| `approve` | Accept AI recommendation |
| `revise` | Choose different option |
| `defer` | Postpone, work alternative |
| `redefine` | Change question or scope |

---

## 7. Anti-Patterns (FORBIDDEN)

| Anti-Pattern | Consequence |
|--------------|-------------|
| Expanding scope without approval | **STOP immediately** |
| Skipping verification steps | **Invalid execution** |
| Making decisions alone | **Invalid execution** |
| Not updating RunState | **Execution incomplete** |
| No evidence left | **Execution unverifiable** |
| Missing DailyReviewPack | **Execution incomplete** |