# Feature 057 — Config Safety Automation (Gitignore Auto-Check)

## Status
`planning`

## Objective
Automatically ensure sensitive configuration files are excluded from git, preventing accidental credential exposure. Integrate gitignore checks into async-dev initialization and provider setup workflows.

---

## Problem Statement

During amazing-briefing-viewer development, we observed:

1. **resend-config.json manual exclusion**: User had to manually remind to exclude `.runtime/resend-config.json`
2. **Cloudflare worker directory not excluded**: `cloudflare/` needed manual gitignore addition
3. **No automated safety check**: `asyncdev init` and `resend-auth setup` don't check gitignore
4. **Risk of credential exposure**: API keys, tokens, secrets could be accidentally committed

**The gap**: Security-conscious defaults exist in documentation, but tooling doesn't enforce them.

---

## Scope

### In Scope

1. **Sensitive file detection**
   - `runtime/sensitive_file_detector.py` - Detect sensitive patterns
   - Patterns: `*config.json`, `*.env`, `*secret*`, `*token*`, `cloudflare/`, `.runtime/`
   - Project-level and global gitignore

2. **Gitignore auto-update**
   - `runtime/gitignore_manager.py` - Manage .gitignore entries
   - Add missing entries automatically
   - Check before provider setup completion
   - Verify at init time

3. **CLI integration**
   - `asyncdev init create` → Check and update gitignore
   - `asyncdev resend-auth setup` → Ensure resend-config excluded
   - `asyncdev doctor` → Check for exposed sensitive files
   - `asyncdev config safety-check` → Dedicated safety check command

4. **Safety rules**
   - `.runtime/` directory (all contents)
   - `*.env` files (environment secrets)
   - `*-config.json` files (provider configs)
   - `*-secret*` files (any secrets)
   - `cloudflare/` (worker credentials)
   - `.secrets/` directory

5. **Warnings and alerts**
   - Warn if sensitive file exists but not gitignored
   - Alert if sensitive file already tracked by git
   - Block provider setup if gitignore not updated

### Out of Scope

1. Removing already-tracked files from git history (manual git filter-branch)
2. Secret encryption (future feature)
3. Secret injection from external vaults
4. Pre-commit hooks (optional follow-up)

---

## Dependencies

| Dependency | Feature | Status |
|------------|---------|--------|
| Gitignore file format | Standard | ✅ N/A |
| Runtime directory | Core | ✅ Complete |
| Resend config schema | Feature 053 | ✅ Complete |
| Doctor command | Feature 033 | ✅ Complete |

---

## Deliverables

1. `runtime/sensitive_file_detector.py` - Pattern detection module
2. `runtime/gitignore_manager.py` - Gitignore management module
3. `cli/commands/config.py` - Config safety CLI commands
4. Updated `init.py` - Add gitignore check
5. Updated `resend_auth.py` - Add gitignore check
6. Updated `doctor.py` - Add sensitive file check
7. `tests/test_config_safety.py` - Safety logic tests
8. Updated `.gitignore` template - Add safety entries

---

## Architecture

### Safety Check Flow

```
Provider setup or init
         ↓
gitignore_manager.check_sensitive_patterns()
         ↓
┌─────────────────────────────────────────────┐
│ Scan for sensitive patterns:                │
│ - .runtime/ exists? → check gitignore       │
│ - *-config.json exists? → check gitignore   │
│ - *.env exists? → check gitignore           │
│ - cloudflare/ exists? → check gitignore     │
└─────────────────────────────────────────────┘
         ↓
Return: SafetyCheckResult
  - safe: boolean
  - missing_entries: [...]
  - tracked_sensitive: [...] (danger!)
  - warnings: [...]
         ↓
If not safe:
  gitignore_manager.add_entries(missing_entries)
  Warn user about tracked_sensitive (manual remediation needed)
```

### Gitignore Manager Operations

```python
class GitignoreManager:
    def check_patterns(self, patterns: list[str]) -> SafetyCheckResult
    def add_entries(self, entries: list[str]) -> None
    def remove_entries(self, entries: list[str]) -> None
    def is_excluded(self, file_path: str) -> bool
    def scan_tracked_sensitive(self) -> list[str]  # Danger zone
```

### Safety Patterns

```yaml
sensitive_patterns:
  directories:
    - ".runtime/"
    - ".secrets/"
    - "cloudflare/"
    - ".credentials/"
  
  files:
    - "*.env"
    - "*.env.local"
    - "*-config.json"
    - "*-secret*"
    - "*token*"
    - "*credentials*"
    - "resend-config.json"
    - ".resend-config.json"
  
  globs:
    - "**/secrets/**"
    - "**/.env*"
    - "**/*secret*"
```

---

## Acceptance Criteria

### Must Pass

1. ✅ `.runtime/` auto-added to gitignore on init
2. ✅ `resend-config.json` auto-checked on `resend-auth setup`
3. ✅ `doctor` detects exposed sensitive files
4. ✅ Provider setup blocked if gitignore not updated (optional override)
5. ✅ Tests pass for safety logic

### Should Pass

1. ✅ `config safety-check` CLI command works
2. ✅ Warn if sensitive file already tracked by git
3. ✅ Support project-level and global gitignore
4. ✅ Backward compatible with existing gitignores

---

## Implementation Phases

### Phase A: Pattern Detector
- Create `sensitive_file_detector.py`
- Define pattern list
- File system scanning logic

### Phase B: Gitignore Manager
- Create `gitignore_manager.py`
- Read/write gitignore
- Check exclusion status
- Track git-tracked files

### Phase C: CLI Integration
- Update `init.py` - Add check at init
- Update `resend_auth.py` - Add check after setup
- Update `doctor.py` - Add sensitive file check
- Create `config.py` - Dedicated safety commands

### Phase D: Testing
- Test suite
- Integration tests
- Edge cases (already tracked, global gitignore)

---

## CLI Commands

### config safety-check

```bash
asyncdev config safety-check --project amazing-briefing-viewer

# Output:
# ✅ .runtime/ - excluded
# ✅ resend-config.json - excluded  
# ⚠️ cloudflare/ - NOT excluded (add to gitignore)
# 🚨 .env.local - TRACKED BY GIT (danger!)
```

### doctor enhancement

```bash
asyncdev doctor --project amazing-briefing-viewer

# Output includes:
# ...
# [Config Safety]
# - Sensitive patterns checked: 8
# - Excluded correctly: 6
# - Missing gitignore entries: 1
# - Exposed in git: 1 (DANGER)
# - Recommendation: Run 'asyncdev config safety-fix'
```

### config safety-fix

```bash
asyncdev config safety-fix --project amazing-briefing-viewer

# Output:
# Adding missing gitignore entries:
# - cloudflare/
# 
# ⚠️ Cannot auto-fix tracked files:
# - .env.local is already tracked by git
# - Manual remediation required:
#   git rm --cached .env.local
#   git commit -m "Remove exposed secrets"
```

---

## Risks

| Risk | Mitigation |
|------|------------|
| User removes gitignore entries later | Doctor check on every run |
| Already tracked sensitive files | Clear warning, manual remediation guide |
| Global gitignore conflict | Support both project and global |
| Missing patterns | Extensible pattern list, user can add |

---

## Estimated Effort

- Phase A: 1-2 hours
- Phase B: 1-2 hours
- Phase C: 2-3 hours
- Phase D: 1-2 hours
- Total: 5-8 hours (1 day loop)

---

## Notes

This feature is critical for preventing credential exposure. The recent session showed that users must manually remind about gitignore, which is a safety gap.

Priority: **P1** - Should be implemented before any real credential usage.

---

## Sensitive File Categories

| Category | Pattern | Risk Level |
|----------|---------|------------|
| Runtime config | `.runtime/*.json` | HIGH (contains API keys) |
| Environment secrets | `*.env` | HIGH (contains secrets) |
| Provider config | `*-config.json` | HIGH (contains tokens) |
| Worker credentials | `cloudflare/` | HIGH (contains worker secrets) |
| Secret directories | `.secrets/` | HIGH (any secrets) |
| Token files | `*token*` | MEDIUM (may contain tokens) |
| Credential files | `*credentials*` | MEDIUM (may contain credentials) |

---

## Integration Points

| Command | Safety Check |
|---------|--------------|
| `asyncdev init create` | Add `.runtime/` to gitignore |
| `asyncdev resend-auth setup` | Check resend-config exclusion |
| `asyncdev doctor` | Full sensitive file scan |
| `asyncdev new-product create` | Check project gitignore |
| `asyncdev run-day execute` | Warn if exposed secrets detected (optional) |