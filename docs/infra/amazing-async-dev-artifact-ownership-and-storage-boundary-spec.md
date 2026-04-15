# amazing-async-dev — Artifact Ownership & Storage Boundary for Managed Repos
## Governance Rule Spec

- **Spec ID:** `amazing-async-dev-artifact-ownership-and-storage-boundary`
- **Type:** Governance / Repository Boundary Rule
- **Priority:** High
- **Status Intent:** Ready for adoption and downstream alignment
- **Purpose:** Define clear ownership and storage rules for artifacts produced when `amazing-async-dev` develops either itself or an externally managed product repository.

---

## 1. Problem Statement

`amazing-async-dev` currently uses a canonical `projects/{product_id}/...` artifact structure for core workflow objects such as product briefs, feature specs, execution packs, execution results, reviews, and runstate. This works clearly when the product being developed is conceptually housed inside the same working environment.

However, ambiguity appears when `amazing-async-dev` is used to develop a real external product repository.

Example ambiguity:
- should the product's feature specs live in `amazing-async-dev/projects/...` or inside the target product repo?
- should run metadata live in the target repo?
- should dogfood reports and friction logs belong to the product repo or to async-dev?
- should async-dev act as the long-term archive for product development history, or only as the orchestration layer?

Without an explicit rule, the system can drift into inconsistent storage behavior across projects.

---

## 2. Goal

Define a stable governance model for artifact ownership and artifact storage location so that:

- product-level artifacts live with the product
- orchestration-level artifacts live with `amazing-async-dev`
- cross-repo development remains understandable and auditable
- `visual-map`-style products can remain self-contained while still being driven by async-dev
- future managed repos follow the same rule without ad hoc decisions

---

## 3. Core Principle

> **Product truth should live with the product. Orchestration truth should live with the orchestrator.**

This is the guiding rule for all storage decisions.

---

## 4. Scope

This governance rule applies to:

- `amazing-async-dev` developing itself
- `amazing-async-dev` developing a separate managed product repo
- single-repo product development
- cross-repo product orchestration
- north-star, feature, review, runstate, dogfood, friction, execution, and verification artifacts

---

## 5. Repository Modes

## Mode A: Self-Hosted Product Mode
This is when the product being developed is effectively the current repository itself.

Examples:
- `amazing-async-dev` developing `amazing-async-dev`
- `amazing-visual-map` developing `amazing-visual-map` inside its own repo

In this mode, product artifacts and execution context may live in the same repository, because the product repo and working repo are the same.

## Mode B: Managed External Product Mode
This is when `amazing-async-dev` is orchestrating development of a different real repository.

Examples:
- `amazing-async-dev` drives work on `amazing-visual-map`
- `amazing-async-dev` drives work on another app/tool/site repo

In this mode, artifact ownership must be split clearly across:
1. the target product repo
2. the async-dev orchestration repo

This spec mainly exists to formalize Mode B.

---

## 6. Canonical Ownership Rule

## 6.1 Product Repo Owns Product Artifacts
The target product repository is the canonical home for artifacts that describe or govern the product itself.

These should live in the product repo:
- product north-star documents
- product brief
- product roadmap documents
- feature specs for that product
- phase specs and phase summaries
- dogfood reports about the product
- friction logs about the product
- product-specific review reports
- product memory artifacts
- product-facing design language docs
- product-specific acceptance reports
- product-local runstate if it describes product evolution rather than async-dev engine state

## 6.2 async-dev Owns Orchestration Artifacts
`amazing-async-dev` is the canonical home for artifacts that describe orchestration, execution policy, agent/runtime behavior, continuation state, and cross-project control.

These should live in async-dev:
- execution packs
- execution results
- engine-level verification records
- orchestration run metadata
- continuation / checkpoint / stop-decision state
- external tool execution directives
- cross-project program registry
- managed project linkage/index files
- orchestration reviews of async-dev itself
- async-dev governance rules
- async-dev runtime schemas/templates
- execution telemetry about how work was carried out

---

## 7. Practical Storage Rule

When `amazing-async-dev` develops an external real product repo:

### Store in the target product repo:
- the product's own canonical documents
- the product's own specs
- the product's own dogfood/factual product reports
- the product's own memory/history artifacts
- product-facing design and roadmap material
- anything that should remain useful even if async-dev disappears

### Store in async-dev:
- orchestration instructions
- execution snapshots
- execution results
- verification metadata
- runtime-level status
- control-plane summaries
- project registry/index references
- anything about how async-dev executed, rather than what the product is

---

## 8. Decision Test

When deciding where an artifact should live, apply this test:

### Question 1
Does this artifact primarily describe the product?

If yes, default to the product repo.

### Question 2
Does this artifact primarily describe async-dev's execution/orchestration/runtime behavior?

If yes, default to async-dev.

### Question 3
Would this artifact still be important and understandable if `amazing-async-dev` no longer existed?

If yes, that is a strong signal it belongs in the product repo.

### Question 4
Would this artifact still matter if the product repo were unchanged, but async-dev's workflow/runtime changed?

If yes, that is a strong signal it belongs in async-dev.

---

## 9. Canonical Examples

## 9.1 Product-Level Artifacts (product repo)
Examples:
- `amazing-visual-map/projects/amazing-visual-map/product-brief.md`
- `amazing-visual-map/projects/amazing-visual-map/features/013-visual-history/feature-spec.md`
- `amazing-visual-map/projects/amazing-visual-map/friction/v2-friction-log.md`
- `amazing-visual-map/projects/amazing-visual-map/phases/phase-3-experience-refinement.md`

These are part of the product's long-term memory.

## 9.2 Orchestration-Level Artifacts (async-dev)
Examples:
- `amazing-async-dev/projects/amazing-visual-map/execution-packs/exec-2026-...md`
- `amazing-async-dev/projects/amazing-visual-map/execution-results/exec-2026-...md`
- `amazing-async-dev/projects/amazing-visual-map/run-control/continuation-state.yaml`
- `amazing-async-dev/projects/amazing-visual-map/registry-link.yaml`

These are part of async-dev's control-plane memory.

---

## 10. Recommended Structure for Managed External Product Mode

## 10.1 Target Product Repo
Suggested canonical structure:
- `projects/{product_id}/product-brief.md`
- `projects/{product_id}/north-star/...`
- `projects/{product_id}/features/{feature_id}/feature-spec.md`
- `projects/{product_id}/features/{feature_id}/completion-report.md`
- `projects/{product_id}/dogfood/...`
- `projects/{product_id}/friction/...`
- `projects/{product_id}/phases/...`
- `projects/{product_id}/reviews/...`

## 10.2 async-dev Repo
Suggested managed-project structure:
- `projects/{product_id}/project-link.yaml`
- `projects/{product_id}/execution-packs/...`
- `projects/{product_id}/execution-results/...`
- `projects/{product_id}/runstate.md`
- `projects/{product_id}/continuation/...`
- `projects/{product_id}/verification/...`
- `projects/{product_id}/orchestration-summaries/...`

Important note:
- async-dev `runstate` in Mode B should mean orchestration runstate, not the full canonical product history if the product has its own repo.

---

## 11. Rule for projects/ Directory Meaning

The meaning of `projects/` depends on repository role:

### In a product repo
`projects/` means:
- product-local canonical development memory
- product-owned feature/spec/phase artifacts

### In async-dev
`projects/` means:
- managed-project orchestration workspace
- execution and control-plane metadata
- registry/linkage to real product repos

The same folder name may exist in both repos, but the ownership semantics are different.

---

## 12. Rule for visual-map

For `amazing-visual-map`, the expected model is:

### In `amazing-visual-map`
Store:
- north-star
- product brief
- feature specs
- friction logs
- dogfood reports
- phase reports
- product journey memory
- any product-facing project artifacts

### In `amazing-async-dev`
Store:
- execution packs used to drive visual-map work
- execution results from running external AI/tool workflows
- verification artifacts for async-dev orchestration
- continuation decisions
- run metadata about how visual-map work was executed

This means `amazing-visual-map` remains a self-contained product repo, while async-dev remains its orchestrator and runtime observer.

---

## 13. Anti-Patterns

The following should be avoided:

### Anti-Pattern A: Product Repo Hollowing
Do not keep all meaningful product history only in async-dev while the actual product repo lacks its own core specs and reports.

### Anti-Pattern B: Orchestrator Archive Overreach
Do not make async-dev the permanent primary archive for another product's design/spec history.

### Anti-Pattern C: Mixed Ownership Without Boundary
Do not store the same class of artifact unpredictably across both repos without a rule.

### Anti-Pattern D: Product-Level Reports Hidden as Runtime Metadata
Do not place product dogfood/friction/feature completion artifacts only inside async-dev execution folders.

### Anti-Pattern E: Runtime State Confused with Product State
Do not treat async-dev runtime continuation state as the same thing as product historical memory.

---

## 14. Migration Guidance

If a managed product currently has product-level artifacts living mainly in async-dev, migrate toward:

1. keep orchestration/runtime artifacts in async-dev
2. move product-owned canonical documents into the product repo
3. leave reference links in async-dev where useful
4. record the new ownership rule in project docs
5. avoid duplicate canonical copies across both repos

During migration:
- product repo should become source of truth for product documents
- async-dev should retain references, execution evidence, and control-plane history

---

## 15. Minimum Required Linkage

For Mode B, async-dev should maintain at least a lightweight linkage record per managed project.

Suggested fields:
- `product_id`
- `repo_name`
- `repo_url`
- `repo_local_path`
- `product_artifact_root`
- `orchestration_artifact_root`
- `current_phase`
- `last_execution_id`
- `last_checkpoint`
- `status`

This allows async-dev to orchestrate without becoming the product's primary archive.

---

## 16. Acceptance Criteria

This governance rule is considered properly adopted when:

1. a managed external product repo has its canonical product specs and product history in the product repo
2. async-dev stores orchestration/runtime/control-plane artifacts for that product in its own repo
3. the distinction is documented and consistently followed
4. `projects/` in each repo has a clear role
5. future managed projects can follow the same pattern without ambiguity
6. `amazing-visual-map` can be explained cleanly under this model

---

## 17. Requested Next Action

Use this governance spec to:

1. formalize storage boundaries in `amazing-async-dev`
2. update docs if needed to clarify `projects/` semantics
3. align future managed projects with this rule
4. decide whether any existing artifacts should be migrated or relabeled
5. avoid future confusion about product-owned vs orchestration-owned files

---

## 18. Final Guiding Statement

> A managed product should remain self-describing in its own repository.  
> `amazing-async-dev` should orchestrate and observe that product, not replace it as the product's primary memory home.
