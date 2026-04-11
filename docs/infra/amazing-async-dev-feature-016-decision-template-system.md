# Feature 016 — Decision Template System

## 1. Feature Summary

### Feature ID
`016-decision-template-system`

### Title
Decision Template System

### Goal
Reduce nightly decision friction in `amazing-async-dev` by introducing reusable, structured decision templates for common decision scenarios.

### Why this matters
`amazing-async-dev` now has a much stronger nightly management layer:

- daily management summary
- decision inbox
- resolved/unresolved issue distinction
- next-day recommendation
- execution and recovery context
- archive/history support

This means the system can now surface what needs human judgment.

However, the next source of friction is that many decision items may still be created ad hoc.  
If every decision is phrased differently, the operator still has to spend unnecessary effort understanding:

- what kind of decision this is
- what the common options are
- whether this blocks tomorrow
- what happens if the decision is deferred
- how similar situations were handled before

This feature exists to make common decisions more structured, consistent, and reusable.

---

## 2. Objective

Introduce a decision template system so common nightly decision scenarios can be represented with clearer structure, more consistency, and better reuse.

This feature should make it easier to:

1. classify decision-needed items
2. present common decision scenarios consistently
3. reduce nightly cognitive overhead
4. improve recommendation quality
5. support future planning and automation based on better decision structure

---

## 3. Scope

### In scope
- define a structured decision template model
- define a first set of supported decision types
- support template-based decision objects in the decision inbox
- improve consistency of decision presentation
- support reusable option/recommendation framing
- document the decision template approach
- integrate templates into the nightly management layer where appropriate

### Out of scope
- fully automatic decision making
- broad AI policy engine
- probabilistic decision optimization
- deep archive-driven recommendation system
- multi-project prioritization engine
- full planning-agent redesign

---

## 4. Success Criteria

This feature is successful when:

1. common decision scenarios are represented more consistently
2. the nightly decision inbox becomes easier to scan and act on
3. decision items are more clearly typed and structured
4. recommendations are easier to interpret
5. blocking impact and defer impact are more explicit
6. the operator spends less effort understanding routine decisions

---

## 5. Core Design Principles

### 5.1 Templates should reduce friction, not create bureaucracy
The goal is to simplify repeated decision patterns, not add ceremony.

### 5.2 Structure should support action
Templates should make decision items easier to choose from, not just prettier.

### 5.3 Start with the most common cases
Do not try to template every possible decision type immediately.

### 5.4 Preserve explicit human judgment
Templates help the operator decide; they do not replace the operator’s judgment.

### 5.5 Support future reuse
Decision templates should make it easier for future features to reuse prior decision patterns.

---

## 6. Main Capabilities

## 6.1 Decision typing

### Purpose
Classify decision-needed items into meaningful categories.

### Recommended initial types
- `technical`
- `scope`
- `priority`

### Notes
The first version should stay small and practical.

---

## 6.2 Template-based decision objects

### Purpose
Represent decisions with a more stable structure.

### Expected fields
At minimum, the system should support:
- `decision_id`
- `decision_type`
- `question`
- `options`
- `recommendation`
- `reason`
- `impact`
- `urgency`
- `blocking_tomorrow`
- `defer_impact`

### Notes
The exact field names may vary, but the intent should remain clear.

---

## 6.3 Reusable decision framing

### Purpose
Make recurring decision patterns easier to present consistently.

### Example recurring scenarios
- continue current implementation path or change approach
- accept partial result or continue execution
- expand current scope or defer to a later feature
- retry after blocker/failure or defer
- choose which task/feature should take priority next

### Notes
The first version only needs a small number of high-value templates.

---

## 6.4 Better nightly decision inbox presentation

### Purpose
Use decision templates to improve the clarity of nightly review.

### Expected improvements
- more consistent decision item formatting
- clearer separation between decision types
- easier understanding of recommendation quality
- clearer indication of whether a decision blocks tomorrow’s work

### Notes
This feature should improve the operator experience directly, not just internal object structure.

---

## 6.5 Future reuse support

### Purpose
Prepare decision structures for future pattern reuse.

### Potential future value
- stronger archive-aware planning
- reusable decision patterns
- more stable next-day recommendation logic
- better handling of repeated blocker/priority choices

### Notes
This feature does not need to implement those later capabilities yet.
It only needs to make them more feasible.

---

## 7. Template Model Expectations

The decision template system should support both:

### 7.1 Decision type classification
Example:
- technical
- scope
- priority

### 7.2 Per-template decision shape
Each decision should be structured enough to capture:
- what is being decided
- which choices exist
- what the system recommends
- why that recommendation is suggested
- whether delay affects tomorrow

### Notes
This can be implemented via:
- template registry
- static definitions
- structured schema-driven logic
- or another lightweight mechanism

The implementation does not need to be over-engineered.

---

## 8. Integration Expectations

This feature should integrate with:

- nightly management summary
- decision inbox generation
- `decisions_needed` structures
- next-day recommendation context where relevant
- archive/history logic only where naturally useful

### Notes
This is primarily a decision-layer refinement feature, not a workflow rewrite.

---

## 9. Deliverables

This feature must add:

### 9.1 Decision template structure
A defined format for reusable decision templates or template-shaped decision objects.

### 9.2 Initial template set
A small, practical first set of supported decision templates.

### 9.3 Inbox integration
Decision template output integrated into nightly decision presentation.

### 9.4 Documentation
At least one document or section explaining:
- what decision templates are
- which types are supported initially
- how they improve nightly decision handling
- how future decision types can be added

---

## 10. Acceptance Criteria

- [ ] decision-needed items support clear structured typing
- [ ] the system supports at least an initial set of decision templates
- [ ] nightly decision inbox presentation becomes more consistent
- [ ] `blocking_tomorrow` is explicit
- [ ] `defer_impact` is explicit
- [ ] recommendation and reason are clearer
- [ ] documentation explains the decision template system clearly

---

## 11. Risks

### Risk 1 — Too many templates too early
Over-expansion would make the system harder to maintain.

**Mitigation:** start with only the highest-value recurring decision types.

### Risk 2 — Template structure without practical benefit
If templates do not reduce nightly decision effort, they are not useful.

**Mitigation:** validate against real nightly review use.

### Risk 3 — Overfitting to current examples
Templates that are too narrow may not generalize well.

**Mitigation:** keep templates moderately abstract and decision-oriented.

### Risk 4 — Decision clutter
If too many low-value decisions are templated, the inbox becomes noisy.

**Mitigation:** focus on decisions that genuinely require human judgment.

---

## 12. Recommended Implementation Order

1. define the minimal decision template model
2. define initial decision types
3. create an initial set of reusable templates
4. integrate templates into nightly decision inbox generation
5. improve operator-facing rendering of templated decisions
6. document the template model and usage

---

## 13. Suggested Validation Questions

This feature should make the system better able to answer:

- what kind of decision is this?
- what are the realistic options?
- what does the system recommend?
- why is that recommendation reasonable?
- does this block tomorrow?
- what happens if I defer this?

If the nightly decision inbox still makes the operator work too hard to answer those questions, this feature is not done.

---

## 14. Definition of Done

Feature 016 is done when:

- common decision scenarios are more consistently structured
- the decision inbox is easier to understand and act on
- recurring decision patterns are captured in reusable forms
- the nightly management layer imposes less decision interpretation burden

If the operator still has to mentally normalize each recurring decision from scratch, this feature is not done.
