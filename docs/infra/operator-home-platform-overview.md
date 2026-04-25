# Operator Home / Platform Overview

## Metadata

- **Document Type**: `product spec / operator surface / platform entrypoint`
- **Status**: `Proposed`
- **Owner**: `async-dev`
- **Scope**: `operator-facing product`
- **Purpose**: `Define a lightweight unified operator entrypoint for the async-dev platform`
- **Target Branch**: `platform/foundation`

---

## 1. Product Summary

`Operator Home / Platform Overview` is a lightweight operator-facing entrypoint for async-dev.

Its purpose is to give the operator a single place to quickly understand:

- what is currently active,
- what is blocked,
- what needs attention,
- what is awaiting acceptance,
- what has recent observer findings,
- where to go next.

This is **not** intended to be a giant all-in-one control center.  
It is a focused platform overview surface that sits above existing capabilities such as:

- execution kernel
- observer
- Recovery Console
- acceptance subsystem
- CLI/mainflow
- project artifacts and evidence

The product should reduce operator context-switching and make the platform feel more coherent and accessible.

---

## 2. Why This Product Is Needed

The platform now has multiple strong capabilities, but they are spread across different commands, artifacts, and focused surfaces.

An operator may need to mentally stitch together:

- active runs
- blocked runs
- recovery-needed work
- acceptance-blocked work
- observer findings
- latest artifacts
- next actions

Even if each subsystem works individually, the platform can still feel fragmented if the operator lacks a simple “home” view.

This product solves that problem by giving async-dev a compact, practical overview layer.

---

## 3. Product Goals

The product should help the operator answer these questions quickly:

1. What is happening right now?
2. What needs my attention?
3. What is blocked?
4. What is waiting on acceptance?
5. What recovery-worthy items exist?
6. What observer findings matter most?
7. What should I click into next?

---

## 4. Non-Goals

This product does **not** aim to:

- replace Recovery Console,
- replace acceptance CLI,
- replace project artifact browsing,
- become a massive dashboard,
- expose every internal detail of the platform,
- manage every operator workflow in v1.

This is intentionally a **home / overview** surface, not a full platform shell.

---

## 5. Core Design Principle

### 5.1 Overview First, Detail Second

This surface should answer “what matters now?” and route the operator to the right specialized surface.

### 5.2 Lightweight, Not Overbuilt

The product should be small and focused. It should not attempt to become a monolithic platform console in v1.

### 5.3 Operator Clarity Over Raw Data Density

The overview should summarize and prioritize. It should not dump raw artifacts and raw state everywhere.

### 5.4 Reuse Existing Platform Truth

The overview should consume canonical platform evidence and state rather than inventing its own disconnected model.

---

## 6. Primary Use Cases

## Use Case A — Start-of-Day Check
The operator opens the platform and immediately sees:

- active runs
- blocked work
- recovery-needed items
- awaiting-acceptance items
- fresh observer findings

## Use Case B — Triage Current Attention
The operator wants to know what requires intervention right now.

## Use Case C — Route Into Specialized Flows
The operator clicks from overview into:

- Recovery Console
- acceptance details
- feature evidence
- relevant CLI/action flow
- latest artifacts

## Use Case D — Confidence Check
The operator wants quick reassurance that the platform is progressing normally and where the hotspots are.

---

## 7. Proposed Product Scope

The first version should remain intentionally narrow.

### Included in v1
- Active Runs overview
- Recovery-needed summary
- Awaiting-Acceptance summary
- Latest significant observer findings
- Latest blocked/completion-gated items
- Quick links into deeper surfaces
- Small number of prioritized next actions

### Explicitly out of scope for v1
- full artifact browser
- full acceptance history browser
- full recovery management UI
- detailed run-editing workflows
- large customizable dashboard system
- role/permission complexity

---

## 8. Main Sections of the Product

## 8.1 Active Runs Section

Shows:
- currently active runs
- status
- product/feature
- last updated
- whether healthy / risky / stale

Purpose:
- give immediate awareness of live work

## 8.2 Needs Attention Section

Shows the most important items requiring operator attention, such as:
- recovery-required
- acceptance-blocked
- observer-critical findings
- completion-gated items

Purpose:
- provide the primary triage view

## 8.3 Awaiting Acceptance Section

Shows:
- items waiting on acceptance
- items currently blocked by acceptance
- items needing re-acceptance

Purpose:
- make acceptance visible without requiring direct CLI inspection first

## 8.4 Observer Highlights Section

Shows:
- latest meaningful observer findings
- severity
- short reason
- suggested next step

Purpose:
- surface supervision insights without forcing the operator into raw observer data

## 8.5 Quick Navigation Section

Links to:
- Recovery Console
- latest acceptance result/details
- key project/feature evidence
- possibly CLI/action guidance

Purpose:
- turn the overview into a routing layer

---

## 9. Information Model

The product should rely on a compact overview model that can be assembled from canonical sources.

Suggested top-level summary objects:

- `active_runs_summary`
- `attention_items`
- `awaiting_acceptance_items`
- `observer_highlights`
- `blocked_items`
- `quick_links`

Each summary item should contain only the minimum useful operator-facing data.

---

## 10. Suggested Fields by Section

## Active Run Item
- run_id
- feature_id or title
- status
- last_updated_at
- health_summary
- linked detail path

## Attention Item
- category
- title
- severity
- reason
- suggested_action
- linked destination

## Acceptance Item
- feature/run reference
- acceptance_status
- completion_blocked
- attempt_count
- latest_result_summary
- linked destination

## Observer Highlight
- finding_type
- severity
- summary
- recommended_action
- linked destination

## Blocked Item
- item reference
- block reason
- related subsystem (acceptance/recovery/other)
- suggested next action

---

## 11. UX Requirements

### 11.1 Fast Readability
The operator should understand the high-level platform situation within seconds.

### 11.2 Clear Prioritization
The most urgent or important items should appear first.

### 11.3 Low Cognitive Load
Do not overload the page with all internal details.

### 11.4 Strong Routing
Every meaningful item should provide a clear “go deeper” path.

### 11.5 Minimal Redundancy
Do not repeat the same information excessively across sections.

---

## 12. Relationship to Existing Products

## Recovery Console
- Recovery Console remains the specialized place to understand and act on recovery issues.
- Operator Home only summarizes recovery-worthy items and routes into the console.

## Acceptance CLI / Acceptance Surfaces
- Acceptance remains its own subsystem and CLI surface.
- Operator Home only surfaces acceptance-significant items and routes to details/actions.

## Observer
- Observer remains the supervision layer.
- Operator Home surfaces the most relevant observer outputs in summarized form.

## Project Artifacts / Evidence
- Evidence remains canonical truth.
- Operator Home should consume rolled-up evidence, not replace it.

---

## 13. Architectural Position

This product belongs to the **Operator Surface** layer of the platform model.

It sits above:
- execution kernel
- observer
- recovery state
- acceptance state
- evidence layer

It should behave as:
- overview layer
- triage layer
- routing layer

not as a replacement for the specialized products below it.

---

## 14. Data Source Requirements

The product should use canonical platform sources such as:

- active run state
- recovery-required summaries
- acceptance summaries
- observer findings
- completion block summaries
- project/feature evidence rollups

It should **not** build truth from ad hoc UI-local guesses.

A summary adapter or overview service layer is recommended.

---

## 15. Recommended Adapter / Service Layer

Introduce a lightweight overview adapter/service that builds the home page from canonical state.

This adapter may provide:

- active runs summary
- attention queue
- acceptance queue
- observer highlight list
- blocked-item summary
- quick-link generation

This prevents the UI layer from becoming a giant aggregation script.

---

## 16. Suggested Navigation Flow

### Operator opens Home
Sees:
- active runs
- attention items
- acceptance queue
- observer highlights

### Operator chooses next action
Examples:
- click recovery item -> Recovery Console detail
- click acceptance-blocked item -> acceptance result/detail
- click observer highlight -> relevant run/feature/evidence
- click blocked item -> relevant recovery/acceptance path

This keeps the home surface intentionally thin but useful.

---

## 17. Expected File Changes

The exact file list may vary depending on chosen UI stack and repo structure, but implementation will likely touch:

### New product files
- overview/home routes
- overview components
- overview adapter/service layer

### Existing integration files
- artifact/evidence resolution helpers
- acceptance summary adapters
- recovery summary adapters
- observer summary adapters
- navigation/link helpers

### Documentation files
- README / operator docs
- platform overview docs
- operator workflow docs

---

## 18. Acceptance Criteria

## AC-001 Overview Surface Exists
A usable Operator Home / Platform Overview surface exists.

## AC-002 Active Runs Visible
The operator can quickly see active runs and their high-level state.

## AC-003 Attention Items Visible
The operator can see prioritized items that require attention.

## AC-004 Acceptance-Relevant Items Visible
Awaiting-acceptance / acceptance-blocked items are surfaced meaningfully.

## AC-005 Observer Highlights Visible
Important observer findings are surfaced in summarized form.

## AC-006 Strong Routing Exists
The operator can route into Recovery Console, acceptance details, or evidence from the overview.

## AC-007 Canonical Data Consumption
The overview uses canonical platform summaries/evidence rather than disconnected mock truth.

## AC-008 Narrow Scope Maintained
The product remains a lightweight home/overview surface and does not become a giant dashboard in v1.

## AC-009 Tests Added
Automated tests cover summary adapter logic, rendering-critical transformations, and routing-critical states.

---

## 19. Test Requirements

At minimum, tests should cover:

### 19.1 Active Run Summary Rendering
- active runs appear correctly
- stale/risky states are surfaced as expected

### 19.2 Attention Item Prioritization
- recovery / blocked / critical items are prioritized sensibly

### 19.3 Acceptance Item Surfacing
- awaiting/blocking acceptance items appear correctly

### 19.4 Observer Highlight Surfacing
- meaningful findings appear in summarized form

### 19.5 Routing Integrity
- overview items resolve to the correct specialized destinations

### 19.6 Empty / Calm State
- when the platform has little requiring attention, the overview behaves clearly rather than looking broken

---

## 20. Implementation Guidance

### 20.1 Preferred Implementation Order
1. define overview adapter/service layer
2. implement active runs and attention summaries
3. implement acceptance and observer summary sections
4. implement routing/links
5. refine prioritization
6. add tests
7. update docs

### 20.2 Avoid These Failure Patterns
- turning the home surface into a giant all-in-one console
- duplicating too much detailed logic from Recovery Console
- surfacing noisy low-value state
- bypassing canonical truth sources
- overwhelming the operator with too much data density

### 20.3 Backward Compatibility
This product should sit cleanly on top of the platform without disrupting existing CLI/operator flows.

---

## 21. Risks and Mitigations

### Risk 1 — Too much overlap with Recovery Console
**Mitigation:** keep the overview focused on summary + routing.

### Risk 2 — Too little useful signal
**Mitigation:** emphasize attention items, blocked items, and observer highlights rather than generic counts only.

### Risk 3 — Data model fragmentation
**Mitigation:** build a summary adapter/service from canonical sources.

### Risk 4 — Product becomes a giant dashboard prematurely
**Mitigation:** enforce narrow v1 scope.

### Risk 5 — Surface looks nice but is operationally weak
**Mitigation:** prioritize routing and actionability over decoration.

---

## 22. Deliverables

This product is complete only when all of the following exist:

- operator home / overview surface
- summary adapter/service layer
- active runs section
- needs-attention section
- awaiting-acceptance section
- observer highlights section
- quick routing into specialized flows
- documentation updates
- automated tests

---

## 23. Definition of Done

This product is considered done only when:

1. the operator can understand the platform’s current situation quickly,
2. attention-worthy work is visible,
3. acceptance/recovery/observer signals feel more unified,
4. the operator has clear next-click routing into deeper tools,
5. async-dev feels more like one platform and less like several adjacent subsystems.

---

## 24. Summary

`Operator Home / Platform Overview` is the lightweight entrypoint that gives async-dev a more coherent operator face.

It does not replace deeper surfaces.  
It helps the operator see what matters now and where to go next.

In short:

> **This product makes the platform easier to understand and easier to operate at a glance.**
