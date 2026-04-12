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

## Learn More

| Resource | What you'll find |
|----------|------------------|
| [docs/quick-start.md](docs/quick-start.md) | 5-minute guide with execution modes explained |
| [examples/single-feature-day-loop/](examples/single-feature-day-loop/) | Full demo with all artifacts |
| [docs/operating-model.md](docs/operating-model.md) | Day loop phases and responsibilities |
| [AGENTS.md](AGENTS.md) | Rules for AI execution |

---

## Day Loop Overview

```
plan-day → run-day → review-night → resume-next-day
```

| Phase | When | What you do |
|-------|------|-------------|
| Morning | 5 min | Define today's bounded task |
| Daytime | 0 min | AI executes autonomously |
| Evening | 20-30 min | Review DailyReviewPack, decide next steps |
| Next day | 2 min | Resume from state, no re-explanation |

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
├─ schemas/            # Artifact schemas (14 files)
├─ templates/          # Fillable templates
├─ runtime/            # State management, adapters
├─ cli/                # CLI commands (18 modules)
├─ tests/              # 533 pytest tests
├─ examples/
│  ├─ single-feature-day-loop/  # Full demo
│  └─ pilot/                     # Advisor integration pilot
├─ projects/           # User products (created by CLI)
└─ products/           # Product templates (placeholder)
```

---

## Testing

```bash
python -m pytest tests/ -v
```

| Category | Tests | Coverage |
|----------|-------|----------|
| CLI commands | 50+ | All asyncdev commands |
| Phase transitions | 18 | RunState transitions |
| Artifact format | 23 | YAML/Markdown generation |
| Error handling | 21 | Missing state, invalid inputs |
| SQLite persistence | 20 | State store, recovery |
| Policy & decisions | 71 | Auto-continue, email channel |
| Integration | 18 | Advisor starter pack consumption |
| **Total** | **533** | |

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

# Starter Pack (advisor integration)
asyncdev new-product create --product-id {id} --name "{name}" --starter-pack starter-pack.yaml
```

---

## Project Status

| Metric | Value |
|--------|-------|
| Features Complete | 22 (001-022) |
| Tests Passing | 533 |
| Package State | Functional alpha |
| Coverage | CLI, state, policy, feedback, integration |

**What this means:**
- All core features are implemented and tested
- Package works for real async development workflows
- Not formally released (no PyPI package, no version tag)
- Suitable for early adopters willing to clone and run

---

## Roadmap

| Milestone | Status | Description |
|-----------|--------|-------------|
| Core System | ✅ Done | Schemas, templates, day loop CLI (001-007) |
| State & Recovery | ✅ Done | SQLite persistence, execution logging (008-012) |
| Archive & History | ✅ Done | Completion flow, query, summary (013-018) |
| Feedback & Policy | ✅ Done | Issue capture, auto-continue, decisions (019-021) |
| Integration | ✅ Done | Advisor starter pack consumption (022) |
| UX Docs | ✅ Done | First-run experience, drift repair (023-024) |
| Formal Release | 🔲 Future | PyPI package, version tagging, CHANGELOG |

---

## Intended User

- Solo builders with limited uninterrupted time
- Part-time makers with many ideas
- Developers who want async AI, not interactive all-day

---

**Start here**: Run the [3-minute first run](#quick-start-3-minute-first-run) above.