#!/usr/bin/env python3
"""
Demo script for single feature day loop.

This script demonstrates the complete async dev workflow:
1. plan-day: Create ExecutionPack
2. run-day: Execute task (mock mode)
3. review-night: Generate DailyReviewPack
4. resume-next-day: Process decision, continue

Usage:
    python demo-day-loop.py [--verbose]

Produces:
    - ExecutionPack
    - ExecutionResult
    - DailyReviewPack
    - RunState updates at each phase
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from runtime.state_store import StateStore, generate_execution_id, update_runstate_from_result
from runtime.review_pack_builder import build_daily_review_pack
from runtime.adapters.llm_adapter import MockLLMAdapter


def setup_demo_project():
    """Create demo project structure."""
    demo_path = Path("examples/single-feature-day-loop/demo-product")

    for subdir in ["execution-packs", "execution-results", "reviews", "logs"]:
        (demo_path / subdir).mkdir(parents=True, exist_ok=True)

    return demo_path


def phase_plan_day(verbose: bool = False):
    """Phase 1: plan-day - Create ExecutionPack."""
    print("\n" + "=" * 60)
    print("PHASE 1: plan-day")
    print("=" * 60)

    demo_path = Path("examples/single-feature-day-loop/demo-product")
    store = StateStore(project_path=demo_path)

    execution_id = generate_execution_id()

    execution_pack = {
        "execution_id": execution_id,
        "feature_id": "001-hello-world-task",
        "task_id": "create-hello-world-file",
        "goal": "Create hello-world.txt with greeting message",
        "task_scope": [
            "Create hello-world.txt",
            "Write greeting message",
            "Verify file content",
        ],
        "must_read": [
            "examples/single-feature-day-loop/demo-product/product-brief.yaml",
            "examples/single-feature-day-loop/demo-product/feature-spec.yaml",
        ],
        "constraints": [
            "Single file only",
            "Mock execution mode",
            "Stop after completion",
        ],
        "deliverables": [
            {"item": "hello-world.txt", "path": "hello-world.txt", "type": "file"}
        ],
        "verification_steps": [
            "Check file exists",
            "Verify content matches expected",
        ],
        "stop_conditions": [
            "File created successfully",
            "Verification passed",
        ],
    }

    store.save_execution_pack(execution_pack)

    runstate = {
        "project_id": "demo-hello-world-001",
        "feature_id": "001-hello-world-task",
        "current_phase": "executing",
        "active_task": "create-hello-world-file",
        "task_queue": [],
        "completed_outputs": [],
        "open_questions": [],
        "blocked_items": [],
        "decisions_needed": [],
        "last_action": f"Created ExecutionPack {execution_id}",
        "next_recommended_action": "Execute task",
        "updated_at": datetime.now().isoformat(),
        "artifacts": {"execution_pack": execution_id},
        "health_status": "healthy",
    }

    store.save_runstate(runstate)

    if verbose:
        print(f"  Execution ID: {execution_id}")
        print(f"  Task: {execution_pack['task_id']}")
        print(f"  Goal: {execution_pack['goal']}")
        print(f"  Deliverables: {execution_pack['deliverables']}")

    print(f"[OK] ExecutionPack saved: execution-packs/{execution_id}.md")
    print(f"[OK] RunState updated: current_phase = executing")

    return execution_id, execution_pack


def phase_run_day(execution_id: str, execution_pack: dict, verbose: bool = False):
    """Phase 2: run-day - Execute task (mock mode)."""
    print("\n" + "=" * 60)
    print("PHASE 2: run-day (mock mode)")
    print("=" * 60)

    demo_path = Path("examples/single-feature-day-loop/demo-product")
    store = StateStore(project_path=demo_path)

    adapter = MockLLMAdapter()
    execution_result = adapter.execute(execution_pack)

    execution_result["execution_id"] = execution_id
    execution_result["completed_items"] = ["hello-world.txt"]
    execution_result["artifacts_created"] = [
        {"name": "hello-world.txt", "path": "hello-world.txt", "type": "file"}
    ]
    execution_result["recommended_next_step"] = "Task completed. Proceed to review-night."

    store.save_execution_result(execution_result)

    output_path = demo_path / "hello-world.txt"
    output_path.write_text("Hello from async dev day loop!\n")

    if verbose:
        print(f"  Status: {execution_result['status']}")
        print(f"  Completed: {execution_result['completed_items']}")
        print(f"  Verification: {execution_result['verification_result']}")

    print(f"[OK] Mock execution complete")
    print(f"[OK] Output file created: hello-world.txt")
    print(f"[OK] ExecutionResult saved: execution-results/{execution_id}.md")

    return execution_result


def phase_review_night(execution_result: dict, verbose: bool = False):
    """Phase 3: review-night - Generate DailyReviewPack."""
    print("\n" + "=" * 60)
    print("PHASE 3: review-night")
    print("=" * 60)

    demo_path = Path("examples/single-feature-day-loop/demo-product")
    store = StateStore(project_path=demo_path)

    runstate = store.load_runstate()

    review_pack = build_daily_review_pack(execution_result, runstate)

    review_pack["what_was_completed"] = [
        "Created hello-world.txt with greeting message",
        "Verified file content",
    ]
    review_pack["evidence"] = [
        {
            "item": "hello-world.txt",
            "path": "hello-world.txt",
            "verified": True,
            "verification_note": "File exists, content matches expected",
        }
    ]
    review_pack["risk_summary"] = "No risks. Simple task completed successfully."
    review_pack["confidence_notes"] = "High confidence. Mock execution verified."

    store.save_daily_review_pack(review_pack)

    runstate["current_phase"] = "reviewing"
    runstate["decisions_needed"] = []
    store.save_runstate(runstate)

    if verbose:
        print(f"  Date: {review_pack['date']}")
        print(f"  Completed: {review_pack['what_was_completed']}")
        print(f"  Evidence: {review_pack['evidence']}")

    print(f"[OK] DailyReviewPack saved: reviews/{review_pack['date']}-review.md")
    print(f"[OK] RunState updated: current_phase = reviewing")

    return review_pack


def phase_resume_next_day(verbose: bool = False):
    """Phase 4: resume-next-day - Continue loop."""
    print("\n" + "=" * 60)
    print("PHASE 4: resume-next-day")
    print("=" * 60)

    demo_path = Path("examples/single-feature-day-loop/demo-product")
    store = StateStore(project_path=demo_path)

    runstate = store.load_runstate()

    runstate["current_phase"] = "completed"
    runstate["decisions_needed"] = []
    runstate["last_action"] = "Day loop completed - feature done"
    runstate["next_recommended_action"] = "Feature complete. Start new feature or project."
    runstate["health_status"] = "healthy"

    store.save_runstate(runstate)

    if verbose:
        print(f"  Phase: {runstate['current_phase']}")
        print(f"  Status: Feature complete")

    print(f"[OK] RunState updated: current_phase = completed")
    print(f"[OK] Feature marked as complete")


def print_summary():
    """Print final summary of demo outputs."""
    print("\n" + "=" * 60)
    print("DEMO SUMMARY")
    print("=" * 60)

    demo_path = Path("examples/single-feature-day-loop/demo-product")

    print("\nGenerated artifacts:")

    packs = list((demo_path / "execution-packs").glob("*.md"))
    if packs:
        print(f"  ExecutionPack: {packs[-1].name}")

    results = list((demo_path / "execution-results").glob("*.md"))
    if results:
        print(f"  ExecutionResult: {results[-1].name}")

    reviews = list((demo_path / "reviews").glob("*.md"))
    if reviews:
        print(f"  DailyReviewPack: {reviews[-1].name}")

    runstate = demo_path / "runstate.md"
    if runstate.exists():
        print(f"  RunState: runstate.md")

    output = demo_path / "hello-world.txt"
    if output.exists():
        print(f"  Output: hello-world.txt")

    print("\nDay loop phases completed:")
    print("  1. plan-day    -> ExecutionPack created")
    print("  2. run-day     -> Task executed (mock)")
    print("  3. review-night -> DailyReviewPack generated")
    print("  4. resume-next-day -> Feature marked complete")


def main():
    parser = argparse.ArgumentParser(description="Demo single feature day loop")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    print("Amazing Async Dev - Single Feature Day Loop Demo")
    print("=" * 60)

    setup_demo_project()

    execution_id, execution_pack = phase_plan_day(verbose=args.verbose)

    execution_result = phase_run_day(execution_id, execution_pack, verbose=args.verbose)

    review_pack = phase_review_night(execution_result, verbose=args.verbose)

    phase_resume_next_day(verbose=args.verbose)

    print_summary()

    print("\n[SUCCESS] Demo complete!")
    print("Check examples/single-feature-day-loop/demo-product/ for artifacts")


if __name__ == "__main__":
    main()