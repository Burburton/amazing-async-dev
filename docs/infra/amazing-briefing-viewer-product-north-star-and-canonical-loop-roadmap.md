# amazing-briefing-viewer — Product North Star, Governance, and Canonical Loop Roadmap
## Mother Document

- **Project ID:** `amazing-briefing-viewer`
- **Document Type:** Product North Star / Execution Constitution / Canonical Roadmap
- **Intended Consumer:** `amazing-async-dev` / `opencode`
- **Status Intent:** Canonical top-level governing document
- **Role:** This document serves as both:
  1. the product north-star for `amazing-briefing-viewer`
  2. the autonomous execution constitution for low-interruption canonical loop development

---

## 1. Product Identity

`amazing-briefing-viewer` is a product-layer application built on top of the `amazing-async-dev` ecosystem.

It is **not** the execution engine itself.
It is **not** another general orchestration framework.
It is **not** a generic dashboard clone.

It is a dedicated product for helping a human quickly understand:

- what happened in a project
- what state the project is currently in
- what risks or blockers matter now
- what the system recommends doing next
- whether human input is required
- what supporting evidence exists

The product exists to transform scattered project artifacts into a **high-signal, decision-friendly project briefing experience**.

### Core product statement
> `amazing-briefing-viewer` turns product artifacts and orchestration artifacts into concise, navigable, decision-oriented project briefings for fast remote human understanding.

---

## 2. Why This Product Exists

`amazing-async-dev` can produce a growing set of artifacts:
- product briefs
- north-star docs
- feature specs
- completion reports
- dogfood reports
- friction logs
- execution results
- audit trails
- continuation state
- email decision artifacts

But those artifacts are still distributed across files, directories, and repositories.
A human often has to manually reconstruct project status from too many sources.

This product exists to reduce that reconstruction burden.

It should answer questions like:

- What changed recently?
- What phase is this project in?
- What is blocked?
- Why did the system stop or continue?
- What should happen next?
- Do I need to intervene?
- Where is the supporting evidence?

---

## 3. Product Goals

## 3.1 Primary Goal
Make it easy for a human to understand a project's current state and next recommended action in minimal time.

## 3.2 Secondary Goals
- make project status easier to review remotely
- reduce the need to read raw logs and multiple artifacts
- improve quality of async human decision-making
- provide a clear bridge between product repo artifacts and async-dev orchestration artifacts
- become a real dogfood product for `amazing-async-dev`

## 3.3 Tertiary Goals
- support future multi-project briefing
- support future briefing quality iteration
- support future integration with async email decision/reporting systems

---

## 4. Product Non-Goals

This product should **not** become:

- a generic project management dashboard
- a Kanban board clone
- a Jira/GitHub issue clone
- a full orchestration engine
- a replacement for `amazing-async-dev`
- a raw log viewer
- an all-purpose team collaboration platform
- a giant knowledge graph system in V1

The first versions should stay tightly focused on:
- briefing quality
- state clarity
- recommendation clarity
- evidence traceability

---

## 5. Core Product Principles

### 5.1 Briefing-first
The product should optimize for understanding, not artifact dumping.

### 5.2 High-signal over exhaustive
Show the most decision-relevant information first.

### 5.3 Decision-friendly structure
A human should quickly understand:
- current status
- risks
- recommended next step
- whether a reply/decision is needed

### 5.4 Product truth + orchestration truth
The viewer should combine:
- product-owned artifacts from the product repo
- orchestration-owned artifacts from `amazing-async-dev`

without confusing the two.

### 5.5 Evidence-backed summarization
Every summary should be traceable back to real artifacts.

### 5.6 Anti-dashboard discipline
Do not flatten the product into a generic admin panel.

### 5.7 Local-first early phases
Early versions should work well in a local-first environment.

---

## 6. Relationship to amazing-async-dev

`amazing-async-dev` remains the execution/orchestration system.

`amazing-briefing-viewer` is a product on top of that ecosystem.

### async-dev responsibilities
- canonical loop execution
- runstate
- execution packs/results
- continuation logic
- email decision channel
- audit trail
- orchestration metadata

### briefing-viewer responsibilities
- load artifacts from product and orchestration sources
- synthesize project state into briefing views
- present concise human-readable project briefings
- clarify current state, recent change, risk, next step, and evidence

### Architectural principle
> `amazing-async-dev` does the work.  
> `amazing-briefing-viewer` helps humans understand the work.

---

## 7. Artifact Boundary Model

This product must respect the governance rule:

> Product truth lives with the product repo.  
> Orchestration truth lives with `amazing-async-dev`.

### Expected artifact inputs from product repo
- north-star documents
- product brief
- feature specs
- phase summaries
- dogfood reports
- friction logs
- product-side reviews

### Expected artifact inputs from async-dev repo
- execution results
- continuation state
- audit artifacts
- email decision artifacts
- orchestration summaries
- provider/runtime status artifacts

The viewer must not collapse these into one indistinguishable blob.

---

## 8. User and Usage Model

## Primary user
A project owner/operator who:
- runs multiple async development loops
- cannot always stay at the screen
- needs to understand project state quickly
- wants better briefings than raw logs or ad hoc summaries

## Primary usage patterns
- open one project and get a current executive brief
- see what changed recently
- understand whether action is needed
- drill into evidence only when needed
- review blocker/risk summaries
- confirm or reject next-step recommendations

---

## 9. Product Surfaces

The initial product should be organized around a small number of strong surfaces.

## 9.1 Executive Brief
The top-level briefing surface.
Should show:
- project identity
- current status
- current phase
- recent important changes
- top risks/blockers
- recommended next step
- whether human decision is needed

## 9.2 What Changed
A compact, decision-relevant recent-changes surface.
Should include:
- feature completion
- new reports
- new dogfood/friction
- new decisions
- major continuation/stop events

## 9.3 Current State
Clear explanation of:
- active / paused / blocked / completed
- current phase
- latest checkpoint
- continuation state
- project maturity

## 9.4 Recommended Next Step
A dedicated surface for:
- what should happen next
- why
- whether autonomous continuation is possible
- whether human decision is required
- alternatives if applicable

## 9.5 Risks / Blockers
A dedicated view for active risks and blockers.

## 9.6 Evidence / Sources
A drill-down surface linking the briefing to the underlying artifacts.

---

## 10. Design Direction

This product should feel like a **briefing workspace**, not a generic dashboard.

### Desired experience tone
- clear
- concise
- deliberate
- trustworthy
- operational
- calm
- decision-oriented

### Suggested metaphors
- command brief
- project situation room
- executive briefing desk
- project pulse

### Avoid
- KPI wall aesthetics
- giant tables as primary interface
- issue-tracker visual language
- dashboard-first product identity
- heavy decorative visuals without briefing value

---

## 11. Data Model Intent

The product should derive a unified briefing model from heterogeneous artifacts.

Core conceptual entities likely include:
- Project
- Phase
- Feature
- BriefingSummary
- StateSnapshot
- Risk
- Blocker
- Recommendation
- EvidenceReference
- DecisionArtifact
- OrchestrationCheckpoint

The viewer should not assume all projects have all artifact types.
It must degrade gracefully.

---

## 12. V1 Product Scope

V1 should be a **single-project briefing viewer**.

### V1 must do
- load one project context
- read from one product repo and one async-dev repo
- derive a usable executive brief
- show recent changes
- show current state
- show recommended next step
- show evidence links/references

### V1 must not do
- multi-project portfolio management
- multi-user collaboration
- advanced permissions
- large-scale search
- complex graph views
- full team workflow management

The goal is a coherent first briefing product, not a platform.

---

## 13. Canonical Loop Suitability

This product is deliberately chosen to fit canonical loop development well.

Why it is suitable:
- clear product identity
- bounded first scope
- natural feature decomposition
- real dogfood value
- uses existing async-dev ecosystem
- can repeatedly trigger meaningful product/design decisions
- ideal for email-based remote review and next-step approval

---

## 14. Autonomous Execution Constitution

This document is not just a vision document.
It is also the execution constitution for low-interruption development.

## 14.1 Autonomy Expectation
`amazing-async-dev` should develop this project with low interruption.

It should:
- derive downstream specs itself
- derive bounded next scopes itself
- continue canonical loop execution by default
- request human input only when a true escalation condition exists

## 14.2 Default progression rule
A completed iteration is a checkpoint, not a default terminal stop.

If:
- there is a meaningful next step
- no escalation condition is triggered
- no external blocker prevents progress

then the loop should continue by default.

## 14.3 Human escalation conditions
Human escalation is appropriate when:
- core product identity would materially change
- two major design directions are both plausible but strategically different
- architecture would shift substantially
- scope expansion would change project category
- external dependency/cost/risk changes materially
- there is no coherent next step

## 14.4 Anti-drift rule
Do not allow the product to drift into:
- generic dashboard implementation
- raw artifact browser
- generic PM tracker
- over-general orchestration tool

---

## 15. Phase Structure

The product should be developed in phases.

# Phase 0 — Product Definition

## Goal
Lock the product constitution and data boundary model.

### Candidate features
- Product North Star & Constitution
- Artifact Input Contract

# Phase 1 — Briefing Foundation

## Goal
Create a single-project V1 that can produce a meaningful executive brief.

### Candidate features
- Single-Project Loader
- Briefing Data Model
- V1 Executive Brief Surface
- Evidence Panel

# Phase 2 — Decision Quality & Usability

## Goal
Improve briefing usefulness for real human decision-making.

### Candidate features
- What Changed Timeline
- Recommendation & Next Step Quality
- Risk / Blocker Briefing
- Briefing Layout Refinement

# Phase 3 — Email Decision / Reporting Integration

## Goal
Make briefing surfaces reflect email decision and reporting artifacts more clearly.

### Candidate features
- Decision Email Trace Surface
- Reply Required Queue
- Status Report Viewer

# Phase 4 — Productization

## Goal
Prepare the product for repeated practical use.

### Candidate features
- Presentation Quality
- Project Link Bootstrap
- Multi-Project Readiness (deferred/limited)

---

## 16. Recommended Initial Feature Sequence

Recommended initial execution order:

1. Product North Star & Constitution
2. Artifact Input Contract
3. Single-Project Loader
4. Briefing Data Model
5. V1 Executive Brief Surface
6. Evidence Panel

This creates the first coherent V1 foundation.

---

## 17. Briefing Quality Requirements

A good briefing should answer these questions quickly:

1. What changed?
2. Where are we now?
3. What is risky or blocked?
4. What is recommended next?
5. Do I need to decide something?
6. What evidence supports this?

The product should optimize for this question set.

---

## 18. Acceptance Mindset for Early Iterations

An early iteration is good if:
- it materially reduces the effort to understand a project's current state
- it preserves a strong briefing identity
- it does not collapse into raw artifact dumping
- the next step becomes easier to judge
- evidence traceability is preserved

---

## 19. Anti-Patterns

Avoid the following:

### Anti-Pattern A — Dashboard Regression
Do not turn the product into a standard admin dashboard.

### Anti-Pattern B — Artifact Dump UI
Do not present undifferentiated lists of files as the product experience.

### Anti-Pattern C — Recommendation Ambiguity
Do not force the user to infer what should happen next from scattered clues.

### Anti-Pattern D — Product/Orchestration Boundary Blur
Do not erase the distinction between product repo truth and orchestration truth.

### Anti-Pattern E — Overscoping V1
Do not prematurely build portfolio/multi-project control before single-project briefing quality is strong.

---

## 20. Recommended Immediate Next Action

Treat this mother document as the governing source for the project.

Required next step:
derive the first downstream spec for the project foundation, covering:

- product input contract
- single-project loader assumptions
- initial briefing data model
- initial executive brief surface
- evidence linkage expectations
- V1 non-goals

Proceed with low-interruption canonical loop execution from this document.

---

## 21. Final Guiding Statement

> `amazing-briefing-viewer` should become the place where a human can open one project and quickly understand what changed, what matters now, what should happen next, and why.
