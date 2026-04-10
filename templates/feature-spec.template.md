# FeatureSpec Template

> Bounded feature definition for day loop execution.

---

## Metadata

| Field | Value |
|-------|-------|
| Object Type | `FeatureSpec` |
| Purpose | Define a bounded feature with goals, scope, acceptance criteria |
| Update Frequency | Medium |
| Owner | Planning workflow or human |

---

## Required Fields

### feature_id
Unique identifier following pattern.

```
Pattern: ^\d{3}-[a-z0-9-]+$
Format: three digits, hyphen, lowercase name
Example: 001-core-object-system
```

### title
Human-readable feature title.

```
Example: Core Object System
```

### goal
What this feature aims to achieve.

```
Min length: 30 characters
Example: Define foundational object model for explicit, stable artifacts
```

### user_value
Value delivered to the user.

```
Example: Contributors understand artifacts and how they connect
```

### scope
What is included in this feature.

```
Type: array (min 2 items)
Example:
  - Define required fields for all six objects
  - Create YAML schema files
  - Create Markdown templates
  - Create example instances
```

### out_of_scope
What is explicitly NOT included.

```
Type: array (min 1 item)
Example:
  - Implementing full CLI
  - Durable execution runtime
  - Dashboard or UI
```

### acceptance_criteria
Conditions for feature completion.

```
Type: array (min 3 items)
Example:
  - All six object schemas exist
  - All six templates exist
  - All six examples exist
  - Documentation explains object roles
```

---

## Optional Fields

### dependencies
Other features or resources this depends on.

```
Type: array of objects
Example:
  - type: decision
    id: schema-format-choice
    status: pending
```

### risks
Potential risks and mitigations.

```
Example:
  - risk: Over-design with too many fields
    mitigation: Keep first version minimal
```

### notes_for_ai
Specific guidance for AI execution.

```
Example: Start with terminology.md for consistent naming
```

### estimated_days
Estimated day loops to complete.

```
Type: integer (1-14)
Example: 3
```

---

## Template Instance

```yaml
feature_id: "[###-feature-name]"
title: "[FEATURE_TITLE]"
goal: "[GOAL_STATEMENT_MIN_30_CHARS]"
user_value: "[VALUE_FOR_USER]"
scope:
  - "[SCOPE_ITEM_1]"
  - "[SCOPE_ITEM_2]"
  - "[SCOPE_ITEM_3]"
out_of_scope:
  - "[OUT_OF_SCOPE_1]"
  - "[OUT_OF_SCOPE_2]"
acceptance_criteria:
  - "[CRITERIA_1]"
  - "[CRITERIA_2]"
  - "[CRITERIA_3]"
  - "[CRITERIA_4]"

# Optional
dependencies:
  - type: "[feature|resource|decision]"
    id: "[DEPENDENCY_ID]"
    status: "[pending|available|blocked]"
risks:
  - risk: "[RISK_DESCRIPTION]"
    mitigation: "[MITIGATION]"
notes_for_ai: "[AI_GUIDANCE]"
estimated_days: [1-14]
```

---

## Validation Checklist

- [ ] feature_id follows ###-name pattern
- [ ] goal is at least 30 characters
- [ ] scope has at least 2 items
- [ ] out_of_scope has at least 1 item
- [ ] acceptance_criteria has at least 3 items
- [ ] All required fields present

---

## Lifecycle Notes

| Aspect | Detail |
|--------|--------|
| Created by | Planning workflow or human |
| Updated | When scope or criteria changes |
| Storage | `projects/{product_id}/features/{feature_id}/feature-spec.md` |
| Format | Markdown with YAML block |

---

## Usage

### For Planning
- Derive from ProductBrief constraints
- Scope informs ExecutionPack task_scope
- Acceptance criteria inform verification steps

### For Execution
- Read FeatureSpec before generating ExecutionPack
- Check dependencies before starting
- Use notes_for_ai as guidance

### For Review
- Check if scope was honored
- Verify acceptance criteria met
- Assess if user_value delivered