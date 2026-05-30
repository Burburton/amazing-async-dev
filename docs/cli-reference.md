# CLI Reference

Complete command reference for `asyncdev` CLI.

## Usage

```bash
python cli/asyncdev.py <command> <subcommand> [OPTIONS]
```

---

## Core Commands

### init

Initialize project structure.

```bash
# Create basic project structure
python cli/asyncdev.py init create

# Check initialization status
python cli/asyncdev.py init status
```

---

### new-product

Create and manage products.

```bash
# Create new product
python cli/asyncdev.py new-product create --product-id <id> --name "<name>"

# Create with starter pack
python cli/asyncdev.py new-product create --product-id <id> --name "<name>" --starter-pack <path.yaml>

# List all products
python cli/asyncdev.py new-product list
```

---

### new-feature

Create and manage features within a product.

```bash
# Create new feature
python cli/asyncdev.py new-feature create --product-id <id> --feature-id <id> --name "<name>"

# List features for a product
python cli/asyncdev.py new-feature list --product-id <id>
```

---

### plan-day

Plan today's bounded task.

```bash
# Create ExecutionPack for today's task
python cli/asyncdev.py plan-day create --product-id <id> --feature-id <id> --task "<task description>"

# Show current RunState and pending tasks
python cli/asyncdev.py plan-day show --project <id>

# Show planning context for current state
python cli/asyncdev.py plan-day context --project <id>
```

---

### run-day

Execute today's bounded task.

```bash
# Execute with external tool mode (recommended for first run)
python cli/asyncdev.py run-day --project <id> --mode external

# Execute with live API mode
python cli/asyncdev.py run-day --project <id> --mode live

# Execute with mock mode (for testing)
python cli/asyncdev.py run-day --project <id> --mode mock

# Quick mock execution
python cli/asyncdev.py run-day mock-quick --project <id>

# Show available execution modes
python cli/asyncdev.py run-day modes
```

---

### review-night

Generate nightly review pack.

```bash
# Generate DailyReviewPack from ExecutionResult and RunState
python cli/asyncdev.py review-night generate --project <id>

# Show latest DailyReviewPack
python cli/asyncdev.py review-night show --project <id>
```

---

### resume-next-day

Resume from decisions.

```bash
# Process decision and continue day loop
python cli/asyncdev.py resume-next-day continue-loop --project <id> --decision <approve|revise|defer>

# Show RunState status for resume
python cli/asyncdev.py resume-next-day status --project <id>

# Resume from blocked state
python cli/asyncdev.py resume-next-day unblock --project <id>

# Handle failed execution
python cli/asyncdev.py resume-next-day handle-failed --project <id>
```

---

### complete-feature

Mark feature as completed.

```bash
# Mark feature as completed
python cli/asyncdev.py complete-feature mark --product-id <id> --feature-id <id>
```

---

### archive-feature

Archive completed feature.

```bash
# Archive a feature
python cli/asyncdev.py archive-feature create --product-id <id> --feature-id <id>

# Backfill historical features into archive
python cli/asyncdev.py backfill --product-id <id>
```

---

### archive

Query and inspect archived features.

```bash
# List archived features
python cli/asyncdev.py archive list --product <id>

# Show detailed archive pack
python cli/asyncdev.py archive show --feature <id>
```

---

## Status & Summary

### status

Show current RunState status.

```bash
python cli/asyncdev.py status --all-features --project <id>
```

---

### summary

Management summary for nightly review.

```bash
# Show today's summary
python cli/asyncdev.py summary today --project <id>

# Show decision inbox
python cli/asyncdev.py summary decisions --project <id>

# Show issues summary
python cli/asyncdev.py summary issues --project <id>

# Show next day recommendation
python cli/asyncdev.py summary next-day --project <id>

# Show summary across all projects
python cli/asyncdev.py summary all-projects
```

---

## Operator Surfaces (Phase 2-4)

### home

Operator Home - Unified platform overview.

```bash
# Show operator home overview
python cli/asyncdev.py home show --project <id>

# Show quick platform status
python cli/asyncdev.py home status

# Check if platform is calm (no attention needed)
python cli/asyncdev.py home calm

# Show all blocking states
python cli/asyncdev.py home blocking --project <id>

# Show recovery summary
python cli/asyncdev.py home recovery --project <id>

# Show decision inbox summary
python cli/asyncdev.py home decision --project <id>

# Direct navigation to surface
python cli/asyncdev.py home navigate <surface> --id <id> --project <id>

# Show unified recovery dashboard
python cli/asyncdev.py home recovery-dashboard --project <id>

# Show attention items (interactive)
python cli/asyncdev.py home attention --project <id> -i
```

---

### recovery

Execution Recovery Console.

```bash
# List executions needing recovery
python cli/asyncdev.py recovery list --project <id>
python cli/asyncdev.py recovery list --all

# Show detailed recovery info
python cli/asyncdev.py recovery show --execution <exec-id>

# Execute recovery action
python cli/asyncdev.py recovery resume --execution <exec-id> --action <unblock|abort|continue|retry|reset> --execute
```

---

### decision

Decision Inbox.

```bash
# List pending decisions
python cli/asyncdev.py decision list --project <id>
python cli/asyncdev.py decision list --all
python cli/asyncdev.py decision list --status <pending|resolved>

# Show detailed decision context
python cli/asyncdev.py decision show --request <request-id>

# Process decision reply
python cli/asyncdev.py decision reply --request <request-id> --command "DECISION A"

# Poll for decision reply (blocking)
python cli/asyncdev.py decision wait --request <request-id> --interval 60 --timeout 3600

# Show resolved decision history
python cli/asyncdev.py decision history --project <id>
python cli/asyncdev.py decision history --all
python cli/asyncdev.py decision history --limit 10
```

---

### session-start

Mandatory blocking state check.

```bash
# Check blocking state for project
python cli/asyncdev.py session-start check --project <id>

# Check all projects
python cli/asyncdev.py session-start check

# Poll for decision reply
python cli/asyncdev.py session-start poll --project <id>

# Show session start status
python cli/asyncdev.py session-start status
```

---

### verification

Verification Console.

```bash
# List verification states
python cli/asyncdev.py verification list --project <id>

# Show detailed verification context
python cli/asyncdev.py verification show --execution <id>

# Classify verification type
python cli/asyncdev.py verification classify --project <id>
python cli/asyncdev.py verification classify --project <id> --feature <id>

# Check completion gate
python cli/asyncdev.py verification gate --project <id>

# Retry failed verification
python cli/asyncdev.py verification retry --project <id>
```

---

### acceptance

Acceptance Console (Feature 077).

```bash
# Run acceptance validation
python cli/asyncdev.py acceptance run --project <id>
python cli/asyncdev.py acceptance run --project <id> --execution <id>
python cli/asyncdev.py acceptance run --project <id> --policy-mode <strict|relaxed>

# Inspect acceptance status
python cli/asyncdev.py acceptance status --project <id>

# Inspect prior acceptance attempts
python cli/asyncdev.py acceptance history --project <id>
python cli/asyncdev.py acceptance history --project <id> --limit 10

# Show detailed acceptance result
python cli/asyncdev.py acceptance result --project <id>
python cli/asyncdev.py acceptance result --project <id> --result-id <id>

# Re-run acceptance after remediation
python cli/asyncdev.py acceptance retry --project <id>
python cli/asyncdev.py acceptance retry --project <id> --execution <id>

# Show recovery status from failed acceptance
python cli/asyncdev.py acceptance recovery --project <id>

# Check completion gate
python cli/asyncdev.py acceptance gate --project <id>
```

---

### evidence

Evidence Summary Console (Feature 079).

```bash
# Show rolled-up evidence summary
python cli/asyncdev.py evidence summary --project <id>
python cli/asyncdev.py evidence summary --project <id> --feature <id>
python cli/asyncdev.py evidence summary --project <id> --save

# Resolve latest artifact of given type
python cli/asyncdev.py evidence latest --project <id> --type <execution_result|acceptance_result>

# Generate and save evidence summary
python cli/asyncdev.py evidence generate --project <id>
python cli/asyncdev.py evidence generate --project <id> --feature <id>

# Answer canonical evidence questions
python cli/asyncdev.py evidence questions --project <id>

# Show diff between execution and acceptance
python cli/asyncdev.py evidence diff --project <id>

# Validate evidence artifacts
python cli/asyncdev.py evidence validate --project <id>
```

---

### observe-runs

Execution Observer (Feature 067).

```bash
# Observe runs for project
python cli/asyncdev.py observe-runs --project <id>

# Observe all runs
python cli/asyncdev.py observe-runs --all

# Filter by severity
python cli/asyncdev.py observe-runs --severity <low|medium|high|critical>
```

---

## Feedback & Policy

### feedback

Record and inspect workflow feedback.

```bash
# Record workflow feedback
python cli/asyncdev.py feedback record --scope <system|product> --description "<description>"

# Add/update triage information
python cli/asyncdev.py feedback triage --feedback-id <id> --triage "<triage-info>"

# List workflow feedback
python cli/asyncdev.py feedback list --followup-needed

# Show detailed feedback
python cli/asyncdev.py feedback show --feedback-id <id>

# Update feedback resolution/status
python cli/asyncdev.py feedback update --feedback-id <id> --status <resolved>

# Show feedback summary
python cli/asyncdev.py feedback summary

# Promote triaged feedback to formal follow-up
python cli/asyncdev.py feedback promote --feedback-id <id> --reason <type>

# Manage promoted feedback
python cli/asyncdev.py feedback promotions
```

---

### policy

Execution policy configuration.

```bash
# Show current policy
python cli/asyncdev.py policy show

# Set execution policy mode
python cli/asyncdev.py policy set --mode <conservative|balanced|low_interruption>
```

---

## Email & Notifications

### email-decision

Async decision channel.

```bash
# Create decision request
python cli/asyncdev.py email-decision create --project <id> --question "<question>" --options "A:...,B:..." --send

# Process decision reply
python cli/asyncdev.py email-decision reply --project <id> --id <id> --command "DECISION A"
```

---

### notification

Notification management.

```bash
python cli/asyncdev.py notification <subcommand>
```

---

### check-inbox

Check pending decisions from webhook.

```bash
python cli/asyncdev.py check-inbox pending
```

---

### gmail-auth / resend-auth

Email provider authentication.

```bash
# Gmail OAuth2 setup
python cli/asyncdev.py gmail-auth

# Resend email provider setup
python cli/asyncdev.py resend-auth
```

---

## Workspace Tools

### snapshot

Workspace snapshot.

```bash
python cli/asyncdev.py snapshot --project <id>
```

---

### doctor

Diagnose workspace health.

```bash
# Run workspace diagnosis
python cli/asyncdev.py doctor --project <id>

# With repair hints
python cli/asyncdev.py doctor --project <id> --repair
```

---

### journal

View loop artifact timeline.

```bash
python cli/asyncdev.py journal --project <id>
```

---

### sqlite

SQLite state store queries.

```bash
python cli/asyncdev.py sqlite <query>
```

---

### inspect-stop

Inspect stop point and recovery options.

```bash
python cli/asyncdev.py inspect-stop --project <id>
```

---

## Configuration

### config

Config safety commands.

```bash
python cli/asyncdev.py config <subcommand>
```

---

### project-link

Project-link management.

```bash
python cli/asyncdev.py project-link <subcommand>
```

---

### browser-test

Browser verification for frontend projects.

```bash
python cli/asyncdev.py browser-test --project <id>
```

---

### frontend-verify-run

Controlled frontend verification recipe.

```bash
python cli/asyncdev.py frontend-verify-run --project <id>
```

---

## Utility

### version

Show version.

```bash
python cli/asyncdev.py version
```

---

## Common Workflows

### First Run

```bash
# 1. Initialize
python cli/asyncdev.py init create

# 2. Create product
python cli/asyncdev.py new-product create --product-id my-app --name "My App"

# 3. Add feature
python cli/asyncdev.py new-feature create --product-id my-app --feature-id feature-001 --name "First Feature"

# 4. Plan task
python cli/asyncdev.py plan-day create --product-id my-app --feature-id feature-001 --task "Create hello.txt"

# 5. Run (external mode)
python cli/asyncdev.py run-day --project my-app --mode external

# 6. Review
python cli/asyncdev.py review-night generate --project my-app

# 7. Resume
python cli/asyncdev.py resume-next-day continue-loop --project my-app --decision approve
```

---

### Check Platform Status

```bash
# Quick status
python cli/asyncdev.py home status

# Detailed overview
python cli/asyncdev.py home show --project <id>

# Check for blocking
python cli/asyncdev.py home blocking --project <id>

# Check if calm
python cli/asyncdev.py home calm
```

---

### Recovery Flow

```bash
# 1. List issues
python cli/asyncdev.py recovery list --project <id>

# 2. Show details
python cli/asyncdev.py recovery show --execution <exec-id>

# 3. Execute recovery
python cli/asyncdev.py recovery resume --execution <exec-id> --action <action> --execute
```

---

### Decision Handling

```bash
# 1. List pending decisions
python cli/asyncdev.py decision list --project <id>

# 2. Show decision context
python cli/asyncdev.py decision show --request <request-id>

# 3. Reply
python cli/asyncdev.py decision reply --request <request-id> --command "DECISION A"
```
