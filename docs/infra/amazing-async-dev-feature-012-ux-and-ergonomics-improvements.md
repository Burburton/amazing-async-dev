# Feature 012 — UX / Ergonomics Improvements

## 1. Feature Summary

### Feature ID
`012-ux-and-ergonomics-improvements`

### Title
UX / Ergonomics Improvements

### Goal
Improve the day-to-day usability of `amazing-async-dev` so that the system feels faster, clearer, and less cognitively heavy for real ongoing use.

### Why this matters
At this stage, `amazing-async-dev` already has a strong functional core:

- artifact-first workflow
- day loop orchestration
- external tool mode
- live API mode hardening
- failure / blocker / decision handling
- completion and archive flow
- SQLite-backed state persistence
- execution logging and recovery hardening
- automated test coverage for the core paths

This means the repository is no longer blocked by the absence of core workflow capability.

The next likely limitation is not whether the system can work.  
The next likely limitation is whether the system is pleasant and efficient enough to use repeatedly in real practice.

Typical usability friction now may include:
- too many commands to remember
- unclear status visibility
- verbose or inconsistent CLI output
- too much manual navigation across artifacts
- unnecessary cognitive load during everyday review/resume flows

This feature exists to reduce that friction.

---

## 2. Objective

Refine the operator experience of `amazing-async-dev` so that common tasks become easier, faster, and clearer without changing the core workflow model.

This feature should improve:

1. CLI usability
2. state and status visibility
3. common operator flows
4. artifact navigation and discoverability
5. clarity of next-step guidance

The goal is not to redesign the product into a UI platform.  
The goal is to make the existing system much easier to operate.

---

## 3. Scope

### In scope
- improve CLI command ergonomics
- improve command help and discoverability
- improve status visibility for products/features
- improve output clarity for common commands
- reduce friction in review/resume/completion/archive flows
- improve navigation between artifacts
- add practical convenience commands if needed
- improve consistency of operator-facing messaging
- document the improved operator experience

### Out of scope
- web dashboard
- graphical UI
- remote collaboration interface
- large settings system
- broad plugin architecture
- full TUI framework unless narrowly justified
- deep redesign of object model or persistence model

---

## 4. Success Criteria

This feature is successful when:

1. the repository is easier to operate repeatedly in real workflows
2. common commands are easier to understand and use
3. status and next-step visibility are noticeably improved
4. artifact navigation requires less manual effort
5. the operator can move through the main workflow with lower cognitive overhead
6. the improvements strengthen usability without destabilizing the core system

---

## 5. Core Design Principles

### 5.1 Optimize for frequent real usage
Favor improvements that reduce repeated daily friction.

### 5.2 Clarity over cleverness
The operator should understand the system’s state and next step quickly.

### 5.3 Keep the workflow model intact
Do not replace the artifact-first async development model.  
Improve its usability.

### 5.4 Make next actions obvious
The system should help the operator answer:
- where am I?
- what just happened?
- what should I do next?

### 5.5 Prefer small high-value improvements
Do not overbuild a full UX platform.  
Focus on the operator’s most common pain points.

---

## 6. Main Capability Areas

## 6.1 CLI usability improvements

### Purpose
Make commands easier to discover, understand, and execute correctly.

### Possible improvements
- clearer command naming
- better `--help` output
- more consistent option naming
- useful aliases for frequent actions
- improved subcommand organization

### Notes
Focus on the commands that are used most often in the day loop and lifecycle flow.

---

## 6.2 Status visibility

### Purpose
Make it easier to inspect the current state of work.

### Possible improvements
- product status summary
- feature status summary
- blocked/failed/ready indicators
- current phase visibility
- most recent activity visibility
- archive status visibility

### Notes
This does not require a dashboard.  
CLI-readable summaries may be sufficient in v1.

---

## 6.3 Next-step guidance

### Purpose
Reduce ambiguity after each major action.

### Possible improvements
- better guidance after `plan-day`
- better guidance after `run-day`
- better guidance after `review-night`
- clearer resume guidance
- clearer recovery guidance
- clearer completion/archive guidance

### Notes
The operator should not have to infer the next step from raw artifacts alone.

---

## 6.4 Artifact navigation improvements

### Purpose
Make it easier to find the right file at the right time.

### Possible improvements
- direct links/paths in command output
- clear canonical artifact path display
- feature-local summary views
- archive artifact visibility
- reduced manual path hunting

### Notes
This should especially help with:
- `ExecutionPack`
- `ExecutionResult`
- `DailyReviewPack`
- `ArchivePack`

---

## 6.5 Common operator flow smoothing

### Purpose
Make repetitive workflows require fewer manual mental steps.

### Candidate flows
- creating a new product
- creating a new feature
- checking current state
- reviewing a blocked feature
- resuming work
- completing/archive a feature
- inspecting the latest execution history

### Notes
The target is not to eliminate all manual choices.  
The target is to make common paths smoother and less tiring.

---

## 7. Candidate Feature Areas

The exact implementation can vary, but this feature should likely address some combination of:

### 7.1 Better status command(s)
Examples:
- `asyncdev status`
- `asyncdev status --product <id>`
- `asyncdev status --feature <id>`

### 7.2 Better review/resume guidance
Examples:
- improved summary after `review-night`
- clearer output after `resume-next-day`
- more explicit blocked/failure guidance

### 7.3 Better artifact path surfacing
Examples:
- print canonical paths for key outputs
- direct operator to the most relevant artifact after each command

### 7.4 Better help/documentation for operators
Examples:
- more practical CLI examples
- clearer README operator paths
- better task-oriented docs

### Notes
The feature does not need to implement all possible ergonomic ideas.  
It should focus on the highest-friction operator pain points first.

---

## 8. Runtime and Architecture Expectations

This feature should work with the current architecture, including:

- CLI layer
- orchestrator
- state store
- SQLite persistence
- execution logging
- archive flow

### Notes
This feature should not require a broad runtime redesign.  
It should improve how the system is operated, not rebuild its internals.

---

## 9. Deliverables

This feature must add:

### 9.1 Operator-facing CLI improvements
A concrete set of improvements to command usability and output clarity.

### 9.2 Better state/status inspection support
A practical way to inspect the current state of products/features.

### 9.3 Better next-step/operator guidance
Command outputs that make subsequent action clearer.

### 9.4 Improved artifact discoverability
Reduced path-hunting and better operator navigation.

### 9.5 Documentation
At least one document or section explaining the improved operator workflow.

---

## 10. Acceptance Criteria

- [ ] common command usage is clearer and more consistent
- [ ] operator-facing help/output is improved
- [ ] product/feature state is easier to inspect
- [ ] key artifacts are easier to find from command output
- [ ] next-step guidance is clearer after major workflow actions
- [ ] common daily flows require less manual cognitive overhead
- [ ] the repository remains stable and does not regress core behavior

---

## 11. Risks

### Risk 1 — Cosmetic changes without real value
UI/UX changes may become superficial without reducing actual operator friction.

**Mitigation:** prioritize repeated daily pain points and workflow bottlenecks.

### Risk 2 — Too much scope expansion
This feature could drift into dashboard or full UI ambitions.

**Mitigation:** keep the focus on practical CLI/operator ergonomics.

### Risk 3 — Inconsistent command behavior
Ergonomic changes may accidentally create naming or output inconsistency.

**Mitigation:** apply a clear command/output consistency pass.

### Risk 4 — Breaking stable operator habits
Too much change may hurt existing workflow familiarity.

**Mitigation:** improve incrementally and preserve core semantics.

---

## 12. Recommended Implementation Order

1. identify the highest-friction operator pain points
2. improve status visibility and next-step guidance
3. improve command help and output consistency
4. improve artifact path discoverability
5. smooth common operator flows
6. update documentation with clearer operator guidance
7. verify core workflows still behave consistently

---

## 13. Suggested Validation Questions

This feature should make the system better able to answer:

- what should I run next?
- where is the relevant artifact?
- what state is this feature in?
- is this feature blocked, active, completed, or archived?
- what is the fastest correct path for the operator right now?

If the operator still has to think too hard about those questions during routine usage, this feature is not done.

---

## 14. Definition of Done

Feature 012 is done when:

- the system is noticeably easier to operate in daily practice
- core status and next-step visibility are improved
- common commands and outputs feel more ergonomic
- artifact discovery is easier
- the async development workflow remains intact but feels smoother to use

If the repository is still functionally capable but operationally tiring, this feature is not done.
