# DailyReviewPack Template

> This template defines the structure of `DailyReviewPack` — the nightly summary for fast human review.

---

## Metadata

| Field | Value |
|-------|-------|
| Object Type | `DailyReviewPack` |
| Purpose | Compress daytime activity for 20–30 minute human review |
| Update Frequency | Once per day (evening) |
| Owner | Review workflow, consumed by human |

---

## Required Fields

### date
- **Type**: date (ISO 8601)
- **Description**: The date of this review
- **Example**: `2024-01-15`

### project_id
- **Type**: string
- **Description**: Project being reviewed
- **Example**: `demo-product-001`

### feature_id
- **Type**: string
- **Description**: Feature being reviewed
- **Example**: `001-core-object-system`

### today_goal
- **Type**: string
- **Description**: What was planned for today
- **Example**: `Define ProductBrief and FeatureSpec schemas`

### what_was_completed
- **Type**: array of strings
- **Description**: Items that were completed today
- **Example**: `["Created product-brief.schema.yaml", "Created feature-spec.schema.yaml"]`

### evidence
- **Type**: array of objects
- **Description**: Evidence linking completion to artifacts
- **Example**: `[{"item": "product-brief.schema.yaml", "path": "schemas/product-brief.schema.yaml", "verified": true}]`

### problems_found
- **Type**: array of strings
- **Description**: Issues encountered during execution
- **Example**: `["Schema validation library not available", "Naming inconsistency in one field"]`

### blocked_items
- **Type**: array of objects
- **Description**: Items still blocked, awaiting resolution
- **Example**: `[{"item": "external-api-access", "reason": "API key pending", "status": "waiting"}]`

### decisions_needed
- **Type**: array of objects
- **Description**: Decisions requiring human judgment tonight
- **Example**: `[{"decision": "schema-format", "options": ["YAML", "JSON"], "recommendation": "YAML", "impact": "all schema files"}]`

### recommended_options
- **Type**: array of objects
- **Description**: AI's recommendations for each decision
- **Example**: `[{"decision": "schema-format", "recommended": "YAML", "reason": "human-readable, easier editing"}]`

### tomorrow_plan
- **Type**: string
- **Description**: Proposed plan for tomorrow
- **Example**: `Continue with RunState and ExecutionPack schemas, then templates`

---

## Optional Fields

### risk_summary
- **Type**: string
- **Description**: Summary of risks identified or escalated
- **Example**: `Scope may expand if dependency graph is complex`

### confidence_notes
- **Type**: string
- **Description**: AI's confidence level in the work
- **Example**: `High confidence on schema definitions. Medium confidence on naming conventions.`

### open_followups
- **Type**: array of strings
- **Description**: Items to follow up later (not blocking)
- **Example**: `["Consider adding validation tests", "Document update rules"]`

---

## Template Instance

```yaml
# DailyReviewPack Instance
date: "[ISO8601_DATE]"
project_id: "[PROJECT_ID]"
feature_id: "[FEATURE_ID]"

## Today's Goal
today_goal: "[WHAT_WAS_PLANNED]"

## What Was Completed
what_was_completed:
  - "[ITEM_1]"
  - "[ITEM_2]"

## Evidence
evidence:
  - item: "[ITEM_NAME]"
    path: "[ARTIFACT_PATH]"
    verified: [true|false]

## Problems Found
problems_found:
  - "[PROBLEM_1]"
  - "[PROBLEM_2]"

## Blocked Items
blocked_items:
  - item: "[BLOCKER_NAME]"
    reason: "[WHY_BLOCKED]"
    status: "[waiting|escalated|deferred]"

## Decisions Needed
decisions_needed:
  - decision: "[DECISION_NAME]"
    options:
      - "[OPTION_1]"
      - "[OPTION_2]"
    recommendation: "[AI_RECOMMENDATION]"
    impact: "[WHAT_THIS_AFFECTS]"

## Recommended Options
recommended_options:
  - decision: "[DECISION_NAME]"
    recommended: "[OPTION]"
    reason: "[WHY_RECOMMENDED]"

## Tomorrow's Plan
tomorrow_plan: "[PROPOSED_NEXT_STEPS]"

# Optional
risk_summary: "[RISK_DESCRIPTION]"
confidence_notes: "[CONFIDENCE_LEVEL]"
open_followups:
  - "[FOLLOWUP_1]"
```

---

## Human Review Workflow

### Step 1: Scan Completion (5 min)
- Read `today_goal`
- Scan `what_was_completed`
- Check `evidence` links

### Step 2: Review Problems (5 min)
- Read `problems_found`
- Assess severity
- Decide if any need immediate action

### Step 3: Make Decisions (10–15 min)
- Review each `decisions_needed`
- Read `recommended_options`
- Choose: approve / revise / defer / redefine

### Step 4: Confirm Tomorrow (2–3 min)
- Read `tomorrow_plan`
- Approve or adjust

### Decision Actions

| Action | Meaning |
|--------|---------|
| Approve | Accept AI recommendation |
| Revise | Choose different option |
| Defer | Postpone decision, work on alternative |
| Redefine | Change the question or scope |

---

## Output Format

After review, human produces:

```yaml
# Human Decision Record
date: "[ISO8601_DATE]"
decisions_made:
  - decision: "[DECISION_NAME]"
    action: "[approved|revised|deferred|redefined]"
    choice: "[CHOSEN_OPTION_OR_NONE]"
    notes: "[OPTIONAL_HUMAN_NOTE]"

next_plan_approved: [true|false]
next_plan_revision: "[IF_FALSE_WHAT_TO_CHANGE]"
```

---

## Validation Checklist

Before presenting to human, verify:

- [ ] `date` is today
- [ ] `today_goal` matches ExecutionPack from this morning
- [ ] `what_was_completed` has evidence links
- [ ] `evidence` paths exist and are verifiable
- [ ] `decisions_needed` has ≤ 3 items (compression target)
- [ ] Each decision has options listed
- [ ] Each decision has a recommendation
- [ ] `tomorrow_plan` is specific enough to generate ExecutionPack

---

## Compression Guidelines

### The 20–30 Minute Target

| Content | Target Time |
|---------|-------------|
| Completion summary | 5 min |
| Problems | 5 min |
| Decisions | 10–15 min |
| Tomorrow plan | 2–3 min |

### How to compress

| Technique | Example |
|-----------|---------|
| Aggregate minor items | "Fixed 3 typos" instead of listing each |
| Focus on impact | "Schema format affects all 6 objects" |
| Limit decisions | ≤ 3 meaningful decisions per pack |
| Link to evidence | Don't repeat details, link to files |

---

## Generation Rules

When building DailyReviewPack:

1. Pull `completed_outputs` from RunState → `what_was_completed`
2. Pull `artifacts` from RunState → `evidence`
3. Pull `blocked_items` from RunState → `blocked_items`
4. Pull `decisions_needed` from RunState → `decisions_needed`
5. Summarize `open_questions` → `problems_found` (if relevant)
6. Infer `next_recommended_action` → `tomorrow_plan`
7. Add recommendations → `recommended_options`

---

## Storage

- **Location**: `projects/{project_id}/reviews/{date}-review.md`
- **Format**: Markdown with YAML block (this template)
- **Persistence**: Immutable after generation (no updates)
- **Archive**: Keep all review packs for history

---

## Example Minimal Pack

```yaml
date: 2024-01-15
project_id: demo-product-001
feature_id: 001-core-object-system

today_goal: Define ProductBrief and FeatureSpec schemas

what_was_completed:
  - Created product-brief.schema.yaml
  - Created feature-spec.schema.yaml

evidence:
  - item: product-brief.schema.yaml
    path: schemas/product-brief.schema.yaml
    verified: true
  - item: feature-spec.schema.yaml
    path: schemas/feature-spec.schema.yaml
    verified: true

problems_found: []

blocked_items: []

decisions_needed:
  - decision: schema-format
    options:
      - YAML
      - JSON
    recommendation: YAML
    impact: all schema files

recommended_options:
  - decision: schema-format
    recommended: YAML
    reason: human-readable, easier editing

tomorrow_plan: Continue with RunState and ExecutionPack schemas
```

**Human review time**: ~10 minutes (1 decision only)