# ExecutionPack Template

> Bounded task definition for daytime AI execution.

---

## Metadata

| Field | Value |
|-------|-------|
| Object Type | `ExecutionPack` |
| Purpose | Constrain AI execution with bounded scope |
| Update Frequency | Never (immutable per execution) |
| Owner | Plan-day workflow |

---

## Required Fields

### execution_id
Unique identifier for this execution run.

```
Pattern: ^exec-[0-9]{8}-[0-9]{3}$
Format: exec-YYYYMMDD-###
Example: exec-20240115-001
```

### feature_id
Feature this execution belongs to.

```
Example: 001-core-object-system
```

### task_id
Task identifier within feature.

```
Example: task-001-schemas
```

### goal
Specific goal for this execution.

```
Min length: 20 characters
Example: Create schema files for ProductBrief and FeatureSpec
```

### task_scope
What is explicitly included.

```
Type: array (min 1 item)
Example:
  - Create product-brief.schema.yaml
  - Create feature-spec.schema.yaml
  - Ensure field definitions match spec
```

### must_read
Files that must be read before execution.

```
Example:
  - docs/infra/amazing-async-dev-feature-001-core-object-system.md
  - docs/terminology.md
```

### constraints
Hard constraints that must not be violated.

```
Example:
  - No scope expansion without approval
  - Use YAML format for schemas
  - Include JSON Schema equivalent
```

### deliverables
Expected outputs.

```
Type: array of objects
Example:
  - item: product-brief.schema.yaml
    path: schemas/product-brief.schema.yaml
    type: file
```

### verification_steps
Steps to verify deliverables.

```
Example:
  - Check all required fields defined
  - Verify JSON Schema valid
  - Confirm naming matches terminology
```

### stop_conditions
Conditions requiring stop.

```
Example:
  - All deliverables completed
  - Blocker encountered
  - Decision needed for scope expansion
  - Unresolvable error
```

---

## Optional Fields

### allowed_tools
Tools AI may use.

```
Example: Read, Write, Grep, Bash
```

### notes
Additional guidance.

### priority
Task priority level.

```
Values: high, medium, low
```

### time_limit
Maximum execution time.

```
Example: 4h
```

---

## Template Instance

```yaml
execution_id: "exec-[YYYYMMDD]-[###]"
feature_id: "[FEATURE_ID]"
task_id: "[TASK_ID]"
goal: "[GOAL_MIN_20_CHARS]"
task_scope:
  - "[SCOPE_ITEM_1]"
  - "[SCOPE_ITEM_2]"
must_read:
  - "[FILE_PATH_1]"
  - "[FILE_PATH_2]"
constraints:
  - "[CONSTRAINT_1]"
  - "[CONSTRAINT_2]"
deliverables:
  - item: "[DELIVERABLE_NAME]"
    path: "[FILE_PATH]"
    type: "[file|artifact|log]"
verification_steps:
  - "[STEP_1]"
  - "[STEP_2]"
stop_conditions:
  - "[CONDITION_1]"
  - "[CONDITION_2]"

# Optional
allowed_tools:
  - "[TOOL_1]"
  - "[TOOL_2]"
notes: "[GUIDANCE]"
priority: "[high|medium|low]"
time_limit: "[DURATION]"
```

---

## Execution Rules

### MUST
- Stay inside task_scope
- Read all must_read files first
- Honor all constraints
- Complete all deliverables
- Run all verification_steps
- Stop at any stop_condition
- Update RunState after each action
- Leave evidence of work

### MUST NOT
- Expand scope without approval
- Make architectural decisions alone
- Skip verification steps
- Proceed when blocked
- Continue after stop_condition met

---

## Validation Checklist

- [ ] execution_id follows pattern
- [ ] goal is at least 20 characters
- [ ] task_scope has at least 1 item
- [ ] deliverables has at least 1 item
- [ ] stop_conditions includes completion
- [ ] must_read paths exist or flagged

---

## Lifecycle Notes

| Aspect | Detail |
|--------|--------|
| Created by | plan-day workflow |
| Updated | Never (immutable) |
| Consumed by | run-day workflow |
| Storage | `projects/{project_id}/execution-packs/{execution_id}.md` |
| Format | Markdown with YAML block |

---

## Usage

### For Execution
- Read ExecutionPack at start
- Honor all constraints strictly
- Stop immediately at stop_conditions
- Produce all deliverables
- Run all verification_steps

### For Review
- Check if scope was honored
- Verify all deliverables produced
- Check verification results