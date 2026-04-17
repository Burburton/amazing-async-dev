# amazing-async-dev — Email-First Human Decision & Reporting Channel
## Multi-Phase Feature Roadmap Spec

- **Program ID:** `amazing-async-dev-email-first-human-decision-and-reporting-channel`
- **Primary Goal:** Establish email as the canonical asynchronous human decision and reporting channel for `amazing-async-dev`, building on the existing lightweight feedback mechanism.
- **Execution Style:** Designed for step-by-step implementation through `async-dev` / `opencode` canonical loop.
- **Recommended Starting Feature ID:** `040-email-first-human-decision-and-reporting-channel`
- **Priority:** High
- **Scope Style:** Phased, feature-by-feature delivery with clear closure at each stage.

---

## 1. Why This Program Exists

`amazing-async-dev` can now autonomously develop and iterate for long stretches, but real-world execution still regularly encounters moments where human input is needed:

- choosing between multiple valid directions
- providing missing business or product information
- approving or rejecting a next step
- responding to blockers or ambiguity
- deciding whether to continue, pause, or stop
- reviewing concise status updates without sitting in front of the screen for long periods

You already explored a lightweight feedback mechanism before. This program should **build on that**, not replace it from scratch.

The next step is to formalize a durable, low-interruption, auditable, asynchronous human channel.

The best initial medium is **email-first**, because it is:
- asynchronous
- auditable
- low-friction when away from the keyboard
- easy to preserve as a decision record
- compatible with structured templates and parsing
- appropriate for non-urgent but important approvals and next-step control

This program should not be treated as “just send some emails.”
It should become a core capability:

> **Asynchronous Human Decision & Reporting Channel (Email-first)**

---

## 2. Program North Star

Create a robust email-first control and reporting capability so that `amazing-async-dev` can:

1. send high-quality, structured human decision requests
2. send concise, high-signal progress reports
3. parse human replies into structured decisions
4. resume execution from those decisions
5. maintain auditable decision/report history
6. reduce the need for the user to stay at the screen
7. continuously improve report quality over time using best-practice iteration

---

## 3. Core Product Principles

### 3.1 Email-first, not email-only
Email is the canonical first channel.
Other channels may come later as adapters, but email is the primary initial implementation.

### 3.2 Decision quality matters as much as transport
The system must not only deliver messages.
It must frame decisions clearly and help the human respond quickly.

### 3.3 Reporting must be concise and actionable
A good report is not a raw log dump.
It should be structured for fast human scanning and response.

### 3.4 Build on the existing feedback mechanism
Do not discard prior feedback/reporting work.
Use it as the basis for stronger decision and reporting flows.

### 3.5 Separate reporting from decision requests
Not every email needs a reply.
Some are status reports; some require action.

### 3.6 Auditability is mandatory
Every outbound request and inbound reply should be traceable in artifacts.

### 3.7 Human interruption should stay low
The channel exists to reduce friction, not create noisy pseudo-chat by email.

---

## 4. Best-Practice Reporting Requirements

The content design of these emails matters.
This should be treated as a first-class design problem, not just string formatting.

The system should aim for reports that are:

- **precise**: fact-based, not vague
- **brief**: readable in one screen when possible
- **actionable**: clear about what needs to happen next
- **structured**: predictable layout
- **decision-friendly**: easy to approve, reject, choose, or defer
- **evidence-backed**: references to tests, commits, artifacts, reports
- **high-signal**: avoid low-value verbosity

### Recommended decision/request structure
1. one-line summary
2. current status
3. what changed
4. blocker / question
5. options
6. recommended option
7. default if no reply
8. reply instructions
9. evidence links / references

### Recommended pure status-report structure
1. one-line summary
2. what changed
3. current state
4. current risks / blockers
5. recommended next step
6. whether any reply is required
7. evidence links / references

This reporting format should itself be treated as an iterative design surface that can improve through future features.

---

## 5. Program Structure

This program should be implemented across multiple features.
Do not try to do everything in one giant feature.

Recommended structure:

- **Phase 1:** Email decision request baseline
- **Phase 2:** Reply parsing and execution resumption
- **Phase 3:** Reporting quality and best-practice summarization
- **Phase 4:** Governance, audit trail, and operational hardening
- **Phase 5:** Higher-level automation and optional adapters

Each phase below includes recommended features.

---

# Phase 1 — Email Decision Request Baseline

## Goal
Make `amazing-async-dev` capable of sending structured decision-request emails when human input is required.

## Why this phase first
This creates the smallest useful asynchronous control loop:
- system hits a decision point
- system sends a clear email
- human can read and respond later

This phase should focus on outbound quality before building more advanced inbound reply handling.

---

## Feature 040 — Email-First Human Decision & Reporting Channel Foundation
### Objective
Create the initial email-first channel and decision-request artifact model, building on the existing lightweight feedback mechanism.

### Scope
- define canonical email-first channel concept
- define outbound decision-request object/schema
- define decision-request artifact location
- define minimal email template for decision requests
- define minimal status-report template
- support sending a structured email when escalation / human input is needed
- distinguish:
  - informational report
  - decision request
  - approval request
  - blocker notice

### Must-have outputs
- decision email template
- status email template
- transport/send mechanism
- artifact for sent request metadata
- linkage to project/run/execution context
- basic docs and governance wording

### Non-goals
- full reply parsing
- smart summarization quality tuning
- mobile one-tap UX
- non-email channels

### Acceptance criteria
- system can send a structured email for a real decision point
- email type is explicit
- project/run context is preserved
- sent-email artifacts are recorded
- lightweight reporting mechanism is reused or migrated forward, not abandoned

---

## Feature 041 — Decision Request Content Contract
### Objective
Standardize the content structure of outbound decision emails so humans can respond quickly and consistently.

### Scope
- define required sections for decision requests
- define required sections for blocker emails
- define option list structure
- define recommended option structure
- define timeout/default behavior field
- define reply instruction field
- define concise executive summary rule
- define anti-patterns for noisy/overlong emails

### Must-have outputs
- decision email content contract
- examples for:
  - choose A/B/C
  - approve/reject
  - provide missing info
  - continue/pause/stop
- lint/check rules if feasible

### Acceptance criteria
- all decision-request emails follow a consistent shape
- a reviewer can identify decision, options, recommendation, and expected reply quickly
- content is concise and action-oriented

---

# Phase 2 — Reply Parsing and Execution Resumption

## Goal
Allow the user to reply by email and have `amazing-async-dev` parse that response into structured decisions and resume execution.

## Why this phase matters
Without inbound handling, email is only a notification channel.
This phase makes it a real async control channel.

---

## Feature 042 — Email Reply Parsing & Decision Extraction
### Objective
Parse email replies into structured decisions that the system can consume.

### Scope
- define supported reply intents:
  - approve
  - reject
  - choose option A/B/C
  - continue
  - pause
  - stop
  - defer
  - provide missing value
- define reply grammar / parsing rules
- support simple natural-but-structured replies
- persist parsed decision artifact
- record confidence / parse status if helpful

### Must-have outputs
- reply parsing rules
- decision object schema
- reply-to-decision artifact pipeline
- clear invalid / ambiguous reply handling

### Non-goals
- advanced free-form conversational interpretation
- multi-turn negotiation intelligence

### Acceptance criteria
- system can parse common structured replies correctly
- system can detect ambiguous replies and request clarification
- parsed decisions are stored and inspectable

---

## Feature 043 — Decision Application & Continuation Resume
### Objective
Resume execution from parsed decisions.

### Scope
- map parsed decision to continuation behavior
- update runstate / continuation state
- record decision provenance
- continue canonical loop after valid reply
- preserve low-interruption model

### Must-have outputs
- reply -> action mapping
- decision application logic
- continuation resume behavior
- audit trail linking request, reply, and resumed action

### Acceptance criteria
- a valid human reply can unblock or redirect execution
- resumed execution references the decision artifact
- continuation is traceable and policy-aligned

---

# Phase 3 — Reporting Quality & Best-Practice Summarization

## Goal
Upgrade the feedback mechanism into a high-quality reporting system that produces concise, precise, efficient work reports.

## Why this phase matters
This is where the system starts to feel truly useful in real remote operation.
The transport alone is not enough.
The content quality is critical.

---

## Feature 044 — High-Signal Status Reporting Format
### Objective
Create a best-practice status report format for email-based updates.

### Scope
- define canonical “what changed / current state / risk / next step” format
- define one-screen summary target
- define evidence reference conventions
- define when a report should ask for reply vs not
- define summary length rules
- define anti-log-dump behavior

### Must-have outputs
- canonical status email/report template
- examples for:
  - progress update
  - milestone closure
  - blocker summary
  - dogfood results
- style guidance for concise high-signal reporting

### Acceptance criteria
- status reports are compact and readable
- evidence remains available without cluttering the body
- reports are more useful than raw execution logs

---

## Feature 045 — Recommendation & Next-Step Framing
### Objective
Improve how the system recommends what should happen next in reports and requests.

### Scope
- standardize “recommended next step” framing
- standardize “why this is the recommendation”
- distinguish:
  - recommendation
  - required decision
  - optional future work
- improve clarity on whether the system can continue autonomously or needs input

### Acceptance criteria
- reports clearly tell the human what the system recommends next
- humans do not need to infer the recommended path from scattered details
- reports are easier to approve quickly

---

## Feature 046 — Reporting Best-Practice Research & Iteration Pack
### Objective
Treat reporting quality as an iterative product surface and codify best practices.

### Scope
- research best practices for concise executive updates, project status summaries, and approval-oriented reporting
- compare current report format with best-practice targets
- define iterative refinements
- create a reusable reporting rubric
- identify future report improvements

### Notes
This is intentionally a quality-iteration feature, not just implementation plumbing.
It should be allowed to evolve over time.

### Acceptance criteria
- best-practice guidance is documented
- report quality can be evaluated against a rubric
- follow-up improvements are identified clearly

---

# Phase 4 — Governance, Audit Trail, and Operational Hardening

## Goal
Make the email decision/reporting channel reliable, governable, and auditable.

---

## Feature 047 — Decision & Reporting Audit Trail
### Objective
Ensure outbound reports, outbound requests, inbound replies, and downstream actions are all traceable.

### Scope
- define audit record structure
- link sent email -> reply -> parsed decision -> applied action
- preserve timestamps and message identity
- keep artifacts understandable for later review

### Acceptance criteria
- a reviewer can reconstruct what was asked, what was answered, and what happened next
- missing links are detectable

---

## Feature 048 — Escalation Policy Integration for Email Channel
### Objective
Make sure the email channel is used only at the right moments and with the right escalation discipline.

### Scope
- define when to send email
- define when not to send email
- distinguish informational reports from required human decisions
- integrate with continuation / escalation policy
- avoid spamming the user

### Acceptance criteria
- email use is policy-governed
- the system does not over-email
- decision requests align with true escalation conditions or designated human-decision checkpoints

---

## Feature 049 — Operational Robustness & Failure Handling
### Objective
Handle email-send failures, parsing failures, delayed replies, timeout behavior, and partial state safely.

### Scope
- send failure handling
- duplicate reply handling
- timeout/default-path behavior
- invalid reply fallback
- pause/resume consistency
- partial delivery awareness if relevant

### Acceptance criteria
- the channel behaves safely under failure conditions
- unresolved decision states are explicit
- timeout behavior is inspectable and policy-driven

---

# Phase 5 — Higher-Level Automation and Optional Extensions

## Goal
Extend the channel once the baseline email system is real, trustworthy, and useful.

---

## Feature 053 — Resend Email Provider Integration
### Objective
Integrate Resend as the real email transport/provider for the existing Email-First Human Decision & Reporting Channel.

### Scope
- integrate Resend for outbound email sending
- support decision requests, status reports, and blocker emails
- persist provider-specific message metadata
- define inbound handling path for replies/events
- connect inbound email flow to existing decision/reply pipeline
- integrate provider failures with existing robustness/failure-handling logic
- define configuration, secrets, and environment expectations
- support safe testing modes (mock/sandbox/dry-run)

### Acceptance criteria
- outbound emails sent via Resend API
- message ID persisted in decision request record
- webhook handler receives and parses inbound replies
- reply linked to original decision request
- integration with existing reply pipeline (Feature 043)
- API errors handled via Feature 049 failure handling

---

## Feature 050 — new-product / project-link Email Channel Integration
### Objective
Integrate email contact and decision-channel setup into project bootstrap flows.

### Scope
- include decision-channel configuration in new-product flow
- ensure project-link metadata can reference email decision settings
- make the channel easier to enable consistently

### Acceptance criteria
- new managed projects can be configured with the email channel in a standard way
- channel setup is no longer ad hoc

---

## Feature 051 — Summary Digest Modes
### Objective
Add digest-style reporting after the core report quality is already solid.

### Scope
- daily summary mode
- milestone summary mode
- weekly digest mode
- optional quiet mode / batch mode

### Acceptance criteria
- reporting cadence can be configured
- digest mode reduces noise without losing key signal

---

## Feature 052 — Future Adapter Readiness (Non-Email)
### Objective
Prepare for future Slack / Telegram / approval-link / mobile adapter channels without changing email-first governance.

### Scope
- abstract channel adapter boundary
- preserve email as canonical baseline
- define portability of decision/report objects

### Acceptance criteria
- other channels can later be added without redesigning core decision/report artifacts
- email remains the canonical first implementation

---

## 6. Recommended Execution Order

Recommended sequence for `async-dev` / `opencode`:

1. **040** — foundation
2. **041** — decision request content contract
3. **042** — reply parsing
4. **043** — apply decision and resume
5. **044** — status reporting format
6. **045** — next-step framing
7. **047** — audit trail
8. **048** — escalation integration
9. **049** — robustness
10. **053** — Resend email provider integration (production transport)
11. **046** — best-practice reporting iteration pack
12. **050** — bootstrap integration
13. **051** — digest modes
14. **052** — adapter readiness

Notes:
- `046` can start earlier as research, but its outputs are more valuable once real examples from 040-045 exist.
- `047-049` should not be neglected just because the transport works.
- `053` provides real email transport via Resend API, critical for production use.

---

## 7. Recommended Minimal First Slice

If you want the smallest strong first implementation:

### Start with:
- **040**
- **041**
- **042**
- **043**

This gives you:
- outbound decision email
- structured decision content
- reply parsing
- continuation resume

That is the first true async human control loop.

Then immediately follow with:
- **044**
- **045**

to improve report quality and next-step clarity.

---

## 8. Suggested Artifact Concepts

These can be refined during implementation.

### Decision request artifacts
- request id
- project id
- execution id
- reason
- summary
- options
- recommendation
- timeout/default
- email metadata

### Reply/decision artifacts
- request id
- reply id
- parsed intent
- parsed choice
- provided values
- parse confidence/status
- ambiguity flag
- applied action

### Reporting artifacts
- report id
- report type
- summary
- what changed
- blockers
- recommendation
- reply required yes/no
- linked evidence

---

## 9. Validation Scenarios

Use real async-dev scenarios to validate the channel:

1. human approval needed to continue a new phase
2. system encounters two valid directions and requests choice
3. blocker requires missing product information
4. system sends a pure milestone report that needs no reply
5. human replies from away from keyboard with a concise command
6. system resumes correctly from that reply
7. report quality is compared against a concise best-practice rubric

---

## 10. Anti-Patterns

Avoid these failures:

### Anti-Pattern A — Raw log dump emails
Do not send large unstructured execution logs as the primary human-facing message.

### Anti-Pattern B — Email as pseudo-chat
Do not turn email into a noisy turn-by-turn control stream.

### Anti-Pattern C — No recommendation
Do not ask the human what to do without presenting a recommended path.

### Anti-Pattern D — No default policy
Do not send decision requests without a timeout/default action model where appropriate.

### Anti-Pattern E — Reply cannot be parsed
Do not rely entirely on free-form unbounded prose without a recoverable parsing strategy.

### Anti-Pattern F — No audit linkage
Do not allow sent email, received reply, and resumed action to become disconnected artifacts.

---

## 11. Definition of Program Success

This program is successful when:

- `amazing-async-dev` can send concise, structured, high-signal decision emails
- the user can reply asynchronously without staying at the screen
- replies can be parsed and applied
- the system can resume execution from those replies
- reporting quality is measurably better than raw feedback/log dumps
- the whole flow is auditable
- email becomes a real operational human decision channel, not just a notification feature

---

## 12. Requested Next Action

Use this roadmap spec to execute the program feature-by-feature.

Recommended immediate first step:
- start **Feature 040**
- explicitly build on the prior lightweight feedback mechanism
- treat email-first decision and reporting as a core async-dev capability, not a side utility

---

## 13. Final Guiding Statement

> `amazing-async-dev` should be able to run for long periods autonomously, and when human input is needed, request it asynchronously through concise, high-quality, auditable email interaction that leads directly back into continued execution.
