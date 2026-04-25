# amazing-async-dev

**Personal Async AI Development OS**

A lightweight system for solo builders: AI works during the day, you review at night.

---

## Quick Start (3-Minute First Run)

Get started with the full day loop in 3 minutes:

```bash
# 1. Install
git clone https://github.com/Burburton/amazing-async-dev.git
cd amazing-async-dev
pip install -e .

# 2. Initialize
python cli/asyncdev.py init create

# 3. Create your first product
python cli/asyncdev.py new-product create --product-id my-first-app --name "My First App"

# 4. Add a feature
python cli/asyncdev.py new-feature create --product-id my-first-app --feature-id feature-001 --name "Hello World"

# 5. Plan today's task
python cli/asyncdev.py plan-day create --product-id my-first-app --feature-id feature-001 --task "Create hello-world.txt"

# 6. Run (external tool mode - safest for first run)
python cli/asyncdev.py run-day --product-id my-first-app --mode external

# 7. Review tonight
python cli/asyncdev.py review-night generate --product-id my-first-app

# 8. Resume tomorrow
python cli/asyncdev.py resume-next-day continue-loop --product-id my-first-app --decision approve
```

---

## What Success Looks Like

After your first successful run, you'll see these artifacts:

```
projects/my-first-app/
├── product-brief.yaml          # Your product definition
├── runstate.md                 # Current phase (planning → executing → reviewing)
├── features/feature-001/
│   └── feature-spec.yaml       # Feature scope and acceptance criteria
├── execution-packs/
│   └── exec-*.md               # Today's bounded task
├── execution-results/
│   └── exec-*.md               # AI's structured output
└── reviews/
    └── YYYY-MM-DD-review.md    # DailyReviewPack for your review
```

A successful first run produces:
- `execution-results/*.md` with `status: success`
- `reviews/*.md` with completed items and evidence
- `runstate.md` showing `current_phase: reviewing`

---

## Recommended First Mode

**Use External Tool Mode for your first run.**

This mode generates an `ExecutionPack.md` file that you can hand to any AI tool (Claude Code, OpenCode, Cursor, etc.). It's the safest path because:
- You control which AI tool executes
- You can review the ExecutionPack before execution
- No API keys required

```bash
python cli/asyncdev.py run-day --product-id my-first-app --mode external
```

Then open the generated `ExecutionPack.md` and hand it to your preferred AI tool.

---

## Initialization Modes

`amazing-async-dev` supports two ways to start:

### Mode A: Direct Initialization (Default)

Create products and features directly:

```bash
python cli/asyncdev.py new-product create --product-id my-app --name "My App"
python cli/asyncdev.py new-feature create --product-id my-app --feature-id feature-001 --name "First Feature"
```

This is the baseline path. No external tools required.

### Mode B: Starter-Pack Initialization (Optional)

Use a starter-pack file to pre-configure workflow hints:

```bash
python cli/asyncdev.py new-product create --product-id my-app --name "My App" --starter-pack starter-pack.yaml
```

This imports policy mode hints, workflow preferences, and recommended capabilities from a pre-generated pack.

**Starter-pack mode is optional.** The [amazing-skill-pack-advisor](https://github.com/Burburton/amazing-skill-pack-advisor) is a first-party ecosystem tool that can generate compatible starter packs, but it is never required for async-dev usage.

---

## Verify Your Setup

Before starting real work, confirm initialization works:

| Resource | Purpose |
|----------|---------|
| [docs/verify.md](docs/verify.md) | **Official verification guide** - smoke-test both initialization modes |
| [examples/verify-initialization](examples/verify-initialization/) | Minimal starter pack for quick testing |

Quick test:
```bash
# Direct mode (always works)
python cli/asyncdev.py new-product create --product-id test-verify --name "Test"

# Starter-pack mode (optional)
python cli/asyncdev.py new-product create --product-id test-verify --name "Test" --starter-pack examples/verify-initialization/starter-pack.yaml
```

---

## Learn More

| Resource | What you'll find |
|----------|------------------|
| [examples/README.md](examples/README.md) | **Onboarding guide** - start here for first run |
| [examples/single-feature-day-loop](examples/single-feature-day-loop/) | Default onboarding example with copy-paste commands |
| [examples/snapshot-output.md](examples/snapshot-output.md) | Workspace snapshot examples for both initialization modes |
| [examples/doctor-output.md](examples/doctor-output.md) | Doctor diagnosis examples for all health states |
| [docs/doctor.md](docs/doctor.md) | Workspace diagnosis and next-action recommendations |
| [docs/quick-start.md](docs/quick-start.md) | 5-minute guide with execution modes explained |
| [docs/verify.md](docs/verify.md) | Smoke-verification for initialization |
| [docs/operating-model.md](docs/operating-model.md) | Day loop phases and responsibilities |
| [AGENTS.md](AGENTS.md) | Rules for AI execution |

---

## Day Loop Overview

```
plan-day → run-day → review-night → resume-next-day
```

**Canonical Loop (Verified)** — The validated operator daily rhythm:

| Phase | When | What you do | CLI Command |
|-------|------|-------------|-------------|
| Morning | 5 min | Define today's bounded task | `plan-day create --project <id>` |
| Daytime | 0 min | AI executes autonomously | `run-day execute --project <id>` |
| Evening | 20-30 min | Review DailyReviewPack, decide next steps | `review-night generate --project <id>` |
| Next day | 2 min | Resume from state, no re-explanation | `resume-next-day continue-loop --project <id>` |

**Time investment**: ~30 minutes per day. AI handles the rest.

---

## Why This Exists

Most solo builders don't lack ideas. They lack uninterrupted build time.

`amazing-async-dev` is designed for:
- AI making stable progress during the day
- Human spending only 1-2 hours at night reviewing
- Work resuming the next day without re-explanation

---

## Core Problem

Without structure, AI tends to:
- drift outside intended scope
- expand tasks beyond useful boundaries
- lose continuity across days
- require too much human re-contextualization

This system enforces:
- **artifact-first workflow** (explicit artifacts, not conversation history)
- **day-sized execution** (bounded tasks fitting half-day to one day)
- **state-based resume** (next day starts from RunState)
- **small, closed loops** (clear scope, stop conditions, expected outputs)

---

## Design Principles

1. **Artifact-first** — System moves through explicit artifacts
2. **Day-sized** — Tasks fit half-day to one day of AI work
3. **Nightly decisions** — Human reviews only what requires judgment
4. **Resume by state** — Next day starts from RunState, not memory
5. **Stable boundaries** — Each execution has clear scope and outputs

---

## Core Objects

| Object | Purpose |
|--------|---------|
| `ProductBrief` | Minimum structured product idea |
| `FeatureSpec` | Bounded feature with goals, scope, criteria |
| `RunState` | Current state (pause/resume/continuity) |
| `ExecutionPack` | Package for daytime AI execution |
| `ExecutionResult` | Structured outcome of execution |
| `DailyReviewPack` | Nightly summary for human review |
| `AcceptanceResult` | Validation outcome against acceptance criteria (Feature 069) |

---

## Repository Structure

```text
amazing-async-dev/
├─ README.md           # This file
├─ AGENTS.md           # AI execution rules
├─ LICENSE             # MIT license
├─ pyproject.toml      # Package config
├─ .gitignore          # Git exclusions
├─ docs/
│  ├─ quick-start.md   # 5-minute guide
│  ├─ operating-model.md
│  ├─ architecture.md
│  ├─ terminology.md
│  ├─ real-asyncdev-consumption-pilot.md
│  └─ contract-validation-report.md
├─ schemas/            # Artifact schemas (YAML)
├─ templates/          # Fillable templates
├─ runtime/            # State management, adapters
├─ cli/                # CLI commands
├─ tests/              # pytest tests
├─ examples/
│  ├─ README.md                  # Onboarding guide - start here
│  ├─ single-feature-day-loop/   # Default onboarding example
│  ├─ core-objects/              # Schema examples
│  └─ pilot/                     # Advisor integration pilot
├─ projects/           # User products (created by CLI)
└─ products/           # Product templates (placeholder)
```

---

## Testing

```bash
python -m pytest tests/ -v
```

| Category | Coverage |
|----------|----------|
| CLI commands | All asyncdev commands |
| Phase transitions | RunState transitions |
| Artifact format | YAML/Markdown generation |
| Error handling | Missing state, invalid inputs |
| SQLite persistence | State store, recovery |
| Policy & decisions | Auto-continue, email channel |
| Integration | Advisor starter pack consumption |
| Snapshot | Workspace visibility, cross-repo state |
| Review-night | Enriched operator pack, doctor integration |
| Resume-next-day | Decision pack alignment, prior context |
| Plan-day | Resume context alignment, planning mode inference |
| Recovery Console | Operator surface for recovery |
| Decision Inbox | Operator surface for decisions |
| Session Start | Blocking alert, mandatory check |
| Execution Observer | Supervision layer (Feature 067) |

Run `pytest --collect-only` for current count.

---

## Implementation Status

All core features complete:

| Feature | Description |
|---------|-------------|
| Core Object System | Schemas, templates, examples |
| Day Loop CLI | plan-day, run-day, review-night, resume-next-day |
| Execution Modes | External tool + live API |
| State Persistence | SQLite-based storage |
| Archive System | Feature completion, history query |
| Feedback Capture | Issue capture, triage, promotion |
| Execution Policy | Auto-continue safe, pause for risky |
| Decision Channel | Email-first async decisions |
| Starter Pack Integration | Advisor → async-dev handoff |
| Execution Observer | Supervision layer for runtime health (Feature 067) |
| Recovery Console | Operator surface for execution recovery |
| Decision Inbox | Operator surface for decision management |
| Session Start | Mandatory blocking state check (Feature 065) |
| Acceptance Console | Operator surface for acceptance validation (Feature 077) |

---

## Feature Lifecycle

```
planning → executing → reviewing → blocked → completed → archived
```

| Phase | CLI |
|-------|-----|
| Unblock | `asyncdev resume-next-day unblock` |
| Complete | `asyncdev complete-feature mark` |
| Archive | `asyncdev archive-feature create` |

---

## Success Criteria

1. AI works independently for hours on bounded tasks
2. Nightly review takes 20-30 minutes
3. Human handles few meaningful decisions
4. Next day resumes from state, not explanation
5. Completed features archived with lessons

---

## CLI Reference

```bash
# Initialization
asyncdev init create
asyncdev new-product create --product-id {id} --name "{name}"
asyncdev new-feature create --product-id {id} --feature-id {id} --name "{name}"

# Day Loop
asyncdev plan-day create --product-id {id} --feature-id {id} --task "{task}"
asyncdev run-day --product-id {id} --mode {external|live|mock}
asyncdev review-night generate --product-id {id}
asyncdev resume-next-day continue-loop --product-id {id} --decision {approve|revise|defer}

# Completion & Archive
asyncdev complete-feature mark --product-id {id} --feature-id {id}
asyncdev archive-feature create --product-id {id} --feature-id {id}
asyncdev archive list --product {id}
asyncdev archive show --feature {id}

# Status & Summary
asyncdev summary today --project {id}
asyncdev summary decisions --project {id}
asyncdev status --all-features --project {id}

# Feedback
asyncdev feedback record --scope {system|product} --description "..."
asyncdev feedback list --followup-needed
asyncdev feedback promote --feedback-id {id} --reason {type}

# Policy
asyncdev policy show
asyncdev policy set --mode {conservative|balanced|low_interruption}

# Decision Channel
asyncdev email-decision create --project {id} --question "..." --options "A:...,B:..." --send
asyncdev email-decision reply --project {id} --id {id} --command "DECISION A"

# Recovery Console (Operator Surface - Phase 2)
asyncdev recovery list [--project {id}] [--all]
asyncdev recovery show --execution exec-{project}-{feature}
asyncdev recovery resume --execution exec-{project}-{feature} --action {unblock|abort|continue|retry|reset} [--execute]

# Execution Observer (Supervision Layer - Feature 067)
asyncdev observe-runs --project {id}
asyncdev observe-runs --all
asyncdev observe-runs --severity {low|medium|high|critical}

# Decision Inbox (Operator Surface - Phase 3)
asyncdev decision list [--project {id}] [--all] [--status {status}]
asyncdev decision show --request {request_id}
asyncdev decision reply --request {request_id} --command "DECISION A"
asyncdev decision wait --request {request_id} [--interval 60] [--timeout 3600]
asyncdev decision history [--project {id}] [--all] [--limit 10]

# Session Start (Mandatory - Feature 065)
asyncdev session-start check [--project {id}]
asyncdev session-start poll --project {id}
asyncdev session-start status

# Acceptance Console (Feature 077)
asyncdev acceptance run --project {id} [--execution {id}] [--policy-mode {strict|relaxed}]
asyncdev acceptance status --project {id}
asyncdev acceptance history --project {id} [--limit 10]
asyncdev acceptance result --project {id} [--result-id {id}]
asyncdev acceptance retry --project {id} [--execution {id}]
asyncdev acceptance recovery --project {id}
asyncdev acceptance gate --project {id}

# Starter Pack (advisor integration)
asyncdev new-product create --product-id {id} --name "{name}" --starter-pack starter-pack.yaml
```

---

## Project Status

| Metric | Value |
|--------|-------|
| Platform Layers | Execution Kernel (Layer A) + Operator Surfaces (Layer B) + Policy/Recipe (Layer C) |
| Package State | Functional alpha |
| Canonical Loop | ✅ Verified (3-day dogfooding) |
| Kernel Stability | Hardened (026-036 milestone complete) |

**What this means:**
- Execution kernel is stable and verified through real dogfooding
- Operator surfaces (Recovery Console, Decision Inbox, Session Start, Observer) implemented
- Policy/recipe layer partially implemented (frontend verification, closeout)
- Platform structure documented in docs/architecture.md
- Not formally released (no PyPI package, no version tag)
- Suitable for early adopters willing to clone and run

See docs/architecture.md for platform layer model.

---

## Milestone Checkpoints

### 026–036 Milestone — Canonical Loop Verified and Hardened (2026-04-13)

**Status**: ✅ COMPLETED

This milestone marks the completion and validation of Features 026–036:

| Deliverable | Status |
|-------------|--------|
| Canonical loop defined | ✅ `docs/infra/canonical-operator-loop-v1.md` |
| Documentation aligned | ✅ `docs/infra/documentation-alignment-notes-v1.md` |
| 3-day dogfooding completed | ✅ `docs/infra/dogfooding-final-summary.md` |
| Friction classified | ✅ No capability gaps found |
| UX hardening applied | ✅ run-day --project parameter added |
| Loop Journal Viewer | ✅ Functional ecosystem tool |

**Key Findings from Dogfooding**:
- `review-night` → `resume-next-day` → `plan-day` → `run-day` works correctly
- Resume-next-day significantly reduces context reconstruction
- Planning mode inference (continue_work, recover_and_continue, etc.) works
- Execution intent alignment helps stay on bounded target
- No capability gaps — only UX consistency issue (fixed)

**Canonical Loop Commands** (all now support `--project`):
```bash
asyncdev review-night generate --project <id>
asyncdev resume-next-day continue-loop --project <id> --decision approve
asyncdev plan-day create --project <id> --feature <fid> --task "..."
asyncdev run-day execute --project <id> --mode external
```

**Next Phase**: Use validated loop in real projects, capture friction, open features only when true gaps identified.

---

## Roadmap

| Milestone | Status | Description |
|-----------|--------|-------------|
| Core System | ✅ Done | Schemas, templates, day loop CLI (001-007) |
| State & Recovery | ✅ Done | SQLite persistence, execution logging (008-012) |
| Archive & History | ✅ Done | Completion flow, query, summary (013-018) |
| Feedback & Policy | ✅ Done | Issue capture, auto-continue, decisions (019-021) |
| Integration | ✅ Done | Advisor starter pack consumption (022) |
| UX Docs | ✅ Done | First-run, drift repair, onboarding, positioning, verification, snapshot, doctor, recovery, feedback handoff, feedback draft, review-night enriched, resume-next-day alignment, plan-day resume context, run-day intent alignment (023-036) |
| **026–036 Validation** | ✅ **Done** | **Canonical loop verified, dogfooding completed, UX hardened** |
| Formal Release | 🔲 Future | PyPI package, version tagging, CHANGELOG |

---

## Ecosystem

`amazing-async-dev` is part of the amazing ecosystem, but works independently.

### amazing-skill-pack-advisor (Optional)

[amazing-skill-pack-advisor](https://github.com/Burburton/amazing-skill-pack-advisor) is a first-party ecosystem tool that helps with project intake and initialization planning. It can generate starter packs that async-dev consumes.

**Key points:**
- Advisor is **optional** - async-dev works without it
- Advisor improves initialization quality, but is not required
- The integration boundary is the `starter-pack` file format, not advisor internals
- Any compatible provider could theoretically generate starter packs

### Integration Contract

The `starter-pack` schema defines the contract between any provider and async-dev. async-dev validates the schema, not the source.

---

## Intended User

- Solo builders with limited uninterrupted time
- Part-time makers with many ideas
- Developers who want async AI, not interactive all-day

---

**Start here**: Run the [3-minute first run](#quick-start-3-minute-first-run) above.