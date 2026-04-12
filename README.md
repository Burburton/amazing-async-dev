# amazing-async-dev

**Personal Async AI Development OS**

A lightweight development operating system for solo builders who want AI to make steady progress during the day and only need human review and direction at night.

---

## Why this exists

Most solo builders do not lack ideas.  
They lack uninterrupted build time.

`amazing-async-dev` is designed for a very specific working style:

- AI should be able to make stable progress during the day
- the human should only spend 1–2 hours at night reviewing, correcting, and deciding direction
- work should resume the next day without re-explaining everything

This repository is not trying to be a giant autonomous engineering platform.  
It is trying to be a practical async development operating system for a single builder.

---

## Core problem

If AI is left alone without structure, it tends to:

- drift outside the intended scope
- expand tasks beyond useful boundaries
- lose continuity across days
- produce work that is hard to review quickly
- require too much human re-contextualization

This project solves that by enforcing:

- **artifact-first workflow**
- **day-sized execution**
- **state-based resume**
- **nightly human decision packs**
- **small, closed development loops**

---

## What this repository is

`amazing-async-dev` is an async development core that defines:

- product and feature artifacts
- run state management
- execution packs for daytime AI work
- nightly review packs for fast human review
- a simple day loop:
  - plan the day
  - run the day
  - review at night
  - resume the next day

---

## What this repository is not

This repository is **not**:

- a generic multi-team platform
- a large agent society
- a complex orchestration framework
- a UI-first product
- a plugin marketplace
- a huge spec framework clone

It is intentionally narrow.

---

## Design principles

### 1. Artifact-first
The system moves forward through explicit artifacts, not vague conversation history.

### 2. Day-sized execution
A task should fit into half a day to one day of AI work.

### 3. Human decisions at night
The human should only review what truly requires judgment.

### 4. Resume by state
The next day should start from `RunState`, not from memory reconstruction.

### 5. Stable boundaries
Each execution unit should have a clear scope, stop condition, and expected outputs.

---

## Core objects

| Object | Purpose |
|--------|---------|
| `ProductBrief` | Minimum structured representation of a product idea |
| `FeatureSpec` | Bounded feature with goals, scope, acceptance criteria |
| `RunState` | Current working state (pause/resume/continuity) |
| `ExecutionPack` | Package for daytime AI execution |
| `ExecutionResult` | Structured outcome of daytime execution |
| `DailyReviewPack` | Nightly summary for fast human review |

---

## Core workflow

```
plan-day → run-day → review-night → resume-next-day
```

| Phase | Description |
|-------|-------------|
| `plan-day` | Choose bounded task for the day |
| `run-day` | AI executes within constrained scope |
| `review-night` | Generate compact review pack for human |
| `resume-next-day` | Continue from decisions and state |

---

## Repository structure

```text
amazing-async-dev/
├─ README.md
├─ AGENTS.md
├─ docs/
│  ├─ vision.md
│  ├─ operating-model.md
│  ├─ architecture.md
│  ├─ terminology.md
│  └─ decisions/
├─ schemas/
├─ templates/
├─ skills/
├─ workflows/
├─ runtime/
├─ cli/
├─ projects/
├─ tests/
└─ examples/
```

---

## Current phase

**v0 — Single Feature Daily Loop**

The first goal: prove AI can independently make useful progress on a small feature during the day, and the human can review and redirect it quickly at night.

---

## Testing

The project has comprehensive test coverage using pytest.

### Run tests

```bash
python -m pytest tests/ -v
```

### Test coverage

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_cli_init.py` | 6 | init create/status commands |
| `test_cli_new_product.py` | 8 | new-product create/list |
| `test_cli_new_feature.py` | 7 | new-feature create/list |
| `test_plan_day.py` | 11 | plan-day create/show |
| `test_review_night.py` | 11 | review-night generate/show |
| `test_resume_next_day.py` | 20 | continue-loop/status/unblock/handle-failed |
| `test_runstate_transitions.py` | 18 | Phase transitions |
| `test_artifact_generation.py` | 23 | YAML/Markdown format |
| `test_error_handling.py` | 21 | Error handling |
| `test_complete_archive.py` | 16 | Completion & archive flow |
| `test_sqlite_state_store.py` | 20 | SQLite persistence layer |
| `test_execution_logging.py` | 23 | Execution logging & recovery |
| `test_live_api_hardening.py` | 27 | Live API error handling & retry |
| `test_ux_improvements.py` | 13 | UX improvements (status, paths, next-step) |
| `test_backfill.py` | 17 | Historical archive backfill |
| `test_workflow_feedback.py` | 29 | Workflow feedback capture |
| `test_feedback_promotion.py` | 22 | Feedback promotion / issue escalation |
| `test_execution_policy.py` | 38 | Execution policy / auto-continue rules |
| **Total** | **482** | |

### Test categories

- **CLI commands**: All asyncdev commands have test coverage
- **Phase transitions**: RunState transitions between planning/executing/reviewing/blocked
- **Artifact format**: YAML block extraction and markdown generation
- **Error handling**: Missing state, invalid inputs, corrupted files
- **SQLite persistence**: Structured state store with recovery queries
- **Recovery classification**: Stop-point classification and resume eligibility

---

## Implementation status

| Feature | Status | Description |
|---------|--------|-------------|
| 001 | ✅ Complete | Core Object System - schemas, templates, examples |
| 002 | ✅ Complete | Day Loop CLI - plan-day, run-day, review-night, resume-next-day |
| 003 | ✅ Complete | Single Feature Demo - full async day loop |
| 004 | ✅ Complete | Dual Execution Mode - external tool + live API |
| 005 | ✅ Complete | Failure/Blocker/Decision Flow |
| 006 | ✅ Complete | Initialization Commands - init, new-product, new-feature |
| 007 | ✅ Complete | Tests & Stability - 240 tests passing |
| 008 | ✅ Complete | Completion & Archive Flow - complete-feature, archive-feature |
| 009 | ✅ Complete | SQLite State Store - structured persistence layer |
| 010 | ✅ Complete | Execution Logging & Recovery Hardening - recovery classification, inspect-stop |
| 011 | ✅ Complete | Live API Mode Hardening - API failure classification, retry logic, error handling |
| 012 | ✅ Complete | UX/Ergonomics Improvements - enhanced status, path display, next-step guidance |
| 013 | ✅ Complete | Historical Archive Backfill - backfill historical features into archive system |
| 014 | ✅ Complete | Archive Query / History Inspection - archive list/show with filters |
| 015 | ✅ Complete | Daily Management Summary / Decision Inbox - nightly review layer |
| 016 | ✅ Complete | Decision Template System - structured decision templates |
| 017 | ✅ Complete | Archive-aware Plan Agent - history-aware planning |
| 018 | ✅ Complete | Limited Batch Operations - batch status, archive, backfill, summary |
| 019a | ✅ Complete | Workflow Feedback Capture - lightweight issue capture for system hardening |
| 019b | ✅ Complete | Workflow Feedback Triage - confidence levels, problem domain classification |
| 019c | ✅ Complete | Feedback Promotion / Issue Escalation - controlled promotion to formal follow-up |
| 020 | ✅ Complete | Low-Interruption Execution Policy - auto-continue safe transitions, pause for risky |

---

## Feature Lifecycle

### Active Phases
- `planning` → `executing` → `reviewing` → `blocked`
- Blocked features: use `asyncdev resume-next-day unblock`

### Completion Phase
- `completed` - Feature marked as finished
- Use: `asyncdev complete-feature mark`
- Validates: no blockers, no pending decisions

### Archive Phase
- `archived` - Feature preserved for future reference
- Use: `asyncdev archive-feature create`
- Archives stored in: `projects/{product}/archive/{feature}/archive-pack.yaml`

### ArchivePack captures
- `delivered_outputs` - What was actually delivered
- `acceptance_result` - Were criteria satisfied?
- `lessons_learned` - What worked / what to improve
- `reusable_patterns` - Patterns for future features
- `decisions_made` - Key decisions during implementation
- `unresolved_followups` - Items still open

---

## Success criteria

1. AI can work independently for several hours on a bounded feature
2. Nightly review takes about 20–30 minutes
3. Human handles only a small number of meaningful decisions
4. Next day resumes from state instead of repeated explanation
5. Completed features archived with lessons for future work

---

## Planned CLI

```bash
asyncdev init
asyncdev new-product
asyncdev new-feature
asyncdev plan-day
asyncdev run-day
asyncdev review-night
asyncdev resume-next-day
asyncdev complete-feature mark
asyncdev archive-feature create
asyncdev sqlite history --project {id} --feature {id}
asyncdev sqlite transitions --project {id}
asyncdev sqlite recovery --project {id} --feature {id}
asyncdev sqlite features --project {id}
asyncdev sqlite snapshot --project {id}
asyncdev inspect-stop show --project {id}
asyncdev inspect-stop history --project {id}
asyncdev inspect-stop guidance --project {id}

# Feature 014: Archive Query
asyncdev archive list
asyncdev archive list --recent --limit 10
asyncdev archive list --product {id} --has-patterns
asyncdev archive show --feature {id}

# Feature 015: Daily Management Summary
asyncdev summary today
asyncdev summary decisions
asyncdev summary issues
asyncdev summary next-day

# Feature 018: Batch Operations
asyncdev status --all-features --project {id}
asyncdev archive list --product {id} --has-lessons
asyncdev backfill batch --project {id} --dry-run
asyncdev backfill batch --project {id} --all --limit 5
asyncdev summary all-projects

# Feature 019a: Workflow Feedback
asyncdev feedback record --scope system --type cli_behavior --description "..."
asyncdev feedback record --scope product --product {id} --type execution_pack --description "..."
asyncdev feedback list
asyncdev feedback list --followup-needed
asyncdev feedback show --feedback-id {id}
asyncdev feedback update --feedback-id {id} --resolution fixed
asyncdev feedback summary

# Feature 019b: Workflow Feedback Triage
asyncdev feedback triage --feedback-id {id} --confidence high --domain async_dev --escalation-recommendation candidate_issue
asyncdev feedback triage --feedback-id {id} --confidence uncertain --triage-note "Needs review"

# Feature 019c: Feedback Promotion
asyncdev feedback promote --feedback-id {id} --reason system_bug --note "Priority fix"
asyncdev feedback promotions list
asyncdev feedback promotions list --status open --reason system_bug
asyncdev feedback promotions show --promotion-id {id}
asyncdev feedback promotions update --promotion-id {id} --status addressed --note "Fixed"

# Feature 020: Execution Policy
asyncdev policy show
asyncdev policy set --mode balanced
asyncdev policy modes
asyncdev policy scope-flag --set-flag true
asyncdev policy scope-flag --clear
asyncdev policy risky-actions --list
asyncdev policy risky-actions --clear-all
```

---

## Implementation roadmap

| Version | Features |
|---------|----------|
| v0 | Local files, markdown/yaml artifacts, Python CLI, manual invocation |
| v1 | SQLite-based state, better pause/resume, execution logging, failure recovery |
| v2 | Optional durable runtime, approval entry points, lightweight dashboard |

---

## Intended user

- solo builders
- part-time builders
- builders with many product ideas but little uninterrupted time
- builders who want AI to work asynchronously, not interactively all day

---

## First step

Start with **Feature 001: Core Object System**.

See `docs/infra/amazing-async-dev-feature-001-core-object-system.md` for details.