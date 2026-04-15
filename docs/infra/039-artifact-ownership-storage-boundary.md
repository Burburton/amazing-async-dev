# Feature 039: Artifact Ownership & Storage Boundary Governance

> Formalize artifact ownership and storage boundaries for managed external product repos.

---

## Metadata

| Field | Value |
|-------|-------|
| feature_id | `039-artifact-ownership-storage-boundary` |
| title | Artifact Ownership & Storage Boundary Governance |
| goal | Establish clear ownership boundaries between product-owned artifacts and orchestration-owned artifacts, enabling managed external product development without ambiguity |
| user_value | Managed products like amazing-visual-map remain self-contained while async-dev orchestrates them cleanly; future managed projects follow the same rule without ad hoc decisions |
| status | planning |

---

## Problem Statement

**Current ambiguity:**
`amazing-async-dev` currently uses a canonical `projects/{product_id}/...` artifact structure that works for self-hosted products, but becomes ambiguous when developing external managed repositories.

**Questions without clear answers:**
- Should product feature specs live in async-dev or the target product repo?
- Should dogfood/friction logs belong to the product or async-dev?
- Should async-dev be the long-term archive for product development history?

**Anti-patterns observed:**
1. Product Repo Hollowing - meaningful product history only in async-dev
2. Orchestrator Archive Overreach - async-dev becomes primary archive for another product
3. Mixed Ownership Without Boundary - same artifact class stored unpredictably

---

## Goal

Define and implement a stable governance model:

1. **Product-level artifacts live with the product**
2. **Orchestration-level artifacts live with async-dev**
3. **Cross-repo development remains understandable and auditable**
4. **Managed products remain self-contained**
5. **Future managed projects follow the same pattern without ambiguity**

---

## Core Principle

> **Product truth should live with the product. Orchestration truth should live with the orchestrator.**

---

## Repository Modes

### Mode A: Self-Hosted Product Mode
The product being developed is the current repository itself.

Examples:
- `amazing-async-dev` developing `amazing-async-dev`
- `amazing-visual-map` developing itself inside its own repo

In this mode, product artifacts and execution context may live in the same repository.

### Mode B: Managed External Product Mode
`amazing-async-dev` orchestrates development of a different real repository.

Examples:
- `amazing-async-dev` drives work on `amazing-visual-map`
- `amazing-async-dev` drives work on another app/tool/site repo

In this mode, artifact ownership must be split clearly.

---

## Ownership Boundary

### Product Repo Owns (Product Truth)
| Artifact | Description |
|----------|-------------|
| ProductBrief | Product scope and constraints |
| FeatureSpec | Feature boundaries and acceptance criteria |
| Feature completion reports | Feature-level outcomes |
| North-star documents | Product vision |
| Roadmap documents | Product phases |
| Dogfood reports | Product experience logs |
| Friction logs | Product friction documentation |
| Product memory artifacts | Product-specific lessons |
| Phase reports | Product phase summaries |
| Product reviews | Product-specific review packs |

**Decision test**: "Would this artifact still matter if async-dev disappeared?" → Yes → Product repo

### async-dev Owns (Orchestration Truth)
| Artifact | Description |
|----------|-------------|
| ExecutionPack | Bounded task definition |
| ExecutionResult | Execution outcome |
| Orchestration runstate | Execution state (not product history) |
| Verification records | Engine-level verification |
| Continuation state | Checkpoint/stop-decision state |
| Project-link metadata | Managed project linkage |
| Cross-project registry | Program-level coordination |
| Orchestration telemetry | How work was carried out |
| async-dev governance docs | This repo's rules |

**Decision test**: "Would this artifact matter if product repo unchanged but async-dev workflow changed?" → Yes → async-dev

---

## Storage Structure

### In Product Repo (Mode B)
```
projects/{product_id}/
├── product-brief.md           # Product scope
├── north-star/                # Product vision
├── features/
│   └── {feature_id}/
│       ├── feature-spec.md    # Feature definition
│       └── completion-report.md
├── dogfood/                   # Experience logs
├── friction/                  # Friction documentation
├── phases/                    # Phase summaries
└── reviews/                   # Product reviews
```

### In async-dev (Mode B)
```
projects/{product_id}/
├── project-link.yaml          # Linkage metadata (NEW)
├── execution-packs/           # Bounded tasks
├── execution-results/         # Outcomes
├── runstate.md                # Orchestration state
├── continuation/              # Checkpoint state
└── verification/              # Engine-level verification
```

---

## Scope

### In Scope
1. **project-link.yaml schema** - New linkage metadata structure
2. **Architecture documentation** - Mode A/B distinction in docs/architecture.md
3. **Terminology update** - Governance terms in docs/terminology.md
4. **AGENTS.md governance section** - Boundary rules for AI execution
5. **Template for project-link** - project-link.template.md
6. **Example structure** - Managed project example

### Out of Scope
1. Migration of existing artifacts (to be handled as follow-up)
2. CLI changes for project-link management (future feature)
3. Automated artifact routing (future feature)
4. Cross-repo sync mechanisms (future feature)

---

## Implementation Plan

### Phase 1: Schema & Template
| Step | File | Change |
|------|------|--------|
| 1.1 | `schemas/project-link.schema.yaml` | New schema for linkage metadata |
| 1.2 | `templates/project-link.template.md` | Template with usage guide |

### Phase 2: Documentation
| Step | File | Change |
|------|------|--------|
| 2.1 | `docs/architecture.md` | Add Section: Repository Modes |
| 2.2 | `docs/terminology.md` | Add governance terms (Mode A, Mode B, product truth, orchestration truth) |
| 2.3 | `AGENTS.md` | Add Section 10: Governance Boundary Rules |

### Phase 3: Example
| Step | File | Change |
|------|------|--------|
| 3.1 | `examples/managed-project/` | New example showing Mode B structure |
| 3.2 | `examples/managed-project/project-link.yaml` | Example linkage file for amazing-visual-map |

---

## project-link.yaml Schema Fields

```yaml
schema_type: project-link
version: "1.0"
description: Linkage metadata for managed external product repos

required:
  - product_id
  - repo_name
  - repo_url
  - ownership_mode

optional:
  - repo_local_path
  - product_artifact_root
  - orchestration_artifact_root
  - current_phase
  - last_execution_id
  - last_checkpoint
  - status
  - sync_notes

fields:
  product_id:
    type: string
    description: Unique identifier for the managed product
    example: "amazing-visual-map"
    required: true

  repo_name:
    type: string
    description: Repository name
    example: "amazing-visual-map"
    required: true

  repo_url:
    type: string
    description: Remote repository URL
    example: "https://github.com/user/amazing-visual-map"
    required: true

  ownership_mode:
    type: enum
    description: Repository ownership mode
    values:
      - self_hosted     # Mode A: Product in same repo
      - managed_external # Mode B: Product in separate repo
    example: "managed_external"
    required: true

  repo_local_path:
    type: string
    description: Local filesystem path to product repo (if available)
    example: "../amazing-visual-map"
    required: false

  product_artifact_root:
    type: string
    description: Root path for product-owned artifacts (in product repo)
    example: "projects/amazing-visual-map"
    required: false

  orchestration_artifact_root:
    type: string
    description: Root path for orchestration artifacts (in async-dev)
    example: "projects/amazing-visual-map"
    required: false

  current_phase:
    type: string
    description: Current development phase
    example: "phase-3-experience-refinement"
    required: false

  last_execution_id:
    type: string
    description: Most recent execution ID
    example: "exec-20260414-001"
    required: false

  status:
    type: enum
    description: Managed project status
    values:
      - active
      - paused
      - completed
      - archived
    example: "active"
    required: false
```

---

## AGENTS.md Governance Section (Section 10)

```markdown
## 10. Governance Boundary Rules

### 10.1 Repository Mode Classification
Before execution, determine ownership_mode:
- `self_hosted`: Product and orchestrator in same repo (Mode A)
- `managed_external`: Product in separate repo (Mode B)

### 10.2 Product Truth Rule (MANDATORY)
Product-owned artifacts MUST live in the product repo:
- ProductBrief, FeatureSpec, feature completion reports
- Dogfood reports, friction logs, phase summaries
- Product memory, north-star documents

### 10.3 Orchestration Truth Rule (MANDATORY)
Orchestration-owned artifacts MUST live in async-dev:
- ExecutionPack, ExecutionResult, orchestration runstate
- Verification records, continuation state
- Project-link metadata, orchestration telemetry

### 10.4 Anti-Patterns (FORBIDDEN)
| Anti-Pattern | Consequence |
|--------------|-------------|
| Product Repo Hollowing | **STOP** - Product must own its canonical docs |
| Orchestrator Archive Overreach | **STOP** - async-dev is not product archive |
| Mixed Ownership Without Boundary | **STOP** - Must classify before storing |

### 10.5 Decision Test
Before creating/storing an artifact:
1. Does this describe the product? → Product repo
2. Does this describe async-dev execution? → async-dev
3. Would this matter if async-dev disappeared? → Product repo
4. Would this matter if async-dev workflow changed? → async-dev
```

---

## Acceptance Criteria

| ID | Criteria |
|----|----------|
| AC-1 | project-link.schema.yaml exists with required fields |
| AC-2 | architecture.md documents Mode A and Mode B |
| AC-3 | terminology.md includes governance terms |
| AC-4 | AGENTS.md has Section 10 with governance rules |
| AC-5 | Example structure shows managed project layout |
| AC-6 | amazing-visual-map can be explained under this model |

---

## Migration Implications for Existing Projects

### amazing-visual-map (Example)

**Current state**: Likely has artifacts in both repos (needs assessment)

**Target state**:
| In amazing-visual-map | In amazing-async-dev |
|----------------------|----------------------|
| ProductBrief | ExecutionPacks |
| FeatureSpecs | ExecutionResults |
| Friction logs | Orchestration runstate |
| Dogfood reports | Project-link.yaml |
| Phase reports | Verification records |

**Migration approach**:
1. Keep orchestration artifacts in async-dev
2. Move product-owned canonical docs to visual-map repo
3. Leave reference links in async-dev where useful
4. Record new ownership in project-link.yaml

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Existing artifacts already in wrong location | Migration plan as follow-up, not blocking |
| Confusion about "projects/" meaning | Explicit documentation of role difference |
| Mixed mode usage in same project | Clear ownership_mode field in project-link |
| Tooling doesn't respect boundary | Manual enforcement via AGENTS.md rules initially |

---

## Estimated Days

1-2 day loops

---

## Notes for AI

1. This is primarily a documentation/schema feature
2. Start with schema and template (foundational)
3. Documentation updates follow schema
4. Example structure validates the model
5. Migration is follow-up work, not this feature

---

## Definition of Done

- [ ] project-link.schema.yaml created
- [ ] project-link.template.md created
- [ ] architecture.md updated with Mode A/B
- [ ] terminology.md updated with governance terms
- [ ] AGENTS.md Section 10 added
- [ ] Example managed-project structure created
- [ ] Tests pass (810+)