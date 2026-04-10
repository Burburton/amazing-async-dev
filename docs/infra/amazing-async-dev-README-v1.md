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

### ProductBrief
The minimum structured representation of a product idea.

### FeatureSpec
A bounded feature definition with goals, scope, non-goals, and acceptance criteria.

### RunState
The current working state of a project or feature, used for pause/resume and continuity.

### ExecutionPack
The package given to AI for daytime work.

### ExecutionResult
The structured result returned after daytime execution.

### DailyReviewPack
The nightly summary prepared for fast human review and decision-making.

---

## Core workflow

### 1. plan-day
Choose the most appropriate bounded task for the current day.

### 2. run-day
Let AI execute within a constrained scope and produce structured outputs.

### 3. review-night
Generate a compact nightly review pack for the human.

### 4. resume-next-day
Use the latest decisions and state to continue work the next day.

---

## Repository structure

```text
amazing-async-dev/
├─ README.md
├─ AGENTS.md
├─ docs/
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

The first goal is not to build a complete platform.

The first goal is to prove one thing:

> AI can independently make useful progress on a small feature during the day, and the human can review and redirect it quickly at night.

---

## Initial milestones

### Feature 001 — Core Object System
Define the six core objects with schemas, templates, and examples.

### Feature 002 — Day Loop CLI
Implement the basic commands:
- `plan-day`
- `run-day`
- `review-night`
- `resume-next-day`

### Feature 003 — Single Feature Demo
Run one real feature through the full async day loop.

---

## Success criteria

This repository is successful if it can achieve the following:

1. AI can work independently for several hours on a bounded feature
2. the nightly review takes about 20–30 minutes
3. the human only handles a small number of meaningful decisions
4. the next day resumes from state instead of from repeated explanation

---

## Planned command surface

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

## Near-term implementation strategy

### v0
- local files
- markdown/yaml artifacts
- Python CLI
- manual invocation

### v1
- SQLite-based state
- better pause/resume
- execution logging
- failure recovery

### v2
- optional durable runtime
- optional approval entry points
- optional lightweight dashboard

---

## AGENTS.md expectations

Any AI agent operating in this repository should:

- read the required artifacts before acting
- stay strictly inside task scope
- stop at decision boundaries
- update `RunState`
- produce reviewable outputs
- prepare a useful nightly review pack

---

## Intended user

This project is designed first for:

- solo builders
- part-time builders
- builders with many product ideas but little uninterrupted time
- builders who want AI to work asynchronously, not interactively all day

---

## Long-term vision

Over time, `amazing-async-dev` should become a reliable personal development operating system:

- product idea in
- bounded async execution out
- low-cost nightly review
- stable multi-day continuity
- increasing reuse of artifacts, templates, and patterns

---

## First step

Start with **Feature 001: Core Object System**.

Until the object model is stable, everything else should remain lightweight.
