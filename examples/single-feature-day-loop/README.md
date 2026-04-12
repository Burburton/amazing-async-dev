# Single Feature Day Loop Demo

**The default onboarding example** - complete the full day loop in 5-10 minutes.

---

## Copy-Paste Command Sequence

Run this from the repository root:

```bash
# 1. Initialize (creates projects/ directory)
python cli/asyncdev.py init create

# 2. Create demo product
python cli/asyncdev.py new-product create --product-id demo-001 --name "Demo Product"

# 3. Add feature
python cli/asyncdev.py new-feature create --product-id demo-001 --feature-id hello-world --name "Hello World"

# 4. Plan today's task
python cli/asyncdev.py plan-day create --product-id demo-001 --feature-id hello-world --task "Create hello-world.txt with greeting message"

# 5. Run (mock mode - no AI required)
python cli/asyncdev.py run-day --product-id demo-001 --mode mock

# 6. Review tonight
python cli/asyncdev.py review-night generate --product-id demo-001

# 7. Resume tomorrow
python cli/asyncdev.py resume-next-day continue-loop --product-id demo-001 --decision approve
```

---

## Expected Output

After successful execution, verify:

```
projects/demo-001/
├── product-brief.yaml         # Your product definition
├── runstate.md                # Shows: current_phase: reviewing
├── features/hello-world/
│   └── feature-spec.yaml      # Feature scope and acceptance criteria
├── execution-packs/
│   └── exec-YYYYMMDD-*.md     # Shows: task_id, goal, task_scope
├── execution-results/
│   └── exec-YYYYMMDD-*.md     # Shows: status: success, completed_items
└── reviews/
    └── YYYY-MM-DD-review.md   # Shows: what_was_completed, evidence
```

### Success Indicators

Check these files for success markers:

| File | Success Marker |
|------|----------------|
| `execution-results/*.md` | `status: success` |
| `reviews/*.md` | `completed_items: [...]` with evidence |
| `runstate.md` | `current_phase: reviewing` or `completed` |

---

## Alternative: Run Demo Script

```bash
cd examples/single-feature-day-loop
python demo-day-loop.py --verbose
```

This script runs a pre-configured demo with existing artifacts.

---

## Troubleshooting

### "Product already exists"

```
Product already exists: projects/demo-001
Use different --product-id or delete existing
```

**Fix**:
```bash
rm -rf projects/demo-001
# Then re-run new-product create
```

### "Feature not found"

```
Feature not found: hello-world
```

**Fix**: Create feature first:
```bash
python cli/asyncdev.py new-feature create --product-id demo-001 --feature-id hello-world --name "Hello World"
```

### "Current phase is planning"

```
Cannot run-day: current_phase is planning
```

**Fix**: Run plan-day before run-day:
```bash
python cli/asyncdev.py plan-day create --product-id demo-001 --feature-id hello-world --task "..."
```

### "No execution packs"

```
No execution packs to run
```

**Fix**: Plan creates the execution pack:
```bash
python cli/asyncdev.py plan-day create --product-id demo-001 --feature-id hello-world --task "Create hello.txt"
```

### Wrong product ID

Commands must use the same `--product-id` throughout. If you created `demo-001`, all subsequent commands must use `--product-id demo-001`.

---

## What This Demo Shows

The day loop workflow:

```
plan-day → run-day → review-night → resume-next-day
```

| Phase | What Happens |
|-------|--------------|
| plan-day | Creates ExecutionPack with bounded task |
| run-day | Executes task (mock mode simulates success) |
| review-night | Generates DailyReviewPack for review |
| resume-next-day | Updates RunState, continues workflow |

---

## Key Concepts

### Bounded Execution

ExecutionPack constrains AI scope:
- `task_scope`: What to do (explicit list)
- `constraints`: What NOT to do
- `stop_conditions`: When to stop

### Evidence-Based Progress

DailyReviewPack requires verification:
- `verified: true` for each deliverable
- `verification_note`: How verified

### State-Based Resume

RunState enables continuation:
- `current_phase`: Where you are
- `completed_outputs`: What's done
- `next_recommended_action`: What's next

---

## Verification Checklist

After running, check:

- [ ] `execution-packs/exec-*.md` exists
- [ ] `execution-results/exec-*.md` shows `status: success`
- [ ] `reviews/*.md` shows `what_was_completed`
- [ ] `runstate.md` shows `current_phase: reviewing` or `completed`

---

## Next Steps

1. Run with a real task (change `--task` to your actual work)
2. Try external tool mode: `--mode external`
3. Create your own product with real features
4. Read [docs/operating-model.md](../../docs/operating-model.md) for details