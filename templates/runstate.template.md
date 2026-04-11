# RunState Template

> This template defines the structure of `RunState` — the core continuity object for pause/resume operations.

---

## Metadata

| Field | Value |
|-------|-------|
| Object Type | `RunState` |
| Purpose | Current execution state for pause/resume |
| Update Frequency | High (every action) |
| Owner | Execution and review workflows |

---

## Required Fields

### project_id
- **Type**: string
- **Description**: Unique identifier for the project
- **Example**: `demo-product-001`

### feature_id
- **Type**: string
- **Description**: Unique identifier for the active feature
- **Example**: `001-core-object-system`

### current_phase
- **Type**: string (enum)
- **Description**: Current phase in the day loop
- **Allowed values**: `planning`, `executing`, `reviewing`, `blocked`, `completed`, `archived`
- **Example**: `executing`

### active_task
- **Type**: string
- **Description**: ID or description of the task currently being executed
- **Example**: `create-product-brief-schema`

### task_queue
- **Type**: array of strings
- **Description**: Ordered list of tasks waiting to be executed
- **Example**: `["create-feature-spec-schema", "create-runstate-schema", "create-templates"]`

### completed_outputs
- **Type**: array of strings
- **Description**: List of outputs that have been completed
- **Example**: `["schemas/product-brief.schema.yaml", "templates/product-brief.template.md"]`

### open_questions
- **Type**: array of strings
- **Description**: Questions that need answers but are not blocking execution
- **Example**: `["Should we use YAML or JSON for schemas?"]`

### blocked_items
- **Type**: array of objects
- **Description**: Items blocking progress, awaiting resolution
- **Example**: `[{"item": "external-api-access", "reason": "API key not available", "since": "2024-01-15"}]`

### decisions_needed
- **Type**: array of objects
- **Description**: Decisions that require human judgment
- **Example**: `[{"decision": "schema-format-choice", "options": ["YAML", "JSON"], "impact": "all schema files"}]`

### last_action
- **Type**: string
- **Description**: Description of the most recent action taken
- **Example**: `Created product-brief.schema.yaml with required fields`

### next_recommended_action
- **Type**: string
- **Description**: AI's recommendation for what to do next
- **Example**: `Proceed to create feature-spec.schema.yaml`

### updated_at
- **Type**: datetime (ISO 8601)
- **Description**: Timestamp of the last state update
- **Example**: `2024-01-15T10:30:00Z`

---

## Optional Fields

### artifacts
- **Type**: object (map)
- **Description**: Key artifacts produced during execution
- **Example**: `{"schema_file": "schemas/product-brief.schema.yaml", "template_file": "templates/product-brief.template.md"}`

### notes
- **Type**: string
- **Description**: Free-form notes about the current state
- **Example**: `Schema definitions align with Feature 001 spec. No blockers encountered yet.`

### health_status
- **Type**: string (enum)
- **Description**: Overall health of the execution
- **Allowed values**: `healthy`, `warning`, `blocked`, `failed`
- **Example**: `healthy`

---

## Template Instance

```yaml
# RunState Instance
project_id: "[PROJECT_ID]"
feature_id: "[FEATURE_ID]"
current_phase: "[planning|executing|reviewing|blocked|completed]"
active_task: "[ACTIVE_TASK_DESCRIPTION]"
task_queue:
  - "[TASK_1]"
  - "[TASK_2]"
  - "[TASK_3]"
completed_outputs:
  - "[OUTPUT_1]"
  - "[OUTPUT_2]"
open_questions:
  - "[QUESTION_1]"
blocked_items:
  - item: "[BLOCKER_NAME]"
    reason: "[WHY_BLOCKED]"
    since: "[DATE]"
decisions_needed:
  - decision: "[DECISION_NAME]"
    options:
      - "[OPTION_1]"
      - "[OPTION_2]"
    impact: "[WHAT_THIS_AFFECTS]"
last_action: "[LAST_ACTION_DESCRIPTION]"
next_recommended_action: "[NEXT_STEP]"
updated_at: "[ISO8601_DATETIME]"

# Optional
artifacts:
  key: "[ARTIFACT_PATH]"
notes: "[FREE_FORM_NOTES]"
health_status: "[healthy|warning|blocked|failed]"
```

---

## Update Rules

| Event | Fields to Update |
|-------|------------------|
| Start task | `active_task`, `current_phase` → `executing`, `updated_at` |
| Complete output | `completed_outputs` (append), `last_action`, `updated_at` |
| Add to queue | `task_queue` (append), `updated_at` |
| Hit blocker | `blocked_items` (append), `current_phase` → `blocked`, `updated_at` |
| Resolve blocker | `blocked_items` (remove), `current_phase` → `executing`, `updated_at` |
| Need decision | `decisions_needed` (append), `updated_at` |
| Make decision | `decisions_needed` (remove), `updated_at` |
| End execution | `current_phase` → `reviewing`, `next_recommended_action`, `updated_at` |

---

## Validation Checklist

Before saving RunState, verify:

- [ ] `project_id` is non-empty
- [ ] `feature_id` is non-empty
- [ ] `current_phase` is a valid enum value
- [ ] `task_queue` has at least one item (if executing)
- [ ] `updated_at` is current timestamp
- [ ] `last_action` describes the most recent change
- [ ] All blockers have a `reason` and `since` field
- [ ] All decisions have `options` listed

---

## Usage Notes

### For AI Execution
- Read RunState at start of each action
- Update RunState after each action
- Check `blocked_items` before proceeding
- Check `decisions_needed` before proceeding
- Never proceed if `current_phase` is `blocked`

### For Human Review
- Check `current_phase` to understand status
- Review `completed_outputs` for progress
- Review `decisions_needed` for items requiring judgment
- Review `blocked_items` for items requiring resolution
- Confirm `next_recommended_action` aligns with intent

### For Resume
- RunState is the single source of truth
- No conversation history needed for resume
- Start from `active_task` or `next_recommended_action`
- Continue `task_queue` in order

---

## Storage

- **Location**: `projects/{project_id}/runstate.md`
- **Format**: Markdown with YAML block (this template)
- **Persistence**: Save after every update
- **Backup**: Optional version history via git