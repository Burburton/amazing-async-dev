# Batch Operations (Feature 018)

Limited batch capabilities to reduce repetitive operator work.

---

## Overview

Feature 018 introduces a small, safe set of batch operations:

- **Batch status** - Inspect multiple features at once
- **Batch archive query** - Already supported via filters
- **Batch backfill** - Process multiple eligible features
- **Batch summary** - Portfolio view across all projects

---

## Commands

### Batch Status Inspection

```bash
# Show all features in a project
asyncdev status --project demo-product --all-features

# Output: table with feature ID, phase, status, archive state
```

### Batch Archive Query

```bash
# Filter archives by patterns or lessons
asyncdev archive list --product {id} --has-patterns
asyncdev archive list --product {id} --has-lessons
asyncdev archive list --recent --limit 10
```

### Batch Backfill

```bash
# Preview what would be backfilled
asyncdev backfill batch --project demo --dry-run

# Process all eligible features (requires --all)
asyncdev backfill batch --project demo --all

# Limit batch size
asyncdev backfill batch --project demo --all --limit 5
```

Safety features:
- Requires explicit `--all` flag
- `--dry-run` for preview
- Shows summary before processing
- Reports each result

### Batch Summary

```bash
# Portfolio view across all projects
asyncdev summary all-projects
```

Shows:
- Project count
- Phase distribution
- Blocked items total
- Pending decisions total
- Archived features total

---

## Safety Boundaries

**What batch operations do NOT support:**

- Concurrent execution of multiple active features
- Multi-feature autonomous orchestration
- Multi-project scheduling
- Broad bulk mutations without safeguards

**Design principle:** Batch should reduce repetition, not increase execution risk.

---

## Typical Usage Patterns

### Morning Portfolio Check

```bash
asyncdev summary all-projects
asyncdev status --project {active-project} --all-features
```

### Bulk Archive Review

```bash
asyncdev archive list --recent --has-lessons
asyncdev archive show --feature {id}
```

### Historical Feature Cleanup

```bash
asyncdev backfill list --project {id}
asyncdev backfill batch --project {id} --dry-run
asyncdev backfill batch --project {id} --all --limit 10
```

---

## Integration with Existing Commands

Batch operations extend existing commands:

| Existing | Batch Extension |
|----------|-----------------|
| `status` | `--all-features` |
| `archive list` | `--has-patterns`, `--has-lessons` (already existed) |
| `backfill create` | `batch` subcommand |
| `summary today` | `all-projects` subcommand |

---

## Definition of Done

Feature 018 is complete when:

- Multiple statuses can be inspected efficiently
- Multiple archives can be queried with filters
- Historical backfill can run in batch mode
- Batch behavior is explicit and safe
- Repetitive effort is reduced