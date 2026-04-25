# Feature 080 — Auto Email Notification for Decision and Day-End Events

## Metadata

- **Feature ID**: `080-auto-email-notification-for-decision-and-day-end-events`
- **Feature Name**: `Auto Email Notification for Decision and Day-End Events`
- **Feature Type**: `notification integration / async decision channel / platform automation`
- **Priority**: `High`
- **Status**: `Proposed`
- **Owner**: `async-dev`
- **Target Branch**: `platform/foundation`
- **Related Areas**:
  - `decision channel`
  - `review-night`
  - `run-day`
  - `resume-next-day`
  - `email-decision`
  - `Resend integration`
  - `async human-in-the-loop workflow`

---

## 1. Problem Statement

`async-dev` already has the concept of an async decision channel and email-based decision workflows, but the platform currently appears to rely too much on manual invocation of email-related commands.

As a result, important human-facing events may not automatically notify the operator, including cases such as:

- a major human decision is required,
- an execution is blocked pending operator input,
- a critical escalation-worthy state is reached,
- the day ends and a review summary exists,
- a meaningful day-end status should be sent automatically.

This creates a platform gap:

> the async decision/email channel exists as a capability, but not yet as a fully integrated event-driven platform behavior.

In practice, this means the operator may not receive timely email notifications through Resend when they most need them.

The platform therefore under-delivers on one of its key value propositions:

- low-interruption async execution,
- selective human attention,
- email-first decision handling,
- day-end awareness without constant monitoring.

Feature 080 closes that gap by making email notifications automatic for specific platform events, especially:

1. decision-required events,
2. day-end / review-night summary events.

---

## 2. Goal

Integrate automatic email notification into async-dev’s canonical flows so that the system can proactively notify the operator through Resend when:

- a major human decision is required,
- a meaningful blocked state requires human input,
- the day ends and a summary should be delivered.

After this feature, the platform should support a real email-first async workflow rather than a mostly manual email command path.

---

## 3. Non-Goals

This feature does **not** aim to:

- redesign the decision channel from scratch,
- replace Decision Inbox or Recovery Console,
- create a full notification center for every minor event,
- send emails for every state transition,
- redesign Resend itself,
- introduce a large messaging abstraction layer beyond what is needed now.

This feature is specifically about **automatic email triggering for important decision and day-end events**.

---

## 4. Core Design Principle

### 4.1 Notify Only When It Matters

Automatic email should be used for significant events, not for every minor platform update.

### 4.2 Event-Driven, Not Manual-Only

The system should trigger notifications from canonical platform events rather than requiring operators to remember manual commands.

### 4.3 Email as Async Attention Interface

Email is not just a transport layer here. It is part of the platform’s human-in-the-loop operating model.

### 4.4 Resend Should Be a Real Delivery Path

If email-first is a platform promise, Resend delivery must be integrated as an actual operational path, not only as a latent capability.

---

## 5. Target Outcomes

After this feature is complete, async-dev should be able to:

1. detect when a major decision-worthy event occurs,
2. automatically create and send an email notification for that decision when policy allows,
3. detect when the day-end summary/review-night result is ready,
4. automatically send a day-end email summary,
5. avoid duplicate or noisy sends,
6. persist enough notification state to know what was sent and why.

The operator should no longer need to constantly watch the platform to know when important attention is required.

---

## 6. Required Functional Changes

### 6.1 Define Notification Event Types

Introduce a clear set of email-notifiable platform event types.

At minimum, recommended event types include:

- `major_decision_required`
- `blocked_waiting_for_human_decision`
- `critical_escalation_required`
- `day_end_summary_ready`

The exact names may vary, but the event model should be explicit.

### 6.2 Decision-Triggered Email Automation

When the platform reaches a decision-requiring state that is important enough for human attention, it should automatically:

- create a decision notification payload,
- invoke the email decision channel,
- send the email through Resend (or configured email path),
- record delivery attempt state.

This should happen through canonical runtime flow rather than manual-only CLI usage.

### 6.3 Day-End Summary Email Automation

When the platform produces a day-end or `review-night` summary that qualifies for notification, it should automatically:

- generate a day-end email payload,
- send the summary through Resend,
- record delivery attempt state,
- avoid duplicate sends for the same review artifact.

### 6.4 Notification State Persistence

The platform must persist email notification state so it can answer:

- was a decision email already sent for this event?
- was a day-end summary email already sent?
- when was it sent?
- was delivery attempted and did it fail?
- is retry needed?

This is essential to avoid duplicate sends and to support debugging.

### 6.5 Delivery Failure Handling

If email sending fails, the system must not silently drop the event.

It should:

- persist failure state,
- surface the failure clearly,
- optionally mark retry-needed state,
- avoid pretending that notification succeeded.

### 6.6 Trigger Integration Into Mainflows

The automation should be integrated into real platform flows, especially where appropriate:

- `run-day`
- `review-night`
- `resume-next-day`
- decision state transitions
- escalation paths

This feature must not remain a detached helper.

### 6.7 Notification Policy / Noise Control

Automatic email behavior should be controlled by simple policy rules, such as:

- only major decisions trigger email,
- not every blocked state is email-worthy,
- one day-end summary per day or review cycle,
- duplicate suppression for identical unresolved decision events.

This will keep the email channel useful rather than noisy.

---

## 7. Detailed Requirements

### 7.1 Canonical Notification Model

The feature should define a structured notification event model, including fields such as:

- `event_type`
- `run_id` or related object reference
- `feature_id` / `product_id`
- `reason`
- `severity`
- `email_required`
- `email_sent`
- `email_sent_at`
- `delivery_status`
- `related_artifacts`
- `dedupe_key`

The exact schema may vary, but the platform should not rely on ad hoc booleans scattered through the codebase.

### 7.2 Dedupe Strategy

The system must avoid sending duplicate emails for the same unresolved event.

Examples:

- the same blocked decision event should not send repeatedly every loop,
- the same day-end review should not produce multiple summary emails unless explicitly re-triggered.

A dedupe key or equivalent canonical identity is recommended.

### 7.3 Email Payload Design

The email payloads should be clear and operator-useful.

#### Decision Email Should Typically Include
- why human attention is needed
- what decision is required
- current context summary
- suggested options or next action
- links or references to relevant artifacts/workflows

#### Day-End Email Should Typically Include
- what happened today
- current platform/project status
- active or blocked items
- items needing attention
- key recovery or acceptance signals if relevant

The email should reduce the need to open the platform just to understand whether attention is needed.

### 7.4 Delivery Path

The system should use the actual configured email path, expected to include Resend integration where configured.

The implementation must clarify:

- what configuration is required,
- what happens if Resend is unavailable,
- how send failures are surfaced,
- what command/service actually performs the send.

### 7.5 Mainflow Hooking

The feature must explicitly hook the automation into real event points.

Examples:

- after a decision-worthy state is persisted,
- after `review-night generate` produces a review artifact,
- after a major escalation-worthy failure state is detected,
- when a run transitions into a human-blocked state.

The exact hook locations should be identified concretely in the implementation.

### 7.6 Manual Compatibility

Manual `email-decision` workflows may still exist, but they should become secondary for these canonical events.

The system should support both:

- auto-send when policy says so,
- manual send/debug path when needed.

---

## 8. Expected File Changes

The exact file list may vary, but implementation is expected to touch categories like the following.

### 8.1 Notification / Email Integration

Potential areas:

- decision/email notification model helpers
- Resend send path integration
- notification dedupe/state persistence helpers
- email payload builders

### 8.2 Existing Mainflows

Likely updates:

- `cli/commands/run_day.py`
- `cli/commands/review_night.py`
- `cli/commands/resume_next_day.py`
- decision-channel related modules
- escalation/recovery state integration where relevant

### 8.3 Existing Email Command/Service Layer

Likely updates:

- `email-decision` implementation
- send helpers
- delivery result persistence
- configuration handling

### 8.4 Documentation Updates

Likely updates:

- README / async decision docs
- operator docs
- email configuration docs
- Resend integration guidance
- day-end workflow docs

---

## 9. Acceptance Criteria

## AC-001 Notification Event Model Exists
There is a structured model for important email-notifiable events.

## AC-002 Major Decision Emails Auto-Send
When a qualifying major decision event occurs, async-dev can automatically send a decision email through the configured email path.

## AC-003 Day-End Summary Emails Auto-Send
When a qualifying day-end summary is generated, async-dev can automatically send a day-end email.

## AC-004 Dedupe Works
The system avoids duplicate sends for the same unresolved event or same day-end summary artifact.

## AC-005 Delivery State Persists
The platform records whether send attempts succeeded, failed, or require retry.

## AC-006 Failures Are Visible
Email delivery failures are surfaced clearly rather than silently ignored.

## AC-007 Mainflow Integration Exists
The send logic is actually hooked into canonical flows such as decision transitions and review-night.

## AC-008 Noise Is Controlled
Notification policy avoids spamming operators for low-value events.

## AC-009 Documentation Updated
Operators can understand what is automatic, what is manual, and how to configure/use the email path.

## AC-010 Tests Added
Automated tests cover trigger logic, dedupe behavior, payload generation, and delivery-state handling.

---

## 10. Test Requirements

At minimum, the feature should include tests for the following scenarios.

### 10.1 Major Decision Trigger
- a major decision-worthy state occurs,
- notification event is created,
- email send path is invoked,
- delivery state is persisted.

### 10.2 Day-End Summary Trigger
- a day-end/review-night summary is created,
- summary email is generated and sent,
- duplicate sends are suppressed for the same summary.

### 10.3 Dedupe Behavior
- repeated loops on the same unresolved event do not spam duplicate emails.

### 10.4 Delivery Failure Handling
- send path fails,
- failure is persisted and surfaced,
- system does not mark the event as successfully notified.

### 10.5 Manual Compatibility
- manual email-decision flow still works or remains understandable where applicable.

### 10.6 Policy Filtering
- low-significance events do not trigger auto email when policy says they should not.

---

## 11. Implementation Guidance

### 11.1 Preferred Implementation Order

Recommended sequence:

1. define notification event model and dedupe strategy,
2. define payload builders for decision and day-end emails,
3. integrate send state persistence,
4. hook into decision-trigger paths,
5. hook into `review-night` day-end path,
6. add failure handling,
7. add tests,
8. update docs.

### 11.2 Avoid These Failure Patterns

The implementation must avoid:

- sending email for every minor blocked state,
- leaving send behavior manual-only,
- failing silently when Resend delivery fails,
- duplicating send logic in many places,
- unclear event identity leading to duplicate sends,
- payloads that are too vague to help the operator.

### 11.3 Backward Compatibility

The feature should preserve manual email workflows for debugging and fallback, while establishing auto-send as the canonical path for important events.

---

## 12. Risks and Mitigations

### Risk 1: Email noise / spam
**Mitigation:** use explicit event types, significance filtering, and dedupe keys.

### Risk 2: Delivery failures become invisible
**Mitigation:** persist delivery state and surface failures clearly.

### Risk 3: Mainflow hooks are incomplete
**Mitigation:** identify and wire the exact canonical event points rather than relying on loose helper usage.

### Risk 4: Payloads are not actually helpful
**Mitigation:** include actionable context and references to relevant artifacts or next steps.

### Risk 5: Resend configuration issues create confusion
**Mitigation:** document required configuration and failure behavior clearly.

---

## 13. Deliverables

The feature is complete only when all of the following exist:

- structured notification event model
- major decision auto-email path
- day-end summary auto-email path
- delivery-state persistence
- dedupe mechanism
- failure handling
- mainflow integration
- documentation updates
- automated tests

---

## 14. Definition of Done

This feature is considered done only when:

1. important decision and day-end events can automatically notify the operator by email,
2. the auto-send path is integrated into canonical platform flows,
3. duplicate sends are controlled,
4. failures are visible and debuggable,
5. the email-first async decision promise becomes a real platform behavior rather than a mostly manual capability.

---

## 15. Suggested OpenCode / async-dev Execution Notes

Recommended execution intent:

- treat this as a canonical notification integration feature,
- prioritize event correctness and dedupe,
- make auto-send real for significant events,
- keep manual commands as fallback/debug tools,
- strengthen the platform’s async human-in-the-loop story.

Recommended planning questions:

- what exactly counts as a major decision event?
- what exact review-night artifact should trigger day-end email?
- what is the canonical dedupe key strategy?
- how should send failures be persisted and surfaced?
- where are the exact mainflow hook points?

---

## 16. Suggested Commit / Completion Framing

The completion report should explicitly demonstrate:

- which events now trigger auto email,
- how Resend send flow is invoked,
- how duplicate suppression works,
- how failures are handled,
- how run-day/review-night/resume-next-day now connect to email notification.

It should not claim completion merely because manual email commands exist.

---

## 17. Summary

Feature 080 turns the email-first decision channel into a more complete platform behavior by automatically notifying the operator for:

- important decision events
- day-end summary events

This strengthens async-dev’s core promise of low-interruption, asynchronous human attention.

In short:

> **080 makes critical human attention events proactively reach the operator by email.**
