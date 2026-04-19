# Feature 056 — Browser Verification Auto Integration

## Status
`complete`

## Objective
Automate browser verification for frontend projects by integrating Playwright into async-dev's execution flow. Eliminate manual Playwright invocation and enforce Feature 038's verification gate rules automatically.

---

## Problem Statement

During amazing-briefing-viewer development (frontend project), we observed:

1. **AGENTS.md has rules but no tooling**: Feature 038 defines `verification_type` classification and verification gate, but no CLI integration exists
2. **Manual Playwright invocation**: AI must manually call `skill_mcp` with playwright, easily forgotten
3. **ExecutionResult manual fill**: `browser_verification` field exists but must be manually populated
4. **No dev server coordination**: AI must manually start dev server, wait, then test browser
5. **Verification skipped risk**: Frontend projects may complete without actual browser testing

**The gap**: The rules exist in AGENTS.md Section 9, but execution doesn't enforce them.

---

## Scope

### In Scope

1. **Verification type classification**
   - Auto-detect from feature/task characteristics
   - Types: `backend_only`, `frontend_noninteractive`, `frontend_interactive`, `frontend_visual_behavior`, `mixed_app_workflow`
   - Classification based on: feature tags, file changes, project type

2. **Dev server management**
   - Auto-start dev server for frontend verification
   - Poll for server readiness
   - Handle long-running server processes
   - Cleanup after verification

3. **Playwright integration**
   - `runtime/browser_verifier.py` - Playwright automation module
   - Auto-capture screenshots
   - Console error detection
   - Accessibility snapshot capture
   - Scenario execution

4. **CLI command**
   - `asyncdev browser-test --project <id>` - Run browser verification
   - Options: `--url`, `--scenarios`, `--timeout`

5. **ExecutionResult integration**
   - Auto-populate `browser_verification` field
   - Record: executed, passed, failed, scenarios_run, screenshots, duration

6. **Exception handling**
   - Playwright unavailable → record exception_reason
   - CI/container limitations → handle gracefully
   - Missing credentials → skip with documentation

### Out of Scope

1. Full E2E test suite (future feature)
2. Browser performance testing
3. Visual regression testing
4. Multi-browser testing (Safari, Firefox)
5. Mobile viewport testing

---

## Dependencies

| Dependency | Feature | Status |
|------------|---------|--------|
| AGENTS.md verification gate | Feature 038 | ✅ Documented |
| ExecutionResult schema | Core | ✅ Complete |
| Playwright MCP | External | ✅ Available via skill_mcp |
| Runtime configuration | Core | ✅ Complete |

---

## Deliverables

1. `runtime/verification_classifier.py` - Auto-classify verification_type
2. `runtime/browser_verifier.py` - Playwright automation module
3. `runtime/dev_server_manager.py` - Dev server lifecycle management
4. `cli/commands/browser_test.py` - New CLI command
5. `cli/commands/run_day.py` update - Auto-trigger browser verification
6. `tests/test_browser_verifier.py` - Verifier tests
7. Updated AGENTS.md - Tool integration section

---

## Architecture

### Verification Classification Flow

```
Feature/Task execution
         ↓
verification_classifier.classify(task_context)
         ↓
┌─────────────────────────────────────────────┐
│ Classification rules:                       │
│ - src/components/*.tsx → frontend_*         │
│ - docs/*.md → backend_only                  │
│ - src/api/*.py → backend_only               │
│ - UI changes in spec → frontend_interactive │
│ - Visual behavior spec → frontend_visual    │
│ - Mixed files → mixed_app_workflow          │
└─────────────────────────────────────────────┘
         ↓
Return: verification_type
```

### Browser Verification Flow (frontend_interactive)

```
run-day detects frontend_interactive
         ↓
dev_server_manager.start(project)
         ↓
Poll localhost:3000-3006 until ready (timeout: 60s)
         ↓
browser_verifier.run(project_url)
         ↓
┌─────────────────────────────────────────────┐
│ Playwright actions:                         │
│ 1. Navigate to URL                          │
│ 2. Capture accessibility snapshot           │
│ 3. Check console errors                     │
│ 4. Execute defined scenarios                │
│ 5. Capture screenshots                     │
└─────────────────────────────────────────────┘
         ↓
Generate browser_verification result:
  - executed: true
  - passed: N
  - failed: M
  - scenarios_run: [...]
  - screenshots: [...]
  - console_errors: [...]
         ↓
dev_server_manager.stop()
         ↓
Write to ExecutionResult.browser_verification
```

### Exception Handling

```yaml
browser_verification:
  executed: false
  exception_reason: "playwright_unavailable"
  exception_details: "Playwright MCP not available in this environment"
  fallback: "Manual verification required"
```

---

## Acceptance Criteria

### Must Pass (FR-7 from Feature 038)

1. ✅ Frontend-interactive task MUST NOT be marked `status: success` without browser verification
2. ✅ OR valid `browser_verification.exception_reason` recorded with explanation
3. ✅ `verification_type` auto-classified based on task context
4. ✅ Dev server auto-started and polled for readiness
5. ✅ Playwright invoked after server ready
6. ✅ ExecutionResult `browser_verification` field auto-populated
7. ✅ Console errors detected and recorded

### Should Pass

1. ✅ Screenshots captured and paths recorded
2. ✅ Accessibility snapshot captured
3. ✅ Multiple scenarios executed
4. ✅ Exception handling for all defined reasons
5. ✅ Tests pass

---

## Exception Reasons (from Feature 038)

| Reason | When to Use |
|--------|-------------|
| `playwright_unavailable` | Playwright MCP not available |
| `environment_blocked` | Environment constraints prevent execution |
| `browser_install_failed` | Browser installation failed |
| `ci_container_limitation` | CI/container cannot run browser |
| `missing_credentials` | Required credentials not available |
| `deterministic_blocker` | Known blocker prevents meaningful verification |
| `reclassified_noninteractive` | Feature reclassified as non-interactive |

---

## Implementation Phases

### Phase A: Classification Logic
- Create `verification_classifier.py`
- Implement classification rules
- Task context analysis

### Phase B: Dev Server Manager
- Create `dev_server_manager.py`
- Server start/stop/poll logic
- Multiple framework support (Vite, Next.js, React)

### Phase C: Browser Verifier
- Create `browser_verifier.py`
- Playwright MCP integration
- Console error capture
- Screenshot capture
- Accessibility snapshot

### Phase D: CLI Integration
- Create `browser_test.py` CLI command
- Update `run_day.py` to auto-trigger verification
- ExecutionResult population

---

## CLI Commands

### browser-test

```bash
# Auto-detect and run
asyncdev browser-test --project amazing-briefing-viewer

# With specific URL
asyncdev browser-test --project amazing-briefing-viewer --url http://localhost:3000

# With scenarios
asyncdev browser-test --project amazing-briefing-viewer --scenarios "render,console-check"

# With timeout
asyncdev browser-test --project amazing-briefing-viewer --timeout 120
```

### run-day integration

```bash
asyncdev run-day execute --project amazing-briefing-viewer --mode external
# → If frontend_interactive detected:
#    → Auto-start dev server
#    → Run browser verification
#    → Populate ExecutionResult
```

---

## Risks

| Risk | Mitigation |
|------|------------|
| Dev server port conflict | Try multiple ports (3000-3006), warn user |
| Playwright MCP unavailable | Graceful exception with manual fallback |
| Long verification time | Timeout config, async scenarios |
| CI environment limitations | Detect CI, apply exception handling |

---

## Estimated Effort

- Phase A: 1-2 hours
- Phase B: 2-3 hours
- Phase C: 3-4 hours
- Phase D: 2-3 hours
- Total: 8-12 hours (1-2 day loops)

---

## Notes

This feature is critical for frontend product development. The AGENTS.md rules (Feature 038) define the behavior, but tooling must enforce it.

Priority: **P1** - Frontend projects (like briefing-viewer) cannot be verified without this integration.

---

## Verification Type Classification Rules

| Pattern | verification_type |
|---------|------------------|
| `src/components/*.tsx` modified | `frontend_interactive` |
| `src/pages/*.tsx` modified | `frontend_interactive` |
| `src/styles/*.css` modified | `frontend_visual_behavior` |
| `docs/*.md` only | `backend_only` |
| `src/api/*.py` only | `backend_only` |
| `tests/*.py` only | `backend_only` |
| Mix of frontend + backend | `mixed_app_workflow` |
| Feature spec mentions "UI" or "component" | `frontend_interactive` |