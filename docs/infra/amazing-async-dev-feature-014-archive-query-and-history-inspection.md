# Feature 014 — Archive Query / History Inspection

## 1. Feature Summary

### Feature ID
`014-archive-query-and-history-inspection`

### Title
Archive Query / History Inspection

### Goal
Make the archive layer in `amazing-async-dev` actively usable by adding practical query and inspection capabilities for archived features, decisions, lessons learned, and reusable patterns.

### Why this matters
`amazing-async-dev` now has a meaningful lifecycle history system:

- explicit completion flow
- explicit archive flow
- `ArchivePack`
- dedicated archive storage
- historical archive backfill
- SQLite-backed state and event persistence

This means the repository can now preserve historical work in a more complete way.

However, preserved history is only valuable if it can be inspected and reused efficiently.

Without archive query and inspection support, the system remains weak in these areas:

- finding relevant historical features
- reviewing past outcomes quickly
- discovering reusable patterns
- learning from prior blockers and decisions
- understanding project evolution over time

This feature exists to turn archive from passive storage into an actively useful historical asset layer.

---

## 2. Objective

Add practical archive query and history inspection capability to `amazing-async-dev` so operators can retrieve, inspect, and reuse archived knowledge without manually navigating raw archive directories.

This feature should make it easier to:

1. list archived features
2. inspect archived feature details
3. filter archive history by useful dimensions
4. surface lessons learned and reusable patterns
5. use archive history as an input to future development decisions

---

## 3. Scope

### In scope
- add archive listing capability
- add archive detail inspection capability
- add structured filtering for archive history
- support inspection of lessons learned and reusable patterns
- support practical CLI-based archive querying
- improve discoverability of archive artifacts and metadata
- document archive query and inspection workflow

### Out of scope
- semantic search
- embeddings-based retrieval
- dashboard or graphical history browser
- advanced analytics
- cross-repo historical aggregation
- automated planning based on archive history
- large knowledge graph construction

---

## 4. Success Criteria

This feature is successful when:

1. archived features can be listed without manually browsing directories
2. a single archived feature can be inspected through a clear command
3. archive history can be filtered in useful ways
4. lessons learned and reusable patterns are easy to inspect
5. the archive becomes practically reusable rather than just stored
6. the operator can understand historical outcomes with much lower friction

---

## 5. Core Design Principles

### 5.1 Query should serve reuse
The archive should not only answer “what happened?”  
It should also help answer “what should I reuse?”

### 5.2 Keep the first version structured and practical
Do not jump to semantic retrieval too early.  
Start with strong structured inspection.

### 5.3 Preserve artifact-first philosophy
Archive files remain important.  
Query/inspection should help operators reach them quickly.

### 5.4 Favor low-friction CLI access
The first useful version should work well through CLI and structured outputs.

### 5.5 Make historical context operational
History should inform current work, not remain passive documentation.

---

## 6. Main Capabilities

## 6.1 Archive listing

### Purpose
Allow operators to see archived features without manually traversing the filesystem.

### Expected functionality
- list all archived features
- list archived features by product
- sort or show recency
- show high-level metadata such as:
  - feature ID
  - title
  - archived date
  - status
  - lesson/pattern availability

### Notes
This should be the most basic archive access layer.

---

## 6.2 Archive detail inspection

### Purpose
Allow operators to inspect one archived feature in a structured, readable way.

### Expected inspection content
- feature identity
- delivered outputs
- acceptance outcome
- unresolved follow-ups
- decisions made
- lessons learned
- reusable patterns
- artifact links

### Notes
This should be strong enough that the operator does not need to manually open multiple files in the common case.

---

## 6.3 Archive filtering

### Purpose
Allow operators to narrow archive history to relevant subsets.

### Useful initial filters
- by product
- by feature ID
- by recency
- by status
- by presence of reusable patterns
- by presence of unresolved follow-ups

### Notes
The first version should remain practical and structured.

---

## 6.4 Lessons learned inspection

### Purpose
Make lessons from past features easy to review.

### Expected support
- inspect lessons for a specific archived feature
- optionally show archive entries with lessons present
- make lessons easy to reuse during future planning or review

### Notes
This should help the archive become development memory, not just storage.

---

## 6.5 Reusable pattern inspection

### Purpose
Make reusable patterns discoverable across archived features.

### Expected support
- inspect reusable patterns for a given archived feature
- list archive records that contain reusable patterns
- surface pattern-related summaries in archive query output

### Notes
The goal is structured discoverability, not full semantic similarity search.

---

## 7. CLI Expectations

The exact command shape may vary, but the first version should likely support commands equivalent to:

```bash
asyncdev archive list
asyncdev archive show --feature <id> --product <id>
asyncdev archive list --product <id>
asyncdev archive list --recent
asyncdev archive list --has-patterns
```

### Notes
The command set should stay small and coherent.

---

## 8. Data Source Expectations

This feature should use the current archive system as its source of truth, likely including:

- archive artifact files such as `archive-pack.yaml`
- SQLite archive metadata and indexes where useful

### Notes
The implementation should define clearly:
- what comes from archive files
- what comes from SQLite indexes
- how the two work together

---

## 9. Output Expectations

Archive query output should be useful both for humans and future tooling.

### Desirable qualities
- concise for list views
- more detailed for single archive inspection
- path-aware, so the operator can still reach the underlying archive artifact
- consistent with the repository’s operator-facing CLI style

### Notes
Prefer practical readability over heavy formatting complexity.

---

## 10. Deliverables

This feature must add:

### 10.1 Archive list capability
A command or command set that can list archived features.

### 10.2 Archive detail inspection capability
A command or command set that can inspect a single archived feature.

### 10.3 Archive filtering capability
At least a practical first set of structured filters.

### 10.4 Archive lessons/pattern visibility
Practical access to lessons learned and reusable patterns from archive records.

### 10.5 Documentation
At least one document or section explaining:
- how to query archive history
- how to inspect archived features
- how lessons/patterns are surfaced
- how archive query fits into operator workflow

---

## 11. Acceptance Criteria

- [ ] archived features can be listed through CLI
- [ ] a single archived feature can be inspected through CLI
- [ ] archive listing supports at least a useful first set of filters
- [ ] lessons learned are visible through inspection flow
- [ ] reusable patterns are visible through inspection flow
- [ ] archive query results help operators find the right archive artifact more quickly
- [ ] documentation explains archive query and inspection clearly

---

## 12. Risks

### Risk 1 — Building too much too early
Archive query could drift into dashboard/search ambitions too fast.

**Mitigation:** keep the first version CLI-first and structured.

### Risk 2 — Weak source-of-truth boundaries
If it is unclear whether files or SQLite drive query results, behavior may become confusing.

**Mitigation:** define a clear archive data source model.

### Risk 3 — Low-value listing without reuse support
Simple list output alone may not make archive meaningfully useful.

**Mitigation:** include lessons and reusable patterns in the first meaningful inspection layer.

### Risk 4 — Too much detail in common paths
If archive output becomes too verbose, operators may not use it.

**Mitigation:** distinguish list views from detailed show views.

---

## 13. Recommended Implementation Order

1. define archive query source model
2. implement archive list command
3. implement archive detail inspection command
4. add useful first filters
5. surface lessons learned and reusable patterns
6. improve operator-facing output clarity
7. document archive query workflow

---

## 14. Suggested Validation Questions

This feature should make the system better able to answer:

- what archived features exist?
- which archived features belong to this product?
- what did that archived feature actually deliver?
- what lessons came out of it?
- what patterns are worth reusing?
- where is the underlying archive artifact?

If the operator still has to manually dig through archive directories to answer those questions, this feature is not done.

---

## 15. Definition of Done

Feature 014 is done when:

- archived history is practically queryable
- archived features can be inspected without manual filesystem digging
- lessons learned and reusable patterns are surfaced clearly
- archive becomes an active historical asset layer rather than passive storage

If archive records exist but remain awkward to find and reuse, this feature is not done.
