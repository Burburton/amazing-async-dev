# Terminology

This document establishes consistent terminology for `amazing-async-dev`. All schemas, templates, and documentation should use these terms.

---

## Core Objects

### product
A product idea with bounded scope, represented by `ProductBrief`.

| Term | Usage |
|------|-------|
| product_id | Unique identifier |
| ProductBrief | Object representing a product |
| product-brief | File name suffix |

### feature
A bounded feature within a product, represented by `FeatureSpec`.

| Term | Usage |
|------|-------|
| feature_id | Unique identifier (format: ###-name) |
| FeatureSpec | Object representing a feature |
| feature-spec | File name suffix |

### task
A day-sized unit of work within a feature.

| Term | Usage |
|------|-------|
| task_id | Identifier within feature |
| task_scope | Bounded scope for execution |
| task_queue | Ordered list of pending tasks |
| active_task | Current task being executed |

### runstate
The current execution state, represented by `RunState`.

| Term | Usage |
|------|-------|
| RunState | Object representing state |
| runstate | File name suffix |
| current_phase | Phase in day loop |

### execution-pack
The bounded input for daytime execution.

| Term | Usage |
|------|-------|
| ExecutionPack | Object representing pack |
| execution-pack | File name suffix |
| execution_id | Unique identifier (format: exec-YYYYMMDD-###) |

### execution-result
The structured outcome of execution.

| Term | Usage |
|------|-------|
| ExecutionResult | Object representing result |
| execution-result | File name suffix |

### review-pack
The nightly summary for human review.

| Term | Usage |
|------|-------|
| DailyReviewPack | Object representing pack |
| daily-review-pack | File name suffix |
| review-night | Workflow phase |

---

## Workflow Phases

### plan-day
Morning planning phase.

| Term | Usage |
|------|-------|
| plan-day | Phase name |
| planning | Phase enum value |

### run-day
Daytime execution phase.

| Term | Usage |
|------|-------|
| run-day | Phase name |
| executing | Phase enum value |

### review-night
Evening review phase.

| Term | Usage |
|------|-------|
| review-night | Phase name |
| reviewing | Phase enum value |

### resume-next-day
Morning continuation phase.

| Term | Usage |
|------|-------|
| resume-next-day | Phase name |

---

## State Concepts

### blocked
Execution cannot proceed due to external dependency.

| Term | Usage |
|------|-------|
| blocked | Phase enum value |
| blocked_items | List in RunState |
| blocked_reasons | List in ExecutionResult |

### decision
A choice requiring human judgment.

| Term | Usage |
|------|-------|
| decisions_needed | List in RunState |
| decisions_required | List in ExecutionResult |
| decisions_needed | List in DailyReviewPack |

### completed
Work finished successfully.

| Term | Usage |
|------|-------|
| completed | Phase enum value |
| completed_outputs | List in RunState |
| completed_items | List in ExecutionResult |
| what_was_completed | Field in DailyReviewPack |

### partial
Work finished but incomplete.

| Term | Usage |
|------|-------|
| partial | Status enum value |

---

## File Naming

### Schema files
Pattern: `{object-name}.schema.yaml`

| Object | File |
|--------|------|
| ProductBrief | product-brief.schema.yaml |
| FeatureSpec | feature-spec.schema.yaml |
| RunState | runstate.schema.yaml |
| ExecutionPack | execution-pack.schema.yaml |
| ExecutionResult | execution-result.schema.yaml |
| DailyReviewPack | daily-review-pack.schema.yaml |

### Template files
Pattern: `{object-name}.template.md`

| Object | File |
|--------|------|
| ProductBrief | product-brief.template.md |
| FeatureSpec | feature-spec.template.md |
| RunState | runstate.template.md |
| ExecutionPack | execution-pack.template.md |
| ExecutionResult | execution-result.template.md |
| DailyReviewPack | daily-review-pack.template.md |

### Example files
Pattern: `{object-name}.example.yaml`

| Object | File |
|--------|------|
| ProductBrief | product-brief.example.yaml |
| FeatureSpec | feature-spec.example.yaml |
| RunState | runstate.example.yaml |
| ExecutionPack | execution-pack.example.yaml |
| ExecutionResult | execution-result.example.yaml |
| DailyReviewPack | daily-review-pack.example.yaml |

---

## ID Patterns

| Type | Pattern | Example |
|------|---------|---------|
| product_id | ^[a-z0-9-]+$ | demo-product-001 |
| feature_id | ^\d{3}-[a-z0-9-]+$ | 001-core-object-system |
| execution_id | ^exec-[0-9]{8}-[0-9]{3}$ | exec-20240115-001 |
| task_id | task-###-description | task-001-schemas |

---

## Field Name Conventions

### Lists
Use plural nouns: `constraints`, `scope`, `options`

### Objects
Use singular nouns: `goal`, `status`, `date`

### Timestamps
Use `*_at`: `updated_at`

### Identifiers
Use `*_id`: `project_id`, `feature_id`, `execution_id`

### Counts
Use `*_count` or singular nouns: `passed`, `failed`

---

## Directional Terms

| Direction | Usage |
|-----------|-------|
| next | Forward: next_recommended_action, tomorrow_plan |
| last | Backward: last_action |
| previous | Historical reference |

---

## Status Terms

### Execution status
| Status | Meaning |
|--------|---------|
| success | All deliverables completed |
| partial | Some deliverables completed |
| blocked | Cannot proceed |
| failed | Execution failed |
| stopped | Stopped at condition |

### Phase status
| Phase | Meaning |
|-------|---------|
| planning | Choosing task |
| executing | Running task |
| reviewing | Generating review |
| blocked | Waiting for resolution |
| completed | Feature done |

### Health status
| Status | Meaning |
|--------|---------|
| healthy | No issues |
| warning | Minor issues |
| blocked | Cannot proceed |
| failed | Critical issue |

---

## Human Actions

| Action | Meaning |
|--------|---------|
| approve | Accept recommendation |
| revise | Choose different option |
| defer | Postpone, work on alternative |
| redefine | Change question or scope |

---

## Avoid These Terms

| Avoid | Use Instead |
|-------|--------------|
| sprint | day loop |
| epic | feature |
| backlog | feature candidates |
| agent | AI executor |
| conversation | artifact |
| memory | state |
| context | RunState |

---

## Governance Terms (Feature 039)

### Repository Modes

| Term | Definition |
|------|------------|
| self_hosted | Mode A - Product and orchestrator in same repository |
| managed_external | Mode B - Product in separate repository, async-dev orchestrates |
| ownership_mode | Field indicating which mode applies |

### Ownership Concepts

| Term | Definition |
|------|------------|
| product truth | Artifacts describing the product itself (ProductBrief, FeatureSpec, etc.) |
| orchestration truth | Artifacts describing async-dev execution behavior (ExecutionPack, ExecutionResult, etc.) |
| product repo | Repository containing product-owned canonical documents |
| orchestration repo | async-dev repository containing execution metadata |

### Boundary Artifacts

| Term | Usage |
|------|-------|
| ProjectLink | Object representing managed product linkage |
| project-link | File name suffix |
| project-link.yaml | Linkage metadata file |
| product_artifact_root | Root path for product-owned artifacts |
| orchestration_artifact_root | Root path for orchestration artifacts |

### Governance Anti-Patterns

| Term | Definition |
|------|------------|
| product repo hollowing | Product lacks its own canonical documents |
| orchestrator archive overreach | async-dev becomes primary archive for another product |
| mixed ownership without boundary | Same artifact class stored unpredictably across repos |

---

## Consistency Check

Before creating or editing any artifact, verify:
- [ ] Uses terms from this document
- [ ] File names follow patterns
- [ ] IDs follow patterns
- [ ] Field names follow conventions
- [ ] Avoids deprecated terms
- [ ] For Mode B, follows ownership boundary rules