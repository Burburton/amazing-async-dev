# amazing-skill-pack-advisor — V1.1 Spec

## 1. Version Summary

### Version
`v1.1`

### Version Title
Real async-dev Consumption Pilot

### Goal
Validate that `amazing-skill-pack-advisor` can operate as a real upstream product for `amazing-async-dev` by proving that a generated starter pack can be consumed in an end-to-end async-dev-managed workflow.

### Why v1.1 matters
V0 established the core advisory product:
- project intake
- project classification
- capability recommendation
- starter pack export

V1 strengthened the starter pack contract and its integration semantics for `amazing-async-dev`.

At that point, the most important open question is no longer:
- can the advisor produce a good recommendation artifact?

It becomes:
- can async-dev actually consume that artifact in a real workflow?
- does the handoff reduce setup ambiguity in practice?
- does the upstream → downstream flow work smoothly enough to be worth keeping?

This version exists to answer those questions through real end-to-end validation.

---

## 2. Product Objective for v1.1

Prove that the advisor’s starter pack is not just readable, but operationally consumable by `amazing-async-dev`.

This version should make it possible to:

1. generate a starter pack from a realistic project intake
2. hand that starter pack to `amazing-async-dev`
3. initialize a new async-dev product from it
4. verify that async-dev can interpret the starter pack in a useful way
5. run at least the first part of a real workflow using that initialization path
6. capture friction and contract gaps for future improvement

---

## 3. Core Thesis

The value of `amazing-skill-pack-advisor` is not fully proven until the starter pack is used in a real downstream execution system.

V1.1 is therefore about:
- consumption
- validation
- friction discovery
- contract proof

not about:
- expanding recommendation breadth
- adding speculative intelligence
- building more isolated advisory logic

---

## 4. Scope

### In scope
- real starter pack generation
- real async-dev ingestion path
- real product initialization using starter pack
- validation of starter pack interpretation
- end-to-end example flow
- contract gap detection
- friction logging and lessons learned
- documentation of the real integration path

### Out of scope
- broad new recommendation domains
- deep UI work
- best-practice web research
- broad plugin system
- full automation of every downstream step
- multi-product orchestration
- advanced portfolio behavior

---

## 5. Pilot Focus

This version should focus on one clear pilot flow:

```text
project intake
-> advisor starter pack generation
-> async-dev product creation from starter pack
-> first workflow execution path
-> review of contract fit and friction
```

The emphasis is on proving that this chain is real and useful.

---

## 6. Main Capability Areas

## 6.1 Real starter pack generation for pilot use

### Purpose
Generate one or more realistic starter packs that are not only examples, but actual upstream inputs for async-dev.

### Expected requirements
- realistic intake examples
- valid starter pack export
- contract-compliant output
- clear mapping to async-dev expectations

### Notes
The pilot artifact should be treated like a real handoff object, not synthetic documentation.

---

## 6.2 Real async-dev consumption

### Purpose
Validate that async-dev can read and use the starter pack in product initialization.

### Expected use
The pilot should verify whether async-dev can use the starter pack to influence:
- product initialization defaults
- workflow mode assumptions
- early setup decisions
- first-feature planning assumptions

### Notes
This is the most important value check in v1.1.

---

## 6.3 End-to-end handoff flow

### Purpose
Prove the full upstream -> downstream path in practice.

### Expected chain
- intake file prepared
- advisor exports starter pack
- async-dev consumes starter pack
- async-dev initializes product
- async-dev begins real managed workflow

### Notes
This must be shown as a real flow, not just described abstractly.

---

## 6.4 Contract validation and friction discovery

### Purpose
Identify what still does not fit cleanly between advisor output and async-dev consumption.

### Expected outputs
- contract mismatches
- ambiguous fields
- ignored fields
- missing fields
- confusing defaults
- friction points in real use

### Notes
This is a validation version, so surfacing these gaps is part of success, not failure.

---

## 6.5 Real integration documentation

### Purpose
Document how the ecosystem handoff actually works in practice.

### Expected documentation content
- intake -> starter pack -> async-dev flow
- required files
- contract assumptions
- command examples
- known limitations
- friction found during pilot

### Notes
The documentation should help future users or future automation layers.

---

## 7. Pilot Flow Expectations

The pilot flow should likely include at least one real scenario such as:

### Step 1
Create a realistic `project-intake.yaml`

### Step 2
Run advisor export flow:
```bash
advisor recommend --input project-intake.yaml --output starter-pack.yaml
```

### Step 3
Consume it in async-dev:
```bash
asyncdev new-product create --starter-pack starter-pack.yaml
```

### Step 4
Verify that product initialization is meaningfully influenced by the starter pack

### Step 5
Begin first workflow-managed execution path

### Step 6
Document what worked and what did not

---

## 8. Contract Validation Expectations

This version should verify questions such as:

- does async-dev understand the starter pack shape correctly?
- are required / optional / deferred capabilities clear enough?
- are workflow defaults consumable in practice?
- are any fields ignored unexpectedly?
- are there contract fields missing for a smooth downstream workflow?

### Notes
The pilot should explicitly record these findings.

---

## 9. Repository Deliverables

This version should produce:

### 9.1 Real pilot intake example(s)
Not just synthetic examples, but true integration examples.

### 9.2 Real pilot starter pack(s)
Artifacts actually used to drive async-dev initialization.

### 9.3 Integration validation report
A document or artifact describing:
- what worked
- what did not
- what contract gaps remain
- what should be improved next

### 9.4 Updated integration docs
Documentation that reflects the validated real path, not only intended future compatibility.

---

## 10. Suggested Documentation Additions

### 10.1 `docs/real-asyncdev-consumption-pilot.md`
Describe the actual pilot flow.

### 10.2 `docs/contract-validation-report.md`
Capture what the pilot revealed.

### 10.3 `examples/pilot/`
Contain pilot intake and starter pack artifacts used in the real test.

---

## 11. Acceptance Criteria

- [ ] at least one realistic starter pack is generated and used for real async-dev initialization
- [ ] the advisor -> async-dev handoff is validated through a real flow
- [ ] contract fit and mismatches are explicitly documented
- [ ] async-dev consumes the starter pack in a materially useful way
- [ ] the end-to-end pilot produces actionable next-step findings
- [ ] documentation reflects real, validated integration behavior

---

## 12. Risks

### Risk 1 — Pilot remains too synthetic
If the “pilot” is only a documentation exercise, it will not prove real value.

**Mitigation:** require real starter pack generation and real async-dev consumption.

### Risk 2 — Contract ambiguity is hidden
If mismatches are glossed over, future integration work will remain weak.

**Mitigation:** explicitly record friction and ignored/missing semantics.

### Risk 3 — Over-expanding scope
The version could drift into building large new advisory logic instead of validating integration.

**Mitigation:** keep the focus on handoff proof and contract validation.

### Risk 4 — Weak downstream usage
If async-dev “consumes” the starter pack but does nothing meaningful with it, the pilot will be shallow.

**Mitigation:** require materially useful initialization influence.

---

## 13. Recommended Implementation Order

1. select a real pilot scenario
2. create realistic pilot intake
3. generate pilot starter pack
4. run real async-dev consumption path
5. inspect contract fit and friction
6. document the pilot outcome
7. identify the next integration improvements

---

## 14. Suggested Validation Questions

This version should make it easier to answer:

- can the advisor’s starter pack actually drive async-dev initialization?
- does the handoff feel operationally real?
- which parts of the contract are already good enough?
- which parts are still ambiguous or missing?
- is the advisor now genuinely valuable as an ecosystem upstream product?

If the answer is still “the artifact looks good, but the real downstream usage is unclear,” then v1.1 is not done.

---

## 15. Definition of Done

V1.1 is done when:

- the advisor starter pack is used in a real async-dev-managed initialization flow
- the integration path is validated end-to-end
- contract gaps are explicitly identified
- the product’s upstream ecosystem role is proven in practice rather than only in theory

If the handoff from advisor to async-dev still feels mostly hypothetical, v1.1 is not done.
