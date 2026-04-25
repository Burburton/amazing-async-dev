# async-dev Platform Readiness Model

## Purpose

Define what makes the async-dev platform "ready" beyond individual feature completion.

---

## Platform-Level Acceptance Criteria

### Execution Kernel Stability

The execution kernel is considered "stable enough" when:

| Criterion | Evidence | Status |
|-----------|----------|--------|
| Day loop commands work end-to-end | 3-day dogfooding completed | ✅ Verified |
| State persists across interruptions | RunState survives process exit | ✅ Verified |
| Resume works from state | Next day starts without re-explanation | ✅ Verified |
| Execution boundaries honored | ExecutionResult matches ExecutionPack scope | ✅ Verified |
| SQLite persistence operational | Events logged, recovery queries work | ✅ Verified |

### Operator Surface Coherence

Operator surfaces are considered "integrated" when:

| Criterion | Evidence | Status |
|-----------|----------|--------|
| CLI entrypoint exists | `asyncdev recovery`, `decision`, `session-start` | ✅ Implemented |
| Consumes canonical state | Uses StateStore, not mock data | ✅ Verified (066a) |
| Triggers real actions | Recovery actions wired to flows | ✅ Verified (066a) |
| Documentation explains purpose | README CLI Reference, AGENTS.md | ✅ Present |

### Policy Layer Foundation

Policy/recipe layer is considered "functional" when:

| Criterion | Evidence | Status |
|-----------|----------|--------|
| Verification recipe executes | FrontendVerificationRecipe runs | ✅ Implemented (062) |
| Browser verification orchestrated | Feature 060 orchestrator | ✅ Implemented |
| Closeout policy enforced | Feature 061 closeout | ✅ Implemented |
| Escalation rules defined | Feature 064 blocking protocol | ✅ Implemented |

---

## Maturity Levels

| Level | Name | Description | Current State |
|-------|------|-------------|---------------|
| **Functional Alpha** | Core works, surfaces exist | Kernel stable, operator surfaces implemented, policy layer partial | ✅ Current |
| **Hardened Alpha** | Edge cases handled | All layers tested, error recovery robust | In progress |
| **Beta** | Production-ready paths | Verified through multiple real projects, docs complete | Future |
| **Stable** | Release-ready | Versioned, changelog, migration guides | Future |

---

## What Is Production-Ready

| Component | Ready? | Notes |
|-----------|--------|-------|
| Day loop commands | ✅ Yes | Verified through dogfooding |
| SQLite persistence | ✅ Yes | Recovery queries tested |
| RunState management | ✅ Yes | Survives interruption |
| Recovery Console | ✅ Yes | CLI functional, wired to flows |
| Decision Inbox | ✅ Yes | CLI functional |
| Session Start | ✅ Yes | Blocking protocol enforced |
| Execution Observer | ✅ Yes | CLI functional, findings displayed |
| Frontend verification | ⚠️ Partial | Recipe exists, needs more test coverage |
| Live API mode | ⚠️ Partial | Works, error handling matured |

---

## What Remains Alpha/Experimental

| Area | Status | Hardening Needed |
|------|--------|------------------|
| Policy layer completeness | Alpha | More recipe types |
| Cross-project orchestration | Experimental | Mode B tested with more projects |
| Large-scale execution | Unverified | Multi-week feature execution |
| External tool integration | Alpha | More tool configurations tested |

---

## Platform Coherence Checklist

A coherent async-dev platform should satisfy:

1. **Layer model visible**: docs/architecture.md explains kernel/operator/policy layers ✅
2. **Operator surfaces positioned**: CLI Reference shows Recovery Console, Decision Inbox as operator surfaces ✅
3. **Status language consistent**: "Implemented" vs "Proposed" used consistently ✅
4. **Counts trustworthy**: No drifting counts that contradict reality ✅
5. **Cross-links work**: Core docs reference each other ✅
6. **Newcomer readable**: New reader can understand what async-dev is ✅

---

## Status Language Definitions

| Term | Meaning |
|------|---------|
| **Implemented** | Feature complete, CLI/runtime exists, tests pass |
| **Proposed** | Spec written, implementation not started |
| **Functional Alpha** | Works for early adopters, edge cases may exist |
| **Hardened** | Tested for edge cases, error recovery robust |
| **Verified** | Tested through real usage (dogfooding, projects) |

---

## Recommended Next Hardening

Based on current platform state:

1. **Policy layer recipes**: Add more verification recipe types
2. **Cross-project testing**: Verify Mode B with multiple external products
3. **Long-running execution**: Test multi-week feature completion
4. **Error recovery**: Add more recovery playbooks for edge cases
5. **Documentation alignment**: Keep counts accurate as platform evolves

---

## Summary

async-dev is a **functional alpha platform**:

- Execution kernel is stable and verified
- Operator surfaces are implemented and integrated
- Policy layer foundation exists, hardening in progress
- Platform structure is documented and coherent

The platform is ready for early adopters who:
- Understand alpha-stage limitations
- Can handle edge cases through manual intervention
- Want to dogfood and provide feedback