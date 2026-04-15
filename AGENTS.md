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

## 7. ExecutionResult Convention (External Tool Mode)

When executing via external tools (OpenCode, Claude Code, etc.), **MUST** write ExecutionResult to the agreed path.

### Write Path
```
projects/{project_id}/execution-results/{execution_id}.md
```

Or in demo mode:
```
examples/single-feature-day-loop/execution-results/{execution_id}.md
```

### Required Format
```yaml
execution_id: "{execution_id}"
status: success|partial|blocked|failed|stopped
completed_items:
  - "[item_1]"
  - "[item_2]"
artifacts_created:
  - name: "[artifact_name]"
    path: "[file_path]"
    type: file|artifact|log
verification_result:
  passed: N
  failed: M
  skipped: K
  details:
    - "[detail_1]"
issues_found:
  - "[issue_1]"
blocked_reasons:
  - "[reason_1]"
decisions_required:
  - "[decision_1]"
recommended_next_step: "[next_action]"
metrics:
  files_read: N
  files_written: M
  actions_taken: K
notes: "[execution_notes]"
duration: "[estimated_duration]"
```

### After Writing ExecutionResult
1. User runs: `asyncdev resume-next-day`
2. System detects ExecutionResult at agreed path
3. RunState updated, DailyReviewPack generated
4. Day loop continues

---

## 8. Anti-Patterns (FORBIDDEN)

| Anti-Pattern | Consequence |
|--------------|-------------|
| Expanding scope without approval | **STOP immediately** |
| Skipping verification steps | **Invalid execution** |
| Making decisions alone | **Invalid execution** |
| Not updating RunState | **Execution incomplete** |
| No evidence left | **Execution unverifiable** |
| Missing DailyReviewPack | **Execution incomplete** |

---

## 9. Interactive Frontend Verification Gate (Feature 038)

### 9.1 Classification Rule
When executing a feature/task, determine `verification_type`:
- `backend_only`: No browser verification required
- `frontend_noninteractive`: Browser verification optional
- `frontend_interactive`: Browser verification mandatory
- `frontend_visual_behavior`: Browser verification mandatory
- `mixed_app_workflow`: Browser verification mandatory for frontend portion

### 9.2 Completion Gate (FR-7)
A frontend-interactive task MUST NOT be marked `status: success` unless:
1. `browser_verification.executed: true` and results recorded
2. OR valid `browser_verification.exception_reason` recorded with explanation

### 9.3 Playwright Invocation Policy (FR-9)
When `verification_type` requires browser verification:
- MUST invoke `/playwright` skill after server startup
- MUST NOT stop at "server ready" without browser run
- MUST capture evidence (scenarios, screenshots)

### 9.4 Orchestration Continuation (FR-10)
After server startup for frontend verification:
- MUST continue to browser verification stage
- MUST handle long-running server processes
- MUST poll for server readiness before Playwright launch

### 9.5 Exception Handling
If browser verification cannot run, MUST record structured exception:

| Exception Reason | When to Use |
|------------------|-------------|
| `playwright_unavailable` | Playwright tooling not available in environment |
| `environment_blocked` | Environment constraints prevent execution |
| `browser_install_failed` | Browser installation failed |
| `ci_container_limitation` | CI/container environment cannot run browser |
| `missing_credentials` | Required credentials not available for test path |
| `deterministic_blocker` | Known blocker prevents meaningful verification |
| `reclassified_noninteractive` | Feature reclassified as non-interactive |

### 9.6 Evidence Requirements
For browser verification, ExecutionResult MUST include:
- `browser_verification.executed`: boolean
- `browser_verification.passed`: count of passed scenarios
- `browser_verification.failed`: count of failed scenarios
- `browser_verification.scenarios_run`: list of executed scenarios
- `browser_verification.screenshots`: paths to screenshot artifacts (optional)
- `browser_verification.duration`: time spent

### 9.7 Core Principle

> **For interactive frontend work, environment setup is not verification.**
> **Server startup is a prerequisite step, not a validation result.**

---

## 10. Governance Boundary Rules (Feature 039)

### 10.1 Repository Mode Classification
Before execution, determine `ownership_mode` from project-link.yaml:
- `self_hosted`: Product and orchestrator in same repo (Mode A)
- `managed_external`: Product in separate repo (Mode B)

If project-link.yaml missing, assume `self_hosted`.

### 10.2 Product Truth Rule (MANDATORY)
Product-owned artifacts MUST live in the product repo:
- ProductBrief, FeatureSpec, feature completion reports
- Dogfood reports, friction logs, phase summaries
- Product memory artifacts, north-star documents

For Mode B, these artifacts belong in the target product repository, NOT in async-dev.

### 10.3 Orchestration Truth Rule (MANDATORY)
Orchestration-owned artifacts MUST live in async-dev:
- ExecutionPack, ExecutionResult, orchestration runstate
- Verification records, continuation state
- Project-link metadata, orchestration telemetry

For Mode B, these artifacts belong in async-dev's `projects/{product_id}/`.

### 10.4 projects/ Directory Meaning

| Repository | projects/ Meaning |
|------------|-------------------|
| Product repo (Mode A/B) | Product-local canonical development memory |
| async-dev (Mode A) | Same as product repo (coexistent) |
| async-dev (Mode B) | Managed-project orchestration workspace |

### 10.5 Decision Test (MANDATORY)
Before creating/storing an artifact, apply this test:

1. Does this describe the product? → Product repo
2. Does this describe async-dev execution? → async-dev
3. Would this matter if async-dev disappeared? → Product repo
4. Would this matter if async-dev workflow changed but product unchanged? → async-dev

### 10.6 Anti-Patterns (FORBIDDEN)

| Anti-Pattern | Consequence |
|--------------|-------------|
| Product Repo Hollowing | **STOP** - Product must own its canonical docs |
| Orchestrator Archive Overreach | **STOP** - async-dev is not product archive |
| Mixed Ownership Without Boundary | **STOP** - Must classify ownership before storing |
| Runtime State Confused with Product State | **STOP** - Orchestration runstate ≠ product history |

### 10.7 Example: amazing-visual-map

When orchestrating `amazing-visual-map` from async-dev:

| In amazing-visual-map | In amazing-async-dev |
|----------------------|----------------------|
| ProductBrief | ExecutionPacks |
| FeatureSpecs | ExecutionResults |
| Friction logs | Orchestration runstate |
| Dogfood reports | Project-link.yaml |
| Phase reports | Continuation state |

This ensures `amazing-visual-map` remains self-contained while async-dev orchestrates.