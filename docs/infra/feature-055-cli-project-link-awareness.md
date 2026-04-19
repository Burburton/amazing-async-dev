# Feature 055 — CLI Project-Link Awareness & Artifact Routing

## Status
`complete`

## Objective
Make all async-dev CLI commands aware of `project-link.yaml` and automatically route artifacts to the correct repository based on `ownership_mode`. This enables seamless Mode B (managed_external) product development without manual path management.

---

## Problem Statement

During amazing-briefing-viewer development (Mode B), we observed:

1. **CLI commands ignore project-link**: `new-feature`, `plan-day`, etc. don't read `project-link.yaml`
2. **Manual artifact routing**: AI must manually decide where to write FeatureSpec (product repo vs async-dev)
3. **Path confusion**: `projects/{product_id}/` exists in both repos with different meanings
4. **Governance gap**: Feature 039 defined the schema but CLI integration never completed

**The gap**: The governance boundary rules exist in AGENTS.md Section 10, but CLI tools don't enforce them.

---

## Scope

### In Scope

1. **Project-link loader**
   - `runtime/project_link_loader.py` - Load and validate project-link.yaml
   - Detect `ownership_mode` (self_hosted vs managed_external)
   - Resolve paths for both product and orchestration artifacts

2. **CLI command updates**
   - `new-feature create` → Write FeatureSpec to product repo (Mode B)
   - `plan-day create` → Write ExecutionPack to async-dev (Mode B)
   - `run-day execute` → Write ExecutionResult to async-dev (Mode B)
   - `review-night generate` → Read from both repos, write DailyReviewPack to async-dev
   - `complete-feature mark` → Write completion report to product repo (Mode B)

3. **Path resolution**
   - `product_artifact_root` for product-owned artifacts
   - `orchestration_artifact_root` for async-dev artifacts
   - Relative path resolution from `repo_local_path`

4. **Validation**
   - Check project-link exists before Mode B operations
   - Validate ownership_mode matches expected behavior
   - Warn if artifact written to wrong location

5. **Cross-repo operations**
   - `asyncdev project-link validate` - Check artifact placement
   - `asyncdev project-link sync` - Report discrepancies between repos

### Out of Scope

1. Automatic artifact migration (follow-up feature)
2. Git cross-repo sync (future)
3. Multi-project portfolio (future)
4. Remote repo operations (git clone, push)

---

## Dependencies

| Dependency | Feature | Status |
|------------|---------|--------|
| project-link schema | Feature 039 | ✅ Complete |
| AGENTS.md governance | Feature 039 | ✅ Complete |
| StateStore | Core | ✅ Complete |
| FeatureSpec schema | Core | ✅ Complete |
| ExecutionPack schema | Core | ✅ Complete |

---

## Deliverables

1. `runtime/project_link_loader.py` - Project-link loading and path resolution
2. `runtime/artifact_router.py` - Artifact routing based on ownership
3. `cli/commands/project_link.py` - New CLI commands for project-link management
4. Updated CLI commands (new-feature, plan-day, run-day, review-night, complete-feature)
5. `tests/test_project_link_loader.py` - Loader tests
6. `tests/test_artifact_router.py` - Routing tests
7. Updated AGENTS.md - CLI routing rules

---

## Architecture

### Project-Link Loading Flow

```
CLI command invoked with --project <id>
         ↓
project_link_loader.load(project_id)
         ↓
┌─────────────────────────────────────┐
│ Check projects/{id}/project-link.yaml│
│ - exists? → Mode B                   │
│ - not exists? → Mode A (self_hosted) │
└─────────────────────────────────────┘
         ↓
Return ProjectLinkContext:
  - ownership_mode
  - product_repo_path
  - orchestration_repo_path
  - product_artifact_root
  - orchestration_artifact_root
```

### Artifact Routing Decision

```python
def route_artifact(artifact_type: str, context: ProjectLinkContext) -> Path:
    """
    Route artifact to correct repo based on ownership rules.
    
    Product-owned (write to product repo in Mode B):
    - ProductBrief
    - FeatureSpec
    - FeatureCompletionReport
    - DogfoodReport
    - FrictionLog
    - PhaseSummary
    - NorthStar
    
    Orchestration-owned (write to async-dev in Mode B):
    - ExecutionPack
    - ExecutionResult
    - RunState
    - VerificationRecord
    - ContinuationState
    - DailyReviewPack (summary only)
    """
```

### Mode Detection Logic

| Condition | Mode | Behavior |
|-----------|------|----------|
| project-link.yaml exists with `managed_external` | Mode B | Route artifacts per ownership rules |
| project-link.yaml exists with `self_hosted` | Mode A | All artifacts in same repo |
| No project-link.yaml | Mode A (default) | All artifacts in async-dev |

---

## Acceptance Criteria

### Must Pass

1. ✅ CLI commands read project-link.yaml automatically
2. ✅ Mode B: FeatureSpec written to product repo
3. ✅ Mode B: ExecutionPack written to async-dev
4. ✅ Mode A: All artifacts in single repo (unchanged behavior)
5. ✅ Validation warns if artifact placed incorrectly
6. ✅ Tests pass for routing logic

### Should Pass

1. ✅ `asyncdev project-link validate` command works
2. ✅ Cross-repo path resolution handles relative paths
3. ✅ Error if project-link.yaml invalid schema
4. ✅ Backward compatible with Mode A projects

---

## Implementation Phases

### Phase A: Core Loader
- Create `project_link_loader.py`
- Load and validate project-link.yaml
- Resolve repo paths

### Phase B: Artifact Router
- Create `artifact_router.py`
- Implement routing rules per Feature 039
- Mode detection logic

### Phase C: CLI Integration
- Update `new-feature` command
- Update `plan-day` command
- Update `run-day` command
- Update `review-night` command
- Update `complete-feature` command

### Phase D: Validation Commands
- `asyncdev project-link validate`
- `asyncdev project-link sync`
- Documentation updates

---

## CLI Command Changes

### new-feature create

```bash
# Before (Mode A only)
asyncdev new-feature create --product-id my-app --feature-id feature-001

# After (Mode B aware)
asyncdev new-feature create --product-id amazing-briefing-viewer --feature-id feature-001
# → FeatureSpec written to G:/Workspace/amazing-briefing-viewer/docs/features/
```

### project-link validate

```bash
asyncdev project-link validate --project amazing-briefing-viewer
# Output:
# - Product repo artifacts: 15 found
# - Orchestration repo artifacts: 8 found
# - Discrepancies: 0
# - Status: OK
```

### project-link sync

```bash
asyncdev project-link sync --project amazing-briefing-viewer
# Output:
# - Checking artifact alignment...
# - FeatureSpecs: product repo has 13, expected 13 ✓
# - ExecutionPacks: async-dev has 1, expected 1 ✓
# - RunState: async-dev ✓
```

---

## Risks

| Risk | Mitigation |
|------|------------|
| Relative path resolution fails | Support absolute paths, validate at init |
| Product repo not accessible locally | Check `repo_local_path` existence, fallback to remote |
| Backward compatibility break | Mode A projects unaffected (no project-link.yaml) |
| Schema validation strict | Allow optional fields, warn on missing |

---

## Estimated Effort

- Phase A: 2-3 hours
- Phase B: 2-3 hours
- Phase C: 2-3 hours
- Phase D: 1-2 hours
- Total: 7-10 hours (1-2 day loops)

---

## Notes

This feature is critical for Mode B product development. Without it, the governance boundary rules in AGENTS.md are purely advisory, not enforced by tooling.

Priority: **P1** - Should be implemented before using async-dev for additional managed products.