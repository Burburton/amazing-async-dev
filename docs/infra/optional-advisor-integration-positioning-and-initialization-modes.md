# Optional Advisor Integration Positioning & Initialization Modes

## Document Metadata
- Spec ID: cross-repo-optional-advisor-integration-positioning
- Status: Draft
- Scope: Cross-repo (`amazing-async-dev` + `amazing-skill-pack-advisor`)
- Priority: High
- Type: Positioning / UX / Integration boundary consolidation

---

## 1. Summary

This spec defines the official cross-repo positioning between `amazing-async-dev` and `amazing-skill-pack-advisor`.

The required outcome is:

- `amazing-async-dev` remains independently usable as the workflow / execution OS.
- `amazing-skill-pack-advisor` is positioned as an optional, first-party ecosystem integration.
- Starter-pack initialization is supported as an enhancement path, not a mandatory prerequisite.
- Documentation, examples, and integration wording across both repos are aligned to this model.

This is a small but foundational consolidation feature. It does **not** add new execution capability. It clarifies product boundary, default usage expectations, and initialization modes.

---

## 2. Problem Statement

The current cross-repo relationship is functionally working, but product interpretation can still drift toward an implicit assumption that `advisor` is the upstream default path into `async-dev`.

That creates several risks:

1. It weakens the standalone identity of `amazing-async-dev`.
2. It makes the ecosystem feel more tightly coupled than intended.
3. It raises perceived setup complexity for new users.
4. It makes future ecosystem extensibility harder, because `advisor` starts to look like a required control plane rather than one optional provider.

The intended model is different:

- `async-dev` is the execution OS.
- `advisor` is one optional ecosystem component that can improve project initialization.
- The integration contract is the `starter-pack` format, not the `advisor` implementation itself.

---

## 3. Core Principle

**`amazing-async-dev` must remain fully usable without `amazing-skill-pack-advisor`. `amazing-skill-pack-advisor` should improve initialization quality and speed, but must never become a required dependency.**

This principle must be reflected in:

- README positioning
- Quick-start flows
- Initialization docs
- Examples
- Integration wording
- Validation expectations

---

## 4. Product Positioning

### 4.1 amazing-async-dev

`amazing-async-dev` is the workflow / execution OS of the amazing ecosystem.

It owns:
- product initialization
- feature lifecycle execution
- workflow state transitions
- low-interruption execution policy
- asynchronous human decision handling
- feedback capture / triage / escalation

It must support direct usage without any other amazing ecosystem project.

### 4.2 amazing-skill-pack-advisor

`amazing-skill-pack-advisor` is an optional, first-party ecosystem component for:
- intake
- classification
- recommendation
- starter-pack export

It helps users move from project intake to execution-ready initialization, but it is not the only valid way to start work in `async-dev`.

### 4.3 Integration Boundary

The integration boundary between the two repos is the `starter-pack` contract.

`async-dev` consumes compatible starter-pack files.
It does **not** depend on `advisor` internals, repo layout, or CLI implementation.

This ensures:
- loose coupling
- future provider extensibility
- cleaner testing boundaries
- preservation of `async-dev` as a standalone product

---

## 5. Initialization Modes

`amazing-async-dev` must officially support two parallel initialization modes.

### Mode A — Direct Initialization
Direct initialization is the standalone default capability of `async-dev`.

Example intent:
- create product manually
- define project context inside `async-dev`
- proceed without any starter-pack input

This mode proves that `async-dev` is independently usable.

### Mode B — Starter-Pack Initialization
Starter-pack initialization is the optional ecosystem-enhanced path.

Example intent:
- generate a starter-pack externally
- initialize `async-dev` with `--starter-pack`
- import planning / policy / workflow hints from the contract

This mode improves startup quality and reduces manual setup, but it must be presented as optional.

### Positioning Requirement
Docs and examples must present these as:
- **Direct mode** = baseline built-in path
- **Starter-pack mode** = recommended ecosystem enhancement when available

They must **not** present starter-pack mode as mandatory.

---

## 6. Goals

### Primary Goals
1. Align both repos to the same optional-integration positioning.
2. Make initialization modes explicit and easy to understand.
3. Preserve `async-dev` standalone usability in docs and examples.
4. Clarify that `advisor` is a first-party provider, not a required dependency.
5. Reduce user confusion about where each repo fits in the workflow.

### Secondary Goals
1. Prepare the ecosystem for additional future starter-pack providers.
2. Improve cross-repo onboarding clarity.
3. Reduce architectural coupling at the messaging layer.

---

## 7. Non-Goals

This spec does **not** require:
- new starter-pack schema features
- new execution policy logic
- new async decision behaviors
- a new UI/dashboard
- auto-installation of advisor from async-dev
- runtime invocation of advisor by async-dev
- mandatory ecosystem orchestration

This is a positioning and initialization-mode consolidation feature, not a new platform capability feature.

---

## 8. Required Changes

### 8.1 Changes in amazing-async-dev

#### README / Docs
Update positioning and initialization sections so that:
- direct/manual initialization is clearly documented
- starter-pack initialization is clearly documented as optional
- `advisor` is referenced as a first-party ecosystem option, not a prerequisite

Suggested wording direction:
- `async-dev supports direct initialization and optional starter-pack initialization.`
- `amazing-skill-pack-advisor is a first-party ecosystem provider that can generate compatible starter packs.`

#### Quick Start / Onboarding
Quick-start content should include both:
- a direct path
- a starter-pack path

If only one path is highlighted as the easiest ecosystem flow, it must still explicitly state that the alternative direct path remains fully supported.

#### Examples
Examples should make mode distinction clear.
Recommended structure:
- one minimal direct-init example
- one starter-pack-init example

#### Terminology
Use neutral, contract-oriented names such as:
- starter-pack consumer
- starter-pack loader
- starter-pack validator

Avoid wording that implies `advisor` is hard-wired into async-dev.

### 8.2 Changes in amazing-skill-pack-advisor

#### README / Docs
Update repo positioning so that `advisor` is described as:
- an optional ecosystem component
- a first-party starter-pack provider for async-dev
- recommended when users want intake-to-initialization assistance

Avoid wording that implies:
- async-dev should normally begin only through advisor
- advisor is the canonical required upstream control layer

#### Usage Docs
Usage docs should show the handoff to async-dev as:
- one supported downstream path
- a first-party ecosystem integration path
- not the only valid way to initialize work in async-dev

#### Contract Docs
Contract docs should reinforce that:
- async-dev consumes the contract
- any compatible provider could theoretically produce the same contract
- advisor is one official provider in the ecosystem

---

## 9. UX / Messaging Requirements

All user-facing wording across both repos should preserve the following hierarchy:

1. `async-dev` is the core execution product.
2. `advisor` is an optional ecosystem accelerator.
3. `starter-pack` is the contract boundary.
4. direct init remains valid and supported.
5. starter-pack init is optional but useful.

The wording should avoid:
- `required upstream`
- `default mandatory path`
- `must use advisor first`
- any messaging that makes async-dev seem unusable on its own

---

## 10. Validation Requirements

The implementation is complete only if a new reader can correctly infer all of the following from public docs:

1. `async-dev` can be used independently.
2. `advisor` is optional.
3. `advisor` is part of the same ecosystem.
4. starter-pack integration is supported.
5. the contract boundary is file/schema-based, not implementation-coupled.
6. there are two valid initialization modes.

A reviewer should be able to inspect the updated docs and answer these questions correctly without additional explanation.

---

## 11. Acceptance Criteria

### AC-1 Positioning Alignment
Both repositories describe the relationship in aligned terms:
- `async-dev` = execution OS / standalone core
- `advisor` = optional first-party ecosystem component

### AC-2 Initialization Mode Clarity
`async-dev` documentation explicitly documents both:
- direct initialization
- starter-pack initialization

### AC-3 Optionality Preservation
No primary documentation path implies that `advisor` is required for `async-dev` usage.

### AC-4 Contract Boundary Clarity
Cross-repo docs clearly state that the integration boundary is the starter-pack contract, not the advisor implementation.

### AC-5 Example Coverage
At least one example or doc path exists for:
- direct mode
- starter-pack mode

### AC-6 Messaging Consistency
No conflicting wording remains in README / usage / integration docs across the two repos.

---

## 12. Suggested Implementation Scope

### Preferred Scope
Keep this feature intentionally small.

Recommended deliverables:
- README updates in both repos
- one concise initialization-modes section in `async-dev`
- one concise ecosystem-positioning section in `advisor`
- one cross-reference doc or note that explains the optional handoff model
- example labels or example notes clarifying direct vs starter-pack mode

### Avoid in This Feature
Do not expand into:
- new CLI subcommands
- plugin runtime systems
- new starter-pack fields
- provider registries
- UI surfaces

Those can be considered later if needed.

---

## 13. Risks if Not Done

If this positioning is not formalized now:
- `advisor` may gradually become perceived as mandatory
- `async-dev` may lose standalone clarity
- new users may overestimate setup complexity
- future integrations may be harder because the ecosystem boundary is not cleanly preserved
- docs may drift into contradictory mental models again

---

## 14. Recommended Repository Ownership

### Primary repo
- `amazing-async-dev`

Reason:
The main behavioral effect is on how initialization modes are presented to users of the execution OS.

### Secondary repo
- `amazing-skill-pack-advisor`

Reason:
Advisor messaging must be adjusted to match the same ecosystem model.

---

## 15. Definition of Done

This spec is done when:
- both repos expose aligned positioning
- both initialization modes are visible and understandable
- advisor is clearly optional
- async-dev is clearly standalone-capable
- no public-facing wording suggests hard dependency
- reviewers agree the ecosystem relationship is now obvious from docs alone

---

## 16. One-Line Canonical Statement

**`amazing-async-dev` is the standalone execution OS of the amazing ecosystem. `amazing-skill-pack-advisor` is an optional first-party component that can generate compatible starter packs to improve async-dev initialization, but it is never required for async-dev usage.**
