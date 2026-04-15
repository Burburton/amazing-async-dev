# Project-Link Template

> Linkage metadata for managed external product repos.

---

## Metadata

| Field | Value |
|-------|-------|
| Object Type | `ProjectLink` |
| Purpose | Define ownership boundary and linkage for managed products |
| Update Frequency | Low |
| Owner | async-dev orchestration layer |

---

## Required Fields

### product_id
Unique identifier for the managed product.

```
Pattern: ^[a-z0-9-]+$
Example: amazing-visual-map
```

### repo_name
Repository name.

```
Example: amazing-visual-map
```

### repo_url
Remote repository URL.

```
Example: https://github.com/Burburton/amazing-visual-map
```

### ownership_mode
Repository ownership mode determining artifact storage boundary.

```
Values: self_hosted, managed_external
Default: self_hosted
```

| Mode | Meaning |
|------|---------|
| `self_hosted` | Mode A - Product and orchestrator in same repo |
| `managed_external` | Mode B - Product in separate repo, async-dev orchestrates |

---

## Optional Fields

### repo_local_path
Local filesystem path to product repo (relative to async-dev).

```
Example: ../amazing-visual-map
```

### product_artifact_root
Root path for product-owned artifacts within the product repo.

```
Default: projects/{product_id}
```

### orchestration_artifact_root
Root path for orchestration artifacts within async-dev.

```
Default: projects/{product_id}
```

### current_phase
Current development phase in the product repo.

```
Example: phase-3-experience-refinement
```

### last_execution_id
Most recent execution ID.

```
Pattern: exec-YYYYMMDD-###
Example: exec-20260414-001
```

### status
Managed project status.

```
Values: active, paused, completed, archived
Default: active
```

### sync_notes
Notes about artifact sync state or migration status.

```
Example: Product specs migrated to product repo. Orchestration artifacts remain in async-dev.
```

---

## Template Instance

```yaml
product_id: "[PRODUCT_ID]"
repo_name: "[REPO_NAME]"
repo_url: "[REPO_URL]"
ownership_mode: "[self_hosted|managed_external]"

# Optional
repo_local_path: "[RELATIVE_PATH]"
product_artifact_root: "projects/{product_id}"
orchestration_artifact_root: "projects/{product_id}"
current_phase: "[CURRENT_PHASE]"
last_execution_id: "exec-[YYYYMMDD]-[###]"
status: "[active|paused|completed|archived]"
sync_notes: "[SYNC_STATUS]"
created_at: "[TIMESTAMP]"
updated_at: "[TIMESTAMP]"
```

---

## Ownership Boundary

### Mode A: self_hosted
When product repo == working repo:
- All artifacts may coexist in `projects/{product_id}/`
- No separation needed

### Mode B: managed_external
When product repo != async-dev repo:

**Product repo owns:**
| Artifact | Location |
|----------|----------|
| ProductBrief | `projects/{product_id}/product-brief.md` |
| FeatureSpec | `projects/{product_id}/features/{feature_id}/feature-spec.md` |
| Dogfood reports | `projects/{product_id}/dogfood/` |
| Friction logs | `projects/{product_id}/friction/` |
| Phase summaries | `projects/{product_id}/phases/` |

**async-dev owns:**
| Artifact | Location |
|----------|----------|
| ExecutionPack | `projects/{product_id}/execution-packs/` |
| ExecutionResult | `projects/{product_id}/execution-results/` |
| Orchestration runstate | `projects/{product_id}/runstate.md` |
| Project-link | `projects/{product_id}/project-link.yaml` |
| Continuation state | `projects/{product_id}/continuation/` |

---

## Decision Test

Before creating/storing an artifact:

1. **Does this describe the product?** → Product repo
2. **Does this describe async-dev execution?** → async-dev
3. **Would this matter if async-dev disappeared?** → Product repo
4. **Would this matter if async-dev workflow changed but product unchanged?** → async-dev

---

## Validation Checklist

- [ ] product_id matches pattern
- [ ] repo_url is valid URL
- [ ] ownership_mode is valid enum
- [ ] If managed_external, product_artifact_root documented
- [ ] If managed_external, orchestration_artifact_root documented

---

## Lifecycle Notes

| Aspect | Detail |
|--------|--------|
| Created by | new-product workflow or manual |
| Updated | When execution completes, phase changes, status changes |
| Storage | `projects/{product_id}/project-link.yaml` |
| Format | YAML |

---

## Usage

### For Managed Product Setup
1. Create project-link.yaml in async-dev `projects/{product_id}/`
2. Set ownership_mode to `managed_external`
3. Document product repo URL and local path
4. Define artifact roots for both repos

### For Execution
- Read project-link to determine ownership mode
- Route artifacts to correct repo based on ownership
- Record execution metadata in async-dev
- Leave product artifacts in product repo

### For Review
- Check if artifacts follow ownership boundary
- Verify product repo has canonical product docs
- Verify async-dev has orchestration metadata

---

## Example: amazing-visual-map

```yaml
product_id: "amazing-visual-map"
repo_name: "amazing-visual-map"
repo_url: "https://github.com/Burburton/amazing-visual-map"
ownership_mode: "managed_external"
repo_local_path: "../amazing-visual-map"
product_artifact_root: "projects/amazing-visual-map"
orchestration_artifact_root: "projects/amazing-visual-map"
current_phase: "phase-3-experience-refinement"
last_execution_id: "exec-20260414-001"
status: "active"
sync_notes: "Product specs in product repo. Execution packs/results in async-dev."
```

This enables:
- `amazing-visual-map` to own its feature specs, friction logs, dogfood reports
- `amazing-async-dev` to own execution packs, results, and orchestration state
- Clear boundary preventing orchestrator archive overreach