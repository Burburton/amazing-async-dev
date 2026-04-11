# ArchivePack Template

> This template defines the structure of `ArchivePack` — the archived summary of a completed feature.

---

## Metadata

| Field | Value |
|-------|-------|
| Object Type | `ArchivePack` |
| Purpose | Preserve completed feature record with lessons and patterns |
| Update Frequency | Never (immutable) |
| Owner | Archive workflow |

---

## Required Fields

### feature_id
- **Type**: string (pattern: `\d{3}-[a-z0-9-]+`)
- **Description**: Unique identifier for the archived feature
- **Example**: `001-core-object-system`

### product_id
- **Type**: string
- **Description**: Product this feature belonged to
- **Example**: `demo-product-001`

### title
- **Type**: string
- **Description**: Human-readable feature title
- **Example**: `Core Object System`

### final_status
- **Type**: string (enum)
- **Description**: Final completion status
- **Allowed values**: `completed`, `partial`, `abandoned`
- **Example**: `completed`

### delivered_outputs
- **Type**: array of objects
- **Description**: What was actually delivered
- **Example**:
  ```yaml
  - name: "product-brief.schema.yaml"
    path: "schemas/product-brief.schema.yaml"
    type: "schema"
  ```

### acceptance_result
- **Type**: object
- **Description**: Acceptance criteria evaluation
- **Required sub-fields**: `satisfied`, `unsatisfied`, `overall`
- **Example**:
  ```yaml
  satisfied:
    - "All six object schemas exist"
    - "All six templates exist"
  unsatisfied:
    - "Example data incomplete"
  overall: "mostly-satisfied"
  ```

### unresolved_followups
- **Type**: array of objects
- **Description**: Items that remain open after completion
- **Example**:
  ```yaml
  - item: "Add validation tests"
    priority: "medium"
    reason: "Deferred for next feature"
  ```

### decisions_made
- **Type**: array of objects
- **Description**: Key decisions made during implementation
- **Example**:
  ```yaml
  - decision: "Use YAML for schemas"
    rationale: "Human-readable, better for documentation"
    impact: "All schema files"
  ```

### lessons_learned
- **Type**: array of objects
- **Description**: What worked well and what to improve
- **Min items**: 1
- **Example**:
  ```yaml
  - lesson: "Small scope definitions work better"
    context: "Day-sized tasks completed reliably"
  ```

### reusable_patterns
- **Type**: array of objects
- **Description**: Patterns that can be reused in future features
- **Min items**: 1
- **Example**:
  ```yaml
  - pattern: "Schema + Template + Example structure"
    applicability: "All object definitions"
  ```

### archived_at
- **Type**: datetime (ISO 8601)
- **Description**: When this archive was created
- **Example**: `2024-01-15T18:00:00Z`

---

## Optional Fields

### implementation_summary
- **Type**: string
- **Description**: Brief summary of what was implemented
- **Example**: `Defined six core objects with schemas, templates, and examples.`

### risk_notes
- **Type**: array of objects
- **Description**: Risk observations from implementation
- **Example**:
  ```yaml
  - risk: "Schema complexity grew unexpectedly"
    mitigation: "Stay minimal for v1"
  ```

### deferred_items
- **Type**: array of objects
- **Description**: Items explicitly deferred to future work
- **Example**:
  ```yaml
  - item: "Advanced validation rules"
    reason: "Out of v1 scope"
    suggested_feature: "002-validation"
  ```

### related_features
- **Type**: array of strings
- **Description**: Features that depend on or relate to this one
- **Example**: `["002-day-loop-cli", "003-single-feature-demo"]`

### archive_version
- **Type**: string
- **Description**: Version of archive format
- **Example**: `1.0`

---

## Template Instance

```yaml
# ArchivePack Instance
feature_id: "[FEATURE_ID]"
product_id: "[PRODUCT_ID]"
title: "[FEATURE_TITLE]"
final_status: "[completed|partial|abandoned]"

delivered_outputs:
  - name: "[OUTPUT_NAME]"
    path: "[OUTPUT_PATH]"
    type: "[schema|template|example|documentation|code]"

acceptance_result:
  satisfied:
    - "[CRITERIA_1]"
    - "[CRITERIA_2]"
  unsatisfied:
    - "[CRITERIA_N]"
  overall: "[fully-satisfied|mostly-satisfied|partial]"

unresolved_followups:
  - item: "[FOLLOWUP_ITEM]"
    priority: "[high|medium|low]"
    reason: "[WHY_UNRESOLVED]"

decisions_made:
  - decision: "[DECISION_NAME]"
    rationale: "[WHY_THIS_CHOICE]"
    impact: "[WHAT_THIS_AFFECTS]"

lessons_learned:
  - lesson: "[LESSON_TEXT]"
    context: "[CONTEXT_OR_EXAMPLE]"
  - lesson: "[LESSON_TEXT]"
    context: "[CONTEXT_OR_EXAMPLE]"

reusable_patterns:
  - pattern: "[PATTERN_NAME]"
    applicability: "[WHERE_TO_REUSE]"
  - pattern: "[PATTERN_NAME]"
    applicability: "[WHERE_TO_REUSE]"

archived_at: "[ISO8601_DATETIME]"

# Optional
implementation_summary: "[BRIEF_SUMMARY]"
risk_notes:
  - risk: "[RISK_OBSERVED]"
    mitigation: "[HOW_HANDLED]"
deferred_items:
  - item: "[ITEM_DEFERRED]"
    reason: "[WHY_DEFERRED]"
    suggested_feature: "[FEATURE_ID]"
related_features:
  - "[RELATED_FEATURE_1]"
  - "[RELATED_FEATURE_2]"
archive_version: "1.0"
```

---

## Archive Philosophy

The archive should answer these questions for every completed feature:

- **What was this feature trying to achieve?** → `title`, `goal` (from FeatureSpec)
- **What was actually delivered?** → `delivered_outputs`
- **Was acceptance achieved?** → `acceptance_result`
- **What is still unresolved?** → `unresolved_followups`
- **What important decisions were made?** → `decisions_made`
- **What should be reused next time?** → `reusable_patterns`
- **Where are the important artifacts?** → `delivered_outputs[].path`

---

## Validation Checklist

Before saving ArchivePack, verify:

- [ ] `feature_id` follows pattern `\d{3}-[a-z0-9-]+`
- [ ] `final_status` is valid enum value
- [ ] `delivered_outputs` has at least one item
- [ ] `lessons_learned` has at least one item
- [ ] `reusable_patterns` has at least one item
- [ ] `acceptance_result` has `overall` field
- [ ] `archived_at` is valid datetime

---

## Storage

- **Location**: `projects/{product_id}/archive/{feature_id}/archive-pack.yaml`
- **Format**: YAML (this template)
- **Persistence**: Immutable after creation
- **Access**: For future feature planning, knowledge retrieval

---

## Usage Notes

### For Future Feature Planning
- Read archive packs to understand similar work done before
- Apply reusable patterns to new features
- Avoid repeating lessons learned

### For Knowledge Retrieval
- Search archive packs by feature_id or pattern
- Reference decisions made for similar choices
- Find precedent for implementation approaches

### For Portfolio Review
- Review delivered_outputs across all archives
- Assess unresolved_followups that need attention
- Evaluate lessons learned for process improvement