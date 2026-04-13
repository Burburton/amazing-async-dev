# loop-journal-viewer-project-brief

## Title
Loop Journal Viewer — Dogfooding Project Brief

## Summary
Build a small, real companion tool that reads async-dev loop artifacts and presents them as a concise, human-readable daily journal view.

The purpose of this project is twofold:

1. serve as a real dogfooding project for the 026–036 async-dev loop
2. create a reusable amazing-ecosystem utility that makes async-dev artifacts easier to inspect over time

This should be treated as a small, practical product, not a demo-only mock project.

---

## Why This Project
The current async-dev direction has strengthened the operator loop around:

- `review-night`
- `resume-next-day`
- `plan-day`
- `run-day`

A natural way to dogfood that loop is to build a tool that consumes the artifacts produced by that loop and shows them as one coherent history.

That makes this project valuable in two ways:

### 1. Immediate dogfooding value
It will pressure-test whether async-dev artifacts are actually:
- readable
- consistent
- named clearly
- structured enough to support downstream consumption

### 2. Future ecosystem value
If useful, Loop Journal Viewer can later become:
- an async-dev companion tool
- a lightweight artifact timeline viewer
- a debugging aid for loop usability
- a foundation for later ecosystem integrations

---

## Product Definition
Loop Journal Viewer is a lightweight viewer that reads async-dev loop outputs and presents them as a timeline-oriented journal of daily work.

At minimum, it should help answer:
- what happened yesterday?
- what did review-night conclude?
- what did resume-next-day carry forward?
- what did plan-day decide?
- what did run-day execute?
- where are the repeated friction points?

---

## Product Positioning
This project should be positioned as:

- a **small real utility**
- a **dogfooding project for async-dev**
- a **future-usable amazing ecosystem companion tool**

It should **not** be positioned as:
- a full dashboard platform
- a heavy observability system
- a replacement for async-dev commands
- a full artifact database product

---

## Project Goal
Deliver a small working tool that can ingest a real sequence of async-dev loop artifacts and render a coherent daily journal/timeline for a project or feature.

The project should be small enough to build in a few days, but real enough to expose actual friction in the async-dev loop.

---

## Core Use Cases

### Use Case 1 — Daily Loop Inspection
A user selects a project/workspace and sees a chronological view of:
- nightly review summary
- morning resume summary
- daily planning summary
- run summary

### Use Case 2 — Feature Story Reconstruction
A user selects a feature and sees how it evolved across multiple days:
- previous decision
- resumed context
- daily plan
- execution outcome

### Use Case 3 — Artifact Friction Detection
A user notices:
- duplicated fields
- confusing terms
- missing continuity
- weak summaries
- inconsistent artifact naming

This use case is especially valuable for dogfooding async-dev itself.

---

## Recommended V1 Scope
Keep V1 tight.

### V1 should do:
- read existing async-dev artifacts from filesystem
- detect a small set of loop artifact types
- normalize them into a timeline view
- show concise summaries for each artifact/event
- support filtering by project or feature when possible
- render in a simple, practical interface

### V1 should not do:
- edit artifacts
- mutate async-dev state
- add heavy search/indexing
- build a full web backend
- add authentication
- introduce a database unless absolutely necessary
- become a generalized observability platform

---

## Recommended V1 Artifact Inputs
V1 should focus on artifacts related to the canonical loop.

At minimum, support reading/parsing these kinds of outputs when available:

- review-night artifact / nightly operator pack
- resume-next-day summary/context
- plan-day output / ExecutionPack summary
- run-day summary / execution result summary

Optional if already easy:
- doctor summary
- verification summary
- closeout summary
- feedback handoff summary

The viewer should gracefully degrade when some artifact types are missing.

---

## Recommended V1 Output Model
Normalize artifacts into a common internal event model such as:

- timestamp / day
- artifact type
- project/workspace
- feature (if available)
- short title
- short summary
- key fields
- source file path

This does not need to be exposed as a formal product API in V1, but internal normalization will make the viewer cleaner and easier to extend.

---

## Recommended UI/UX Direction
Keep the interface lightweight and fast to build.

### Good V1 directions
- terminal/TUI viewer
- simple local web UI
- static/local HTML render
- lightweight React/Vite UI if already preferred

### Recommendation
Choose the interface style that:
- is fastest to dogfood
- is easiest to run locally
- does not introduce unnecessary product complexity

A lightweight local web UI or simple TUI would both be reasonable.

---

## Suggested V1 Screens / Views

### 1. Journal Timeline View
Main view showing chronological entries such as:
- Review Night
- Resume Next Day
- Plan Day
- Run Day

Each entry should show:
- time/day
- type
- concise summary
- key signal(s)

### 2. Feature-Focused View
Optional but useful:
show entries grouped by feature so the user can see feature evolution over time.

### 3. Entry Detail View
Click/expand a journal item to see:
- richer summary
- selected key fields
- original source path

---

## V1 Interaction Principles
- prefer clarity over visual richness
- prefer concise summaries over full raw dumps
- preserve source traceability
- show enough structure to reveal async-dev loop continuity
- do not hide the fact that the tool is reading artifacts
- do not attempt to replace async-dev command outputs entirely

---

## Dogfooding Value
This project is especially good for dogfooding because it will quickly reveal whether async-dev artifacts are:

- too verbose
- too inconsistent
- too repetitive
- insufficiently connected across commands
- missing stable identifiers
- weakly summarized

In other words, the viewer will not only be a product — it will also act as a mirror for async-dev quality.

---

## Success Criteria for the Project
This project is successful if:

1. it can read real async-dev artifacts from a real dogfooding run
2. it produces a coherent daily journal/timeline
3. it helps a human understand loop history faster than opening raw files one by one
4. it exposes real async-dev artifact usability issues
5. it is small enough to be completed and iterated quickly

---

## Recommended 3–5 Day Build Path

### Day 1 — Scope and input audit
- inspect actual async-dev artifacts from the current loop
- choose the minimal supported artifact set
- define the normalized internal event model
- decide the UI form (TUI or local web UI)

### Day 2 — Parsing and normalization
- build file readers for selected artifact types
- normalize them into journal entries
- handle missing/partial fields gracefully

### Day 3 — Main viewer
- build the main timeline/journal view
- show concise summaries and source references
- validate against real artifacts

### Day 4 — Feature grouping / polish
- add feature grouping or filtering if feasible
- improve summary rendering
- improve readability and handling of inconsistent artifacts

### Day 5 — Dogfooding and feedback
- use the tool against a real async-dev project history
- record async-dev artifact friction
- decide whether the viewer itself should continue as a reusable ecosystem tool

---

## Suggested Technical Direction
Keep tech choices pragmatic.

### Good choices
- Python CLI/TUI if speed matters most
- simple local web app if readability matters more
- lightweight file-based ingestion
- no database in V1 unless clearly necessary

### Avoid in V1
- complex backend services
- remote sync
- multi-user support
- heavy infra
- broad plugin architecture

---

## Suggested Repository Strategy
This can be:
- a small standalone repo
or
- a temporary small project repo used for dogfooding first

Recommendation:
Start as a small standalone project with a clear V1 scope.

That keeps it real and reusable later.

---

## Suggested Deliverables
For V1, async-dev should ideally produce:

1. a small working Loop Journal Viewer
2. a short README
3. a sample run against real async-dev artifacts
4. a short dogfooding note describing what this project revealed about async-dev artifact quality

---

## Non-Goals
This project should not try to solve all of the following in V1:
- analytics
- metrics dashboards
- artifact editing
- distributed coordination
- GitHub issue automation
- full search/indexing platform
- OpenSpec/Superpowers integration
- async-dev command replacement

---

## Recommended Instruction for async-dev
Treat this as a real, bounded dogfooding product.

Keep it small, real, and useful.

The project should help answer:
- is the async-dev loop readable as a timeline?
- are the artifacts coherent enough to support downstream consumption?
- what breaks when a simple viewer tries to consume them?

That feedback is as important as the viewer itself.
