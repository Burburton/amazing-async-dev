# Reporting Best-Practice Guide for Async-Dev Email Channel

## Feature 046 — Reporting Best-Practice Research & Iteration Pack

### Purpose

This guide codifies best practices for high-signal executive status reporting, derived from research on McKinsey Pyramid Principle, Harvard Business Review, AI Advisory Board, WhenNotesFly, and professional communication frameworks.

---

## 1. Core Structural Frameworks

### 1.1 BLUF (Bottom Line Up Front) — THE GOLD STANDARD

**Rule**: All executive communication must lead with the conclusion, recommendation, or request.

**Wrong**:
```
We've been working on the API integration for the past week. 
We explored three approaches and analyzed the tradeoffs. 
After careful consideration, we recommend Option B.
```

**Right**:
```
Recommend: Option B for API integration - 40% faster delivery, 
$20K lower cost. Three alternatives evaluated, full analysis attached.
```

**Application**: The `summary` field in async-dev status reports MUST state decision/recommendation/ask in the first line.

---

### 1.2 Pyramid Principle (McKinsey)

**Rule**: Structure hierarchically from conclusion → supporting argument → details.

**Three-Line Formula**:
1. Recommendation/decision/outcome
2. Why it matters (risk or opportunity with numbers)
3. What you need from them

**Example**:
```
1. Deploy to staging Friday (recommendation)
2. Reduces customer impact risk by 80% (why)
3. Approval needed by Thursday 3pm (what needed)
```

---

### 1.3 One-Screen Constraint

**Rule**: Status reports must fit on a single laptop screen or printed page.

**Limits**:
| Format | Maximum |
|--------|---------|
| Pure text | 250-400 words |
| Bullets | 6-10 bullets + optional exhibit |
| Email body | One screen (no scrolling) |

**Application**: `compress_report_for_one_screen()` function enforces this.

---

## 2. Decision-Readiness Requirements

### 2.1 Explicit Ask — Mandatory

**Rule**: Every report must end with one of three things:
- A **decision** you need
- An **alignment** you're seeking  
- An **awareness** you're building

**Decision Format**:
```
Decision: Approve $50K Q3 reallocation for pilot
Deadline: By Friday 3pm
```

**Alignment Format**:
```
Confirm: This approach aligns with board growth priorities
Reply by: Thursday
```

**Awareness Format**:
```
FYI only: Flagging this trend for quarterly review
No reply needed
```

---

### 2.2 Options + Recommendation — NEVER Just Options

**Rule**: Presenting options without recommendation pushes analytical work back to the executive.

**Wrong**:
```
We evaluated three vendors. All have strengths and weaknesses.
```

**Right**:
```
Recommend Vendor B. 
- $400K cost advantage over Vendor A
- 2-week faster implementation than Vendor C
- Tradeoff: less customization (acceptable per requirements)
```

**Gap in Current Format**: No `options` field exists. Blocker reports should include structured options.

---

### 2.3 Decision Deadline

**Rule**: Include explicit deadline for blockers and decision requests.

**Format**: `Decision needed by [date] [time]`

**Gap in Current Format**: No `decision_deadline` field exists.

---

## 3. Content Quality Rules

### 3.1 Outcomes Over Activities

**Rule**: Progress bullets describe outcomes, not activity logs.

**Weak**:
- "Met with security team"
- "Discussed architecture options"
- "Started work on tests"

**Strong**:
- "Completed security review - cleared for staging rollout"
- "Validated architecture with 5 customer calls"
- "Finished tests - 100% pass rate"

---

### 3.2 Quantification Over Qualification

**Rule**: Every qualitative claim should be accompanied by a quantitative one.

**Transformation Table**:
| Qualitative | Quantitative |
|-------------|--------------|
| "Significant cost savings" | "$2.3M annual reduction, 18% of spend" |
| "Improved customer experience" | "NPS 28→51; support tickets -40%" |
| "Fast timeline" | "8 weeks from approval to launch" |
| "High risk" | "3/5 comparable implementations exceeded budget by >30%" |

---

### 3.3 Blocker/Risk Separation

**Rule**: Separate blockers (present) from risks (future).

**Blocker Format**:
```
BLOCKED: production access for vendor tests since Jan 18
Impact: delays end-to-end validation
Owner: IT Ops
Next step: approve access request by Jan 25
```

**Risk Format**:
```
RISK: vendor SLA change (probability: medium, impact: high)
Trigger: if contract renewal delayed
Mitigation: backup vendor identified
```

**Gap in Current Format**: `risks_blockers` combines both - should be separate fields.

---

### 3.4 Confident Framing — No Hedging

**Rule**: Use active voice, avoid hedging words.

**Hedging Words to Avoid**: maybe, might, could, perhaps, possibly, think, guess, probably

**Passive Patterns to Avoid**: "was decided", "was completed", "it was", "were done"

**Wrong**: "I think we could maybe proceed"

**Right**: "Proceed with deployment"

---

## 4. Signal-to-Noise Optimization

### 4.1 Changed Items Only

**Rule**: Report what's new/different, not full status retelling.

**Signal (Keep)**:
- What changed trajectory
- Completed milestones
- New blockers
- Dependency movements

**Noise (Remove)**:
- "Everything moving as planned"
- Full status report when nothing changed
- Meeting notes without decisions
- Vanity metrics without context

---

### 4.2 No Vanity Metrics

**Rule**: Metrics must be tied to decisions/outcomes.

**Vanity (Remove)**:
- "Total lines of code: 50,000"
- "Number of files: 200"

**Actionable (Keep)**:
- "Tests passed: 150/150 (100%)"
- "Resolved blockers: 3"
- "Time to resolution: 2 hours (target: 4 hours)"

---

### 4.3 Truncation Applied

**Rule**: Links for details, not inline expansion.

**Pattern**: 
```
What Changed (3 of 7 shown):
- Completed Feature 046 ✓
- Resolved blocker ✓  
- Shipped milestone ✓
[See execution-result.md for full details]
```

---

## 5. Anti-Patterns (FORBIDDEN)

| Anti-Pattern | Why It Fails | Severity |
|--------------|--------------|----------|
| Building up to recommendation | Executives stop reading before conclusion | HIGH |
| Over-including methodology | Executive doesn't need your journey | MEDIUM |
| Hedging language | Signals uncertainty | MEDIUM |
| Passive voice | Obscures responsibility | LOW |
| Implicit ask | Executives can't act on implied requests | HIGH |
| "Everything is fine" | False confidence, hides problems | HIGH |
| Options without recommendation | Pushes analysis back to executive | HIGH |
| Long narrative paragraphs | Gets skimmed and misunderstood | MEDIUM |
| Vanity metrics | No actionable context | MEDIUM |
| Blocker/Risk mixed | Blurs urgency | MEDIUM |

---

## 6. Quality Rubric Summary

### Scoring Categories (100 points total)

**Structure (25 pts)**:
- BLUF compliance (8)
- One-screen fit (6)
- Format consistency (6)
- Explicit headers (5)

**Decision-Readiness (30 pts)**:
- Explicit ask (10)
- Options provided (8)
- Recommendation stated (7)
- Deadline included (5)

**Content Quality (25 pts)**:
- Outcomes not activities (8)
- Quantified claims (7)
- Blocker/risk separated (5)
- No hedging (5)

**Signal-to-Noise (20 pts)**:
- Changed items only (8)
- No vanity metrics (6)
- Truncation applied (6)

### Quality Levels

| Level | Score | Description |
|-------|-------|-------------|
| Excellent | 90-100 | Fully compliant with best practices |
| Good | 75-89 | Mostly compliant, minor gaps |
| Acceptable | 60-74 | Meets minimum standards |
| Needs Improvement | 40-59 | Significant gaps, requires revision |
| Poor | 0-39 | Does not meet standards |

---

## 7. Future Improvements (Identified Gaps)

| ID | Description | Priority | Category |
|----|-------------|----------|----------|
| 046-01 | Add options structure with pros/cons format | HIGH | Decision-Readiness |
| 046-02 | Separate blockers from risks in template | HIGH | Content Quality |
| 046-03 | Add decision_deadline field | HIGH | Decision-Readiness |
| 046-04 | Strengthen quantification enforcement | MEDIUM | Content Quality |
| 046-05 | Add SCQA framework support | LOW | Structure |
| 046-06 | Add executive summary for multi-feature | LOW | Structure |

---

## 8. Sources

| Source | Key Contribution |
|--------|-----------------|
| McKinsey Pyramid Principle | BLUF structure, conclusion-first |
| Harvard Business Review (Porter/Nohria) | CEO time constraints, attention scarcity |
| Confidence Playbook | C-suite communication guide, quantification |
| AI Advisory Board | Status report templates, blocker/risk separation |
| WhenNotesFly | SCQA, anti-patterns, executive communication |
| Umbrex | One-screen criteria, executive summary checklist |
| Nielsen Norman Group | Signal-to-noise optimization |

---

## 9. Application to Async-Dev

### Current Format Assessment

| Aspect | Current State | Best Practice Alignment |
|--------|---------------|------------------------|
| BLUF | `summary` at top | ✅ Aligned |
| One-screen | `compress_report_for_one_screen()` | ✅ Aligned |
| Decision-readiness | `recommendation_type` + `continuation_status` | ⚠️ Partial |
| Explicit ask | `reply_required` flag | ⚠️ Binary, not specific |
| Options structure | Not implemented | ❌ Gap |
| Quantification | `metrics` dict optional | ⚠️ Weak enforcement |
| Blocker/risk separation | Combined in `risks_blockers` | ❌ Gap |
| Deadline | Not implemented | ❌ Gap |

### Recommended Enhancements

1. Add `options` field to blocker reports
2. Split `risks_blockers` into `blockers` + `risks`
3. Add `decision_deadline` field
4. Strengthen `metrics` requirement for milestone/blocker types
5. Enhance `explicit_ask` from binary flag to structured format

---

## 10. Usage

Evaluate report quality:

```python
from runtime.report_quality_rubric import evaluate_report_quality

result = evaluate_report_quality(report)
print(f"Score: {result['total_score']}/100")
print(f"Level: {result['quality_level']}")
print(f"Gaps: {result['gaps']}")
```

Get improvement priorities:

```python
priorities = get_improvement_priorities(result)
for p in priorities:
    print(f"{p['criterion']}: {p['action']} (priority: {p['priority']})")
```

Compare format to best practice:

```python
comparison = compare_format_to_best_practice(report)
for gap in comparison['gaps']:
    print(gap)
```