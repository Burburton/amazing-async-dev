# Real async-dev Consumption Pilot (v1.1)

## Purpose

Validate that `amazing-skill-pack-advisor` can operate as a real upstream product for `amazing-async-dev` by proving that a generated starter pack can be consumed in an end-to-end async-dev-managed workflow.

## Pilot Scenario

- **Profile Type**: AI tooling solo MVP
- **Intake File**: `examples/pilot/pilot-intake.yaml`
- **Starter Pack**: `examples/pilot/pilot-starter-pack.yaml`

## Validated Flow

### Step 1: Project Intake

```yaml
product_type: "ai_tooling"
technical_stack:
  primary_language: "python"
  framework: "typer"
  persistence: "sqlite"
current_stage: "mvp"
team_mode: "solo"
preferences:
  iteration_style: "fast_iteration"
  automation_level: "low"
  external_tool_first: true
constraints:
  daily_time_available: "limited_1h"
  workflow_overhead_tolerance: "very_low"
```

### Step 2: Advisor Starter Pack Generation

```bash
cd amazing-skill-pack-advisor
python cli/advisor.py export --input examples/pilot/pilot-intake.yaml --output examples/pilot/pilot-starter-pack.yaml
```

Output:
- Profile: AI tooling or workflow product - solo builder, mvp stage
- Required skills: 4 (nightly-summary, decision-templates, archive-aware-plan, external-tool-mode)
- Optional skills: 3 (limited-batch-ops, enhanced-status, next-step-guidance)
- Deferred skills: 4

### Step 3: async-dev Product Creation

```bash
cd amazing-async-dev
python cli/asyncdev.py new-product create \
  --product-id pilot-ai-tool \
  --name "Pilot AI Tool" \
  --starter-pack examples/pilot/pilot-starter-pack.yaml
```

Output:
- Product directory created
- `product-brief.yaml` enhanced with starter pack context
- `runstate.md` populated with workflow hints

### Step 4: Verification Results

#### product-brief.yaml

```yaml
product_id: pilot-ai-tool
name: Pilot AI Tool
problem: '[AI tooling or workflow product - solo builder, mvp stage] Pilot AI Tool - problem to be defined'
starter_pack_context:
  - 'Product type: ai_tooling'
  - 'Stage: mvp'
  - 'Team mode: solo'
  - 'Required skills: nightly-summary, decision-templates, archive-aware-plan, external-tool-mode'
```

#### runstate.md

```yaml
workflow_hints:
  policy_mode: balanced
  execution: external-tool-first
  review: lightweight-summary
  planning: archive-aware-planning
  archive: minimal-archive
  decision_handling: pause_for_human
```

## Contract Fields Consumed

| Advisor Field | async-dev Target | Status |
|---------------|------------------|--------|
| `project_profile.summary` | `product-brief.problem` prefix | ✅ Consumed |
| `project_profile.product_type` | `starter_pack_context` | ✅ Consumed |
| `project_profile.stage` | `starter_pack_context` | ✅ Consumed |
| `project_profile.team_mode` | `starter_pack_context` | ✅ Consumed |
| `required_skills` | `starter_pack_context` | ✅ Consumed |
| `workflow_mode.execution` | `runstate.workflow_hints.execution` | ✅ Consumed |
| `workflow_mode.review` | `runstate.workflow_hints.review` | ✅ Consumed |
| `workflow_mode.planning` | `runstate.workflow_hints.planning` | ✅ Consumed |
| `workflow_mode.archive` | `runstate.workflow_hints.archive` | ✅ Consumed |
| `workflow_defaults.policy_mode_hint` | `runstate.workflow_hints.policy_mode` | ✅ Consumed |
| `workflow_defaults.decision_handling` | `runstate.workflow_hints.decision_handling` | ✅ Consumed |
| `integration_metadata.contract_version` | Validation gate | ✅ Validated |
| `asyncdev_compatibility.compatible` | Validation gate | ✅ Validated |
| `asyncdev_compatibility.minimum_version` | Warning generation | ✅ Consumed |

## Test Coverage

- 18 integration tests in `test_starter_pack_integration.py`
- Contract version validation
- Field mapping validation
- End-to-end pilot artifact consumption
- Error handling (missing file, invalid YAML, incompatible pack)

## Definition of Done Checklist

- [x] Real starter pack generated from realistic intake
- [x] async-dev consumed starter pack successfully
- [x] Product-brief enhanced with advisor context
- [x] Runstate populated with workflow hints
- [x] Contract fields validated and consumed
- [x] Integration tests added
- [x] Documentation reflects validated flow

## Next Steps

1. Add CLI tests for `--starter-pack` parameter in `test_cli_new_product.py`
2. Test workflow hints influence on execution policy
3. Add advisor README update for v1.1 pilot status