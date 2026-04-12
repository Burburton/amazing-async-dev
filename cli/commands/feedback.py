"""Workflow feedback commands - record, triage, list, and inspect workflow issues.

Feature 019a: Workflow Feedback Capture
Feature 019b: Workflow Feedback Triage

Commands:
    asyncdev feedback record              - Record a workflow feedback item
    asyncdev feedback triage              - Triage a feedback item
    asyncdev feedback list                - List workflow feedback items
    asyncdev feedback show --feedback-id  - Show specific feedback details
    asyncdev feedback update              - Update feedback resolution/status
    asyncdev feedback summary             - Show summary of follow-up needed
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runtime.workflow_feedback_store import WorkflowFeedbackStore, create_workflow_feedback_for_review
from cli.utils.output_formatter import print_next_step
from cli.utils.path_formatter import get_relative_path

app = typer.Typer(help="Record, triage, and inspect workflow feedback")
console = Console()


@app.command()
def record(
    domain: str = typer.Option(None, "--domain", "-d", help="Problem domain: async_dev, product, uncertain (auto-inferred if not set)"),
    issue_type: str = typer.Option(..., "--type", "-t", help="Issue type (see schema for valid values)"),
    detected_by: str = typer.Option("operator", "--by", "-b", help="Who detected: operator, ai_executor, review_process, etc."),
    detected_in: str = typer.Option(..., "--in", "-i", help="Context where detected (workflow phase, command, file)"),
    description: str = typer.Option(..., "--description", help="Issue description"),
    context_summary: str = typer.Option(..., "--context", help="What system was doing at detection (repair context)"),
    product: str = typer.Option(None, "--product", "-p", help="Product ID (required for product/uncertain domain)"),
    feature: str = typer.Option(None, "--feature", "-f", help="Feature ID (optional)"),
    execution: str = typer.Option(None, "--execution", "-e", help="Execution ID (optional)"),
    suspected: str = typer.Option(None, "--suspected", help="Hypothesis about root cause (strongly recommended)"),
    workaround: str = typer.Option(None, "--workaround", help="How issue was worked around (strongly recommended)"),
    reproduce: str = typer.Option(None, "--reproduce", help="How to investigate/reproduce later (strongly recommended)"),
    command_ctx: str = typer.Option(None, "--command", help="CLI command that triggered issue"),
    expected: str = typer.Option(None, "--expected", help="What should have happened"),
    actual: str = typer.Option(None, "--actual", help="What actually happened"),
    self_corrected: bool = typer.Option(False, "--self-corrected", help="Issue was self-corrected"),
    requires_followup: bool = typer.Option(True, "--followup/--no-followup", help="Requires follow-up attention"),
    confidence: str = typer.Option(None, "--confidence", "-c", help="Confidence: low, medium, high"),
    escalation: str = typer.Option(None, "--escalation", help="Escalation: ignore, track_only, review_needed, candidate_issue"),
    impact: str = typer.Option(None, "--impact", help="Impact description"),
    priority: str = typer.Option(None, "--priority", help="Priority: high, medium, low"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Record a workflow feedback item with repair context.

    context_summary is required for repair value - explains what system was doing.
    suspected/workaround/reproduce are strongly recommended for debugging.

    Examples:
        asyncdev feedback record --type cli_behavior --in "status" --description "Wrong phase" --context "Running status check"
        asyncdev feedback record --domain product --product my-app --type execution_pack --description "Wrong sequence" --context "Reviewing ExecutionPack" --suspected "Feature numbering bug" --workaround "Manual edit"
    """
    root = Path.cwd() if path == Path("projects") else path

    project_path = path / product if product else None
    store = WorkflowFeedbackStore(project_path=project_path, runtime_path=root / ".runtime")

    try:
        feedback = store.record_feedback(
            problem_domain=domain,
            issue_type=issue_type,
            detected_by=detected_by,
            detected_in=detected_in,
            description=description,
            context_summary=context_summary,
            self_corrected=self_corrected,
            requires_followup=requires_followup,
            product_id=product,
            feature_id=feature,
            execution_id=execution,
            suspected_problem=suspected,
            temporary_fix=workaround,
            reproduction_hint=reproduce,
            command_context=command_ctx,
            expected_behavior=expected,
            actual_behavior=actual,
            impact=impact,
            confidence=confidence,
            escalation_recommendation=escalation,
            priority=priority,
        )

        console.print(Panel(f"Feedback Recorded: {feedback['feedback_id']}", border_style="green"))

        table = Table(show_header=False)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Problem Domain", feedback.get("problem_domain", ""))
        table.add_row("Issue Type", feedback.get("issue_type", ""))
        table.add_row("Detected By", feedback.get("detected_by", ""))
        table.add_row("Detected In", feedback.get("detected_in", ""))
        table.add_row("Description", feedback.get("description", "")[:50])
        table.add_row("Context", feedback.get("context_summary", "")[:50])
        if feedback.get("suspected_problem"):
            table.add_row("Suspected", feedback.get("suspected_problem", "")[:50])
        if feedback.get("temporary_fix"):
            table.add_row("Workaround", feedback.get("temporary_fix", "")[:50])
        table.add_row("Self Corrected", str(feedback.get("self_corrected", False)))
        table.add_row("Requires Followup", str(feedback.get("requires_followup", True)))
        if feedback.get("confidence"):
            table.add_row("Confidence", feedback.get("confidence", ""))
        if feedback.get("escalation_recommendation"):
            table.add_row("Escalation", feedback.get("escalation_recommendation", ""))
        if feedback.get("priority"):
            table.add_row("Priority", feedback.get("priority", ""))
        table.add_row("Detected At", feedback.get("detected_at", "")[:19])

        console.print(table)

        domain = feedback.get("problem_domain", "")
        feedback_path = root / ".runtime" / "workflow-feedback" / f"{feedback['feedback_id']}.yaml"
        if domain in ("product", "uncertain") and project_path:
            feedback_path = project_path / "workflow-feedback" / f"{feedback['feedback_id']}.yaml"

        console.print(f"\n[dim]Feedback file: {get_relative_path(feedback_path, root)}[/dim]")
        console.print(f"[dim]root: {root}[/dim]")

        if feedback.get("triaged_at"):
            console.print("\n[cyan]Triage completed during record[/cyan]")

        if feedback.get("escalation_recommendation") == "candidate_issue":
            console.print("\n[yellow]Marked as candidate for formal issue creation[/yellow]")

        store.close()

    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def triage(
    feedback_id: str = typer.Option(..., "--feedback-id", "-f", help="Feedback ID to triage"),
    domain: str = typer.Option(None, "--domain", "-d", help="Problem domain: async_dev, product, uncertain"),
    confidence: str = typer.Option(None, "--confidence", "-c", help="Confidence: low, medium, high"),
    escalation: str = typer.Option(None, "--escalation", help="Escalation: ignore, track_only, review_needed, candidate_issue"),
    note: str = typer.Option(None, "--note", "-n", help="Triage explanation note"),
    product: str = typer.Option(None, "--product", "-p", help="Product ID hint (optional)"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Add/update triage information for a feedback item.

    Triage adds classification layer:
    - problem_domain: Is this async-dev, product, or uncertain?
    - confidence: How certain is the classification?
    - escalation: What should happen with this item?

    Examples:
        asyncdev feedback triage --feedback-id wf-20260411-001 --domain async_dev --confidence high
        asyncdev feedback triage --feedback-id wf-20260411-001 --escalation candidate_issue --note "This is a CLI bug"
    """
    root = Path.cwd() if path == Path("projects") else path

    project_path = path / product if product else None
    store = WorkflowFeedbackStore(project_path=project_path, runtime_path=root / ".runtime")

    try:
        updated = store.triage_feedback(
            feedback_id=feedback_id,
            problem_domain=domain,
            confidence=confidence,
            escalation_recommendation=escalation,
            triage_note=note,
        )

        if not updated:
            console.print(f"[red]Feedback not found: {feedback_id}[/red]")
            store.close()
            raise typer.Exit(1)

        console.print(Panel(f"Feedback Triage Updated: {feedback_id}", border_style="green"))

        table = Table(show_header=False)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Feedback ID", updated.get("feedback_id", ""))
        table.add_row("Problem Domain", updated.get("problem_domain", ""))
        table.add_row("Confidence", updated.get("confidence", "medium"))
        table.add_row("Escalation", updated.get("escalation_recommendation", "track_only"))
        if updated.get("triage_note"):
            table.add_row("Triage Note", updated.get("triage_note", ""))
        table.add_row("Triaged At", updated.get("triaged_at", "")[:19])

        console.print(table)

        domain_desc = {
            "async_dev": "Issue in amazing-async-dev system",
            "product": "Issue in product being built",
            "uncertain": "Needs operator review",
        }
        escalation_desc = {
            "ignore": "Not worth tracking",
            "track_only": "Keep recorded, no action needed",
            "review_needed": "Should review in nightly review",
            "candidate_issue": "Candidate for formal async-dev issue",
        }

        domain_val = updated.get("problem_domain") or ""
        escalation_val = updated.get("escalation_recommendation") or ""
        console.print(f"\n[dim]Domain: {domain_desc.get(domain_val, '')}[/dim]")
        console.print(f"[dim]Escalation: {escalation_desc.get(escalation_val, '')}[/dim]")

        store.close()

        if updated.get("escalation_recommendation") == "candidate_issue":
            print_next_step(
                action="Consider creating formal async-dev issue",
                command="Document in system hardening backlog",
            )
        elif updated.get("escalation_recommendation") == "review_needed":
            print_next_step(
                action="Will appear in nightly review",
                command="asyncdev feedback list --escalation review_needed",
            )

    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")
        store.close()
        raise typer.Exit(1)


@app.command("list")
def list_feedback(
    domain: str = typer.Option(None, "--domain", "-d", help="Filter by domain: async_dev, product, uncertain"),
    product: str = typer.Option(None, "--product", "-p", help="Filter by product ID"),
    issue_type: str = typer.Option(None, "--type", "-t", help="Filter by issue type"),
    confidence: str = typer.Option(None, "--confidence", "-c", help="Filter by confidence"),
    escalation: str = typer.Option(None, "--escalation", help="Filter by escalation"),
    followup_needed: bool = typer.Option(False, "--followup-needed", help="Only items requiring follow-up"),
    self_corrected: bool = typer.Option(None, "--self-corrected/--not-self-corrected", help="Filter by self-corrected status"),
    status: str = typer.Option(None, "--status", help="Filter by status: open, investigating, resolved, closed"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """List workflow feedback items with optional filters.

    Examples:
        asyncdev feedback list
        asyncdev feedback list --domain async_dev
        asyncdev feedback list --escalation candidate_issue
        asyncdev feedback list --product my-app
        asyncdev feedback list --followup-needed
    """
    root = Path.cwd() if path == Path("projects") else path

    project_path = path / product if product else None
    store = WorkflowFeedbackStore(project_path=project_path, runtime_path=root / ".runtime")

    feedbacks = store.list_feedback(
        problem_domain=domain,
        product_id=product,
        issue_type=issue_type,
        confidence=confidence,
        escalation_recommendation=escalation,
        requires_followup=followup_needed if followup_needed else None,
        self_corrected=self_corrected,
        status=status,
        limit=limit,
    )

    if not feedbacks:
        console.print("[dim]No workflow feedback found[/dim]")
        if product:
            console.print(f"[dim]Product: {product}[/dim]")
        if domain:
            console.print(f"[dim]Domain: {domain}[/dim]")
        console.print(f"[dim]path: {get_relative_path(path, root)}[/dim]")
        store.close()
        return

    title = "Workflow Feedback"
    if domain:
        title += f" ({domain})"
    if escalation:
        title += f" [{escalation}]"
    if followup_needed:
        title += " [followup-needed]"

    console.print(Panel(title, border_style="blue"))

    table = Table(show_header=True)
    table.add_column("Feedback ID", style="cyan", width=16)
    table.add_column("Domain", style="dim", width=10)
    table.add_column("Issue Type", style="yellow", width=14)
    table.add_column("Confidence", style="blue", width=10)
    table.add_column("Escalation", style="magenta", width=16)
    table.add_column("Status", style="green", width=10)
    table.add_column("Description", style="white", width=25)

    for fb in feedbacks:
        table.add_row(
            fb.get("feedback_id", "")[:16],
            fb.get("problem_domain", ""),
            fb.get("issue_type", ""),
            fb.get("confidence", "-"),
            fb.get("escalation_recommendation", "track_only"),
            fb.get("status", "open"),
            fb.get("description", "")[:25],
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(feedbacks)} items[/dim]")

    async_dev_count = sum(1 for fb in feedbacks if fb.get("problem_domain") == "async_dev")
    candidate_count = sum(1 for fb in feedbacks if fb.get("escalation_recommendation") == "candidate_issue")
    if async_dev_count > 0:
        console.print(f"[dim]async_dev domain: {async_dev_count}[/dim]")
    if candidate_count > 0:
        console.print(f"[dim]candidate_issue: {candidate_count}[/dim]")

    console.print(f"[dim]path: {get_relative_path(path, root)}[/dim]")

    store.close()

    print_next_step(
        action="Inspect specific feedback",
        command="asyncdev feedback show --feedback-id <id>",
        hints=["Use --domain async_dev to find async-dev issues"],
    )


@app.command()
def show(
    feedback_id: str = typer.Option(..., "--feedback-id", "-f", help="Feedback ID to inspect"),
    product: str = typer.Option(None, "--product", "-p", help="Product ID hint (optional)"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show detailed workflow feedback for a specific item.

    Examples:
        asyncdev feedback show --feedback-id wf-20260411-001
        asyncdev feedback show --feedback-id wf-20260411-001 --product my-app
    """
    root = Path.cwd() if path == Path("projects") else path

    project_path = path / product if product else None
    store = WorkflowFeedbackStore(project_path=project_path, runtime_path=root / ".runtime")

    feedback = store.load_feedback(feedback_id)

    if not feedback:
        console.print(f"[red]Feedback not found: {feedback_id}[/red]")
        if product:
            console.print(f"[dim]Product hint: {product}[/dim]")
        console.print(f"[dim]path: {get_relative_path(path, root)}[/dim]")
        store.close()
        raise typer.Exit(1)

    console.print(Panel(f"Workflow Feedback: {feedback_id}", border_style="green"))

    table = Table(show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Feedback ID", feedback.get("feedback_id", ""))
    table.add_row("Problem Domain", feedback.get("problem_domain", ""))
    table.add_row("Issue Type", feedback.get("issue_type", ""))
    table.add_row("Detected By", feedback.get("detected_by", ""))
    table.add_row("Detected In", feedback.get("detected_in", ""))
    if feedback.get("product_id"):
        table.add_row("Product ID", feedback.get("product_id", ""))
    if feedback.get("feature_id"):
        table.add_row("Feature ID", feedback.get("feature_id", ""))
    if feedback.get("execution_id"):
        table.add_row("Execution ID", feedback.get("execution_id", ""))
    table.add_row("Description", feedback.get("description", ""))
    if feedback.get("impact"):
        table.add_row("Impact", feedback.get("impact", ""))
    table.add_row("Self Corrected", str(feedback.get("self_corrected", False)))
    table.add_row("Requires Followup", str(feedback.get("requires_followup", False)))

    console.print(table)

    console.print("\n[bold]Triage Information:[/bold]")
    triage_table = Table(show_header=False)
    triage_table.add_column("Field", style="cyan")
    triage_table.add_column("Value", style="green")

    triage_table.add_row("Confidence", feedback.get("confidence", "Not triaged"))
    triage_table.add_row("Escalation", feedback.get("escalation_recommendation", "Not triaged"))
    if feedback.get("triaged_at"):
        triage_table.add_row("Triaged At", feedback.get("triaged_at", "")[:19])
    if feedback.get("triage_note"):
        triage_table.add_row("Triage Note", feedback.get("triage_note", ""))
    else:
        triage_table.add_row("Status", "[yellow]Not yet triaged[/yellow]")

    console.print(triage_table)

    console.print("\n[bold]Resolution:[/bold]")
    res_table = Table(show_header=False)
    res_table.add_column("Field", style="cyan")
    res_table.add_column("Value", style="green")

    res_table.add_row("Resolution", feedback.get("resolution", "none"))
    if feedback.get("resolution_note"):
        res_table.add_row("Resolution Note", feedback.get("resolution_note", ""))
    res_table.add_row("Tracking Status", feedback.get("status", "open"))
    if feedback.get("priority"):
        res_table.add_row("Priority", feedback.get("priority", ""))
    res_table.add_row("Detected At", feedback.get("detected_at", "")[:19])

    console.print(res_table)

    if feedback.get("artifact_reference"):
        artifact = feedback.get("artifact_reference", {})
        console.print("\n[bold]Artifact Reference:[/bold]")
        console.print(f"  Type: {artifact.get('artifact_type', '')}")
        console.print(f"  Path: {artifact.get('artifact_path', '')}")
        console.print(f"  ID: {artifact.get('artifact_id', '')}")

    feedback_file = feedback.get("_file_path", "")
    if feedback_file:
        console.print(f"\n[dim]Feedback file: {get_relative_path(Path(feedback_file), root)}[/dim]")
    console.print(f"[dim]root: {root}[/dim]")

    store.close()

    if not feedback.get("triaged_at"):
        console.print("\n[yellow]This feedback has not been triaged yet[/yellow]")
        print_next_step(
            action="Add triage classification",
            command="asyncdev feedback triage --feedback-id " + feedback_id + " --domain async_dev",
        )
    elif feedback.get("escalation_recommendation") == "candidate_issue":
        console.print("\n[yellow]Marked as candidate for formal issue[/yellow]")
        print_next_step(
            action="Consider creating async-dev issue",
            command="Document in system hardening backlog",
        )


@app.command()
def update(
    feedback_id: str = typer.Option(..., "--feedback-id", "-f", help="Feedback ID to update"),
    resolution: str = typer.Option(None, "--resolution", "-r", help="New resolution: none, workaround, fixed, deferred, escalated"),
    resolution_note: str = typer.Option(None, "--note", "-n", help="Resolution note"),
    status: str = typer.Option(None, "--status", help="New status: open, investigating, resolved, closed, archived"),
    no_followup: bool = typer.Option(False, "--no-followup", help="Mark as no longer requiring follow-up"),
    product: str = typer.Option(None, "--product", "-p", help="Product ID hint (optional)"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Update workflow feedback resolution/status.

    Examples:
        asyncdev feedback update --feedback-id wf-20260411-001 --resolution fixed
        asyncdev feedback update --feedback-id wf-20260411-001 --status resolved --no-followup
    """
    root = Path.cwd() if path == Path("projects") else path

    project_path = path / product if product else None
    store = WorkflowFeedbackStore(project_path=project_path, runtime_path=root / ".runtime")

    try:
        updated = store.update_feedback(
            feedback_id=feedback_id,
            resolution=resolution,
            resolution_note=resolution_note,
            status=status,
            requires_followup=False if no_followup else None,
        )

        if not updated:
            console.print(f"[red]Feedback not found: {feedback_id}[/red]")
            store.close()
            raise typer.Exit(1)

        console.print(Panel(f"Feedback Updated: {feedback_id}", border_style="green"))

        table = Table(show_header=False)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Feedback ID", updated.get("feedback_id", ""))
        table.add_row("Resolution", updated.get("resolution", "none"))
        if updated.get("resolution_note"):
            table.add_row("Resolution Note", updated.get("resolution_note", ""))
        table.add_row("Status", updated.get("status", "open"))
        table.add_row("Requires Followup", str(updated.get("requires_followup", False)))

        console.print(table)
        console.print(f"\n[dim]Feedback updated[/dim]")

        store.close()

        print_next_step(
            action="View all feedback",
            command="asyncdev feedback list",
        )

    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")
        store.close()
        raise typer.Exit(1)


@app.command()
def summary(
    product: str = typer.Option(None, "--product", "-p", help="Filter by product ID"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show summary of workflow feedback with triage breakdown.

    Examples:
        asyncdev feedback summary
        asyncdev feedback summary --product my-app
    """
    root = Path.cwd() if path == Path("projects") else path

    project_path = path / product if product else None
    store = WorkflowFeedbackStore(project_path=project_path, runtime_path=root / ".runtime")

    summary_data = store.get_followup_summary(product_id=product)

    console.print(Panel("Workflow Feedback Summary", border_style="blue"))

    table = Table(show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green")

    table.add_row("Total Follow-up Needed", str(summary_data.get("total_followup_needed", 0)))
    table.add_row("Self-Corrected (tracking)", str(summary_data.get("self_corrected_count", 0)))
    table.add_row("Open Status", str(summary_data.get("open_count", 0)))
    table.add_row("Candidate Issues", str(summary_data.get("candidate_issue_count", 0)))

    console.print(table)

    by_domain = summary_data.get("by_problem_domain", {})
    if by_domain:
        console.print("\n[bold]By Problem Domain:[/bold]")
        domain_table = Table(show_header=True)
        domain_table.add_column("Domain", style="cyan")
        domain_table.add_column("Count", style="green")

        for domain, count in sorted(by_domain.items(), key=lambda x: x[1], reverse=True):
            domain_table.add_row(domain, str(count))

        console.print(domain_table)

    by_escalation = summary_data.get("by_escalation", {})
    if by_escalation:
        console.print("\n[bold]By Escalation:[/bold]")
        esc_table = Table(show_header=True)
        esc_table.add_column("Escalation", style="magenta")
        esc_table.add_column("Count", style="green")

        for esc, count in sorted(by_escalation.items(), key=lambda x: x[1], reverse=True):
            esc_table.add_row(esc, str(count))

        console.print(esc_table)

    by_type = summary_data.get("by_issue_type", {})
    if by_type:
        console.print("\n[bold]By Issue Type:[/bold]")
        type_table = Table(show_header=True)
        type_table.add_column("Issue Type", style="yellow")
        type_table.add_column("Count", style="green")

        for issue_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:5]:
            type_table.add_row(issue_type, str(count))

        console.print(type_table)

    store.close()

    print_next_step(
        action="View items needing follow-up",
        command="asyncdev feedback list --followup-needed",
        hints=["Use --escalation candidate_issue to find potential issues"],
    )


@app.command()
def promote(
    feedback_id: str = typer.Option(..., "--feedback-id", "-f", help="Feedback ID to promote"),
    summary: str = typer.Option(None, "--summary", "-s", help="Summary for follow-up (defaults to source description)"),
    reason: str = typer.Option("system_bug", "--reason", "-r", help="Promotion reason: system_bug, ux_issue, workflow_improvement, documentation_gap, integration_issue, other"),
    note: str = typer.Option(None, "--note", "-n", help="Optional promotion note"),
    feature: str = typer.Option(None, "--feature", help="Optional candidate feature ID"),
    product: str = typer.Option(None, "--product", "-p", help="Product ID (if feedback is product domain)"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Promote a triaged workflow feedback to formal follow-up.

    Feedback must be triaged first (have confidence and escalation set).

    Examples:
        asyncdev feedback promote --feedback-id wf-20260412-001
        asyncdev feedback promote --feedback-id wf-001 --reason system_bug --note "Priority fix"
    """
    root = Path.cwd() if path == Path("projects") else path

    project_path = path / product if product else None
    store = WorkflowFeedbackStore(project_path=project_path, runtime_path=root / ".runtime")

    try:
        promotion = store.promote_feedback(
            feedback_id=feedback_id,
            summary=summary,
            promotion_reason=reason,
            promotion_note=note,
            candidate_feature=feature,
        )

        console.print(Panel(f"Feedback Promoted: {promotion['promotion_id']}", border_style="green"))

        table = Table(show_header=False)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Promotion ID", promotion.get("promotion_id", ""))
        table.add_row("Source Feedback", promotion.get("source_feedback_id", ""))
        table.add_row("Summary", promotion.get("summary", "")[:60])
        table.add_row("Reason", promotion.get("promotion_reason", ""))
        if promotion.get("promotion_note"):
            table.add_row("Note", promotion.get("promotion_note", "")[:50])
        table.add_row("Status", promotion.get("followup_status", "open"))
        table.add_row("Promoted At", promotion.get("promoted_at", "")[:19])

        console.print(table)

        console.print(f"\n[dim]path: {get_relative_path(root / '.runtime' / 'feedback-promotions', root)}[/dim]")

        print_next_step(
            action="View all promotions",
            command="asyncdev feedback promotions list",
            hints=[
                "Use --status open to see pending follow-ups",
                "This is an internal follow-up record, not a GitHub issue",
            ],
        )

    except ValueError as e:
        console.print(f"[red]Promotion error: {e}[/red]")
        store.close()
        raise typer.Exit(1)

    store.close()


promotions_app = typer.Typer(help="Manage promoted feedback records")
app.add_typer(promotions_app, name="promotions")


@promotions_app.command("list")
def list_promotions(
    status: str = typer.Option(None, "--status", "-s", help="Filter by followup status: open, reviewed, in_progress, addressed, closed"),
    reason: str = typer.Option(None, "--reason", "-r", help="Filter by promotion reason"),
    domain: str = typer.Option(None, "--domain", "-d", help="Filter by source problem domain"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """List promoted feedback records.

    Examples:
        asyncdev feedback promotions list
        asyncdev feedback promotions list --status open
        asyncdev feedback promotions list --reason system_bug
    """
    root = Path.cwd() if path == Path("projects") else path

    from runtime.feedback_promotion_store import FeedbackPromotionStore

    promotion_store = FeedbackPromotionStore(runtime_path=root / ".runtime")

    promotions = promotion_store.list_promotions(
        followup_status=status,
        promotion_reason=reason,
        source_domain=domain,
        limit=limit,
    )

    if not promotions:
        console.print("[dim]No promotions found[/dim]")
        if status:
            console.print(f"[dim]Status: {status}[/dim]")
        console.print(f"[dim]path: {get_relative_path(root / '.runtime' / 'feedback-promotions', root)}[/dim]")
        promotion_store.close()
        return

    title = "Promoted Feedback"
    if status:
        title += f" ({status})"
    if reason:
        title += f" [{reason}]"

    console.print(Panel(title, border_style="green"))

    table = Table(show_header=True)
    table.add_column("Promotion ID", style="cyan", width=18)
    table.add_column("Source", style="dim", width=16)
    table.add_column("Reason", style="yellow", width=18)
    table.add_column("Status", style="green", width=14)
    table.add_column("Summary", width=40)

    for promo in promotions:
        table.add_row(
            promo.get("promotion_id", ""),
            promo.get("source_feedback_id", ""),
            promo.get("promotion_reason", ""),
            promo.get("followup_status", "open"),
            promo.get("summary", "")[:40],
        )

    console.print(table)

    console.print(f"\n[dim]Total: {len(promotions)} items[/dim]")
    if domain:
        console.print(f"[dim]Source domain: {domain}[/dim]")
    console.print(f"[dim]path: {get_relative_path(root / '.runtime' / 'feedback-promotions', root)}[/dim]")

    promotion_store.close()

    print_next_step(
        action="Inspect specific promotion",
        command="asyncdev feedback promotions show --promotion-id <id>",
    )


@promotions_app.command("show")
def show_promotion(
    promotion_id: str = typer.Option(..., "--promotion-id", "-p", help="Promotion ID to show"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Show detailed promotion record.

    Example:
        asyncdev feedback promotions show --promotion-id promo-20260412-001
    """
    root = Path.cwd() if path == Path("projects") else path

    from runtime.feedback_promotion_store import FeedbackPromotionStore

    promotion_store = FeedbackPromotionStore(runtime_path=root / ".runtime")

    promotion = promotion_store.load_promotion(promotion_id)

    if not promotion:
        console.print(f"[red]Promotion not found: {promotion_id}[/red]")
        promotion_store.close()
        raise typer.Exit(1)

    console.print(Panel(f"Promoted Feedback: {promotion_id}", border_style="green"))

    table = Table(show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Promotion ID", promotion.get("promotion_id", ""))
    table.add_row("Source Feedback", promotion.get("source_feedback_id", ""))
    table.add_row("Summary", promotion.get("summary", ""))
    table.add_row("Reason", promotion.get("promotion_reason", ""))
    table.add_row("Status", promotion.get("followup_status", "open"))

    console.print(table)

    console.print("\n[bold]Source Triage Information:[/bold]")
    triage_table = Table(show_header=False)
    triage_table.add_column("Field", style="cyan")
    triage_table.add_column("Value", style="dim")

    triage_table.add_row("Problem Domain", promotion.get("source_problem_domain", ""))
    triage_table.add_row("Confidence", promotion.get("source_confidence", ""))
    triage_table.add_row("Escalation", promotion.get("source_escalation_recommendation", ""))
    triage_table.add_row("Issue Type", promotion.get("source_issue_type", ""))
    triage_table.add_row("Original Description", promotion.get("source_description", "")[:60])

    console.print(triage_table)

    if promotion.get("promotion_note"):
        console.print(f"\n[bold]Promotion Note:[/bold]\n{promotion.get('promotion_note', '')}")

    console.print(f"\n[dim]Promoted at: {promotion.get('promoted_at', '')[:19]}[/dim]")
    console.print(f"[dim]path: {get_relative_path(root / '.runtime' / 'feedback-promotions', root)}[/dim]")

    promotion_store.close()

    print_next_step(
        action="View source feedback",
        command=f"asyncdev feedback show --feedback-id {promotion.get('source_feedback_id', '')}",
        hints=["Use update command to change followup status"],
    )


@promotions_app.command("update")
def update_promotion(
    promotion_id: str = typer.Option(..., "--promotion-id", "-p", help="Promotion ID to update"),
    status: str = typer.Option(None, "--status", "-s", help="New followup status: open, reviewed, in_progress, addressed, closed"),
    note: str = typer.Option(None, "--note", "-n", help="Note on how addressed"),
    path: Path = typer.Option(Path("projects"), help="Projects root path"),
):
    """Update promotion followup status.

    Example:
        asyncdev feedback promotions update --promotion-id promo-001 --status addressed --note "Fixed in commit abc123"
    """
    root = Path.cwd() if path == Path("projects") else path

    from runtime.feedback_promotion_store import FeedbackPromotionStore

    promotion_store = FeedbackPromotionStore(runtime_path=root / ".runtime")

    try:
        updated = promotion_store.update_promotion(
            promotion_id=promotion_id,
            followup_status=status,
            addressed_note=note,
        )

        if not updated:
            console.print(f"[red]Promotion not found: {promotion_id}[/red]")
            promotion_store.close()
            raise typer.Exit(1)

        console.print(Panel(f"Promotion Updated: {promotion_id}", border_style="green"))

        table = Table(show_header=False)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Promotion ID", updated.get("promotion_id", ""))
        table.add_row("Status", updated.get("followup_status", ""))
        if updated.get("addressed_note"):
            table.add_row("Note", updated.get("addressed_note", "")[:50])
        if updated.get("addressed_at"):
            table.add_row("Addressed At", updated.get("addressed_at", "")[:19])

        console.print(table)

    except ValueError as e:
        console.print(f"[red]Validation error: {e}[/red]")
        promotion_store.close()
        raise typer.Exit(1)

    promotion_store.close()


if __name__ == "__main__":
    app()