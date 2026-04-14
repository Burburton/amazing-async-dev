"""plan-day command - Generate ExecutionPack for today's bounded task.

Feature 017: Enhanced with archive-aware, decision-aware, blocker-aware planning.
Feature 035: Enhanced with resume-context-aware morning replan alignment.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.state_store import StateStore, generate_execution_id
from runtime.execution_event_types import ExecutionEventType
from runtime.execution_logger import get_logger
from runtime.plan_aware_agent import (
    generate_aware_execution_pack,
    get_planning_context_summary,
)
from cli.utils.output_formatter import print_next_step, print_success_panel
from cli.utils.path_formatter import get_relative_path
from cli.commands.resume_next_day import (
    _load_latest_review_pack,
    _extract_continuation_context,
)

app = typer.Typer(help="Plan today's bounded execution task")
console = Console()


PLANNING_MODES = {
    "continue_work": "Normal continuation of work",
    "recover_and_continue": "Recovery-oriented bounded plan",
    "verification_first": "Verification-first bounded plan",
    "closeout_first": "Closeout-first bounded plan",
    "blocked_waiting_for_decision": "Blocked state requires decision before execution",
}


def _infer_planning_mode(resume_context: dict[str, Any]) -> str:
    """Infer planning mode from resume context using rule-based mapping."""
    doctor_status = resume_context.get("prior_doctor_status", "")
    
    if doctor_status == "HEALTHY":
        return "continue_work"
    
    if doctor_status == "BLOCKED":
        return "blocked_waiting_for_decision"
    
    if doctor_status == "COMPLETED_PENDING_CLOSEOUT":
        return "closeout_first"
    
    if resume_context.get("prior_recovery_summary"):
        return "recover_and_continue"
    
    if resume_context.get("prior_closeout_reminder"):
        return "closeout_first"
    
    if doctor_status == "ATTENTION_NEEDED":
        return "recover_and_continue"
    
    return "continue_work"


def _get_planning_rationale(mode: str, resume_context: dict[str, Any]) -> dict[str, Any]:
    """Generate rationale explaining why this planning mode was chosen."""
    rationale: dict[str, Any] = {
        "mode": mode,
        "mode_description": PLANNING_MODES.get(mode, ""),
        "reasons": [],
    }
    
    doctor_status = resume_context.get("prior_doctor_status", "")
    if doctor_status:
        rationale["reasons"].append(f"Prior doctor status: {doctor_status}")
    
    if resume_context.get("prior_recommended_action"):
        rationale["prior_recommendation"] = resume_context.get("prior_recommended_action")
    
    if resume_context.get("prior_recovery_summary"):
        rationale["recovery_context"] = resume_context.get("prior_recovery_summary", {}).get("likely_cause", "")
        rationale["reasons"].append("Recovery guidance present from prior night")
    
    if resume_context.get("prior_closeout_reminder"):
        rationale["closeout_context"] = resume_context.get("prior_closeout_reminder", {}).get("status", "")
        rationale["reasons"].append("Closeout reminder present from prior night")
    
    if resume_context.get("is_stale"):
        rationale["warnings"] = ["Resume context may be outdated, current state preferred"]
    
    return rationale


def _display_resume_context_for_planning(resume_context: dict[str, Any], mode: str) -> None:
    """Display resume context before plan preview."""
    console.print("\n[bold cyan]Resume Context for Planning[/bold cyan]")
    
    console.print(f"  Prior Review Date: {resume_context.get('prior_review_timestamp', 'N/A')}")
    
    doctor_status = resume_context.get("prior_doctor_status", "")
    if doctor_status:
        console.print(f"  Prior Doctor Status: {doctor_status}")
    
    if resume_context.get("prior_recommended_action"):
        console.print(f"  Prior Recommendation: {resume_context.get('prior_recommended_action')}")
    
    console.print(f"\n  [bold green]Inferred Planning Mode: {mode}[/bold green]")
    console.print(f"  [dim]{PLANNING_MODES.get(mode, '')}[/dim]")
    
    if resume_context.get("prior_recovery_summary"):
        recovery = resume_context.get("prior_recovery_summary", {})
        console.print(f"\n  [bold yellow]Recovery Guidance:[/bold yellow]")
        console.print(f"  Likely Cause: {recovery.get('likely_cause', '')}")
    
    if resume_context.get("prior_closeout_reminder"):
        closeout = resume_context.get("prior_closeout_reminder", {})
        console.print(f"\n  [bold blue]Closeout Reminder:[/bold blue]")
        console.print(f"  Status: {closeout.get('status', '')}")
    
    if resume_context.get("is_stale"):
        console.print(f"\n  [dim yellow]Note: Resume context may be outdated[/dim yellow]")


@app.command()
def create(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    feature: str = typer.Option("001-core-object-system", help="Feature ID"),
    task: str = typer.Option(None, help="Specific task description"),
    dry_run: bool = typer.Option(False, help="Preview without saving"),
    show_context: bool = typer.Option(False, help="Show full planning context"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Create ExecutionPack for today's bounded task.
    
    Enhanced with archive-aware planning (Feature 017):
    - Uses lessons learned from archived features
    - Accounts for unresolved decisions
    - Accounts for blockers
    - Provides rationale for recommendation
    
    Enhanced with resume-context-aware planning (Feature 035):
    - Consumes prior-night decision context from Feature 034
    - Infers planning mode from resume context
    - Shapes bounded plan based on recovery/verification/closeout signals
    """
    project_path = path / project
    store = StateStore(project_path)
    logger = get_logger(project_path)
    runstate = store.load_runstate()
    root = Path.cwd() if path == Path("projects") else path
    
    resume_context: dict[str, Any] = {}
    planning_mode = "continue_work"
    planning_rationale: dict[str, Any] = {}
    
    review_pack = _load_latest_review_pack(project_path)
    if review_pack:
        resume_context = _extract_continuation_context(review_pack)
        planning_mode = _infer_planning_mode(resume_context)
        planning_rationale = _get_planning_rationale(planning_mode, resume_context)
        _display_resume_context_for_planning(resume_context, planning_mode)

    if runstate is None:
        console.print("[yellow]No existing RunState found. Creating new one.[/yellow]")
        runstate = {
            "project_id": project,
            "feature_id": feature,
            "current_phase": "planning",
            "active_task": "",
            "task_queue": [],
            "completed_outputs": [],
            "open_questions": [],
            "blocked_items": [],
            "decisions_needed": [],
            "last_action": "Initialized RunState",
            "next_recommended_action": "Create first ExecutionPack",
            "updated_at": "",
        }

    feature_id = runstate.get("feature_id", feature)
    product_id = runstate.get("project_id", project)
    previous_phase = runstate.get("current_phase", "planning")

    logger.log_event(
        ExecutionEventType.PLAN_DAY_STARTED,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"project": project, "feature": feature, "task": task},
    )

    if task:
        runstate["active_task"] = task
        runstate["task_queue"] = [task]
    else:
        if not runstate.get("task_queue"):
            console.print("[red]No tasks in queue. Specify --task or update RunState.[/red]")
            logger.close()
            raise typer.Exit(1)
        runstate["active_task"] = runstate["task_queue"][0]

    planning_context = generate_aware_execution_pack(
        runstate=runstate,
        projects_path=path,
        task=task,
    )

    execution_id = generate_execution_id(project_path)
    
    execution_pack = {
        "execution_id": execution_id,
        "project_id": product_id,
        "feature_id": runstate["feature_id"],
        "task_id": planning_context.get("task", runstate["active_task"]),
        "goal": f"Execute: {planning_context.get('task', runstate['active_task'])}",
        "task_scope": [planning_context.get("task", runstate["active_task"])],
        "must_read": [],
        "constraints": ["Stay within task_scope"],
        "deliverables": [{"item": planning_context.get("task", runstate["active_task"]), "path": "", "type": "file"}],
        "verification_steps": ["Verify deliverable exists"],
        "stop_conditions": ["Deliverable completed", "Blocker encountered"],
    }
    
    if planning_context.get("safe_to_execute") is not None:
        execution_pack["safe_to_execute"] = planning_context.get("safe_to_execute")
    
    if planning_context.get("preconditions"):
        execution_pack["preconditions"] = planning_context.get("preconditions", [])
    
    if planning_context.get("estimated_scope"):
        execution_pack["estimated_scope"] = planning_context.get("estimated_scope")
    
    if planning_context.get("rationale"):
        execution_pack["rationale"] = planning_context.get("rationale")
    
    if planning_context.get("archive_references"):
        execution_pack["archive_references"] = planning_context.get("archive_references", [])
    
    if planning_context.get("applicable_lessons"):
        execution_pack["planning_context"] = {
            "archive_summary": planning_context.get("archive_context", {}),
            "decision_summary": planning_context.get("decision_constraints", {}),
            "blocker_summary": planning_context.get("blocker_constraints", {}),
        }
    
    if resume_context:
        execution_pack["planning_mode"] = planning_mode
        execution_pack["resume_context_status"] = "found"
        execution_pack["planning_rationale"] = planning_rationale
        
        if planning_rationale.get("prior_recommendation"):
            execution_pack["prior_recommended_next_action"] = planning_rationale.get("prior_recommendation")
        
        if resume_context.get("prior_doctor_status"):
            execution_pack["prior_doctor_status"] = resume_context.get("prior_doctor_status")
        
        if resume_context.get("prior_recovery_summary"):
            execution_pack["plan_recovery_flag"] = True
        
        if resume_context.get("prior_closeout_reminder"):
            execution_pack["plan_closeout_flag"] = True
    
    if planning_mode == "blocked_waiting_for_decision":
        execution_pack["safe_to_execute"] = False
        execution_pack["preconditions"] = execution_pack.get("preconditions", [])
        execution_pack["preconditions"].append("Resolve pending decisions before execution")
    
    if planning_mode == "recover_and_continue":
        execution_pack["constraints"] = execution_pack.get("constraints", [])
        execution_pack["constraints"].append("Prioritize recovery steps from prior night")
    
    if planning_mode == "closeout_first":
        execution_pack["constraints"] = execution_pack.get("constraints", [])
        execution_pack["constraints"].append("Complete closeout before new work")

    table = Table(title="ExecutionPack Preview")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("execution_id", execution_id)
    table.add_row("feature_id", execution_pack["feature_id"])
    table.add_row("task_id", execution_pack["task_id"])
    table.add_row("goal", execution_pack["goal"])
    
    if execution_pack.get("planning_mode"):
        table.add_row("planning_mode", execution_pack.get("planning_mode"))
    
    safe_status = execution_pack.get("safe_to_execute", True)
    safe_color = "green" if safe_status else "yellow"
    table.add_row("safe_to_execute", f"[{safe_color}]{safe_status}[/{safe_color}]")
    
    if execution_pack.get("estimated_scope"):
        table.add_row("estimated_scope", execution_pack.get("estimated_scope", "N/A"))
    
    if resume_context.get("prior_doctor_status"):
        table.add_row("prior_doctor_status", resume_context.get("prior_doctor_status"))

    console.print(table)

    rationale = execution_pack.get("rationale", {})
    if rationale:
        console.print(Panel(
            rationale.get("primary_reason", "Task selected"),
            title="Rationale",
            border_style="blue",
        ))
        
        warnings = rationale.get("warnings", [])
        if warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for w in warnings[:3]:
                console.print(f"  [yellow]•[/yellow] {w.get('description', '')}")
        
        lessons_applied = rationale.get("lessons_applied", [])
        if lessons_applied:
            console.print("\n[green]Lessons Applied:[/green]")
            for l in lessons_applied[:3]:
                console.print(f"  [green]•[/green] {l.get('lesson', '')} (from {l.get('source', '')})")
        
        patterns_applied = rationale.get("patterns_applied", [])
        if patterns_applied:
            console.print("\n[blue]Patterns Applied:[/blue]")
            for p in patterns_applied[:3]:
                console.print(f"  [blue]•[/blue] {p.get('pattern', '')}")

    if show_context:
        context_summary = get_planning_context_summary(planning_context)
        console.print(Panel(
            context_summary,
            title="Full Planning Context",
            border_style="magenta",
        ))

    if dry_run:
        console.print("[yellow]Dry run - not saving[/yellow]")
        logger.close()
        return

    runstate["current_phase"] = "executing"
    store.save_runstate(runstate)
    store.save_execution_pack(execution_pack)

    logger.log_event(
        ExecutionEventType.PLAN_DAY_COMPLETED,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"execution_id": execution_id, "task": runstate["active_task"]},
    )
    logger.log_transition(
        from_phase=previous_phase,
        to_phase="executing",
        feature_id=feature_id,
        product_id=product_id,
        reason="Plan-day completed",
    )
    logger.close()

    pack_path = store.execution_packs_path / f"{execution_id}.md"
    relative_pack = get_relative_path(pack_path, root)
    relative_runstate = get_relative_path(store.project_path / "runstate.md", root)

    print_success_panel(
        message=f"ExecutionPack created: {execution_id}",
        title="Plan-Day Complete",
        paths=[
            {"label": "ExecutionPack", "path": str(pack_path)},
            {"label": "RunState", "path": str(store.project_path / "runstate.md")},
        ],
        root=root,
    )

    preconditions = execution_pack.get("preconditions", [])
    if not safe_status or preconditions:
        console.print("\n[yellow]Before executing:[/yellow]")
        for p in preconditions:
            console.print(f"  [yellow]•[/yellow] {p}")
    
    print_next_step(
        action="Run the ExecutionPack with selected mode",
        command="asyncdev run-day execute",
        artifact_path=pack_path,
        root=root,
        hints=[
            "External mode: AI reads pack, manual execution",
            "Live mode: Direct API execution (requires DASHSCOPE_API_KEY)",
            "Mock mode: Test the flow without real execution",
            "Use --show-context for full planning context",
        ],
    )


@app.command()
def show(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show current RunState and pending tasks."""
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()
    root = Path.cwd() if path == Path("projects") else path

    if runstate is None:
        console.print("[yellow]No RunState found[/yellow]")
        return

    table = Table(title="Current RunState")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("project_id", runstate.get("project_id", "N/A"))
    table.add_row("feature_id", runstate.get("feature_id", "N/A"))
    table.add_row("current_phase", runstate.get("current_phase", "N/A"))
    table.add_row("active_task", runstate.get("active_task", "N/A"))
    table.add_row("task_queue", str(runstate.get("task_queue", [])))
    table.add_row("completed_outputs", str(len(runstate.get("completed_outputs", []))))
    table.add_row("blocked_items", str(len(runstate.get("blocked_items", []))))
    table.add_row("decisions_needed", str(len(runstate.get("decisions_needed", []))))

    console.print(table)

    runstate_path = store.project_path / "runstate.md"
    console.print(f"\n[dim]RunState: {get_relative_path(runstate_path, root)}[/dim]")
    console.print(f"[dim]root: {root}[/dim]")


@app.command()
def context(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show planning context for current state.
    
    Shows archive, decision, and blocker context without creating ExecutionPack.
    """
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()
    root = Path.cwd() if path == Path("projects") else path

    if runstate is None:
        console.print("[yellow]No RunState found[/yellow]")
        return

    planning_context = generate_aware_execution_pack(
        runstate=runstate,
        projects_path=path,
    )

    console.print(Panel(
        get_planning_context_summary(planning_context),
        title="Planning Context",
        border_style="blue",
    ))

    archive_ctx = planning_context.get("archive_context", {})
    if archive_ctx:
        console.print(f"\n[cyan]Archives Considered:[/cyan] {archive_ctx.get('recent_considered', 0)}")
        console.print(f"[cyan]Lessons Available:[/cyan] {archive_ctx.get('lessons_available', 0)}")
        console.print(f"[cyan]Patterns Available:[/cyan] {archive_ctx.get('patterns_available', 0)}")

    decision_ctx = planning_context.get("decision_constraints", {})
    if decision_ctx:
        console.print(f"\n[yellow]Pending Decisions:[/yellow] {decision_ctx.get('total_pending', 0)}")
        console.print(f"[yellow]Blocking Decisions:[/yellow] {decision_ctx.get('blocking_count', 0)}")

    blocker_ctx = planning_context.get("blocker_constraints", {})
    if blocker_ctx:
        console.print(f"\n[red]Blockers:[/red] {blocker_ctx.get('total_blocked', 0)}")
        console.print(f"[red]Classification:[/red] {blocker_ctx.get('classification', 'N/A')}")

    applicable_lessons = planning_context.get("applicable_lessons", [])
    if applicable_lessons:
        console.print(f"\n[green]Applicable Lessons:[/green]")
        for l in applicable_lessons[:5]:
            console.print(f"  [green]•[/green] {l.get('lesson', '')}")

    applicable_patterns = planning_context.get("applicable_patterns", [])
    if applicable_patterns:
        console.print(f"\n[blue]Applicable Patterns:[/blue]")
        for p in applicable_patterns[:5]:
            console.print(f"  [blue]•[/blue] {p.get('pattern', '')}")

    console.print(f"\n[dim]Use --show-context with plan-day create for full details[/dim]")


if __name__ == "__main__":
    app()