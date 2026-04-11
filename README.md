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
| **Total** | **124** | |

### Test categories

- **CLI commands**: All asyncdev commands have test coverage
- **Phase transitions**: RunState transitions between planning/executing/reviewing/blocked
- **Artifact format**: YAML block extraction and markdown generation
- **Error handling**: Missing state, invalid inputs, corrupted files

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
| 007 | ✅ Complete | Tests & Stability - 124 tests passing |

---

## Success criteria

1. AI can work independently for several hours on a bounded feature
2. Nightly review takes about 20–30 minutes
3. Human handles only a small number of meaningful decisions
4. Next day resumes from state instead of repeated explanation

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