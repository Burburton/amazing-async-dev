# ProductBrief Template

> Minimum structured representation of a product idea.

---

## Metadata

| Field | Value |
|-------|-------|
| Object Type | `ProductBrief` |
| Purpose | Define a product idea with bounded scope |
| Update Frequency | Low (infrequent) |
| Owner | Human or planning workflow |

---

## Required Fields

### product_id
Unique identifier for the product.

```
Format: lowercase alphanumeric with hyphens
Pattern: ^[a-z0-9-]+$
Example: demo-product-001
```

### name
Human-readable product name.

```
Example: Async Task Manager
```

### problem
The problem this product aims to solve.

```
Min length: 20 characters
Example: Solo builders lack uninterrupted maker time...
```

### target_user
Who this product is designed for.

```
Example: Solo builders, part-time makers with many ideas but little time
```

### core_value
The primary value proposition.

```
Example: AI makes bounded progress during day, human reviews at night
```

### constraints
Constraints and non-goals bounding the product scope.

```
Type: array of strings
Example:
  - Single builder, not multi-team
  - Day-sized tasks only
  - No real-time supervision
```

### success_signal
What indicates the product is successful.

```
Example: Human reviews in 30 min, AI runs 4+ hours autonomously
```

---

## Optional Fields

### non_goals
What this product is NOT trying to do.

```
Example:
  - Multi-team coordination
  - Complex agent societies
```

### initial_feature_candidates
Features that could be implemented first.

```
Example:
  - Core Object System
  - Day Loop CLI
  - Single Feature Demo
```

### notes
Free-form notes about product vision.

---

## Template Instance

```yaml
product_id: "[PRODUCT_ID]"
name: "[PRODUCT_NAME]"
problem: "[PROBLEM_STATEMENT_MIN_20_CHARS]"
target_user: "[WHO_THIS_IS_FOR]"
core_value: "[PRIMARY_VALUE_PROPOSITION]"
constraints:
  - "[CONSTRAINT_1]"
  - "[CONSTRAINT_2]"
  - "[CONSTRAINT_3]"
success_signal: "[SUCCESS_INDICATOR]"

# Optional
non_goals:
  - "[NON_GOAL_1]"
  - "[NON_GOAL_2]"
initial_feature_candidates:
  - "[FEATURE_CANDIDATE_1]"
  - "[FEATURE_CANDIDATE_2]"
notes: "[OPTIONAL_NOTES]"
```

---

## Validation Checklist

- [ ] product_id is unique and follows pattern
- [ ] problem is at least 20 characters
- [ ] success_signal is measurable
- [ ] constraints do not conflict with core_value
- [ ] All required fields present

---

## Lifecycle Notes

| Aspect | Detail |
|--------|--------|
| Created by | Human or planning workflow |
| Updated | Infrequently (major scope changes) |
| Storage | `projects/{product_id}/product-brief.md` |
| Format | Markdown with YAML block |

---

## Usage

### For Planning
- Read ProductBrief before creating FeatureSpec
- Constraints inform scope boundaries
- Success_signal guides acceptance criteria

### For Review
- Check if problem statement still valid
- Verify constraints still apply
- Assess if success_signal achievable