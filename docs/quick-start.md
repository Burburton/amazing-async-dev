# Quick Start Guide

Get started with `amazing-async-dev` in 5 minutes.

---

## Installation

```bash
# Clone repository
git clone https://github.com/Burburton/amazing-async-dev.git
cd amazing-async-dev

# Install dependencies
pip install -e .
```

---

## Day Loop Workflow

The system runs a 4-phase daily cycle:

| Phase | CLI Command | What happens |
|-------|-------------|--------------|
| Morning | `asyncdev plan-day` | Human defines today's bounded task |
| Daytime | `asyncdev run-day` | AI executes autonomously |
| Evening | `asyncdev review-night` | Generate review pack |
| Next Day | `asyncdev resume-next-day` | Continue from state |

---

## Execution Modes

Choose how AI executes tasks:

```bash
# External Tool Mode (default)
asyncdev run-day --mode external
# Generates ExecutionPack, triggers external tool (OpenCode, Claude Code)

# Live API Mode
asyncdev run-day --mode live
# Direct API call (requires DASHSCOPE_API_KEY)

# Mock Mode (testing)
asyncdev run-day --mode mock
# Fake execution for testing workflow
```

Check available modes:
```bash
asyncdev run-day modes
```

---

## Quick Example

1. **Morning: Plan**
   ```bash
   asyncdev plan-day create --task "write hello-world"
   ```

2. **Daytime: Execute (External)**
   ```bash
   asyncdev run-day --mode external
   # OpenCode reads ExecutionPack.md and executes
   ```

3. **Evening: Review**
   ```bash
   asyncdev review-night generate
   # Check DailyReviewPack in reviews/
   ```

4. **Next Day: Resume**
   ```bash
   asyncdev resume-next-day continue-loop --decision approve
   ```

---

## Key Files

| Path | Purpose |
|------|---------|
| `projects/{id}/runstate.md` | Current state |
| `projects/{id}/execution-packs/` | Today's task |
| `projects/{id}/execution-results/` | AI's output |
| `projects/{id}/reviews/` | Review packs |

---

## Next Steps

- **Run the onboarding example**: [examples/single-feature-day-loop](../examples/single-feature-day-loop/) - complete the full day loop in 5-10 minutes
- Read `docs/operating-model.md` for detailed workflow
- See `AGENTS.md` for AI execution rules

---

## Optional: Starter-Pack Initialization

For enhanced initialization with workflow hints, you can use a starter-pack:

```bash
# If you have a starter-pack.yaml (from advisor or other source)
asyncdev new-product create --product-id my-app --name "My App" --starter-pack starter-pack.yaml
```

This is optional. The [amazing-skill-pack-advisor](https://github.com/Burburton/amazing-skill-pack-advisor) can generate compatible starter packs, but direct initialization works without it.

---

**Time investment**: 20-30 minutes review per day. AI handles the rest.