# Decision Template System

Feature 016 introduces reusable decision templates for common nightly decision scenarios.

---

## Overview

Decision templates provide:
- Consistent structure for recurring decision patterns
- Clear decision type classification
- Standard options with typical impacts
- Improved nightly decision inbox readability

---

## Template Architecture

### Template Structure

```yaml
template_id: "continue-or-change"
name: "Continue Current Path or Change Approach"
decision_type: technical
description: "Decide whether to continue with current implementation path"
question_keywords:
  - "continue"
  - "change"
  - "alternative"
standard_options:
  - id: continue
    label: "Continue with current approach"
    typical_impact: "Minimal disruption"
  - id: change
    label: "Change to alternative"
    typical_impact: "May require rework"
default_recommendation: "Continue with current approach"
default_blocking: false
default_defer_impact: "Can proceed with current path"
default_urgency: medium
```

### Decision Types

| Type | Description |
|------|-------------|
| `technical` | Implementation/technology choices |
| `scope` | Feature boundary decisions |
| `priority` | Task ordering decisions |
| `design` | Architecture/design choices |

---

## Initial Templates

### 1. continue-or-change (technical)

**Question**: Continue current path or change approach?

**Options**:
- Continue with current approach
- Change to alternative approach
- Defer decision, gather more information

---

### 2. accept-partial-or-continue (scope)

**Question**: Accept partial result or continue execution?

**Options**:
- Accept partial result as sufficient
- Continue execution for full completion
- Escalate to stakeholder decision

---

### 3. retry-or-defer (technical)

**Question**: Retry blocked task or defer?

**Options**:
- Retry same approach
- Try alternative approach
- Defer and work on other tasks

---

### 4. choose-priority (priority)

**Question**: Which task should take priority next?

**Options**:
- Follow original planned order
- Prioritize urgent task
- Prioritize dependency-blocking task

---

## Integration

### How Templates Work

```
Engine → decisions_required → review_pack_builder → template matching → decisions_needed
```

1. Engine creates `decisions_required` during execution
2. `review_pack_builder._convert_decisions()` matches templates
3. Template defaults fill missing fields
4. Enhanced decisions appear in decision inbox

### Template Matching

Templates match by:
- `question_keywords` in decision text
- `question_pattern` substring matching

### Enhanced Decision Output

```yaml
decision_id: "dec-001"
template_id: "continue-or-change"  # Added by template match
template_name: "Continue Current Path or Change Approach"
decision_type: technical  # Set by template
is_template_based: true  # Flag for template vs ad hoc
options:
  - "Continue with current approach"
  - "Change to alternative approach"
blocking_tomorrow: false
defer_impact: "Can proceed with current path"
urgency: medium
```

---

## CLI Display

### `asyncdev summary decisions`

```
Decision 1: dec-001
  Template: continue-or-change
  Question: Continue current path or change approach?
  Type: technical
  Template: Continue Current Path or Change Approach
  
  Options:
    → Continue with current approach (recommended)
      Change to alternative approach
  
  Recommendation: Continue with current approach
  Impact: Minimal disruption
  
  [dim]Defer impact: Can proceed with current path[/dim]
```

### `asyncdev summary today`

```
Decisions Needed: 3
  2 template-based, 1 ad hoc
  [dec-001] [continue-or-change] Continue current approach...
  [dec-002] [retry-or-defer] Retry blocked task...
```

---

## File Locations

| File | Purpose |
|------|---------|
| `runtime/decision_templates.py` | Template registry and matching |
| `templates/decision-templates.yaml` | Template definitions |
| `schemas/decision-template.schema.yaml` | Template validation schema |
| `runtime/review_pack_builder.py` | Integration point |
| `cli/commands/summary.py` | Display enhancements |

---

## Adding New Templates

### Steps

1. Add template to `templates/decision-templates.yaml`
2. Include required fields:
   - `template_id` (unique)
   - `name`
   - `decision_type`
   - `description`
   - `standard_options` (min 2)
3. Add optional matching hints:
   - `question_keywords`
   - `question_pattern`
4. Set defaults:
   - `default_recommendation`
   - `default_blocking`
   - `default_defer_impact`
   - `default_urgency`

---

## Template vs Ad Hoc

| Attribute | Template-based | Ad hoc |
|-----------|----------------|--------|
| `template_id` | Present | Absent |
| `is_template_based` | `true` | `false` |
| Consistency | Guaranteed | Variable |
| Defaults | Applied | Inferred |

---

## Acceptance Criteria

| Criteria | Status |
|----------|--------|
| decision typing supported | ✅ |
| initial template set (4 templates) | ✅ |
| inbox presentation more consistent | ✅ |
| blocking_tomorrow explicit | ✅ |
| defer_impact explicit | ✅ |
| recommendation/reason clearer | ✅ |
| documentation explains system | ✅ |

---

## Future Extensions

Possible future enhancements:
- More decision types
- Archive-aware template recommendations
- Template recommendation logic rules
- Custom project-specific templates