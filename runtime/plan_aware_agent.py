"""Archive-aware, decision-aware, blocker-aware planning agent.

Feature 017: Archive-aware Plan Agent

This module enhances plan-day with:
- Archive awareness: Use lessons_learned, reusable_patterns from archives
- Decision awareness: Account for unresolved/blocking decisions
- Blocker awareness: Avoid blocked work, suggest alternatives
- Explainability: Provide rationale for recommendations

Design Principles (from Feature 017 spec):
1. Planning should remain bounded
2. Reuse history where it matters
3. Respect current execution reality
4. Explain why a recommendation is made
5. Improve trust, not complexity
"""

from pathlib import Path
from typing import Any

from runtime.archive_query import (
    discover_all_archives,
    filter_archives,
    get_archive_detail,
    get_lessons_summary,
    get_patterns_summary,
    get_recent_archives,
)
from runtime.recovery_classifier import (
    classify_recovery,
    check_resume_eligibility,
    get_recovery_guidance,
    RecoveryClassification,
    ResumeEligibility,
)
from runtime.decision_templates import enhance_decision_with_template


# ============================================================================
# Archive-Aware Planning Context
# ============================================================================


def gather_archive_context(
    projects_path: Path,
    product_id: str | None = None,
    feature_id: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Gather relevant archive context for planning.
    
    Args:
        projects_path: Root projects directory
        product_id: Current product ID (filter archives from same product)
        feature_id: Current feature ID (exclude self if archived)
        limit: Maximum archives to consider
        
    Returns:
        Archive context with:
        - recent_archives: List of recent archives with lessons/patterns
        - relevant_lessons: Top lessons applicable to current context
        - relevant_patterns: Top patterns applicable to current context
        - archive_summary: Count of archives, patterns, lessons
    """
    archives = discover_all_archives(projects_path)
    
    # Filter by product if specified
    if product_id:
        archives = filter_archives(archives, product=product_id)
    
    # Get recent archives
    recent = filter_archives(archives, recent=True, limit=limit)
    
    # Collect lessons and patterns from recent archives
    all_lessons = []
    all_patterns = []
    
    for archive in recent:
        pack = archive.get("pack", {})
        
        lessons = pack.get("lessons_learned", [])
        for lesson in lessons:
            lesson["source_archive"] = archive.get("feature_id", "")
            all_lessons.append(lesson)
        
        patterns = pack.get("reusable_patterns", [])
        for pattern in patterns:
            pattern["source_archive"] = archive.get("feature_id", "")
            all_patterns.append(pattern)
    
    return {
        "recent_archives": [
            {
                "feature_id": a.get("feature_id", ""),
                "title": a.get("title", ""),
                "archived_at": a.get("archived_at", ""),
                "patterns_count": a.get("patterns_count", 0),
                "lessons_count": a.get("lessons_count", 0),
            }
            for a in recent
        ],
        "relevant_lessons": all_lessons[:10],
        "relevant_patterns": all_patterns[:10],
        "archive_summary": {
            "total_archives": len(archives),
            "recent_considered": len(recent),
            "lessons_available": len(all_lessons),
            "patterns_available": len(all_patterns),
        },
    }


def get_applicable_lessons(
    archive_context: dict[str, Any],
    task_description: str,
) -> list[dict[str, Any]]:
    """Get lessons applicable to current task.
    
    Args:
        archive_context: Archive context from gather_archive_context()
        task_description: Current task being planned
        
    Returns:
        List of applicable lessons with source archive reference
    """
    lessons = archive_context.get("relevant_lessons", [])
    
    # Simple keyword matching for applicability
    # Keep it practical - not full semantic search
    applicable = []
    
    task_lower = task_description.lower()
    
    for lesson in lessons:
        lesson_text = lesson.get("lesson", "").lower()
        context = lesson.get("context", "").lower()
        
        # Match by task keywords
        task_keywords = extract_task_keywords(task_description)
        
        matches = 0
        for kw in task_keywords:
            if kw in lesson_text or kw in context:
                matches += 1
        
        if matches > 0:
            applicable.append({
                "lesson": lesson.get("lesson", ""),
                "context": lesson.get("context", ""),
                "source_archive": lesson.get("source_archive", ""),
                "relevance_score": matches,
            })
    
    # Sort by relevance, limit to top 5
    applicable.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    return applicable[:5]


def get_applicable_patterns(
    archive_context: dict[str, Any],
    task_description: str,
) -> list[dict[str, Any]]:
    """Get patterns applicable to current task.
    
    Args:
        archive_context: Archive context from gather_archive_context()
        task_description: Current task being planned
        
    Returns:
        List of applicable patterns with source archive reference
    """
    patterns = archive_context.get("relevant_patterns", [])
    
    applicable = []
    task_lower = task_description.lower()
    
    for pattern in patterns:
        pattern_text = pattern.get("pattern", "").lower()
        applicability = pattern.get("applicability", "").lower()
        
        task_keywords = extract_task_keywords(task_description)
        
        matches = 0
        for kw in task_keywords:
            if kw in pattern_text or kw in applicability:
                matches += 1
        
        if matches > 0:
            applicable.append({
                "pattern": pattern.get("pattern", ""),
                "applicability": pattern.get("applicability", ""),
                "source_archive": pattern.get("source_archive", ""),
                "relevance_score": matches,
            })
    
    applicable.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    return applicable[:5]


def extract_task_keywords(task: str) -> list[str]:
    """Extract relevant keywords from task description."""
    keywords = []
    
    # Common development keywords
    dev_keywords = [
        "cli", "command", "runtime", "module", "schema", "template",
        "test", "implement", "add", "create", "enhance", "fix",
        "archive", "decision", "planning", "query", "build",
        "api", "engine", "adapter", "store", "state", "log",
    ]
    
    task_lower = task.lower()
    for kw in dev_keywords:
        if kw in task_lower:
            keywords.append(kw)
    
    return keywords


# ============================================================================
# Decision-Aware Planning Constraints
# ============================================================================


def analyze_decision_constraints(
    runstate: dict[str, Any],
) -> dict[str, Any]:
    """Analyze decision constraints affecting current planning.
    
    Args:
        runstate: Current RunState
        
    Returns:
        Decision constraints:
        - blocking_decisions: Decisions that block tomorrow's progress
        - pending_decisions: All unresolved decisions
        - decision_summary: Count and status
        - safe_to_proceed: Whether planning can proceed safely
    """
    decisions_needed = runstate.get("decisions_needed", [])
    
    blocking_decisions = []
    pending_decisions = []
    
    for decision in decisions_needed:
        enhanced = enhance_decision_with_template(decision)
        
        is_blocking = enhanced.get("blocking_tomorrow", False)
        urgency = enhanced.get("urgency", "medium")
        
        decision_info = {
            "decision": enhanced.get("decision", ""),
            "decision_type": enhanced.get("decision_type", "technical"),
            "urgency": urgency,
            "blocking_tomorrow": is_blocking,
            "options": enhanced.get("options", []),
            "recommendation": enhanced.get("recommendation", ""),
            "defer_impact": enhanced.get("defer_impact", ""),
        }
        
        pending_decisions.append(decision_info)
        
        if is_blocking:
            blocking_decisions.append(decision_info)
    
    safe_to_proceed = len(blocking_decisions) == 0
    
    return {
        "blocking_decisions": blocking_decisions,
        "pending_decisions": pending_decisions,
        "decision_summary": {
            "total_pending": len(pending_decisions),
            "blocking_count": len(blocking_decisions),
            "high_urgency_count": sum(1 for d in pending_decisions if d.get("urgency") == "high"),
        },
        "safe_to_proceed": safe_to_proceed,
    }


def get_decision_safe_alternatives(
    decision_constraints: dict[str, Any],
    task_queue: list[str],
) -> list[str]:
    """Get alternative tasks that can proceed despite blocking decisions.
    
    Args:
        decision_constraints: Decision constraints from analyze_decision_constraints()
        task_queue: Current task queue
        
    Returns:
        Tasks that are safe to execute despite decisions
    """
    blocking_decisions = decision_constraints.get("blocking_decisions", [])
    
    if not blocking_decisions:
        return task_queue
    
    # If decisions block main tasks, look for parallel work
    # Simple heuristic: tasks not directly related to decision topic
    safe_tasks = []
    
    blocked_topics = []
    for d in blocking_decisions:
        decision_text = d.get("decision", "").lower()
        # Extract topic keywords
        blocked_topics.extend(decision_text.split()[:3])
    
    for task in task_queue:
        task_lower = task.lower()
        is_safe = True
        
        for topic in blocked_topics:
            if topic in task_lower:
                is_safe = False
                break
        
        if is_safe:
            safe_tasks.append(task)
    
    return safe_tasks


# ============================================================================
# Blocker-Aware Planning Constraints
# ============================================================================


def analyze_blocker_constraints(
    runstate: dict[str, Any],
) -> dict[str, Any]:
    """Analyze blocker constraints affecting current planning.
    
    Args:
        runstate: Current RunState
        
    Returns:
        Blocker constraints:
        - active_blockers: Items currently blocked
        - blocker_summary: Count and status
        - recovery_state: Recovery classification and guidance
        - safe_to_proceed: Whether planning can proceed
    """
    blocked_items = runstate.get("blocked_items", [])
    
    classification = classify_recovery(runstate)
    eligibility = check_resume_eligibility(runstate)
    guidance = get_recovery_guidance(runstate)
    
    active_blockers = []
    for item in blocked_items:
        blocker_info = {
            "item": item.get("item", ""),
            "reason": item.get("reason", ""),
            "since": item.get("since", ""),
            "resolution_options": item.get("resolution_options", ["unblock"]),
        }
        active_blockers.append(blocker_info)
    
    # Determine if safe to proceed
    safe_to_proceed = (
        classification in (
            RecoveryClassification.READY_TO_RESUME,
            RecoveryClassification.NORMAL_PAUSE,
        )
        and len(blocked_items) == 0
    )
    
    return {
        "active_blockers": active_blockers,
        "blocker_summary": {
            "total_blocked": len(blocked_items),
            "classification": classification.value,
            "eligibility": eligibility.value,
        },
        "recovery_state": {
            "classification": classification.value,
            "eligibility": eligibility.value,
            "recommended_action": guidance.get("recommended_action", ""),
            "explanation": guidance.get("explanation", ""),
        },
        "safe_to_proceed": safe_to_proceed,
    }


def get_blocker_safe_alternatives(
    blocker_constraints: dict[str, Any],
    task_queue: list[str],
) -> list[str]:
    """Get alternative tasks that can proceed despite blockers.
    
    Args:
        blocker_constraints: Blocker constraints from analyze_blocker_constraints()
        task_queue: Current task queue
        
    Returns:
        Tasks that are safe to execute despite blockers
    """
    active_blockers = blocker_constraints.get("active_blockers", [])
    
    if not active_blockers:
        return task_queue
    
    # If blocked, identify tasks not dependent on blocked items
    safe_tasks = []
    
    blocked_items = [b.get("item", "").lower() for b in active_blockers]
    
    for task in task_queue:
        task_lower = task.lower()
        is_safe = True
        
        for blocked_item in blocked_items:
            if blocked_item and blocked_item in task_lower:
                is_safe = False
                break
        
        if is_safe:
            safe_tasks.append(task)
    
    return safe_tasks


# ============================================================================
# Planning Recommendation Generation
# ============================================================================


def generate_planning_rationale(
    task: str,
    archive_context: dict[str, Any],
    decision_constraints: dict[str, Any],
    blocker_constraints: dict[str, Any],
    applicable_lessons: list[dict[str, Any]],
    applicable_patterns: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate rationale for planning recommendation.
    
    Args:
        task: Current task being planned
        archive_context: Archive context
        decision_constraints: Decision constraints
        blocker_constraints: Blocker constraints
        applicable_lessons: Lessons applicable to task
        applicable_patterns: Patterns applicable to task
        
    Returns:
        Rationale with:
        - primary_reason: Main reason for this recommendation
        - factors: List of factors considered
        - lessons_applied: Lessons that influenced decision
        - patterns_applied: Patterns that influenced decision
        - warnings: Any warnings about the plan
        - confidence: Confidence level in recommendation
    """
    factors = []
    warnings = []
    
    # Factor 1: Archive history
    archive_summary = archive_context.get("archive_summary", {})
    if archive_summary.get("lessons_available", 0) > 0:
        factors.append({
            "factor": "archive_history",
            "description": f"Considered {archive_summary.get('recent_considered', 0)} recent archives",
            "weight": "medium",
        })
    
    # Factor 2: Applicable lessons
    if applicable_lessons:
        factors.append({
            "factor": "lessons_learned",
            "description": f"Found {len(applicable_lessons)} applicable lessons",
            "weight": "high",
        })
    
    # Factor 3: Applicable patterns
    if applicable_patterns:
        factors.append({
            "factor": "reusable_patterns",
            "description": f"Found {len(applicable_patterns)} applicable patterns",
            "weight": "medium",
        })
    
    # Factor 4: Decision constraints
    decision_summary = decision_constraints.get("decision_summary", {})
    if decision_summary.get("blocking_count", 0) > 0:
        warnings.append({
            "warning": "blocking_decisions",
            "description": f"{decision_summary.get('blocking_count', 0)} decisions block progress",
            "severity": "high",
        })
        factors.append({
            "factor": "decision_constraints",
            "description": f"{decision_summary.get('total_pending', 0)} pending decisions",
            "weight": "high",
        })
    
    # Factor 5: Blocker constraints
    blocker_summary = blocker_constraints.get("blocker_summary", {})
    if blocker_summary.get("total_blocked", 0) > 0:
        warnings.append({
            "warning": "active_blockers",
            "description": f"{blocker_summary.get('total_blocked', 0)} items blocked",
            "severity": "high",
        })
        factors.append({
            "factor": "blocker_constraints",
            "description": f"State: {blocker_summary.get('classification', 'unknown')}",
            "weight": "high",
        })
    
    # Determine primary reason
    if warnings:
        primary_reason = "Task selected with caution due to constraints"
    elif applicable_lessons or applicable_patterns:
        primary_reason = "Task recommended based on historical patterns and lessons"
    else:
        primary_reason = "Task selected as next logical step in queue"
    
    # Determine confidence
    warning_count = len(warnings)
    if warning_count == 0:
        confidence = "high"
    elif warning_count == 1:
        confidence = "medium"
    else:
        confidence = "low"
    
    return {
        "primary_reason": primary_reason,
        "factors": factors,
        "lessons_applied": [
            {
                "lesson": l.get("lesson", ""),
                "source": l.get("source_archive", ""),
            }
            for l in applicable_lessons[:3]
        ],
        "patterns_applied": [
            {
                "pattern": p.get("pattern", ""),
                "source": p.get("source_archive", ""),
            }
            for p in applicable_patterns[:3]
        ],
        "warnings": warnings,
        "confidence": confidence,
    }


def determine_safe_to_execute(
    decision_constraints: dict[str, Any],
    blocker_constraints: dict[str, Any],
) -> bool:
    """Determine if next task is safe to execute autonomously.
    
    Args:
        decision_constraints: Decision constraints
        blocker_constraints: Blocker constraints
        
    Returns:
        True if safe to execute without human intervention
    """
    decision_safe = decision_constraints.get("safe_to_proceed", True)
    blocker_safe = blocker_constraints.get("safe_to_proceed", True)
    
    return decision_safe and blocker_safe


# ============================================================================
# Main: Generate Archive-aware ExecutionPack
# ============================================================================


def generate_aware_execution_pack(
    runstate: dict[str, Any],
    projects_path: Path,
    task: str | None = None,
) -> dict[str, Any]:
    """Generate enhanced ExecutionPack with archive, decision, blocker awareness.
    
    This is the main entry point for Feature 017 archive-aware planning.
    
    Args:
        runstate: Current RunState
        projects_path: Root projects directory
        task: Specific task (if None, uses task_queue)
        
    Returns:
        Enhanced planning context with:
        - task: Recommended task
        - safe_to_execute: Whether safe to proceed
        - archive_context: Archive history context
        - decision_constraints: Decision constraints
        - blocker_constraints: Blocker constraints
        - applicable_lessons: Lessons for this task
        - applicable_patterns: Patterns for this task
        - rationale: Explanation for recommendation
        - preconditions: Required conditions
        - estimated_scope: Estimated effort level
    """
    product_id = runstate.get("project_id", "")
    feature_id = runstate.get("feature_id", "")
    task_queue = runstate.get("task_queue", [])
    
    # Step 1: Determine task to plan
    if task:
        selected_task = task
    elif task_queue:
        selected_task = task_queue[0]
    else:
        selected_task = ""
    
    # Step 2: Gather archive context
    archive_context = gather_archive_context(
        projects_path,
        product_id=product_id,
        feature_id=feature_id,
    )
    
    # Step 3: Analyze decision constraints
    decision_constraints = analyze_decision_constraints(runstate)
    
    # Step 4: Analyze blocker constraints
    blocker_constraints = analyze_blocker_constraints(runstate)
    
    # Step 5: Get applicable lessons and patterns
    applicable_lessons = get_applicable_lessons(archive_context, selected_task)
    applicable_patterns = get_applicable_patterns(archive_context, selected_task)
    
    # Step 6: Determine if safe to execute
    safe_to_execute = determine_safe_to_execute(decision_constraints, blocker_constraints)
    
    # Step 7: If not safe, find alternatives
    alternatives = []
    if not safe_to_execute:
        decision_safe = get_decision_safe_alternatives(decision_constraints, task_queue)
        blocker_safe = get_blocker_safe_alternatives(blocker_constraints, task_queue)
        
        # Intersection of both safe sets
        alternatives = [t for t in decision_safe if t in blocker_safe]
    
    # Step 8: Generate rationale
    rationale = generate_planning_rationale(
        selected_task,
        archive_context,
        decision_constraints,
        blocker_constraints,
        applicable_lessons,
        applicable_patterns,
    )
    
    # Step 9: Determine preconditions
    preconditions = []
    
    if decision_constraints.get("blocking_decisions"):
        for d in decision_constraints.get("blocking_decisions", []):
            preconditions.append(f"Resolve decision: {d.get('decision', '')}")
    
    if blocker_constraints.get("active_blockers"):
        preconditions.append("Resolve blockers before proceeding")
    
    # Step 10: Estimate scope
    estimated_scope = estimate_task_scope(selected_task, applicable_patterns)
    
    return {
        "task": selected_task,
        "safe_to_execute": safe_to_execute,
        "archive_context": archive_context.get("archive_summary", {}),
        "decision_constraints": decision_constraints.get("decision_summary", {}),
        "blocker_constraints": blocker_constraints.get("blocker_summary", {}),
        "applicable_lessons": applicable_lessons,
        "applicable_patterns": applicable_patterns,
        "rationale": rationale,
        "preconditions": preconditions,
        "estimated_scope": estimated_scope,
        "alternatives": alternatives,
        "archive_references": [
            {
                "feature_id": a.get("feature_id", ""),
                "lessons_count": a.get("lessons_count", 0),
                "patterns_count": a.get("patterns_count", 0),
            }
            for a in archive_context.get("recent_archives", [])[:3]
        ],
    }


def estimate_task_scope(
    task: str,
    applicable_patterns: list[dict[str, Any]],
) -> str:
    """Estimate task scope based on task description and patterns.
    
    Args:
        task: Task description
        applicable_patterns: Patterns applicable to task
        
    Returns:
        Scope estimate: "quick", "half-day", "full-day", "multi-day"
    """
    task_lower = task.lower()
    
    # Quick tasks
    quick_keywords = ["fix", "update", "add test", "refactor", "rename"]
    if any(kw in task_lower for kw in quick_keywords):
        if "create" not in task_lower and "implement" not in task_lower:
            return "quick"
    
    # Multi-day tasks
    multi_keywords = ["feature", "system", "architecture", "major", "complete"]
    if any(kw in task_lower for kw in multi_keywords):
        return "full-day"
    
    # Pattern-based estimation
    if applicable_patterns:
        # If patterns exist, task is likely easier
        return "half-day"
    
    # Default
    return "half-day"


# ============================================================================
# Utility: Get Planning Context Summary
# ============================================================================


def get_planning_context_summary(planning_context: dict[str, Any]) -> str:
    """Generate human-readable summary of planning context.
    
    Args:
        planning_context: Planning context from generate_aware_execution_pack()
        
    Returns:
        Human-readable summary string
    """
    summary_lines = []
    
    task = planning_context.get("task", "")
    safe = planning_context.get("safe_to_execute", True)
    rationale = planning_context.get("rationale", {})
    preconditions = planning_context.get("preconditions", [])
    
    summary_lines.append(f"Task: {task}")
    summary_lines.append(f"Safe to execute: {safe}")
    
    if rationale:
        summary_lines.append(f"Reason: {rationale.get('primary_reason', '')}")
        
        if rationale.get("warnings"):
            for w in rationale.get("warnings", []):
                summary_lines.append(f"Warning: {w.get('description', '')}")
    
    if preconditions:
        summary_lines.append(f"Preconditions: {len(preconditions)} items")
    
    archive_refs = planning_context.get("archive_references", [])
    if archive_refs:
        summary_lines.append(f"Archive refs: {len(archive_refs)} features")
    
    lessons = planning_context.get("applicable_lessons", [])
    if lessons:
        summary_lines.append(f"Lessons applied: {len(lessons)}")
    
    return "\n".join(summary_lines)