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

### 9.8 Verification Completion Enforcement (Feature 059)

**MANDATORY**: After dev server startup for frontend verification, AI agent MUST:

1. Continue to browser verification stage immediately
2. NOT stop at "server ready" without running verification
3. Complete verification within timeout (default: 120 seconds)
4. If blocked, record exception_reason in ExecutionResult

**Anti-Patterns (FORBIDDEN)**:
- Starting dev server → stopping → claiming "ready"
- Attempting manual Playwright → failing → not retrying with CLI
- Leaving `verification_pending` state without completion

**Timeout Behavior**:
- If 120s elapsed without verification → auto-record timeout exception
- `ExecutionResult.browser_verification.executed = false`
- `exception_reason = "verification_timeout"`

**Enforcement Hook**:
- `runtime/verification_session.py` tracks session state
- `runtime/verification_enforcer.py` checks timeout
- System reminder sent if AI stops during `verification_pending`
- ExecutionResult locked during `verification_pending` state

**Session State Flow**:
```
pending → server_started → verification_in_progress → complete/timeout/exception
```

### 9.9 System-Owned Frontend Verification Orchestration (Feature 060)

**CRITICAL**: Frontend verification is now **system-owned**, not agent-optional.

The async-dev runtime now orchestrates frontend verification automatically:
- `run_day` automatically invokes verification orchestrator for frontend tasks
- `resume_next_day` triggers post-external verification for frontend tasks
- Success progression blocked without valid `orchestration_terminal_state`

#### Terminal States

| Terminal State | Valid for Success? | Meaning |
|-----------------|---------------------|---------|
| `not_required` | ✅ Yes | Backend-only task, no verification needed |
| `success` | ✅ Yes | Browser verification completed successfully |
| `exception_accepted` | ✅ Yes | Valid exception recorded (playwright unavailable, etc.) |
| `skipped_by_policy` | ✅ Yes | Explicitly skipped via policy rule |
| `failure` | ❌ No | Verification failed (tests/scenarios failed) |
| `timeout` | ❌ No | Verification timed out (120s exceeded) |
| `required_not_started` | ❌ No | Verification required but never started |
| `in_progress` | ❌ No | Verification still running |

#### Integration Points

1. **run_day live/mock mode**: Orchestrator invoked after engine execution
2. **resume_next_day**: Post-external verification triggered for frontend tasks
3. **Success gate**: `orchestration_terminal_state` checked before marking success

#### ExecutionResult Requirements

For frontend tasks, ExecutionResult MUST now include:
```yaml
orchestration_terminal_state: "success|failure|timeout|exception_accepted|..."
browser_verification:
  executed: true|false
  passed: N
  failed: M
  exception_reason: (if not executed)
```

#### Architecture

```
Feature 056 = capability layer (browser_verifier, dev_server_manager)
Feature 059 = enforcement primitives (verification_session, verification_enforcer)
Feature 060 = orchestration integration (browser_verification_orchestrator)
```

The orchestrator (`runtime/browser_verification_orchestrator.py`) is the integration layer that:
- Determines verification requirement
- Starts dev server
- Runs browser verification
- Captures structured results
- Applies timeout policies
- Returns terminal state

### 9.10 External Execution Closeout Orchestration (Feature 061)

**CRITICAL**: External execution closeout is now **system-owned**, not fire-and-forget.

When running `run-day --mode external --trigger`, the system:
- Triggers external tool execution
- Enters a closeout phase (polls for result readiness)
- Detects missing frontend verification
- Invokes Feature 060 post-external verification when needed
- Classifies final closeout state
- Persists closeout results in ExecutionResult

#### Primary vs Fallback Path

| Path | When | Behavior |
|------|------|----------|
| **Primary** | `run-day --trigger` | Closeout in same lifecycle, verification run immediately |
| **Fallback** | `resume-next-day` | Recovery for interrupted/incomplete closeout |

**Key Change**: `resume-next-day` is now the fallback recovery path, not the primary completion mechanism.

#### Closeout States

| State | Meaning |
|-------|---------|
| `external_execution_triggered` | External tool invoked |
| `external_execution_pending` | Polling for result |
| `external_execution_result_detected` | ExecutionResult file found |
| `post_external_verification_required` | Frontend verification needed but missing |
| `post_external_verification_running` | Feature 060 verification executing |
| `post_external_verification_completed` | Verification finished |
| `external_execution_stalled` | No progress detected |
| `closeout_timeout` | Polling exceeded 120s timeout |
| `closeout_completed_success` | All closeout steps successful |
| `closeout_completed_failure` | Closeout failed |
| `closeout_recovery_required` | Fallback recovery needed |

#### Terminal Classifications

| Classification | Valid for Success? | Meaning |
|----------------|---------------------|---------|
| `success` | ✅ Yes | Closeout completed, verification valid |
| `failure` | ❌ No | Closeout failed |
| `verification_failure` | ❌ No | Frontend verification failed |
| `closeout_timeout` | ❌ No | Polling timeout |
| `stalled` | ❌ No | External execution stalled |
| `recovery_required` | ❌ No | Fallback recovery needed |

#### ExecutionResult Requirements

For external execution closeout, ExecutionResult MUST include:
```yaml
closeout_state: "closeout_completed_success|closeout_timeout|..."
closeout_terminal_state: "success|failure|recovery_required|..."
closeout_result:
  execution_result_detected: true|false
  verification_required: true|false
  verification_completed: true|false
  poll_attempts: N
  elapsed_seconds: M
  recovery_required: true|false
  recovery_reason: (if recovery required)
```

#### Architecture

```
Feature 056 = capability layer (browser_verifier, dev_server_manager)
Feature 059 = enforcement primitives (verification_session, verification_enforcer)
Feature 060 = frontend verification orchestration (browser_verification_orchestrator)
Feature 061 = external closeout lifecycle (external_execution_closeout)
```

The closeout orchestrator (`runtime/external_execution_closeout.py`) is responsible for:
- Polling for ExecutionResult readiness (10s intervals, max 120s)
- Detecting missing frontend verification
- Invoking Feature 060 orchestration when needed
- Classifying terminal closeout state
- Persisting closeout state to ExecutionResult

#### Anti-Patterns (FORBIDDEN)

| Anti-Pattern | Consequence |
|--------------|-------------|
| External mode as pure fire-and-forget | **STOP** - Closeout must run |
| resume-next-day as only verification recovery | **STOP** - Primary path moved forward |
| Re-implementing browser verification in closeout | **STOP** - Use Feature 060 orchestration |
| Freeform logs as closeout truth | **STOP** - Structured state required |

#### Integration Points

1. **run_day external --trigger**: Primary closeout path (polls for result, runs verification)
2. **resume_next_day**: Fallback recovery path (checks closeout_state, completes if needed)

### 9.11 Controlled Frontend Verification Execution Recipe (Feature 062)

**CRITICAL**: Frontend verification execution is now **controlled**, not ad hoc shell improvisation.

External agents often start the frontend dev server and then stop without:
- Running browser verification
- Writing structured ExecutionResult
- Reaching terminal execution outcome

Feature 062 provides a **controlled execution recipe** that enforces a deterministic flow.

#### Recipe Stages (Mandatory Sequence)

| Stage | Action | Transition |
|-------|--------|-------------|
| INITIALIZING | Detect framework | → SERVER_STARTING |
| SERVER_STARTING | Start dev server (controlled) | → READINESS_PROBING |
| READINESS_PROBING | Probe readiness with timeout | → BROWSER_VERIFICATION |
| BROWSER_VERIFICATION | Run Playwright verification | → RESULT_PERSISTING |
| RESULT_PERSISTING | Write structured ExecutionResult | → COMPLETED_SUCCESS |

**STOPPING AT "SERVER READY" IS FORBIDDEN.**

#### Port Discovery Strategy

| Strategy | Priority | Method |
|----------|----------|--------|
| stdout parsing | Primary | Parse dev server output for port (e.g., "Local: http://localhost:5173") |
| port probe | Fallback | Probe known ports in PORT_RANGE if stdout parsing fails |

#### Canonical Entry Point

**CLI command (preferred):**
```bash
asyncdev frontend-verify-run --project <project_id>
```

This recipe guarantees:
- Dev server startup is controlled (not foreground-blocking)
- Port/URL discovery via stdout parsing + fallback probe
- Readiness probe before browser verification
- **MANDATORY** browser verification (not stopping at "server ready")
- Structured execution result persisted automatically

#### ExecutionPack Instruction

When `verification_type` requires browser verification, ExecutionPack includes:
```yaml
frontend_verification_recipe:
  use_recipe: true
  invocation_command: "asyncdev frontend-verify-run --project {project_id}"
  stages:
    - SERVER_STARTING
    - READINESS_PROBING
    - BROWSER_VERIFICATION
    - RESULT_PERSISTING
  stop_at_ready_forbidden: true
  result_required: true
```

External agents MUST follow this instruction instead of ad hoc shell commands.

#### Architecture

```
Feature 056 = capability layer (browser_verifier, dev_server_manager)
Feature 059 = enforcement primitives (verification_session, verification_enforcer)
Feature 060 = frontend verification orchestration (browser_verification_orchestrator)
Feature 061 = external closeout lifecycle (external_execution_closeout)
Feature 062 = execution recipe (frontend_verification_recipe) ← upstream hardening
```

The recipe orchestrator (`runtime/frontend_verification_recipe.py`) ensures:
- Controlled subprocess startup (not foreground-blocking)
- Stdout capture for port detection
- Bounded readiness probe
- Mandatory browser verification invocation
- Structured result persistence

#### Anti-Patterns (FORBIDDEN)

| Anti-Pattern | Consequence |
|--------------|-------------|
| Foreground-blocking `npm run dev` | **STOP** - Use controlled recipe |
| Stopping at "server ready" | **STOP** - Must complete verification |
| Guessing port manually | **STOP** - Use stdout parsing + probe |
| Improvising shell commands | **STOP** - Use CLI recipe |
| Skipping result persistence | **STOP** - Mandatory stage |

#### Integration Points

1. **asyncdev frontend-verify-run**: Canonical recipe entry point
2. **external_tool_engine**: Injects recipe instruction into ExecutionPack
3. **Features 060/061**: Receive structured upstream execution results

---

### 9.12 Frontend Verification Tool Selection (Feature 063)

**CRITICAL**: Frontend verification MUST use Python playwright, NOT MCP skill.

#### Background

The `/playwright` MCP skill invokes an external browser process that blocks the execution flow. This causes:
- Progress blocked waiting for MCP response
- No structured result persistence
- Cannot integrate with `frontend_verification_recipe.py`

#### Required Approach

Use `runtime/browser_verifier.py` via Python:

```python
from runtime.frontend_verification_recipe import FrontendVerificationRecipe

recipe = FrontendVerificationRecipe(
    project_path=Path('path/to/project'),
    execution_id='test-001',
)
result = recipe.execute()
```

#### Anti-Patterns (FORBIDDEN)

| Anti-Pattern | Consequence |
|--------------|-------------|
| Using `/playwright` MCP skill for frontend testing | **STOP** - Will block progress |
| Invoking Playwright MCP without Python wrapper | **STOP** - No structured results |
| Manual browser testing without recipe | **STOP** - Use controlled recipe |

#### Valid MCP Use Cases

The `/playwright` MCP skill is still valid for:
- Manual debugging during development
- Exploratory UI testing
- One-off browser interactions

But NOT for automated frontend verification in async-dev execution.

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