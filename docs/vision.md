# Vision

## Why we built this

Most solo builders face a fundamental asymmetry:

- They have many product ideas
- They have very little uninterrupted maker time
- They cannot afford to babysit AI all day
- They cannot afford to lose context across days

The traditional AI coding assistant model assumes:
- Interactive, continuous human presence
- Conversational memory as context
- Single-session work units

This model fails for solo builders who:
- Work during scattered time windows
- Want AI to progress while they attend other responsibilities
- Need structured, reviewable outputs
- Must resume work days later without re-explanation

---

## What we aim to achieve

`amazing-async-dev` exists to enable a new working pattern:

**Day**: AI makes bounded, stable progress on defined tasks
**Night**: Human reviews, decides, and redirects in 20–30 minutes
**Next Day**: Work resumes from explicit state, not from conversation

We want to prove that:

1. AI can work semi-autonomously for hours without drifting
2. Human review can be compressed to a few meaningful decisions
3. Context continuity can be artifact-based, not memory-based
4. Multiple product ideas can progress in parallel with minimal overhead

---

## Target user profile

This system is designed for:

| Trait | Implication |
|-------|-------------|
| Solo builder | No team coordination overhead |
| Part-time maker | Cannot supervise AI continuously |
| Idea-rich, time-poor | Wants parallel async progress |
| Low tolerance for chaos | Needs structured outputs |
| High decision ownership | Wants control at decision points, not every step |

---

## Success definition

This project succeeds when:

| Criterion | Metric |
|-----------|--------|
| Autonomous execution | AI runs 4+ hours without intervention |
| Review compression | Human review completes in 20–30 minutes |
| Decision leverage | Human handles ≤3 meaningful decisions per day |
| Resume efficiency | Next day starts without re-explanation |
| Parallel capacity | Multiple features advance concurrently |

---

## Non-goals (v0)

We explicitly do not target in the first version:

- Multi-team coordination
- Complex agent societies
- Heavy orchestration engines
- UI-first experiences
- Plugin ecosystems
- High-concurrency scheduling

The first version focuses on **one builder, one feature, one day loop**.

---

## Long-term evolution

### v0 — Single Feature Daily Loop
Prove the core day/night cycle works for one feature.

### v1 — Multi-feature Parallel
Support multiple features advancing in parallel with shared state.

### v2 — Multi-product Portfolio
Support multiple product briefs with prioritization and resource allocation.

### v3 — Integration Hooks
Optional connections to external tools (git, CI, deployment).

---

## Design philosophy

### Artifact-first
Everything that matters lives in files, not in prompt history.
- State is in `RunState`
- Decisions are in `DailyReviewPack`
- Continuity is in artifacts

### Boundaries are sacred
AI cannot expand scope without human approval.
- `ExecutionPack` defines the boundary
- Stop conditions are explicit
- Expansion requires human decision

### Night is for judgment
The human's role is compressed to what truly matters.
- Review progress, not every detail
- Decide direction, not every step
- Redirect scope, not every action

### Day is for execution
AI's role is to deliver bounded outputs.
- Complete defined deliverables
- Leave evidence of work
- Flag decisions and blockers
- Prepare for continuation

---

## How this differs from other approaches

| Approach | Limitation |
|----------|------------|
| Interactive AI assistants | Requires continuous human presence |
| Large autonomous systems | Overkill for single builder, hard to control |
| Spec-first frameworks | Assumes upfront planning, not async evolution |
| Agent orchestration platforms | Too complex for personal use |

`amazing-async-dev` occupies a narrow niche:
- Simple enough for solo use
- Structured enough for async execution
- Explicit enough for fast review
- Stable enough for multi-day continuity

---

## What we believe

1. **Solo builders deserve async leverage** — They should not have to supervise every step
2. **Boundaries enable autonomy** — Constrained scope lets AI move forward safely
3. **Artifacts outlast conversations** — State in files survives session boundaries
4. **Decisions should be leveraged** — Human time should buy direction, not supervision
5. **Small loops beat big plans** — Day-sized cycles are more tractable than multi-week sprints

---

## The first milestone

The first version must answer one question:

> Can AI make useful, bounded progress during the day, and can the human review and redirect it efficiently at night?

If this works, everything else becomes possible.

If this fails, the entire async vision fails.

Start with Feature 001. Prove the object model. Prove the day loop.