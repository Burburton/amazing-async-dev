# async-dev Platform Architecture / Product Positioning

## Metadata

- **Document Type**: `platform architecture / product positioning / strategy spec`
- **Status**: `Proposed`
- **Owner**: `async-dev`
- **Scope**: `platform-level`
- **Purpose**: `Define async-dev as an execution platform rather than a loose collection of automation features`
- **Related Tracks**:
  - `execution kernel stabilization`
  - `verification / closeout / recovery`
  - `operator-facing products`
  - `policy / recipe standardization`

---

## 1. Executive Summary

`async-dev` should be positioned and evolved as an:

> **Async execution platform for real software development**

Its primary value is **not** merely generating code or wrapping agents. Its primary value is enabling software work to be:

- started in a structured way,
- executed across multiple steps and time horizons,
- verified through explicit completion logic,
- recovered when interrupted,
- escalated to humans only when necessary,
- resumed with preserved execution state.

This platform direction is stronger and more differentiated than treating async-dev as a set of disconnected automation features.

The recommended strategic move is:

- keep `async-dev` as the **execution kernel**,
- define narrow and useful **operator surfaces** on top,
- standardize **policy / recipe layers** for different work types,
- avoid unbounded expansion into many loosely connected repos or dashboards.

---

## 2. Product Positioning

## 2.1 What async-dev Is

`async-dev` is a platform for **asynchronous, stateful, verifiable software execution**.

It should be understood as a system that helps drive work from:

- intent
- to execution
- to verification
- to recovery
- to completion

with humans participating selectively and asynchronously.

In product terms, async-dev is best positioned as a combination of:

- **execution engine**
- **workflow/runtime coordinator**
- **human-in-the-loop async operator system**

## 2.2 What async-dev Is Not

`async-dev` should **not** primarily be positioned as:

- just another coding agent wrapper,
- a generic chat interface with tools,
- a dashboard-first product without runtime depth,
- a loose collection of scripts and viewers,
- a speculative workflow repo disconnected from actual execution.

This distinction is important because many systems can generate code, but far fewer can reliably:

- track execution state,
- prove completion,
- recover after interruption,
- support low-interruption human decision making.

---

## 3. Strategic Thesis

The platform’s core thesis is:

> The bottleneck in AI-assisted development is not only code generation. It is reliable execution continuity.

In practice, real software work repeatedly fails on issues like:

- tasks start but do not finish cleanly,
- frontend work starts a server but verification never completes,
- external tools lose the thread,
- operator visibility is poor,
- state is fragmented,
- humans are interrupted too often or too late,
- completion claims are ambiguous.

`async-dev` becomes valuable when it solves these problems better than ordinary coding-agent workflows.

Therefore, the strategic priority is:

1. make execution continuous,
2. make completion verifiable,
3. make interruption recoverable,
4. make human decisions asynchronous and low-friction,
5. make system state inspectable and operable.

---

## 4. Platform Layer Model

The platform should be organized into three primary layers.

## 4.1 Layer A — Execution Kernel

This is the most important layer and should remain the core of async-dev.

### Responsibilities

- run lifecycle management
- execution pack generation
- execution result persistence
- verification orchestration
- closeout handling
- recovery / resume flows
- asynchronous decision hooks
- state persistence and continuity

### Why It Matters

This layer is the hard-to-rebuild core. It is the main source of platform defensibility.

### Examples of Kernel Concerns

- when a run starts
- what artifacts define a run
- whether required verification completed
- what terminal state a run reached
- whether recovery is required
- how interrupted work resumes safely

## 4.2 Layer B — Operator Surface

This layer provides human-facing operational control and visibility.

### Responsibilities

- current run visibility
- blocked / waiting status
- recovery action surfaces
- decision handling surfaces
- verification visibility
- artifact inspection entry points
- explicit operator actions

### Why It Matters

A strong kernel without a usable operator surface remains difficult to manage in real use. This layer turns async-dev into an operable system.

### Examples of Operator Products

- Recovery Console
- Decision Inbox
- Verification Console
- Run Status View
- Artifact Trace Explorer

## 4.3 Layer C — Policy / Recipe Layer

This layer determines how different classes of work should be executed.

### Responsibilities

- task-type-specific execution recipes
- frontend validation recipe
- backend verification recipe
- security / review / test gates
- escalation policies
- approval policies
- specialist / skill-pack selection rules
- risk-based execution strategy

### Why It Matters

Without this layer, every task follows a generic flow and the system remains brittle. Policy and recipe standardization make the platform adaptive and reliable.

### Examples

- frontend tasks require controlled server startup + browser verification
- risky tasks require stronger review gates
- long-running tasks use low-interruption escalation paths
- infrastructure tasks may use different verification logic than UI tasks

---

## 5. Canonical Platform Entities

The platform should define and standardize the core entities it operates on.

## 5.1 Run

Represents a single execution attempt or execution lifecycle unit.

### Typical Fields

- `run_id`
- `product_id`
- `feature_id` or task context
- `mode`
- `status`
- `started_at`
- `completed_at`
- `terminal_state`

## 5.2 ExecutionPack

Represents the structured input package for execution.

### Typical Fields

- objective
- constraints
- required deliverables
- execution instructions
- verification requirements
- policy hints
- artifact destinations
- linked context

## 5.3 ExecutionResult

Represents the structured result of an execution.

### Typical Fields

- completion summary
- verification result
- closeout state
- terminal state
- recovery requirement
- linked artifacts
- error / failure details

## 5.4 VerificationState

Represents required validation state for an execution.

### Typical Fields

- verification required
- verification type
- verification started
- verification completed
- verification success/failure
- failure reason
- accepted exception reason

## 5.5 CloseoutState

Represents post-execution terminalization progress.

### Typical Fields

- closeout started
- closeout in progress
- closeout completed
- closeout timeout
- recovery required

## 5.6 RecoveryState

Represents whether and how an interrupted or incomplete execution can continue.

### Typical Fields

- recovery required
- recovery reason
- suggested action
- resumable from state
- operator decision required

## 5.7 DecisionRequest

Represents a structured request for human input.

### Typical Fields

- decision type
- urgency
- context summary
- options
- default path
- timeout / escalation rule

## 5.8 DecisionResponse

Represents the human decision outcome.

### Typical Fields

- decision
- rationale
- responder
- timestamp
- follow-up action

## 5.9 ArtifactReference

Represents a structured pointer to execution artifacts.

### Typical Fields

- artifact type
- path / identifier
- linked run
- linked feature
- creation time

---

## 6. Canonical Platform Flows

The platform should explicitly define the flows it must support.

## 6.1 Normal Execution Flow

1. objective / feature selected
2. execution pack prepared
3. run starts
4. work is executed
5. verification occurs
6. closeout occurs
7. terminal result is persisted

## 6.2 Verification Flow

1. determine whether verification is required
2. run verification using canonical recipe/orchestrator
3. persist verification state
4. feed verification outcome into success gating

## 6.3 Closeout Flow

1. execution returns control
2. closeout checks for missing terminal conditions
3. missing verification or incomplete result is handled
4. closeout reaches success/failure/recovery state

## 6.4 Recovery Flow

1. run enters incomplete or stalled state
2. structured recovery state is emitted
3. operator or system chooses recovery action
4. execution resumes or retries
5. new result persists updated state

## 6.5 Decision Flow

1. system determines human input is required
2. decision request is created
3. human responds asynchronously
4. execution continues based on structured response

---

## 7. Core Platform Principles

## 7.1 Stateful by Default

The system should preserve enough structured state to resume execution meaningfully.

## 7.2 Verification Before Celebration

A task is not complete because an agent says so. It is complete when required verification and closeout conditions are satisfied.

## 7.3 Recovery Is a First-Class Path

Interruptions and partial failures are normal. Recovery should be a designed flow, not an afterthought.

## 7.4 Human Attention Is Expensive

The platform should minimize unnecessary interruption and ask for input only when structurally required.

## 7.5 Artifacts Are Source of Truth

System truth should live in structured execution artifacts rather than freeform chat or logs alone.

## 7.6 Narrow Operator Surfaces Beat Premature Mega-Dashboards

Build focused operator products first. Do not jump immediately to a giant all-in-one platform shell.

---

## 8. Current Strengths

The platform already has meaningful early strengths.

### Existing Strength Areas

- spec-driven execution orientation
- execution pack / result model direction
- explicit work on verification and closeout
- asynchronous / low-interruption intent
- awareness of recovery and resume semantics
- active dogfooding in real development scenarios

These are not trivial. They suggest the foundation for a differentiated platform already exists.

---

## 9. Current Weaknesses / Platform Gaps

The current system still has important gaps that should shape the next phase.

### Major Gaps

- execution completion still becomes ambiguous in real scenarios
- frontend verification/closeout reliability is still maturing
- operator visibility is insufficient
- state model likely needs more unification
- too many adjacent ideas risk diluting the main platform
- product boundaries across repos are not yet fully clear
- some flows are still too dependent on agent improvisation

These are platform-maturity problems, not signs that the direction is wrong.

---

## 10. Near-Term Strategic Priorities

The next phase should focus on a small number of strategic priorities rather than broad expansion.

## Priority 1 — Stabilize the Execution Kernel

This is the top priority.

### Focus Areas

- verification reliability
- closeout reliability
- terminal state standardization
- recovery signaling
- structured result truthfulness
- dogfooding under real frontend and multi-step cases

### Success Condition

Runs become meaningfully more trustworthy and less ambiguous.

## Priority 2 — Introduce One Narrow Operator Surface

Do not build a giant platform UI yet.

Recommended first operator surface candidates:

- **Execution Recovery Console**
- **Decision Inbox**
- **Verification Console**

Recommended first choice:

> **Execution Recovery Console**

This best complements current kernel work and addresses real operator pain.

## Priority 3 — Standardize Policy / Recipe Layer

Focus on a small number of high-value recipes first.

Recommended early recipes:

- frontend verification recipe
- external closeout recipe
- human decision escalation policy
- verification gating policy

---

## 11. Recommended Product Path

The recommended sequence for platform evolution is:

## Phase 0 — Platform Definition

Create and align around the platform-level architecture and positioning.

### Output

- this positioning document
- canonical layer model
- canonical entity model
- canonical flow model

## Phase 1 — Kernel Stabilization

Focus on making execution, verification, closeout, and recovery structurally reliable.

### Output

- stronger execution truth model
- better verification reliability
- clearer recovery states
- stable dogfooding results

## Phase 2 — One Operator Product

Build one focused operator-facing surface, not a mega dashboard.

### Recommended First Product

- **Execution Recovery Console**

## Phase 3 — Decision Surface

Add **Decision Inbox** to support low-interruption human-in-the-loop operation.

## Phase 4 — Unified Platform Shell

Only after the kernel and one or two operator surfaces are stable should async-dev move toward a unified platform shell.

---

## 12. Recommended First Operator Product

## 12.1 Execution Recovery Console

This is the recommended first operator surface.

### Why This Is the Best First Choice

- directly reflects kernel maturity needs
- clearly different from content viewers like briefing viewer
- solves a real operator pain point
- forces recovery state, suggested actions, and artifact linking to become cleaner
- strengthens platform operability without overreaching

### Core Responsibilities

- list executions in `recovery_required`
- show why each execution needs recovery
- surface suggested next action
- allow continue / retry / resume actions
- show key linked artifacts and last known result state

### Why Not Start With a Giant Control Center

A giant control center is tempting, but likely too broad at this stage. Narrow operator tools will produce better product clarity and better kernel feedback.

---

## 13. Platform Success Criteria

The platform should be considered meaningfully stronger when the following become true.

## 13.1 Execution Reliability

- real runs are less likely to stall ambiguously
- terminal states are clearer
- verification and closeout behave consistently

## 13.2 Recovery Usability

- incomplete runs surface explicit recovery states
- next steps are understandable
- recovery actions are easier to perform

## 13.3 Human Decision Quality

- decision requests are structured and low-friction
- human intervention is minimized but effective
- asynchronous approval paths are practical

## 13.4 Operator Clarity

- operators can tell what is happening now
- blocked reasons are visible
- next actions are clear

## 13.5 Platform Coherence

- repos and features feel part of one platform direction
- core object model is increasingly standardized
- new work reinforces the platform instead of fragmenting it

---

## 14. Things to Avoid

The platform should explicitly avoid the following failure modes.

### 14.1 Feature Sprawl Without Platform Cohesion

Do not keep adding isolated features without checking whether they strengthen the kernel, operator surface, or policy layer.

### 14.2 Premature All-in-One UI

Do not build a giant platform shell before the underlying kernel and operator states are clean enough.

### 14.3 Repo Fragmentation Without Clear Role Boundaries

Do not let multiple repos grow without a clear relationship to the platform model.

### 14.4 Prompt-Only “Fixes”

Do not substitute runtime/state/design fixes with instruction-only patches when the problem is structural.

### 14.5 Ambiguous Completion Semantics

Do not let “done” be inferred loosely from logs or agent claims when artifacts and verification should define truth.

---

## 15. Decision Framework for Future Work

When considering any new feature or project, ask:

1. Does this strengthen the **execution kernel**?
2. Does this provide a clear **operator surface**?
3. Does this standardize or improve the **policy / recipe layer**?

If the answer is no to all three, the work is likely not a current platform priority.

This framework should guide roadmap discipline.

---

## 16. Suggested Next Moves

## Immediate Next Move 1

Continue kernel stabilization and dogfooding of recent verification/closeout work until real runs are meaningfully more reliable.

## Immediate Next Move 2

Start a spec for:

> **Execution Recovery Console**

This should be the first focused operator product.

## Immediate Next Move 3

Use this architecture document as the parent reference for evaluating future UI, workflow, and policy projects.

---

## 17. Summary

The best next step for async-dev is **not** to reinvent itself from scratch, and not to drift into many loosely connected projects.

The strongest path is:

- keep async-dev as the **execution kernel**
- stabilize verification / closeout / recovery
- add one focused **operator surface**
- standardize **policy / recipe layers**
- only later converge into a broader platform shell

In short:

> **async-dev should evolve into a clearer, more operable, more verifiable execution platform for real software development.**
