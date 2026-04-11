# Archive Query / History Inspection

Feature 014 adds practical archive query and history inspection capabilities to `amazing-async-dev`.

---

## Overview

The archive layer now supports active querying instead of passive storage. Operators can:
- List archived features across all products
- Inspect specific archive details
- Filter by patterns, lessons, or recency
- Surface reusable knowledge for future development

---

## CLI Commands

### List Archives

```bash
asyncdev archive list
```

Lists all archived features globally across all products.

**Output includes:**
- Feature ID
- Product ID
- Title
- Status (completed/partial)
- Archived date
- Patterns count
- Lessons count

### Filter Options

```bash
asyncdev archive list --product <id>      # Filter by product
asyncdev archive list --recent            # Sort by most recent
asyncdev archive list --has-patterns      # Only with reusable patterns
asyncdev archive list --has-lessons       # Only with lessons learned
asyncdev archive list --limit 10          # Limit results
```

**Examples:**

```bash
asyncdev archive list --recent --limit 5
asyncdev archive list --product demo-product
asyncdev archive list --has-patterns --has-lessons
```

---

### Show Archive Detail

```bash
asyncdev archive show --feature <id>
asyncdev archive show --feature <id> --product <id>
```

Displays full archive pack for a specific feature.

**Output includes:**
- Feature identity and status
- Delivered outputs
- Lessons learned (with context)
- Reusable patterns (with applicability)
- Decisions made
- Unresolved follow-ups
- Archive pack file path

**Examples:**

```bash
asyncdev archive show --feature 001-auth
asyncdev archive show --feature 001-core --product my-app
```

---

## Data Source Model

**Primary source:** ArchivePack YAML files (`projects/{product}/archive/{feature}/archive-pack.yaml`)

**Secondary source:** SQLite `archive_records` table (metadata index)

Files are human-readable and authoritative. SQLite provides fast metadata queries.

---

## Typical Workflows

### Find Recent Archives

```bash
asyncdev archive list --recent --limit 10
```

### Find Features with Reusable Patterns

```bash
asyncdev archive list --has-patterns
```

### Learn from Past Lessons

```bash
asyncdev archive list --has-lessons
asyncdev archive show --feature 001-auth
```

### Inspect a Specific Archive

```bash
asyncdev archive show --feature 001-auth --product demo-product
```

---

## Integration with Other Commands

| Command | Relationship |
|---------|--------------|
| `asyncdev archive-feature` | Creates archive pack (archiving process) |
| `asyncdev archive` | Queries archive pack (inspection) |
| `asyncdev backfill` | Creates historical archive packs |
| `asyncdev status --all` | Shows archive count per product |

---

## Lessons and Patterns

### Lessons Learned

Each archive pack captures lessons from the feature:

```yaml
lessons_learned:
  - lesson: "Small tasks work better"
    context: "Testing phase"
  - lesson: "Test early in API work"
    context: "API feature development"
```

### Reusable Patterns

Patterns for future features:

```yaml
reusable_patterns:
  - pattern: "Schema-first approach"
    applicability: "Object definitions"
  - pattern: "Template pattern"
    applicability: "Documentation"
```

---

## Implementation Details

| Component | File |
|-----------|------|
| CLI commands | `cli/commands/archive.py` |
| Query logic | `runtime/archive_query.py` |
| Tests | `tests/test_archive_query.py` |

---

## Success Criteria

Feature 014 is complete when:

- [x] Archived features can be listed through CLI
- [x] Single archive can be inspected through CLI
- [x] Filtering supports --recent, --has-patterns, --has-lessons, --product
- [x] Lessons learned are visible in show output
- [x] Reusable patterns are visible in show output
- [x] Archive query results show patterns/lessons counts
- [x] Documentation explains archive query workflow

---

## Related Files

- `docs/infra/amazing-async-dev-feature-014-archive-query-and-history-inspection.md` - Full spec
- `runtime/archive_pack_builder.py` - Archive pack creation
- `cli/commands/archive_feature.py` - Archive creation CLI