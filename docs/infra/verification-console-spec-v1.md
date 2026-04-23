# Verification Console — Specification

## Metadata

- **Document Type**: `operator surface specification`
- **Status**: `Proposed`
- **Owner**: `async-dev`
- **Scope**: `operator-facing product`
- **Related Architecture**: `docs/infra/async-dev-platform-architecture-product-positioning.md` (Priority 2)
- **Related Features**: Feature 038, 056, 059, 060, 062
- **Date**: `2026-04-23`

---

## 1. Purpose

The Verification Console provides operator-facing visibility and control for verification execution across projects.

Per platform architecture (Priority 2):
> "Verification Console" - recommended operator surface candidate

This complements Recovery Console and Decision Inbox by providing visibility into:
- Verification type classification
- Browser verification status
- Frontend recipe execution outcomes
- Verification gate status

---

## 2. Core Responsibilities

1. List verification states across executions
2. Show verification classification and requirements
3. Display browser verification results
4. Surface verification gate status (allowed/blocked)
5. Allow retry of failed frontend verification

---

## 3. Background: Verification Infrastructure

### Existing Components (Already Implemented)

| Component | File | Purpose |
|-----------|------|---------|
| VerificationType | `runtime/verification_classifier.py` | Classification enum (backend_only, frontend_interactive, etc.) |
| Verification Gate | `runtime/verification_gate.py` | Completion gate status |
| Frontend Recipe | `runtime/frontend_verification_recipe.py` | Controlled frontend verification execution |
| Browser Verifier | `runtime/browser_verifier.py` | Playwright-based verification |
| Verification Session | `runtime/verification_session.py` | Session state tracking |
| Verification Enforcer | `runtime/verification_enforcer.py` | Timeout enforcement |

### Verification Types

| Type | Browser Required? | Description |
|------|-------------------|-------------|
| backend_only | No | Backend/api changes only |
| frontend_noninteractive | Optional | Static frontend, no interaction |
| frontend_interactive | Yes | Interactive UI components |
| frontend_visual_behavior | Yes | Visual/animation behavior |
| mixed_app_workflow | Yes | Frontend + backend changes |

---

## 4. Proposed CLI Commands

### 4.1 `asyncdev verification list`

List verification states across executions.

```
asyncdev verification list [--project <project_id>] [--all] [--status <status>]
```

**Output Format**:
```
Verification States:

| Execution ID     | Project      | Type              | Browser Req | Status    | Updated |
|------------------|--------------|-------------------|-------------|-----------|---------|
| exec-20260423-001 | amazing-dev  | frontend_interactive | Yes       | pending   | 2026-04-23 10:30 |
| exec-20260422-003 | demo-product | backend_only      | No          | success   | 2026-04-22 18:15 |
```

### 4.2 `asyncdev verification show`

Show detailed verification context.

```
asyncdev verification show --execution <execution_id>
```

**Output Sections**:
- Verification classification (type, confidence, reasoning)
- Browser verification requirement
- Verification gate status (allowed/blocked)
- Browser verification result (if executed)
- Exception reason (if not executed)
- Frontend recipe stages (if applicable)
- Linked artifacts

### 4.3 `asyncdev verification classify`

Classify verification type for files/task.

```
asyncdev verification classify --files <file1,file2,...> [--description "task description"]
```

**Output**: ClassificationResult with type, confidence, detected_patterns, reasoning.

### 4.4 `asyncdev verification retry`

Retry failed frontend verification.

```
asyncdev verification retry --execution <execution_id> [--timeout 120]
```

**Behavior**: Re-runs FrontendVerificationRecipe for failed frontend verification.

### 4.5 `asyncdev verification gate`

Check completion gate status.

```
asyncdev verification gate --execution <execution_id>
```

**Output**: `allowed` or `blocked` with reason.

---

## 5. Integration Points

### 5.1 Data Sources

| Source | Path | Content |
|--------|------|---------|
| ExecutionResult | `projects/{project}/execution-results/*.md` | `browser_verification`, `verification_result` |
| RunState | `projects/{project}/runstate.md` | `verification_type` hint |
| Verification Classifier | `runtime/verification_classifier.py` | Classification logic |
| Verification Gate | `runtime/verification_gate.py` | Gate validation |

### 5.2 Verification Flow

```
Task → VerificationClassifier → VerificationType
                                     ↓
                            VerificationGate
                                     ↓
                        FrontendVerificationRecipe (if browser required)
                                     ↓
                        BrowserVerifier
                                     ↓
                        ExecutionResult (verification_result field)
                                     ↓
                        Verification Console (operator visibility)
```

---

## 6. Acceptance Criteria

### AC-001 List Verification States
`verification list` shows verification states from ExecutionResults across projects.

### AC-002 Show Verification Details
`verification show` displays classification, gate status, browser results.

### AC-003 Classify Files
`verification classify` returns VerificationType for file changes.

### AC-004 Retry Frontend Verification
`verification retry` re-executes FrontendVerificationRecipe for failed executions.

### AC-005 Gate Status Display
`verification gate` shows completion gate status with blocking reason.

### AC-006 Cross-Project Visibility
`--all` flag lists verification states across all projects.

---

## 7. Non-Goals

- Does NOT create new verification types
- Does NOT modify FrontendVerificationRecipe execution
- Does NOT replace verification classifier logic
- Dashboard UI (CLI-only for this phase)

---

## 8. Implementation Approach

### Phase A — CLI Foundation

Create `cli/commands/verification.py`:
1. `list` command - scan ExecutionResults
2. `show` command - display verification context
3. `classify` command - wrap verification_classifier
4. `retry` command - invoke FrontendVerificationRecipe
5. `gate` command - use verification_gate

### Phase B — Cross-Project Query

- Aggregate verification states from all ExecutionResults
- Group by verification_type
- Show pending/failed/success counts

### Phase C — Retry Integration

- Wire retry command to FrontendVerificationRecipe
- Handle execution_id lookup
- Provide timeout override option

---

## 9. Definition of Done

1. All 5 CLI commands implemented
2. Cross-project verification listing works
3. Classification integration verified
4. Retry successfully invokes frontend recipe
5. Tests cover list/show/classify/retry/gate
6. Documentation updated in README.md

---

## 10. Status

**Proposed** — Ready for implementation.