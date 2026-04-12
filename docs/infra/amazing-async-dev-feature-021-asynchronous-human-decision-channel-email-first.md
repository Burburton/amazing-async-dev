# Feature 021 — Asynchronous Human Decision Channel (Email-first)

## 1. Feature Summary

### Feature ID
`021-asynchronous-human-decision-channel`

### Title
Asynchronous Human Decision Channel (Email-first)

### Goal
Enable `amazing-async-dev` to pause at true human-decision points, notify the operator asynchronously by email, accept structured email replies, and then continue execution without requiring the operator to stay synchronously present at the terminal.

### Why this matters
Feature 020 is expected to define the policy layer for:
- which workflow steps should auto-continue
- which situations must pause
- which actions are risky
- why the system paused

Once that policy exists, a new question becomes important:

> When the system pauses for a real human decision, how should it hand that decision to the operator without forcing the operator to watch the terminal in real time?

This is especially important for the intended async operating model:

- the system should make progress during the day
- the human should only intervene when necessary
- intervention should be asynchronous and low-friction
- the system should be able to resume after a clear reply

Email is a practical first channel because it is:
- widely available
- asynchronous
- easy to review later
- easy to integrate into a human decision loop

This feature exists to turn pause points into an asynchronous decision workflow instead of a synchronous terminal dependency.

---

## 2. Objective

Create the first asynchronous human decision channel for `amazing-async-dev`, using email as the initial delivery and reply mechanism.

This feature should make it possible to:

1. detect that a true human decision is required
2. package the decision into a clear email-friendly decision pack
3. send the decision to the operator
4. accept a structured reply
5. map that reply back into workflow state
6. continue execution after the decision is resolved

This feature is intentionally email-first, not channel-generic from day one.

---

## 3. Scope

### In scope
- define an asynchronous decision request model
- define email as the first supported human decision channel
- send structured decision emails
- define a structured reply format
- parse email replies safely
- update workflow state from accepted replies
- resume execution after decision resolution
- document the email-first decision loop clearly

### Out of scope
- Slack/Telegram/Discord/etc support
- natural language freeform reply understanding
- advanced multi-step conversational inbox
- autonomous decision making without human reply
- multi-user approval routing
- broad notification platform abstractions
- long-running background scheduler design beyond what is required for this loop

---

## 4. Success Criteria

This feature is successful when:

1. true human decision pauses can be delivered asynchronously by email
2. the operator can resolve a decision without returning to the terminal immediately
3. the reply format is structured enough to be reliable
4. workflow state can be updated safely from accepted replies
5. execution can continue after a valid decision reply
6. the async operating model feels meaningfully less interruptive

---

## 5. Core Design Principles

### 5.1 Build on policy, not replace it
This feature depends on the pause/autocontinue boundaries defined by Feature 020.

### 5.2 Keep replies structured and explicit
The first version should prefer safe, parseable reply commands over freeform interpretation.

### 5.3 Preserve traceability
Every email decision request and reply should remain linked to workflow state and decision objects.

### 5.4 Optimize for low interruption
The goal is not more messaging.
The goal is fewer synchronous interruptions.

### 5.5 Keep the first channel narrow
Email-first is enough for the first version.
Do not overbuild a general notification platform.

---

## 6. Main Capabilities

## 6.1 Decision request creation

### Purpose
Create a structured decision request when a pause condition requires human input.

### Expected request content
- decision/request ID
- product / feature context
- reason for pause
- decision type
- question to answer
- options
- recommendation
- consequence of delay
- safe next step after reply

### Notes
This should build naturally on the existing decision inbox and nightly summary structures.

---

## 6.2 Email delivery

### Purpose
Send the decision request to the operator in a readable and actionable email format.

### Expected email qualities
- clear subject line
- concise context
- explicit decision question
- enumerated options
- recommendation shown
- structured reply instructions

### Example subject
```text
[async-dev] Decision needed: amazing-skill-pack-advisor / feature-002
```

### Notes
The operator should be able to understand the request quickly on phone or desktop email.

---

## 6.3 Structured reply format

### Purpose
Provide a reliable reply syntax that can be parsed safely.

### Expected first-version approach
Support a small command-style reply format such as:
- `DECISION B`
- `APPROVE PUSH`
- `DEFER`
- `RETRY`
- `CONTINUE`

### Notes
Do not rely on freeform natural language in v1.

---

## 6.4 Reply parsing and validation

### Purpose
Convert an incoming email reply into a valid workflow decision outcome.

### Expected support
- identify the target decision request
- validate that the reply is syntactically supported
- reject ambiguous or invalid responses
- avoid double-processing the same decision
- preserve decision/reply traceability

### Notes
This is one of the most important safety layers in the feature.

---

## 6.5 Resume after reply

### Purpose
Allow workflow execution to continue once a valid decision reply has been received.

### Expected behavior
- update decision state
- update RunState
- log the response
- mark the pause as resolved
- continue the next safe execution step

### Notes
Resume behavior should still respect Feature 020’s execution policy.

---

## 7. State Model Expectations

This feature should likely introduce or clarify states such as:

- `waiting_for_human_decision`
- `decision_request_sent`
- `decision_reply_received`
- `decision_reply_invalid`
- `decision_resolved`

### Notes
The exact state shape can vary, but the waiting/reply/resolution loop must be explicit.

---

## 8. Decision Request Model Expectations

The exact schema may vary, but the first version should likely support fields such as:

- `decision_request_id`
- `product_id`
- `feature_id`
- `pause_reason_category`
- `decision_type`
- `question`
- `options`
- `recommendation`
- `defer_impact`
- `reply_format_hint`
- `sent_at`
- `status`

### Optional fields
- `recommended_next_action_after_reply`
- `expires_at`
- `delivery_channel`

### Notes
Keep the model practical and tightly scoped to the first email loop.

---

## 9. Email Reply Model Expectations

The first version should likely support fields such as:

- `decision_request_id`
- `reply_value`
- `reply_raw_text`
- `received_at`
- `parsed_result`
- `validation_status`
- `applied_at`

### Notes
The system should preserve enough information to audit what happened later.

---

## 10. Integration Expectations

This feature should integrate with:

- Feature 020 pause/autocontinue policy
- decision inbox
- nightly management summary where useful
- RunState
- execution logging
- workflow feedback if email loop problems occur
- resume logic

### Notes
This feature is a response channel layer, not a replacement for the workflow engine.

---

## 11. CLI / Operator Experience Expectations

The first version should support workflows such as:

- decision request created automatically from a pause condition
- email sent without requiring terminal presence
- operator replies by email using a safe reply format
- system accepts valid reply and continues

The system should also provide enough local visibility to inspect:
- pending decision requests
- sent requests
- invalid replies
- resolved requests

---

## 12. Deliverables

This feature must add:

### 12.1 Asynchronous decision request model
A structured way to represent a decision request sent outside the terminal.

### 12.2 Email delivery flow
A practical email-first notification path.

### 12.3 Structured reply handling
A safe first reply grammar and parser.

### 12.4 Resume integration
A way to continue the workflow after valid reply resolution.

### 12.5 Documentation
At least one document or section explaining:
- when email decisions are sent
- how to reply
- what reply formats are supported
- how invalid replies are handled
- how the system resumes after resolution

---

## 13. Acceptance Criteria

- [ ] true human decision pauses can generate a decision request
- [ ] decision requests can be delivered by email
- [ ] the operator can reply using a structured format
- [ ] valid replies can be parsed and applied
- [ ] invalid replies are rejected safely
- [ ] the workflow can continue after a valid reply
- [ ] documentation explains the email-first decision loop clearly

---

## 14. Risks

### Risk 1 — Reply ambiguity
If replies are too freeform, parsing will be unreliable.

**Mitigation:** use a strict first-version reply grammar.

### Risk 2 — Duplicate or repeated processing
The same reply could be applied twice or the same request could receive conflicting replies.

**Mitigation:** require explicit request linkage and idempotent handling.

### Risk 3 — Channel complexity too early
Trying to support multiple channels at once would slow down delivery.

**Mitigation:** keep the feature email-first only.

### Risk 4 — Async decisions without strong pause policy
If pause logic is not already clear, the system may send too many emails.

**Mitigation:** implement this only on top of Feature 020’s clear policy boundaries.

---

## 15. Recommended Implementation Order

1. define the decision request object
2. define the email content format
3. define the structured reply grammar
4. implement reply parsing and validation
5. implement RunState/resume integration
6. add inspection and logging support
7. document the end-to-end email-first decision loop

---

## 16. Suggested Validation Questions

This feature should make the system better able to answer:

- can the system pause for a real decision without requiring me to watch the terminal?
- can it explain the decision clearly by email?
- can I resolve the decision with a safe structured reply?
- can the system resume after that reply?
- does this reduce interruption without reducing control?

If the operator still has to stay synchronously present at the terminal for most real decisions, this feature is not done.

---

## 17. Definition of Done

Feature 021 is done when:

- real decision pauses can be handed off asynchronously by email
- replies can be parsed and applied safely
- execution can resume after valid decision resolution
- the system better supports a realistic “day execution / async human decision” workflow

If pause points still require the operator to remain synchronously attached to the terminal, this feature is not done.
