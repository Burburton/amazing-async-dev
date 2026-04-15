# Governance Migration Guide (Feature 039)

> Guidance for migrating existing artifacts to comply with ownership boundary rules.

---

## When Migration Is Needed

Migration is needed when:
1. A managed external product has artifacts stored primarily in async-dev
2. The product repo lacks its own canonical documents
3. Artifacts are stored unpredictably across both repos

---

## Migration Steps

### Step 1: Classify Ownership Mode

Check if the product has a separate repository:
- **If yes** → Mode B (managed_external)
- **If no** → Mode A (self_hosted) - no migration needed

### Step 2: Identify Product-Owned Artifacts

For Mode B, identify artifacts that should move to the product repo:
- ProductBrief
- FeatureSpec files
- Dogfood reports
- Friction logs
- Phase summaries
- North-star documents

### Step 3: Create project-link.yaml

In async-dev `projects/{product_id}/`, create:

```yaml
product_id: "{product_id}"
repo_name: "{repo_name}"
repo_url: "{repo_url}"
ownership_mode: "managed_external"
sync_notes: "Migration in progress"
```

### Step 4: Copy Product Artifacts to Product Repo

For each product-owned artifact:
1. Copy from async-dev to product repo `projects/{product_id}/`
2. Verify the copy is complete
3. Keep original in async-dev temporarily (for rollback)

### Step 5: Update project-link.yaml

```yaml
sync_notes: "Migration complete. Product artifacts in product repo."
status: "active"
```

### Step 6: Clean Up async-dev (Optional)

After verification:
- Remove migrated product artifacts from async-dev
- Keep orchestration artifacts (ExecutionPacks, ExecutionResults, runstate)

---

## Migration Checklist

- [ ] Ownership mode classified
- [ ] project-link.yaml created
- [ ] ProductBrief copied to product repo
- [ ] FeatureSpecs copied to product repo
- [ ] Dogfood/Friction logs copied to product repo
- [ ] Phase summaries copied to product repo
- [ ] project-link.yaml sync_notes updated
- [ ] async-dev retains only orchestration artifacts

---

## Anti-Patterns During Migration

| Anti-Pattern | Correct Approach |
|--------------|-------------------|
| Deleting before copying | Copy first, verify, then clean up |
| Duplicate canonical copies | One source of truth per artifact |
| Skipping project-link | Always create linkage metadata |
| Moving orchestration artifacts | Keep ExecutionPacks/Results in async-dev |

---

## Example: amazing-visual-map Migration

### Before Migration
```
amazing-async-dev/projects/amazing-visual-map/
├── product-brief.yaml         # WRONG - should be in product repo
├── features/                  # WRONG - should be in product repo
├── execution-packs/           # CORRECT - stays here
└── execution-results/         # CORRECT - stays here
```

### After Migration
```
# In amazing-visual-map
projects/amazing-visual-map/
├── product-brief.md           # Migrated
├── features/*/feature-spec.md # Migrated
├── dogfood/                   # Migrated
└── friction/                  # Migrated

# In amazing-async-dev
projects/amazing-visual-map/
├── project-link.yaml          # NEW - linkage metadata
├── execution-packs/           # Stays
├── execution-results/         # Stays
└── runstate.md                # Stays (orchestration state)
```

---

## Verification

After migration, verify:
1. Product repo has all canonical product documents
2. async-dev has project-link.yaml
3. async-dev has only orchestration artifacts
4. Product repo is self-contained (would survive async-dev removal)