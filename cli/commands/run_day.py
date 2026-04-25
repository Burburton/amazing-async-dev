"""run-day command - Execute today's task with selected engine mode.

Modes:
- external (default): Generate ExecutionPack for external tools
- live: Direct API execution via BailianLLMAdapter
- mock: Testing and demonstration

Feature 036: Enhanced with planning intent alignment and drift warnings.
Feature 054: Auto email decision trigger integration.
Feature 060: System-owned frontend verification orchestration.
Feature 061: External execution closeout orchestration (primary path).
Hardening: Added --project parameter for canonical loop consistency.
"""

from pathlib import Path
from typing import Any
import subprocess
import typer
from rich.console import Console
from rich.panel import Panel

from runtime.state_store import StateStore
from runtime.engines.factory import get_engine, get_available_modes
from runtime.execution_event_types import ExecutionEventType
from runtime.execution_logger import get_logger
from runtime.auto_email_trigger import check_and_trigger, TriggerSource
from runtime.browser_verification_orchestrator import (
    BrowserVerificationOrchestrator,
    OrchestrationResult,
    OrchestrationTerminalState,
    orchestrate_for_run_day,
)
from runtime.verification_gate import requires_browser_verification
from runtime.external_execution_closeout import (
    orchestrate_external_closeout,
    CloseoutState,
    CloseoutTerminalClassification,
    CloseoutResult,
)
from cli.utils.output_formatter import print_next_step, print_success_panel
from cli.utils.path_formatter import get_relative_path

app = typer.Typer(help="Run today's execution task")
console = Console()


def _auto_trigger_if_needed(project_path: Path, trigger_source: TriggerSource) -> None:
    try:
        result = check_and_trigger(project_path, trigger_source)
        if result.triggered:
            console.print(f"\n[green]Auto-triggered decision email: {result.request_id}[/green]")
        elif result.skipped_reason:
            console.print(f"\n[dim]Auto-trigger skipped: {result.skipped_reason}[/dim]")
        elif result.error_message:
            console.print(f"\n[yellow]Auto-trigger failed: {result.error_message}[/yellow]")
    except Exception as e:
        console.print(f"\n[yellow]Auto-trigger error: {e}[/yellow]")


def _run_frontend_verification(
    project_path: Path,
    execution_pack: dict[str, Any],
    product_id: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    verification_type = execution_pack.get("verification_type", "backend_only")
    
    if not requires_browser_verification(verification_type):
        return result
    
    console.print(f"\n[cyan]Frontend verification required (type: {verification_type})[/cyan]")
    
    try:
        orchestration_result = orchestrate_for_run_day(
            project_path=project_path,
            execution_pack=execution_pack,
            project_id=product_id,
        )
        
        result["orchestration_terminal_state"] = orchestration_result.terminal_state.value
        result["browser_verification"] = orchestration_result.to_dict()["browser_verification"]
        
        if orchestration_result.terminal_state == OrchestrationTerminalState.SUCCESS:
            console.print(f"[green]Frontend verification completed successfully[/green]")
        elif orchestration_result.terminal_state == OrchestrationTerminalState.EXCEPTION_ACCEPTED:
            console.print(f"[yellow]Frontend verification skipped: {orchestration_result.exception_details}[/yellow]")
        else:
            console.print(f"[red]Frontend verification failed: {orchestration_result.terminal_state.value}[/red]")
            if result.get("status") == "success":
                result["status"] = "partial"
        
    except Exception as e:
        console.print(f"[red]Frontend verification orchestration error: {e}[/red]")
        result["browser_verification"] = {
            "executed": False,
            "exception_reason": "environment_blocked",
            "exception_details": str(e),
        }
        result["orchestration_terminal_state"] = OrchestrationTerminalState.EXCEPTION_ACCEPTED.value
    
    return result


PLANNING_MODE_INTENT = {
    "continue_work": "Normal bounded execution toward today's target",
    "recover_and_continue": "Recovery-oriented execution - address recovery concerns first",
    "verification_first": "Verification-first execution - complete verification before expansion",
    "closeout_first": "Closeout-first execution - complete closeout before new work",
    "blocked_waiting_for_decision": "Blocked context - decisions required before forward execution",
}


def _extract_execution_intent(execution_pack: dict[str, Any]) -> dict[str, Any]:
    """Extract planning intent from ExecutionPack."""
    intent: dict[str, Any] = {
        "has_planning_context": False,
        "planning_mode": execution_pack.get("planning_mode", ""),
        "bounded_target": execution_pack.get("goal", ""),
        "prior_doctor_status": execution_pack.get("prior_doctor_status", ""),
        "prior_recommendation": execution_pack.get("prior_recommended_next_action", ""),
    }
    
    if execution_pack.get("planning_mode"):
        intent["has_planning_context"] = True
        intent["intent_summary"] = PLANNING_MODE_INTENT.get(
            execution_pack.get("planning_mode", ""),
            "Execution following daily plan"
        )
    
    if execution_pack.get("plan_recovery_flag"):
        intent["recovery_flag"] = True
    
    if execution_pack.get("plan_closeout_flag"):
        intent["closeout_flag"] = True
    
    if execution_pack.get("safe_to_execute") is False:
        intent["blocked_flag"] = True
    
    return intent


def _display_execution_intent(intent: dict[str, Any]) -> None:
    """Display execution intent summary before execution."""
    if not intent.get("has_planning_context"):
        return
    
    console.print("\n[bold cyan]Execution Intent[/bold cyan]")
    
    planning_mode = intent.get("planning_mode", "")
    if planning_mode:
        console.print(f"  Planning Mode: [green]{planning_mode}[/green]")
    
    if intent.get("intent_summary"):
        console.print(f"  Intent: {intent.get('intent_summary')}")
    
    bounded_target = intent.get("bounded_target", "")
    if bounded_target:
        console.print(f"  Bounded Target: {bounded_target}")
    
    prior_status = intent.get("prior_doctor_status", "")
    if prior_status:
        console.print(f"  Prior Doctor Status: {prior_status}")
    
    prior_rec = intent.get("prior_recommendation", "")
    if prior_rec:
        console.print(f"  Prior Recommendation: {prior_rec}")
    
    alignment_status = "aligned"
    if intent.get("blocked_flag"):
        alignment_status = "blocked-context"
        console.print(f"\n  [bold red]Alignment Status: {alignment_status}[/bold red]")
    elif intent.get("recovery_flag") or intent.get("closeout_flag"):
        alignment_status = "special-mode"
        console.print(f"\n  [bold yellow]Alignment Status: {alignment_status}[/bold yellow]")
    else:
        console.print(f"\n  [bold green]Alignment Status: {alignment_status}[/bold green]")


def _check_drift_warnings(intent: dict[str, Any], execution_pack: dict[str, Any]) -> list[str]:
    """Check for potential drift between planning mode and execution."""
    warnings = []
    
    planning_mode = intent.get("planning_mode", "")
    
    if planning_mode == "blocked_waiting_for_decision":
        warnings.append("Workspace is blocked - forward execution may not be appropriate")
        warnings.append("Consider resolving pending decisions before proceeding")
    
    if planning_mode == "closeout_first":
        task_scope = execution_pack.get("task_scope", [])
        for task in task_scope:
            task_lower = task.lower()
            if any(word in task_lower for word in ["implement", "add", "create", "build", "new"]):
                if "closeout" not in task_lower and "archive" not in task_lower:
                    warnings.append("Closeout-first mode: new expansion work detected before closeout")
    
    if planning_mode == "verification_first":
        task_scope = execution_pack.get("task_scope", [])
        for task in task_scope:
            task_lower = task.lower()
            if "verify" not in task_lower and "check" not in task_lower and "test" not in task_lower:
                warnings.append("Verification-first mode: non-verification work may be premature")
    
    if planning_mode == "recover_and_continue":
        task_scope = execution_pack.get("task_scope", [])
        has_recovery_task = False
        for task in task_scope:
            task_lower = task.lower()
            if any(word in task_lower for word in ["fix", "resolve", "recover", "repair", "unblock"]):
                has_recovery_task = True
        if not has_recovery_task and not intent.get("recovery_flag"):
            warnings.append("Recovery-first mode: ensure recovery concerns are addressed first")
    
    if intent.get("prior_doctor_status") == "BLOCKED" and not intent.get("blocked_flag"):
        warnings.append("Prior doctor status was BLOCKED - verify blockers are resolved")
    
    return warnings


def _display_drift_warnings(warnings: list[str]) -> None:
    """Display drift warnings if present."""
    if not warnings:
        return
    
    console.print("\n[bold yellow]Execution Alignment Notes[/bold yellow]")
    for warning in warnings:
        console.print(f"  [yellow]•[/yellow] {warning}")
    
    console.print("\n  [dim]Execution continues under operator control[/dim]")


@app.command()
def execute(
    project: str = typer.Option(None, help="Project ID to execute"),
    execution_id: str = typer.Option(None, help="Execution ID to run"),
    mode: str = typer.Option(
        "external",
        help="Execution mode: external (default), live, mock"
    ),
    trigger: bool = typer.Option(
        False,
        help="Trigger external tool after preparing pack (external mode only)"
    ),
    dry_run: bool = typer.Option(False, help="Preview without saving"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Execute today's bounded task with selected engine."""
    if project:
        project_path = path / project
        if not project_path.exists():
            console.print(f"[red]Project not found: {project}[/red]")
            console.print(f"[yellow]Path checked: {project_path}[/yellow]")
            raise typer.Exit(1)
        store = StateStore(project_path)
    else:
        store = StateStore()
    
    logger = get_logger(store.project_path)
    
    runstate = store.load_runstate()
    feature_id = runstate.get("feature_id", "") if runstate else ""
    product_id = runstate.get("project_id", "") if runstate else ""

    logger.log_event(
        ExecutionEventType.RUN_DAY_STARTED,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"execution_id": execution_id, "mode": mode, "project": project},
    )
    
    available = get_available_modes()
    if not available.get(mode, False):
        console.print(f"[red]Mode '{mode}' is not available[/red]")
        console.print(f"Available modes: {list(available.keys())}")
        logger.close()
        raise typer.Exit(1)

    engine = get_engine(mode, project_path=store.project_path)
    console.print(Panel(
        f"Mode: {mode}\nEngine: {engine.get_mode_name()}",
        title="Run-Day",
        border_style="blue"
    ))

    if mode == "external":
        return _run_external_mode(execution_id, engine, trigger, dry_run, logger, feature_id, product_id, store)
    elif mode == "live":
        return _run_live_mode(execution_id, engine, dry_run, logger, feature_id, product_id, store)
    elif mode == "mock":
        return _run_mock_mode(execution_id, engine, dry_run, logger, feature_id, product_id, store)


def _run_external_mode(
    execution_id: str | None,
    engine,
    trigger: bool,
    dry_run: bool,
    logger,
    feature_id: str,
    product_id: str,
    store: StateStore,
) -> None:
    """Execute in external tool mode."""
    root = Path.cwd()
    
    if execution_id is None:
        packs = list(store.execution_packs_path.glob("exec-*.md"))
        if not packs:
            console.print("[red]No ExecutionPack found. Run 'asyncdev plan-day' first.[/red]")
            logger.close()
            raise typer.Exit(1)
        execution_id = packs[-1].stem

    execution_pack = store.load_execution_pack(execution_id)
    if execution_pack is None:
        console.print(f"[red]ExecutionPack not found: {execution_id}[/red]")
        logger.close()
        raise typer.Exit(1)
    
    intent = _extract_execution_intent(execution_pack)
    _display_execution_intent(intent)
    warnings = _check_drift_warnings(intent, execution_pack)
    _display_drift_warnings(warnings)

    engine.output_dir = store.execution_packs_path

    prep_result = engine.prepare(execution_pack)

    logger.log_event(
        ExecutionEventType.EXTERNAL_EXECUTION_TRIGGERED,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"execution_id": execution_id, "yaml_path": str(prep_result.get("yaml_path", ""))},
    )

    yaml_path = Path(prep_result.get("yaml_path", ""))
    md_path = Path(prep_result.get("md_path", ""))

    print_success_panel(
        message="ExecutionPack prepared for external execution",
        title="Run-Day Ready",
        paths=[
            {"label": "YAML Pack", "path": str(yaml_path)},
            {"label": "Markdown Pack", "path": str(md_path)},
        ],
        root=root,
    )

    console.print(f"\n[cyan]{prep_result['instructions']}[/cyan]")

    if trigger:
        _trigger_external_tool(prep_result['md_path'])
        logger.log_event(
            ExecutionEventType.RUN_DAY_DISPATCHED,
            feature_id=feature_id,
            product_id=product_id,
            event_data={"execution_id": execution_id, "triggered": True},
        )

        if not dry_run:
            console.print("\n[bold cyan]Entering External Closeout Phase (Feature 061)[/bold cyan]")
            console.print(f"  Waiting for execution result (timeout: 120s)...")
            
            closeout_result = orchestrate_external_closeout(
                project_path=store.project_path,
                execution_id=execution_id,
                execution_pack=execution_pack,
                project_id=product_id,
            )
            
            _handle_closeout_result(
                closeout_result,
                execution_id,
                feature_id,
                product_id,
                logger,
                store,
                root,
            )
            return

    if dry_run:
        console.print("[yellow]Dry run - external mode does not modify state[/yellow]")
        logger.close()
        return

    print_next_step(
        action="Execute the ExecutionPack with external tool",
        command="asyncdev resume-next-day",
        artifact_path=md_path,
        root=root,
        hints=["After execution, run resume-next-day to continue"],
    )


def _check_acceptance_readiness_and_trigger(
    project_path: Path,
    execution_id: str,
    feature_id: str,
    logger,
    console: Console,
) -> None:
    """Check acceptance readiness after closeout success (Feature 077 AC-006)."""
    from runtime.acceptance_readiness import (
        check_acceptance_readiness,
        AcceptanceReadiness,
        AcceptanceTriggerPolicyMode,
    )
    from runtime.acceptance_runner import run_acceptance_from_execution
    from runtime.reacceptance_loop import get_or_create_attempt_history, save_attempt_history
    
    console.print("\n[bold cyan]Checking acceptance readiness...[/bold cyan]")
    
    readiness_result = check_acceptance_readiness(
        project_path,
        execution_id,
        AcceptanceTriggerPolicyMode.FEATURE_COMPLETION_ONLY,
    )
    
    console.print(f"  Readiness: {readiness_result.readiness.value}")
    
    for prereq in readiness_result.prerequisites_checked:
        status_icon = "[green]✓[/green]" if prereq.satisfied else "[yellow]○[/yellow]"
        console.print(f"    {status_icon} {prereq.name}")
    
    if readiness_result.readiness == AcceptanceReadiness.READY:
        console.print("\n[green]Acceptance ready - triggering automatically[/green]")
        
        logger.log_event(
            ExecutionEventType.RUN_DAY_STARTED,
            feature_id=feature_id,
            event_data={"acceptance_triggered": True, "execution_id": execution_id},
        )
        
        result = run_acceptance_from_execution(project_path, execution_id)
        
        if result:
            history = get_or_create_attempt_history(project_path, feature_id, execution_id)
            history.add_attempt(result)
            save_attempt_history(project_path, history)
            
            console.print(f"\n[bold]Acceptance Result: {result.terminal_state.value}[/bold]")
            console.print(f"  Accepted: {len(result.accepted_criteria)}")
            console.print(f"  Failed: {len(result.failed_criteria)}")
            
            if result.terminal_state.value in ["accepted", "conditional"]:
                console.print("[green]Feature ready for completion[/green]")
            else:
                console.print("[yellow]Acceptance requires attention[/yellow]")
                console.print("[cyan]Run 'asyncdev acceptance recovery' for details[/cyan]")
    elif readiness_result.readiness == AcceptanceReadiness.NO_CRITERIA:
        console.print("\n[yellow]No acceptance criteria defined - skipping acceptance[/yellow]")
    elif readiness_result.readiness == AcceptanceReadiness.POLICY_SKIPPED:
        console.print("\n[yellow]Policy prevents auto-trigger - manual acceptance available[/yellow]")
        console.print("[cyan]Run 'asyncdev acceptance run' to trigger manually[/cyan]")
    else:
        console.print(f"\n[yellow]Acceptance not ready: {readiness_result.readiness.value}[/yellow]")
        console.print("[cyan]Run 'asyncdev acceptance status' for details[/cyan]")


def _handle_closeout_result(
    closeout_result: CloseoutResult,
    execution_id: str,
    feature_id: str,
    product_id: str,
    logger,
    store: StateStore,
    root: Path,
) -> None:
    """Handle closeout result and update state (Feature 061 AC-002)."""
    console.print(f"\n[bold]Closeout Status:[/bold] {closeout_result.closeout_state.value}")
    console.print(f"  Poll Attempts: {closeout_result.poll_attempts}")
    console.print(f"  Elapsed: {closeout_result.elapsed_seconds:.1f}s")
    
    if closeout_result.execution_result_detected:
        console.print(f"  Result Detected: [green]Yes[/green]")
    else:
        console.print(f"  Result Detected: [red]No[/red]")
    
    if closeout_result.verification_required:
        console.print(f"  Verification Required: [yellow]Yes[/yellow]")
        console.print(f"  Verification Completed: {closeout_result.verification_completed}")
        console.print(f"  Verification Terminal: {closeout_result.verification_terminal_state or 'N/A'}")
    
    terminal_classification = closeout_result.terminal_classification
    if terminal_classification:
        if terminal_classification == CloseoutTerminalClassification.SUCCESS:
            console.print(f"\n  [bold green]Terminal Classification: {terminal_classification.value}[/bold green]")
        elif terminal_classification == CloseoutTerminalClassification.RECOVERY_REQUIRED:
            console.print(f"\n  [bold yellow]Terminal Classification: {terminal_classification.value}[/bold yellow]")
            if closeout_result.recovery_reason:
                console.print(f"  [yellow]Reason: {closeout_result.recovery_reason}[/yellow]")
        else:
            console.print(f"\n  [bold red]Terminal Classification: {terminal_classification.value}[/bold red]")
    
    logger.log_event(
        ExecutionEventType.EXTERNAL_EXECUTION_CLOSEOUT,
        feature_id=feature_id,
        product_id=product_id,
        event_data={
            "execution_id": execution_id,
            "closeout_state": closeout_result.closeout_state.value,
            "terminal_classification": terminal_classification.value if terminal_classification else None,
            "poll_attempts": closeout_result.poll_attempts,
            "elapsed_seconds": closeout_result.elapsed_seconds,
        },
    )
    
    execution_result = store.load_execution_result(execution_id) or {}
    execution_result["closeout_state"] = closeout_result.closeout_state.value
    execution_result["closeout_terminal_state"] = terminal_classification.value if terminal_classification else None
    execution_result["closeout_result"] = closeout_result.to_dict()
    
    if closeout_result.execution_result_detected and closeout_result.execution_result_valid:
        if terminal_classification == CloseoutTerminalClassification.SUCCESS:
            execution_result["status"] = "success"
        elif terminal_classification == CloseoutTerminalClassification.RECOVERY_REQUIRED:
            execution_result["status"] = "partial"
        else:
            execution_result["status"] = "failed"
    else:
        execution_result["status"] = "failed"
        execution_result["blocked_reasons"] = [{
            "reason": closeout_result.recovery_reason or "External execution did not produce valid result",
            "impact": "Closeout incomplete",
        }]
    
    store.save_execution_result(execution_result)
    
    runstate = store.load_runstate() or {}
    previous_phase = runstate.get("current_phase", "executing")
    
    if terminal_classification == CloseoutTerminalClassification.SUCCESS:
        runstate["current_phase"] = "reviewing"
        runstate["last_action"] = f"External closeout completed: {execution_id}"
        runstate["next_recommended_action"] = "Generate DailyReviewPack"
        
        _check_acceptance_readiness_and_trigger(
            store.project_path,
            execution_id,
            feature_id,
            logger,
            console,
        )
    elif terminal_classification == CloseoutTerminalClassification.RECOVERY_REQUIRED:
        runstate["current_phase"] = "reviewing"
        runstate["last_action"] = f"External closeout recovery needed: {execution_id}"
        runstate["next_recommended_action"] = "Run resume-next-day to recover closeout"
        runstate["blocked_items"] = [{
            "reason": closeout_result.recovery_reason or "Closeout incomplete",
            "resolution": "Resume closeout via resume-next-day",
        }]
    else:
        runstate["current_phase"] = "blocked"
        runstate["last_action"] = f"External closeout failed: {execution_id}"
        runstate["blocked_items"] = [{
            "reason": f"Closeout terminal: {terminal_classification.value if terminal_classification else 'unknown'}",
            "resolution": "Manual intervention required",
        }]
    
    store.save_runstate(runstate)
    
    if runstate.get("decisions_needed") or runstate.get("blocked_items"):
        _auto_trigger_if_needed(store.project_path, TriggerSource.EXTERNAL_TOOL_AUTO)
    
    logger.log_transition(
        from_phase=previous_phase,
        to_phase=runstate["current_phase"],
        feature_id=feature_id,
        product_id=product_id,
        reason=f"External closeout: {closeout_result.closeout_state.value}",
    )
    logger.close()
    
    result_path = store.execution_results_path / f"{execution_id}.md"
    
    if terminal_classification == CloseoutTerminalClassification.SUCCESS:
        print_success_panel(
            message=f"External closeout completed successfully",
            title="Closeout Complete",
            paths=[
                {"label": "ExecutionResult", "path": str(result_path)},
                {"label": "RunState", "path": str(store.project_path / "runstate.md")},
            ],
            root=root,
        )
        print_next_step(
            action="Generate DailyReviewPack for human review",
            command="asyncdev review-night generate",
            artifact_path=result_path,
            root=root,
        )
    elif terminal_classification == CloseoutTerminalClassification.RECOVERY_REQUIRED:
        print_success_panel(
            message=f"External closeout recovery needed",
            title="Closeout Partial",
            paths=[
                {"label": "ExecutionResult", "path": str(result_path)},
            ],
            root=root,
        )
        print_next_step(
            action="Run resume-next-day to complete closeout",
            command="asyncdev resume-next-day continue-loop",
            artifact_path=result_path,
            root=root,
            hints=["Closeout interrupted or verification incomplete"],
        )
    else:
        console.print(f"\n[red]External closeout failed. Check ExecutionResult for details.[/red]")
        print_next_step(
            action="Review failure and decide next action",
            command="asyncdev resume-next-day status",
            artifact_path=result_path,
            root=root,
        )


def _run_live_mode(
    execution_id: str | None,
    engine,
    dry_run: bool,
    logger,
    feature_id: str,
    product_id: str,
    store: StateStore,
) -> None:
    """Execute in live API mode."""
    root = Path.cwd()
    
    runstate = store.load_runstate()
    if runstate is None:
        console.print("[red]No RunState found. Run 'asyncdev plan-day' first.[/red]")
        logger.close()
        raise typer.Exit(1)

    if execution_id is None:
        packs = list(store.execution_packs_path.glob("exec-*.md"))
        if not packs:
            console.print("[red]No ExecutionPack found. Run 'asyncdev plan-day' first.[/red]")
            logger.close()
            raise typer.Exit(1)
        execution_id = packs[-1].stem

    execution_pack = store.load_execution_pack(execution_id)
    if execution_pack is None:
        console.print(f"[red]ExecutionPack not found: {execution_id}[/red]")
        logger.close()
        raise typer.Exit(1)
    
    intent = _extract_execution_intent(execution_pack)
    _display_execution_intent(intent)
    warnings = _check_drift_warnings(intent, execution_pack)
    _display_drift_warnings(warnings)

    prep = engine.prepare(execution_pack)
    if prep.get("status") != "ready":
        console.print(f"[red]ExecutionPack invalid: missing {prep.get('missing_fields', [])}[/red]")
        logger.close()
        raise typer.Exit(1)

    console.print(f"\n[cyan]Executing via API (model: {prep.get('model', 'unknown')})...[/cyan]")

    result = engine.run(execution_pack)
    
    result = _run_frontend_verification(
        store.project_path,
        execution_pack,
        product_id,
        result,
    )

    logger.log_event(
        ExecutionEventType.EXECUTION_RESULT_COLLECTED,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"execution_id": execution_id, "status": result.get("status", "unknown")},
    )

    console.print("\n[green]ExecutionResult:[/green]")
    console.print(f"  Status: {result['status']}")
    console.print(f"  Completed: {result['completed_items']}")
    console.print(f"  Artifacts: {len(result['artifacts_created'])}")

    if dry_run:
        console.print("[yellow]Dry run - not saving[/yellow]")
        logger.close()
        return

    store.save_execution_result(result)
    previous_phase = runstate.get("current_phase", "executing")
    runstate["current_phase"] = "reviewing"
    store.save_runstate(runstate)

    logger.log_transition(
        from_phase=previous_phase,
        to_phase="reviewing",
        feature_id=feature_id,
        product_id=product_id,
        reason="Live execution completed",
    )
    logger.log_event(
        ExecutionEventType.NORMAL_STOP,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"phase": "reviewing"},
    )
    engine.close()
    
    if result.get("decisions_required") or result.get("blocked_reasons"):
        _auto_trigger_if_needed(store.project_path, TriggerSource.RUN_DAY_AUTO)
    
    logger.close()

    result_path = store.execution_results_path / f"{execution_id}.md"

    print_success_panel(
        message=f"Live execution completed: {result['status']}",
        title="Run-Day Complete",
        paths=[
            {"label": "ExecutionResult", "path": str(result_path)},
            {"label": "RunState", "path": str(store.project_path / "runstate.md")},
        ],
        root=root,
    )

    print_next_step(
        action="Generate DailyReviewPack for human review",
        command="asyncdev review-night generate",
        artifact_path=result_path,
        root=root,
    )


def _run_mock_mode(
    execution_id: str | None,
    engine,
    dry_run: bool,
    logger,
    feature_id: str,
    product_id: str,
    store: StateStore,
) -> None:
    """Execute in mock mode for testing."""
    root = Path.cwd()
    
    runstate = store.load_runstate()
    if runstate is None:
        console.print("[yellow]Creating minimal RunState for test[/yellow]")
        runstate = {
            "project_id": product_id or "demo-product-001",
            "feature_id": feature_id or "001-test",
            "current_phase": "executing",
            "active_task": "test-task",
            "task_queue": [],
            "completed_outputs": [],
            "open_questions": [],
            "blocked_items": [],
            "decisions_needed": [],
            "last_action": "Test setup",
            "next_recommended_action": "Run mock",
            "updated_at": "",
        }
        store.save_runstate(runstate)
        feature_id = feature_id or "001-test"
        product_id = product_id or "demo-product-001"

    if execution_id is None:
        packs = list(store.execution_packs_path.glob("exec-*.md"))
        if packs:
            execution_id = packs[-1].stem

    execution_pack = None
    if execution_id and execution_id != "exec-test-001":
        execution_pack = store.load_execution_pack(execution_id)
    
    if execution_pack:
        intent = _extract_execution_intent(execution_pack)
        _display_execution_intent(intent)
        warnings = _check_drift_warnings(intent, execution_pack)
        _display_drift_warnings(warnings)
        test_pack = execution_pack
    else:
        execution_id = "exec-test-001"
        test_pack = {
            "execution_id": execution_id,
            "feature_id": "001-test",
            "task_id": "test-task",
            "goal": "Test execution flow",
            "task_scope": ["test"],
            "deliverables": [{"item": "test-output", "path": "test.md", "type": "file"}],
            "verification_steps": ["Check output"],
            "stop_conditions": ["Complete"],
        }

    result = engine.run(test_pack)
    
    if execution_pack:
        result = _run_frontend_verification(
            store.project_path,
            execution_pack,
            product_id,
            result,
        )

    logger.log_event(
        ExecutionEventType.EXECUTION_RESULT_COLLECTED,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"execution_id": execution_id, "status": result.get("status", "mock"), "mode": "mock"},
    )

    console.print("\n[green]Mock ExecutionResult:[/green]")
    console.print(f"  Status: {result['status']}")
    console.print(f"  Completed: {result['completed_items']}")

    if dry_run:
        console.print("[yellow]Dry run - not saving[/yellow]")
        logger.close()
        return

    store.save_execution_result(result)
    previous_phase = runstate.get("current_phase", "executing")
    runstate["current_phase"] = "reviewing"
    store.save_runstate(runstate)
    
    _auto_trigger_if_needed(store.project_path, TriggerSource.RUN_DAY_AUTO)

    logger.log_transition(
        from_phase=previous_phase,
        to_phase="reviewing",
        feature_id=feature_id,
        product_id=product_id,
        reason="Mock execution completed",
    )
    logger.log_event(
        ExecutionEventType.NORMAL_STOP,
        feature_id=feature_id,
        product_id=product_id,
        event_data={"phase": "reviewing", "mode": "mock"},
    )
    logger.close()

    result_path = store.execution_results_path / f"{execution_id}.md"

    print_success_panel(
        message=f"Mock execution completed: {result['status']}",
        title="Run-Day Mock Complete",
        paths=[
            {"label": "ExecutionResult", "path": str(result_path)},
        ],
        root=root,
    )

    print_next_step(
        action="Generate DailyReviewPack for review",
        command="asyncdev review-night generate",
    )


def _trigger_external_tool(pack_path: str) -> None:
    """Trigger OpenCode to execute the ExecutionPack.

    Uses subprocess to call opencode CLI.
    """
    console.print(f"\n[cyan]Triggering OpenCode...[/cyan]")

    try:
        result = subprocess.run(
            ["opencode", "--file", pack_path],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            console.print("[green]OpenCode triggered successfully[/green]")
            console.print("OpenCode will execute the ExecutionPack.")
            console.print("After completion, run: asyncdev resume-next-day")
        else:
            console.print(f"[red]OpenCode failed: {result.stderr}[/red]")
            console.print("Manual trigger: Open the ExecutionPack.md in your editor")

    except FileNotFoundError:
        console.print("[yellow]OpenCode CLI not found[/yellow]")
        console.print("Manual trigger: Open the ExecutionPack.md in your editor")
    except subprocess.TimeoutExpired:
        console.print("[yellow]OpenCode trigger timed out[/yellow]")
        console.print("Check if OpenCode is running")


@app.command()
def mock_quick(
    project: str = typer.Option(None, help="Project ID to execute"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Quick mock execution for testing the full flow."""
    execute(project=project, mode="mock", execution_id="exec-test-001", trigger=False, dry_run=False, path=path)


@app.command()
def modes():
    """Show available execution modes and their status."""
    available = get_available_modes()

    console.print(Panel("Execution Modes", border_style="green"))

    for mode, is_avail in available.items():
        status = "[green]available[/green]" if is_avail else "[red]not available[/red]"
        console.print(f"  {mode}: {status}")

    console.print("\n[cyan]Usage:[/cyan]")
    console.print("  asyncdev run-day --mode external  (default)")
    console.print("  asyncdev run-day --mode live")
    console.print("  asyncdev run-day --mode mock")
    console.print("  asyncdev run-day --mode external --trigger")


if __name__ == "__main__":
    app()