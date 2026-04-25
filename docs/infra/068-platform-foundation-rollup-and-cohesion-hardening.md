# Feature 068 — Platform Foundation Rollup and Cohesion Hardening

## Metadata

- **Feature ID**: `068-platform-foundation-rollup-and-cohesion-hardening`
- **Feature Name**: `Platform Foundation Rollup and Cohesion Hardening`
- **Feature Type**: `platform integration / documentation alignment / release-readiness hardening`
- **Priority**: `High`
- **Status**: `Implemented`
- **Owner**: `async-dev`
- **Target Branch**: `platform/foundation`
- **Related Areas**:
  - `README / docs alignment`
  - `feature numbering consistency`
  - `platform architecture rollup`
  - `operator surface integration narrative`
  - `platform-level acceptance`

---

## 1. Problem Statement

The `platform/foundation` branch has progressed beyond proof-of-concept and now contains a substantial amount of platform functionality:

- execution kernel concepts and flows,
- day-loop lifecycle commands,
- recovery and resume paths,
- operator-facing surfaces,
- observer/supervision direction,
- a large test surface,
- a meaningful repo structure.

However, the project currently shows a common late-alpha problem:

> the implementation has advanced faster than the platform narrative, numbering, and cohesion model.

This leads to several practical issues:

- README and docs may not fully match current implementation,
- counts and status summaries can drift,
- feature numbering and milestone references can become inconsistent,
- operator surfaces are present but not always situated cleanly in the platform model,
- the platform is stronger than the documentation makes it feel,
- the project risks looking like a pile of features rather than a coherent execution platform.

This does not mean the branch is weak. It means it needs a **rollup / consolidation pass**.

Feature 068 addresses that need by focusing on three outcomes:

1. unify platform documentation and positioning,
2. align feature numbering / milestone / status language,
3. define and validate platform-level acceptance beyond individual feature completion.

---

## 2. Goal

Consolidate `platform/foundation` into a clearer and more coherent platform branch by making the following true:

- documentation matches the current implementation direction,
- feature and status references are internally consistent,
- operator surfaces are clearly placed relative to the execution kernel,
- platform structure is explained cleanly,
- “done” is defined at the platform level, not only at the feature level.

This feature is not primarily about adding major new runtime capability.  
It is about making the existing platform **legible, coherent, and convincingly structured**.

---

## 3. Non-Goals

This feature does **not** aim to:

- redesign the execution kernel,
- replace the current runtime architecture,
- build a brand-new product surface,
- add a large new vertical capability,
- refactor every artifact schema unless needed for consistency,
- rewrite the repo from scratch.

This feature is a **platform rollup and hardening pass**, not a re-foundation effort.

---

## 4. Core Design Principle

### 4.1 The Branch Must Read Like a Platform

A strong implementation is not enough. The repository must also clearly communicate:

- what the platform is,
- how its major parts relate,
- what is complete,
- what is experimental,
- what operators are expected to use,
- what remains to be hardened.

### 4.2 One Coherent Story Beats Many Partial Stories

README, docs, feature numbering, milestone references, and operator narratives must tell one consistent story.

### 4.3 Platform-Level Acceptance Matters

The platform should not be judged only by “feature X exists.”  
It should also be judged by whether:

- the major layers are clear,
- the operator flow is coherent,
- the state/artifact model is believable,
- users can understand what is production-ready vs alpha-ready.

### 4.4 Consolidation Is a Product Move

This is not “just docs cleanup.”  
This is a productization step that improves trust, operability, and future roadmap discipline.

---

## 5. Target Outcomes

After this feature is complete, the `platform/foundation` branch should:

1. present a clear platform structure,
2. explain the relationship among execution kernel, operator surfaces, and policy/recipe layer,
3. expose current capabilities in a coherent and internally consistent way,
4. avoid contradictory feature numbering and completion language,
5. include a platform-level acceptance checklist or readiness model,
6. make it much easier for the next contributor/operator to understand the system quickly.

---

## 6. Required Functional Changes

### 6.1 README Rollup and Alignment

The main README must be updated to reflect the current branch state accurately and cohesively.

At minimum, it must:

- present async-dev as an execution platform,
- clearly distinguish execution kernel vs operator surfaces vs policy/recipe logic,
- reflect current major features consistently,
- avoid stale or conflicting counts/status language,
- explain the current maturity level honestly.

### 6.2 Feature Numbering and Status Consistency Pass

The repository must reconcile feature references across current canonical docs.

This includes ensuring consistency for:

- feature IDs and names,
- complete vs in-progress status,
- milestone/phase references,
- operator product references,
- platform foundation roadmap language.

This does **not** necessarily require renumbering the entire project history, but it does require removing confusing contradictions.

### 6.3 Platform Architecture Reference Integration

The platform architecture/product positioning direction must be integrated into canonical docs, not left as a detached strategy note.

The repo should clearly communicate a layered model such as:

- **Execution Kernel**
- **Operator Surface**
- **Policy / Recipe Layer**

This model should be reflected where appropriate in README and supporting platform docs.

### 6.4 Operator Surface Positioning

The current operator-facing capabilities must be situated clearly in the platform.

Examples may include:

- Recovery Console
- Decision Inbox
- Session Start
- Observer-related operator implications

The docs must make clear:

- what each operator surface is for,
- whether it is implemented vs planned vs alpha,
- how it relates to execution kernel state and artifacts.

### 6.5 Platform-Level Acceptance Model

Add a platform-level acceptance or readiness document/section that answers questions like:

- What makes the execution kernel “stable enough”?
- What is the operator story today?
- What is verified vs still maturing?
- What is functional alpha vs future hardening?
- What counts as platform coherence?

This should help shift evaluation from “feature count” to “platform maturity.”

### 6.6 Optional Small Canonicalization Fixes

If documentation rollup exposes small but important consistency gaps in naming, terminology, or status labels, those may be fixed as part of this feature.

Examples:

- inconsistent naming of major commands/components,
- inconsistent references to feature IDs,
- outdated status labels,
- ambiguous wording around implemented vs planned surfaces.

This feature should allow small canonization fixes, but should avoid opening broad unrelated rewrites.

---

## 7. Detailed Requirements

## 7.1 Canonical Platform Message

The repo should converge on one clear message, for example:

> async-dev is an async execution platform for real software development, with an execution kernel, operator surfaces, and policy/recipe logic.

Exact wording may vary, but the message should be stable and repeated coherently across core docs.

## 7.2 Documentation Scope

The consolidation pass should review at least:

- root README
- any platform architecture / positioning doc
- feature index or completion summary docs
- milestone / phase summary docs
- operator-facing capability references
- any canonical “implementation status” sections

## 7.3 Status Language Policy

The branch should standardize how it uses terms such as:

- complete
- implemented
- functional alpha
- hardened
- verified
- in progress
- planned

These terms should mean something consistent.

## 7.4 Counting Policy

If the repo includes counts such as:

- number of tests,
- number of modules,
- number of completed features,
- number of milestones,

those counts must either:

- be updated to current truth,
- or be removed/rephrased if they are too easy to drift.

### Principle

A smaller accurate status summary is better than a larger stale one.

## 7.5 Layer Mapping

The docs should explicitly map major capabilities to platform layers.

Example mapping:

- day loop / execution packs / results / closeout / recovery = execution kernel
- Recovery Console / Decision Inbox / Session Start = operator surfaces
- verification recipes / escalation rules / gating rules = policy/recipe layer

This does not need to be overcomplicated, but it should be clear.

## 7.6 Alpha-Readiness Honesty

The docs should retain an honest alpha posture where appropriate.

The branch should not overstate readiness.

At the same time, it should present current strengths clearly enough that the project does not look weaker than it is.

### Desired balance

- honest about maturity,
- clear about real working capabilities,
- confident without overselling.

---

## 8. Expected File Changes

The exact file list may vary, but implementation is expected to touch categories like the following.

### 8.1 Canonical Documentation

Likely updates:

- `README.md`
- platform architecture / positioning docs
- implementation status or feature summary docs
- operator product overview docs
- roadmap / milestone summary docs

### 8.2 Small Canonicalization Updates

Possible updates:

- naming consistency in feature references
- status labels
- command/component wording
- docs cross-links

### 8.3 Optional Support Files

If helpful, the feature may add a small supporting canonical doc such as:

- `docs/platform/platform-readiness.md`
- `docs/platform/layer-model.md`
- `docs/platform/status-language.md`

The exact filenames may vary.

---

## 9. Acceptance Criteria

## AC-001 README Is Cohesive
The main README reflects the current platform state coherently and without major internal contradiction.

## AC-002 Feature / Status References Are Consistent
Feature IDs, completion language, and milestone/phase references are internally consistent across canonical docs.

## AC-003 Platform Layer Model Is Visible
The docs clearly communicate the layered structure of the platform.

## AC-004 Operator Surfaces Are Clearly Positioned
Current operator-facing capabilities are described clearly and in relation to the execution kernel.

## AC-005 Platform Acceptance Model Exists
The branch includes a platform-level readiness or acceptance model beyond isolated feature completion.

## AC-006 Counts and Claims Are Trustworthy
Counts, summaries, and capability claims are either accurate or removed/reframed to avoid drift.

## AC-007 Alpha Posture Is Honest
The docs present a credible alpha-stage platform without overselling or understating current functionality.

## AC-008 Documentation Cross-Links Work
Core platform docs link to each other in a way that helps readers navigate the platform model.

## AC-009 Tests/Checks for Documentation Integrity Added if Reasonable
If the repo already supports doc checks or lightweight integrity checks, appropriate validation should be added or updated.

---

## 10. Test / Validation Requirements

At minimum, this feature should validate the following.

### 10.1 README Consistency Review
- no major contradictory counts or statuses remain,
- current platform message is clear.

### 10.2 Feature Reference Consistency
- major feature references across canonical docs align.

### 10.3 Layer Mapping Review
- core capabilities are visibly mapped to platform layers.

### 10.4 Operator Narrative Review
- operator-facing capabilities are described coherently and not treated as unrelated extras.

### 10.5 Status Language Review
- status terms are used consistently enough to avoid reader confusion.

### 10.6 Newcomer Readability Check
- a new reader can understand what async-dev is, what is implemented, and what remains alpha/hardening territory.

This may be done through a structured checklist rather than code tests if appropriate.

---

## 11. Implementation Guidance

## 11.1 Preferred Implementation Order

Recommended sequence:

1. audit current canonical docs and identify contradictions,
2. define the canonical platform message and layer model,
3. roll up README around that model,
4. align feature numbering / milestone / status references,
5. add platform-level readiness/acceptance section or doc,
6. perform a final consistency pass across linked docs.

## 11.2 Avoid These Failure Patterns

The implementation must avoid:

- rewriting too much unrelated content,
- overcomplicating the platform story,
- inventing a polished platform narrative that does not match the implementation,
- keeping stale quantitative claims,
- leaving operator surfaces as detached side mentions,
- treating this as “just docs cleanup” without product coherence goals.

## 11.3 Backward Compatibility

This feature should preserve the current branch direction and major concepts.

It should clarify and unify them, not replace them.

---

## 12. Risks and Mitigations

### Risk 1: Scope expands into broad product redesign
**Mitigation:** keep the focus on cohesion, consistency, and readiness framing.

### Risk 2: Documentation becomes too abstract
**Mitigation:** keep concrete references to current commands, objects, and operator surfaces.

### Risk 3: Feature numbering history is messy
**Mitigation:** prioritize clarity in canonical docs over perfect retroactive renumbering.

### Risk 4: Claims become too conservative and hide progress
**Mitigation:** state strengths clearly while preserving alpha honesty.

### Risk 5: Counts drift again later
**Mitigation:** reduce fragile count-heavy messaging unless it is easy to maintain accurately.

---

## 13. Deliverables

The feature is complete only when all of the following exist:

- rolled-up and aligned README
- consistent canonical feature/status references
- visible platform layer model
- clear operator surface positioning
- platform-level readiness / acceptance framing
- documentation cross-link improvements
- final consistency pass across core docs

---

## 14. Definition of Done

This feature is considered done only when:

1. `platform/foundation` reads like a coherent platform branch rather than a loose feature bundle,
2. core docs no longer materially contradict each other,
3. operator surfaces and execution kernel are situated clearly in the same platform story,
4. platform maturity is described at a branch level, not only feature-by-feature,
5. the repo becomes easier to understand, trust, and continue building on.

---

## 15. Suggested OpenCode / async-dev Execution Notes

Recommended execution intent:

- treat this as a platform cohesion feature,
- optimize for coherence, readability, and trust,
- preserve implementation honesty,
- unify docs around the platform model,
- improve product legibility without starting a redesign.

Recommended planning questions:

- what are the major contradictions today?
- what is the single canonical platform message?
- which docs are canonical vs secondary?
- how should operator surfaces be positioned?
- what does “functional alpha” mean here in platform terms?

---

## 16. Suggested Commit / Completion Framing

The completion report should explicitly demonstrate:

- what contradictions were resolved,
- how the platform layer model is now reflected in the docs,
- how feature/status references were normalized,
- how operator surfaces are now positioned,
- how platform-level acceptance is expressed.

It should not claim completion merely because README wording changed.

---

## 17. Summary

Feature 068 is a rollup and cohesion-hardening pass for the `platform/foundation` branch.

It turns a strong but somewhat drifted alpha branch into a branch that is:

- easier to understand,
- more internally consistent,
- more obviously platform-shaped,
- more trustworthy to contributors and operators.

In short:

> **068 makes the platform foundation legible, coherent, and readiness-aware.**
