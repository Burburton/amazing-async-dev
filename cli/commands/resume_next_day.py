"""resume-next-day command - Continue from human decisions.

Feature 034: Enriched with prior-night decision pack alignment.
Feature 037: Integrated continuation semantics for checkpoint-based progression.
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
from runtime.recovery_classifier import (
    classify_recovery,
    check_resume_eligibility,
    get_recovery_guidance,
    RecoveryClassification,
    ResumeEligibility,
)
from runtime.continuation_evaluator import (
    evaluate_continuation,
    apply_continuation_decision_to_runstate,
    get_continuation_summary,
    should_auto_proceed_to_next_stage,
)
from runtime.continuation_types import ExecutionState
from cli.utils.output_formatter import print_next_step, print_success_panel
from cli.utils.path_formatter import get_relative_path

app = typer.Typer(help="Resume from human decisions, start next day loop")
console = Console()


def _load_latest_review_pack(project_path: Path) -> dict[str, Any] | None:
    """Load latest enriched review pack if available and not stale.
    
    Returns None if:
    - No reviews directory
    - No review files
    - Review pack is stale (date != today)
    - Review pack cannot be parsed
    """
    reviews_dir = project_path / "reviews"
    if not reviews_dir.exists():
        return None
    
    review_files = sorted(reviews_dir.glob("*-review.md"), reverse=True)
    if not review_files:
        return None
    
    latest_review = review_files[0]
    
    store = StateStore(project_path)
    review_date = latest_review.stem.replace("-review", "")
    review_pack = store.load_daily_review_pack(review_date)
    
    if review_pack is None:
        return None
    
    today = datetime.now().strftime("%Y-%m-%d")
    if review_pack.get("date") != today:
        review_pack["is_stale"] = True
        review_pack["stale_date"] = review_pack.get("date")
    
    return review_pack


def _extract_continuation_context(review_pack: dict[str, Any]) -> dict[str, Any]:
    """Extract continuation-relevant fields from review pack.
    
    Returns concise context for resume display.
    """
    context: dict[str, Any] = {
        "prior_review_timestamp": review_pack.get("date", ""),
        "prior_review_status": "found",
        "is_stale": review_pack.get("is_stale", False),
    }
    
    doctor_assessment = review_pack.get("doctor_assessment")
    if doctor_assessment:
        context["prior_doctor_status"] = doctor_assessment.get("doctor_status", "")
        context["prior_health_status"] = doctor_assessment.get("health_status", "")
        context["prior_initialization_mode"] = doctor_assessment.get("initialization_mode", "")
        context["prior_current_phase"] = doctor_assessment.get("current_phase", "")
        context["prior_recommended_action"] = doctor_assessment.get("recommended_action", "")
        context["prior_suggested_command"] = doctor_assessment.get("suggested_command", "")
        
        if doctor_assessment.get("recovery_summary"):
            context["prior_recovery_summary"] = doctor_assessment["recovery_summary"]
        
        if doctor_assessment.get("feedback_handoff"):
            context["prior_feedback_handoff"] = doctor_assessment["feedback_handoff"]
        
        if doctor_assessment.get("closeout_reminder"):
            context["prior_closeout_reminder"] = doctor_assessment["closeout_reminder"]
    
    if review_pack.get("tomorrow_plan"):
        context["prior_tomorrow_plan"] = review_pack.get("tomorrow_plan")
    
    return context


def _display_prior_context(context: dict[str, Any]) -> None:
    """Display prior-night context in resume output.
    
    Passive display - user chooses to act on the information.
    """
    if context.get("is_stale"):
        console.print(f"\n[dim yellow]Prior review from {context.get('stale_date')} may be outdated[/dim yellow]")
        return
    
    console.print("\n[bold cyan]Prior Night Context[/bold cyan]")
    
    console.print(f"  Review Date: {context.get('prior_review_timestamp', 'N/A')}")
    
    doctor_status = context.get("prior_doctor_status", "")
    if doctor_status:
        status_color = _get_status_color(doctor_status)
        console.print(f"  Doctor Status: [{status_color}]{doctor_status}[/{status_color}]")
    
    if context.get("prior_initialization_mode"):
        console.print(f"  Initialization: {context['prior_initialization_mode']}")
    
    if context.get("prior_current_phase"):
        console.print(f"  Prior Phase: {context['prior_current_phase']}")
    
    if context.get("prior_recommended_action"):
        console.print(f"\n  [bold]Prior Recommended Action:[/bold] {context['prior_recommended_action']}")
    
    if context.get("prior_suggested_command"):
        console.print(f"  [green]Prior Suggested: {context['prior_suggested_command']}[/green]")
    
    recovery = context.get("prior_recovery_summary")
    if recovery:
        console.print(f"\n  [bold yellow]Prior Recovery Guidance[/bold yellow]")
        console.print(f"  Likely Cause: {recovery.get('likely_cause', '')}")
        if recovery.get("recovery_steps"):
            console.print(f"  Steps: {len(recovery['recovery_steps'])} actions pending")
    
    feedback = context.get("prior_feedback_handoff")
    if feedback:
        console.print(f"\n  [bold magenta]Prior Feedback Handoff[/bold magenta]")
        console.print(f"  {feedback.get('suggestion', '')}")
    
    closeout = context.get("prior_closeout_reminder")
    if closeout:
        console.print(f"\n  [bold blue]Prior Closeout Reminder[/bold blue]")
        console.print(f"  {closeout.get('status', '')}")
        console.print(f"  Action: {closeout.get('action', '')}")


def _get_status_color(status: str) -> str:
    """Get color for doctor status."""
    if status == "HEALTHY":
        return "green"
    elif status == "ATTENTION_NEEDED":
        return "yellow"
    elif status == "BLOCKED":
        return "red"
    elif status == "COMPLETED_PENDING_CLOSEOUT":
        return "blue"
    return "white"


@app.command()
def continue_loop(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    decision: str = typer.Option("approve", help="Human decision: approve/revise/defer/redefine"),
    revise_choice: str = typer.Option(None, help="Choice if decision=revise"),
    dry_run: bool = typer.Option(False, help="Preview without saving"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
    force: bool = typer.Option(False, help="Force resume even if eligibility check fails"),
):
    """Process human decision and continue day loop."""
    project_path = path / project
    store = StateStore(project_path)
    logger = get_logger(project_path)
    runstate = store.load_runstate()
    root = Path.cwd() if path == Path("projects") else path

    if runstate is None:
        console.print("[red]No RunState found[/red]")
        logger.close()
        raise typer.Exit(1)

    review_pack = _load_latest_review_pack(project_path)
    if review_pack:
        context = _extract_continuation_context(review_pack)
        _display_prior_context(context)

    feature_id = runstate.get("feature_id", "")
    product_id = runstate.get("project_id", "")
    previous_phase = runstate.get("current_phase", "planning")

    logger.log_event(
        ExecutionEventType.RESUME_NEXT_DAY_STARTED,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"decision": decision},
    )

    eligibility = check_resume_eligibility(runstate)
    classification = classify_recovery(runstate)

    if eligibility not in (ResumeEligibility.ELIGIBLE, ResumeEligibility.NEEDS_DECISION) and not force:
        guidance = get_recovery_guidance(runstate)
        console.print(Panel("Resume Blocked", title="Recovery Check", border_style="red"))
        console.print(f"[yellow]Classification: {classification.value}[/yellow]")
        console.print(f"[yellow]Eligibility: {eligibility.value}[/yellow]")
        console.print(f"\n[bold]Recommended Action:[/bold] {guidance['recommended_action']}")
        console.print(f"[bold]Explanation:[/bold] {guidance['explanation']}")
        if guidance.get("warnings"):
            for w in guidance["warnings"]:
                console.print(f"[red]Warning: {w}[/red]")
        console.print("\n[cyan]Use --force to override, or follow recommended action above[/cyan]")
        logger.log_event(
            ExecutionEventType.RESUME_BLOCKED,
            feature_id=feature_id,
            product_id=product_id,
            event_data={"classification": classification.value, "eligibility": eligibility.value},
        )
        logger.close()
        raise typer.Exit(1)

    logger.log_event(
        ExecutionEventType.RESUME_VALIDATED,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"classification": classification.value, "force": force},
    )

    decisions_needed = runstate.get("decisions_needed", [])

    if not decisions_needed:
        console.print("[green]No pending decisions. Ready to continue.[/green]")
    else:
        console.print(f"[yellow]Processing decision: {decision}[/yellow]")

        if decision == "approve":
            runstate["decisions_needed"] = []
            console.print("[green]All decisions approved[/green]")
            logger.log_event(
                ExecutionEventType.DECISION_APPROVED,
                feature_id=feature_id,
                product_id=product_id,
                event_data={"decision_count": len(decisions_needed)},
            )

        elif decision == "revise":
            if not revise_choice:
                console.print("[red]Must specify --revise-choice for revise decision[/red]")
                logger.close()
                raise typer.Exit(1)
            console.print(f"[green]Decision revised to: {revise_choice}[/green]")
            runstate["decisions_needed"] = []
            logger.log_event(
                ExecutionEventType.DECISION_REVISED,
                feature_id=feature_id,
                product_id=product_id,
                event_data={"choice": revise_choice},
            )

        elif decision == "defer":
            console.print("[yellow]Decision deferred. Moving to alternative task.[/yellow]")
            logger.log_event(
                ExecutionEventType.DECISION_DEFERRED,
                feature_id=feature_id,
                product_id=product_id,
                event_data={"deferred_count": len(decisions_needed)},
            )

        elif decision == "redefine":
            console.print("[yellow]Decision redefined. Scope updated.[/yellow]")
            runstate["decisions_needed"] = []
            logger.log_event(
                ExecutionEventType.DECISION_ESCALATED,
                feature_id=feature_id,
                product_id=product_id,
                event_data={"action": "redefine"},
            )

    runstate["current_phase"] = "planning"
    runstate["last_action"] = f"Resumed with decision: {decision}"

    if runstate.get("task_queue"):
        next_task = runstate["task_queue"][0]
        runstate["next_recommended_action"] = f"Execute: {next_task}"
    else:
        runstate["next_recommended_action"] = "Add tasks to queue or complete feature"

    console.print(Panel(f"Resume Summary", title="resume-next-day", border_style="blue"))

    console.print(f"[bold]Current Phase:[/bold] {runstate['current_phase']}")
    console.print(f"[bold]Next Task:[/bold] {runstate.get('active_task', 'None')}")
    console.print(f"[bold]Queue:[/bold] {len(runstate.get('task_queue', []))} pending")
    console.print(f"[bold]Completed:[/bold] {len(runstate.get('completed_outputs', []))} outputs")
    
    continuity_context = runstate.get("continuity_context", {})
    if continuity_context:
        console.print("\n[bold cyan]Continuation Status[/bold cyan]")
        continuation_allowed = continuity_context.get("continuation_allowed", True)
        status_color = "green" if continuation_allowed else "red"
        console.print(f"  Continuation Allowed: [{status_color}]{continuation_allowed}[/{status_color}]")
        if continuity_context.get("next_intended_stage"):
            console.print(f"  Next Intended Stage: {continuity_context.get('next_intended_stage')}")
        if continuity_context.get("stop_reason"):
            console.print(f"  [yellow]Stop Reason: {continuity_context.get('stop_reason')}[/yellow]")

    if dry_run:
        console.print("[yellow]Dry run - not saving[/yellow]")
        logger.close()
        return

    store.save_runstate(runstate)

    logger.log_transition(
        from_phase=previous_phase,
        to_phase="planning",
        feature_id=feature_id,
        product_id=product_id,
        reason=f"Resumed with decision: {decision}",
    )
    logger.close()

    runstate_path = store.project_path / "runstate.md"

    print_success_panel(
        message=f"RunState updated with decision: {decision}",
        title="Resume Complete",
        paths=[
            {"label": "RunState", "path": str(runstate_path)},
        ],
        root=root,
    )

    print_next_step(
        action="Plan next execution cycle",
        command="asyncdev plan-day create",
        artifact_path=runstate_path,
        root=root,
    )


@app.command()
def status(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show current RunState status for resume."""
    project_path = path / project
    store = StateStore(project_path)
    runstate = store.load_runstate()

    if runstate is None:
        console.print("[yellow]No RunState found[/yellow]")
        return

    review_pack = _load_latest_review_pack(project_path)
    if review_pack:
        context = _extract_continuation_context(review_pack)
        console.print(Panel("Prior Review Summary", title="review-night alignment", border_style="cyan"))
        
        doctor_status = context.get("prior_doctor_status", "")
        if doctor_status:
            status_color = _get_status_color(doctor_status)
            console.print(f"Prior Doctor Status: [{status_color}]{doctor_status}[/{status_color}]")
        
        console.print(f"Prior Review Date: {context.get('prior_review_timestamp', 'N/A')}")
        
        if context.get("prior_recommended_action"):
            console.print(f"Prior Recommended: {context['prior_recommended_action']}")
        
        if context.get("prior_suggested_command"):
            console.print(f"[green]Prior Suggested: {context['prior_suggested_command']}[/green]")
        
        if context.get("is_stale"):
            console.print(f"\n[dim yellow]Note: Prior review may be outdated[/dim yellow]")

    console.print(Panel("Current State", title="resume-status"))

    console.print(f"Phase: {runstate.get('current_phase')}")
    console.print(f"Project: {runstate.get('project_id')}")
    console.print(f"Feature: {runstate.get('feature_id')}")

    classification = classify_recovery(runstate)
    eligibility = check_resume_eligibility(runstate)
    guidance = get_recovery_guidance(runstate)

    table = Table(title="Recovery Status")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Classification", classification.value)
    table.add_row("Eligibility", eligibility.value)
    table.add_row("Recommended", guidance["recommended_action"])
    console.print(table)

    if runstate.get("decisions_needed"):
        console.print("\n[bold yellow]Pending Decisions:[/bold yellow]")
        for d in runstate["decisions_needed"]:
            console.print(f"  - {d.get('decision', 'unknown')}")
            console.print(f"    Options: {d.get('options', [])}")

    if runstate.get("blocked_items"):
        console.print("\n[bold red]Blocked Items:[/bold red]")
        for b in runstate["blocked_items"]:
            console.print(f"  - {b.get('reason', 'unknown')}")

    console.print(f"\n[bold]Completed Outputs:[/bold] {len(runstate.get('completed_outputs', []))}")
    console.print(f"[bold]Task Queue:[/bold] {len(runstate.get('task_queue', []))} pending")
    console.print(f"[bold]Next Recommended:[/bold] {runstate.get('next_recommended_action', 'N/A')}")


if __name__ == "__main__":
    app()


@app.command()
def unblock(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    reason: str = typer.Option(None, help="Resolution note for blocker"),
    retry: bool = typer.Option(False, help="Retry the same task"),
    alternative: str = typer.Option(None, help="Alternative task to try"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Resume from blocked state to executing."""
    project_path = path / project
    store = StateStore(project_path)
    logger = get_logger(project_path)
    runstate = store.load_runstate()

    if runstate is None:
        console.print("[red]No RunState found[/red]")
        logger.close()
        raise typer.Exit(1)

    current_phase = runstate.get("current_phase")
    feature_id = runstate.get("feature_id", "")
    product_id = runstate.get("project_id", "")

    classification = classify_recovery(runstate)
    if classification != RecoveryClassification.BLOCKED:
        console.print(f"[yellow]Current classification: {classification.value}[/yellow]")
        guidance = get_recovery_guidance(runstate)
        console.print(f"[bold]Recommended:[/bold] {guidance['recommended_action']}")
        console.print("This command is only for blocked state.")
        logger.close()
        raise typer.Exit(1)

    blocked_items = runstate.get("blocked_items", [])

    logger.log_event(
        ExecutionEventType.BLOCKED_ENTERED,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"blocked_count": len(blocked_items), "phase": current_phase},
    )

    console.print(Panel("Unblock State", title="resume-next-day unblock", border_style="green"))

    console.print(f"[bold]Blocked Items:[/bold] {len(blocked_items)}")
    if blocked_items:
        for item in blocked_items[:3]:
            console.print(f"  - {item.get('reason', 'unknown')}")

    resolution_note = reason or "Manual unblock"
    console.print(f"\n[cyan]Resolution:[/cyan] {resolution_note}")

    runstate["current_phase"] = "planning"
    runstate["blocked_items"] = []
    runstate["last_action"] = f"Unblocked: {resolution_note}"

    logger.log_event(
        ExecutionEventType.BLOCKED_RESOLVED,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"resolution": resolution_note, "retry": retry, "alternative": alternative},
    )

    if retry:
        console.print("[green]Will retry same task[/green]")
        runstate["next_recommended_action"] = f"Retry: {runstate.get('active_task', 'unknown')}"
    elif alternative:
        console.print(f"[green]Will try alternative: {alternative}[/green]")
        runstate["active_task"] = alternative
        runstate["next_recommended_action"] = f"Execute: {alternative}"
    else:
        console.print("[yellow]Choose next action: --retry or --alternative[/yellow]")
        runstate["next_recommended_action"] = "Review blocker resolution, plan next task"

    store.save_runstate(runstate)

    logger.log_transition(
        from_phase="blocked",
        to_phase="planning",
        feature_id=feature_id,
        product_id=product_id,
        reason=f"Unblock: {resolution_note}",
    )
    logger.close()

    console.print("\n[green]Blocker resolved. Ready to continue.[/green]")
    console.print("Next: Run 'asyncdev plan-day' to create new ExecutionPack")


@app.command()
def handle_failed(
    project: str = typer.Option("demo-product-001", help="Project ID"),
    report: bool = typer.Option(False, help="Generate failure report"),
    escalate: bool = typer.Option(False, help="Escalate as decision needed"),
    abandon: bool = typer.Option(False, help="Abandon task and move to next"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Handle failed execution state."""
    project_path = path / project
    store = StateStore(project_path)
    logger = get_logger(project_path)
    runstate = store.load_runstate()

    if runstate is None:
        console.print("[red]No RunState found[/red]")
        logger.close()
        raise typer.Exit(1)

    feature_id = runstate.get("feature_id", "")
    product_id = runstate.get("project_id", "")
    previous_phase = runstate.get("current_phase", "executing")

    console.print(Panel("Handle Failed State", title="resume-next-day handle-failed", border_style="yellow"))

    console.print("[yellow]Failed execution detected[/yellow]")
    console.print("Converting to blocked state for human intervention...")

    logger.log_event(
        ExecutionEventType.FAILED_ENTERED,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"active_task": runstate.get("active_task", "")},
    )

    if escalate:
        decision_item = {
            "decision": f"Task {runstate.get('active_task', 'unknown')} failed",
            "options": ["retry", "alternative approach", "abandon"],
            "recommendation": "Retry with adjusted parameters",
            "impact": "Feature progress blocked",
            "urgency": "high",
        }
        runstate["decisions_needed"] = [decision_item]
        runstate["current_phase"] = "reviewing"
        console.print("[cyan]Escalated to decision needed[/cyan]")
        logger.log_event(
            ExecutionEventType.DECISION_ESCALATED,
            feature_id=feature_id,
            product_id=product_id,
            event_data={"action": "escalate", "decision": decision_item["decision"]},
        )

    elif abandon:
        runstate["blocked_items"] = []
        runstate["current_phase"] = "planning"
        if runstate.get("task_queue"):
            runstate["active_task"] = runstate["task_queue"][0]
            runstate["task_queue"] = runstate["task_queue"][1:]
        console.print("[green]Task abandoned. Moving to next[/green]")
        logger.log_event(
            ExecutionEventType.FAILED_HANDLED,
            feature_id=feature_id,
            product_id=product_id,
            event_data={"action": "abandon"},
        )

    else:
        runstate["current_phase"] = "blocked"
        runstate["blocked_items"] = [{
            "reason": "Execution failed",
            "resolution": "Needs human intervention",
            "options": ["Retry", "Change approach", "Abandon"],
        }]
        console.print("[yellow]State set to blocked[/yellow]")
        console.print("Use 'asyncdev resume-next-day unblock' to resolve")
        logger.log_event(
            ExecutionEventType.FAILED_HANDLED,
            feature_id=feature_id,
            product_id=product_id,
            event_data={"action": "blocked"},
        )

    runstate["last_action"] = f"Handled failed state: {escalate or abandon or 'blocked'}"

    store.save_runstate(runstate)

    logger.log_transition(
        from_phase=previous_phase,
        to_phase=runstate["current_phase"],
        feature_id=feature_id,
        product_id=product_id,
        reason="Failed state handled",
    )
    logger.close()

    console.print("\nNext action depends on choice:")
    if escalate:
        console.print("  Run 'asyncdev review-night' to see decision options")
    elif abandon:
        console.print("  Run 'asyncdev plan-day' to plan next task")
    else:
        console.print("  Run 'asyncdev resume-next-day unblock' to resolve blocker")