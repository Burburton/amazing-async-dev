# 028 — Repo-linked Workspace Snapshot

## Status
Proposed

## Type
Cross-repo usability consolidation feature

## Repositories
- Primary: `amazing-async-dev`
- Secondary: `amazing-skill-pack-advisor` (small alignment only)

## Summary
Introduce a lightweight, operator-facing workspace snapshot in `amazing-async-dev` that makes the current cross-repo operating state easy to understand at a glance.

The snapshot must show whether a product was initialized directly or from a starter pack, surface the current execution state, show recent verification/review signals, and optionally display starter-pack linkage metadata when present.

This feature is intentionally **not** a new orchestration layer, dashboard platform, or required control surface. It is a compact visibility layer designed to reduce usage complexity and make it easier to judge whether the overall system is actually running correctly.

## Background
Recent features established the core cross-repo foundation:
- advisor is positioned as an **optional** first-party ecosystem component, not a required upstream dependency
- async-dev supports both direct/manual initialization and starter-pack initialization
- official verification entry points now exist for checking initialization flows
- onboarding and first-run documentation have been strengthened

That means the current gap is no longer:
- “How are these repos related?”
- “How do I verify setup once?”

The new gap is:
- “What is my current workspace state right now?”
- “Which mode am I in?”
- “What is the latest signal that things are healthy or blocked?”
- “What should I do next?”

As the number of repos and supported paths grows, this visibility gap increases operator friction.

## Problem Statement
A user can now:
- initialize directly inside async-dev
- initialize from an advisor-generated starter pack
- verify setup using the official verification flow
- run features through the async-dev operating loop

However, it is still too hard to answer simple, practical questions during use:
- Is this workspace using direct mode or starter-pack mode?
- If starter-pack mode is used, what provider and contract version is linked?
- What product and feature are currently active?
- What phase is the workflow currently in?
- Is there a pending async human decision?
- What was the latest verification result?
- What was the latest review artifact?
- What is the recommended next action?

Without a single status view, users must manually infer state from scattered files, commands, examples, and repo knowledge.

## Goal
Provide a single, lightweight workspace snapshot that makes the current operating state easy to inspect.

## Non-Goals
This feature must not:
- create a new required control layer above async-dev
- make advisor mandatory
- introduce a full web dashboard or UI application
- replace existing onboarding, verification, or execution flows
- redefine workflow state architecture
- require live cross-repo network calls
- assume advisor is the only possible starter-pack provider

## Product Principle
`amazing-async-dev` must remain fully usable without advisor.

The workspace snapshot may surface optional starter-pack/provider linkage when present, but must not imply that advisor is required.

## User Outcomes
After this feature, a user should be able to answer the following in one place:
- how the workspace was initialized
- what the current execution state is
- whether the workspace looks healthy or blocked
- whether verification has been run recently and what happened
- whether human input is pending
- what action to take next

## Scope

### In Scope
In `amazing-async-dev`:
- define a workspace snapshot concept and output structure
- provide a human-readable status view
- include starter-pack linkage fields when present
- include verification/review/decision summaries where available
- include a recommended next step field
- add docs and example output
- expose the snapshot through a lightweight CLI entry or equivalent documented command path

In `amazing-skill-pack-advisor`:
- add small documentation alignment only, if needed
- clarify that starter-pack linkage shown in async-dev snapshots is optional metadata surfaced by the consumer side

### Out of Scope
- visual analytics dashboard
- browser UI
- live repo synchronization
- persistent telemetry service
- multi-workspace fleet management
- automatic remediation engine
- provider-specific logic beyond generic starter-pack metadata display

## Functional Requirements

### FR-1: Initialization Mode Visibility
The snapshot must clearly show initialization mode:
- `direct`
- `starter-pack`
- `unknown` (only if the system cannot determine the mode safely)

### FR-2: Optional Provider Linkage
When starter-pack metadata is available, the snapshot must show optional linkage information such as:
- provider name
- starter-pack source path
- contract version
- compatibility metadata or compatibility result

If this information is absent, the snapshot must degrade gracefully and remain usable.

### FR-3: Current Operating State Summary
The snapshot must include a compact summary of current workspace state, including at minimum:
- current product
- current feature
- current phase or nearest equivalent state marker
- latest significant command or workflow checkpoint if available

### FR-4: Verification Signal
The snapshot must include the latest available verification signal, such as:
- whether official verify flow has been run
- most recent verify result
- location or reference to the latest verify artifact, if present

If no verification has been run, the snapshot must say so explicitly.

### FR-5: Review Signal
The snapshot must include a concise review signal, such as:
- latest review artifact
- latest review phase marker
- whether review output is present or missing

### FR-6: Async Decision Signal
The snapshot must indicate whether there are pending async human decisions, including at minimum:
- pending decision state present / absent
- optional count if available

### FR-7: Recommended Next Step
The snapshot must provide a simple recommended next action, for example:
- run verification
- continue execution
- answer pending decision
- review latest artifact
- archive completed feature

This recommendation must be heuristic and lightweight, not a hard workflow lock.

### FR-8: Human-readable Output
The snapshot must be readable by a human operator without requiring knowledge of internal file structure.

A markdown-style or terminal summary is acceptable.

### FR-9: Example Output
The repo must include at least one example snapshot output showing:
- direct mode
n- starter-pack mode

If two examples are too heavy, at minimum include one real example and one documented field explanation for the alternate mode.

## UX Requirements

### UX-1
The feature must feel like a status/visibility aid, not a new workflow users must learn.

### UX-2
The output must prioritize clarity over completeness.

### UX-3
The most important fields should be near the top:
- initialization mode
- current product/feature
- current phase
- verification status
- pending decisions
- next step

### UX-4
Starter-pack linkage should appear as optional contextual information, not the center of the view.

## Suggested Output Shape
The exact implementation may vary, but the output should resemble the following logical structure:

```md
Workspace Snapshot

Initialization
- Mode: starter-pack
- Provider: amazing-skill-pack-advisor
- Starter Pack: ./starter-pack.yaml
- Contract Version: 2.0
- Compatibility: compatible

Execution State
- Product: product-x
- Feature: 028-repo-linked-workspace-snapshot
- Phase: implementation
- Last Checkpoint: review-night completed

Signals
- Verification: passed (latest: docs/verify-output.md)
- Review: present (latest: artifacts/review-night.md)
- Pending Decisions: 1

Recommended Next Step
- Respond to pending async decision before resuming execution.
```

## Implementation Guidance

### Preferred Direction
Implement this first as a lightweight CLI and/or generated text artifact in `amazing-async-dev`.

Examples:
- `asyncdev status`
- `asyncdev workspace snapshot`
- or a documented status-generation command path with stable output

### Data Source Strategy
Prefer existing local state and artifacts already managed by async-dev.

Do not require:
- network access to advisor
- live repo crawling
- remote contract introspection

The snapshot should be based on already available local files, state records, and generated artifacts.

### Degradation Strategy
If some signals are unavailable, the snapshot must still render and should mark fields as:
- missing
- not yet run
- unknown

It must not fail merely because optional metadata is absent.

## Repository Changes

### Primary Changes: `amazing-async-dev`
Potential areas:
- CLI entry for snapshot/status
- snapshot generation utility/module
- docs describing the feature
- example output under `examples/`
- README link in onboarding / verify / operator-facing sections

### Secondary Changes: `amazing-skill-pack-advisor`
Only if needed:
- minimal README/docs note confirming that async-dev may display optional starter-pack/provider linkage metadata
- no new mandatory contract behavior required for this feature

## Acceptance Criteria

### AC-1
A user can generate a single workspace snapshot from async-dev.

### AC-2
The snapshot clearly indicates whether the workspace is in direct mode or starter-pack mode.

### AC-3
When starter-pack metadata exists, the snapshot surfaces provider/linkage information without making it mandatory.

### AC-4
The snapshot includes current product, current feature, and current phase (or best available equivalent).

### AC-5
The snapshot includes the latest verification signal and clearly indicates when verification has not been run.

### AC-6
The snapshot includes a pending async decision signal.

### AC-7
The snapshot includes a clear recommended next step.

### AC-8
README and/or operator-facing docs link users to this capability.

### AC-9
At least one example snapshot is committed to the repo.

## Test Expectations
Tests should cover, where practical:
- direct mode snapshot generation
- starter-pack mode snapshot generation
- missing optional provider metadata
- missing verification artifacts
- pending decision present / absent
- graceful rendering when some fields are unavailable

## Risks
- over-designing this into a dashboard instead of a snapshot
- accidentally implying advisor is required
- tightly coupling snapshot generation to a specific provider
- surfacing too much internal detail and reducing clarity

## Mitigations
- keep output compact and operator-focused
- center execution state, not provider identity
- make starter-pack linkage optional and secondary
- prefer heuristic summaries over deep orchestration logic

## Definition of Done
This feature is complete when:
- async-dev can generate a readable workspace snapshot
- the snapshot covers initialization mode, execution state, key signals, and next step
- optional advisor linkage is shown only when present
- docs and example output are added
- no new required dependency on advisor is introduced

## Recommended Follow-up
If this feature proves useful in practice, a future follow-up may add:
- richer formatting
- machine-readable export
- historical status comparison
- multi-workspace summaries

Those are explicitly future possibilities, not part of this feature.
