# Managed Project Example

> Demonstrates Mode B (managed_external) artifact boundary for amazing-visual-map.

---

## Overview

This example shows how `amazing-async-dev` orchestrates a managed external product (`amazing-visual-map`) while respecting artifact ownership boundaries.

---

## Repository Mode

| Property | Value |
|----------|-------|
| ownership_mode | `managed_external` |
| product repo | `amazing-visual-map` |
| orchestration repo | `amazing-async-dev` |

---

## Artifact Distribution

### Product Repo (amazing-visual-map)

```
amazing-visual-map/
└── projects/
    └── amazing-visual-map/
        ├── product-brief.md           # Product scope
        ├── north-star/                # Product vision
        │   └── vision-v1.md
        ├── features/
        │   ├── 013-visual-history/
        │   │   ├── feature-spec.md
        │   │   └── completion-report.md
        │   └── 015-map-interaction/
        │       └── feature-spec.md
        ├── dogfood/
        │   └── phase-2-dogfood.md
        ├── friction/
        │   └── v2-friction-log.md
        ├── phases/
        │   ├── phase-1-foundation.md
        │   ├── phase-2-core-features.md
        │   └── phase-3-experience-refinement.md
        └── reviews/
            └── 2026-04-10-review.md
```

**Product truth lives with the product.**

### Orchestration Repo (amazing-async-dev)

```
amazing-async-dev/
└── projects/
    └── amazing-visual-map/
        ├── project-link.yaml          # Linkage metadata
        ├── execution-packs/
        │   ├── exec-20260410-001.md
        │   └── exec-20260412-001.md
        ├── execution-results/
        │   ├── exec-20260410-001.md
        │   ├── exec-20260412-001.md
        ├── runstate.md                # Orchestration state
        ├── continuation/
        │   └── checkpoint-state.yaml
        └── verification/
            └── browser-test-results.yaml
```

**Orchestration truth lives with the orchestrator.**

---

## project-link.yaml Example

```yaml
product_id: "amazing-visual-map"
repo_name: "amazing-visual-map"
repo_url: "https://github.com/Burburton/amazing-visual-map"
ownership_mode: "managed_external"
repo_local_path: "../amazing-visual-map"
product_artifact_root: "projects/amazing-visual-map"
orchestration_artifact_root: "projects/amazing-visual-map"
current_phase: "phase-3-experience-refinement"
last_execution_id: "exec-20260414-001"
status: "active"
sync_notes: "Product specs migrated to product repo. Orchestration artifacts in async-dev."
created_at: "2026-04-01T10:00:00Z"
updated_at: "2026-04-15T12:30:00Z"
```

---

## Decision Test Examples

### Example 1: New FeatureSpec
**Question**: Where should a new FeatureSpec for visual-map be stored?

**Decision Test**:
1. Does this describe the product? → YES (feature definition)
2. Does this describe async-dev execution? → NO
3. Would this matter if async-dev disappeared? → YES (product needs it)

**Result**: Store in `amazing-visual-map/projects/amazing-visual-map/features/{feature_id}/feature-spec.md`

### Example 2: ExecutionPack
**Question**: Where should the ExecutionPack be stored?

**Decision Test**:
1. Does this describe the product? → NO (task definition)
2. Does this describe async-dev execution? → YES (how to run)
3. Would this matter if async-dev workflow changed? → YES

**Result**: Store in `amazing-async-dev/projects/amazing-visual-map/execution-packs/`

### Example 3: Dogfood Report
**Question**: Where should a dogfood report about visual-map UX be stored?

**Decision Test**:
1. Does this describe the product? → YES (product experience)
2. Would this matter if async-dev disappeared? → YES (product history)

**Result**: Store in `amazing-visual-map/projects/amazing-visual-map/dogfood/`

---

## Migration Guidance

If artifacts are currently stored in wrong location:

1. **Keep orchestration artifacts in async-dev** (no migration needed)
2. **Move product artifacts to product repo** (copy, not delete initially)
3. **Leave reference links in async-dev** where useful
4. **Update project-link.yaml** with sync_notes documenting migration status
5. **Avoid duplicate canonical copies** (one source of truth per artifact)

---

## Anti-Pattern Examples

### Wrong: Product Specs Only in async-dev
```
amazing-async-dev/
└── projects/
    └── amazing-visual-map/
        └── features/
            └── 001-core/
                └── feature-spec.md  # WRONG - should be in product repo
```

### Wrong: Execution Packs in Product Repo
```
amazing-visual-map/
└── projects/
    └── amazing-visual-map/
        └── execution-packs/         # WRONG - orchestration artifact
            └── exec-001.md
```

### Correct: Boundary Respected
```
# Product repo has product truth
amazing-visual-map/projects/amazing-visual-map/features/001/feature-spec.md

# async-dev has orchestration truth
amazing-async-dev/projects/amazing-visual-map/execution-packs/exec-001.md
```

---

## Key Principle

> A managed product should remain self-describing in its own repository.
> `amazing-async-dev` should orchestrate and observe that product, not replace it as the product's primary memory home.