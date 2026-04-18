"""Browser Verifier - Feature 056.

Playwright integration for frontend verification:
- Console error capture
- Screenshot capture
- Accessibility snapshot
- Scenario execution
- Exception handling
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class BrowserVerificationStatus(str, Enum):
    """Browser verification status."""
    SUCCESS = "success"
    FAILED = "failed"
    EXCEPTION = "exception"
    SKIPPED = "skipped"


class ExceptionReason(str, Enum):
    """Exception reasons from Feature 038."""
    PLAYWRIGHT_UNAVAILABLE = "playwright_unavailable"
    ENVIRONMENT_BLOCKED = "environment_blocked"
    BROWSER_INSTALL_FAILED = "browser_install_failed"
    CI_CONTAINER_LIMITATION = "ci_container_limitation"
    MISSING_CREDENTIALS = "missing_credentials"
    DETERMINISTIC_BLOCKER = "deterministic_blocker"
    RECLASSIFIED_NONINTERACTIVE = "reclassified_noninteractive"


@dataclass
class ScenarioResult:
    """Result of a single browser scenario."""
    name: str
    passed: bool
    error_message: str | None = None
    screenshot_path: str | None = None
    duration_seconds: float = 0.0


@dataclass
class ConsoleError:
    """Console error captured from browser."""
    level: str
    message: str
    url: str | None = None
    line: int | None = None


@dataclass
class BrowserVerificationResult:
    """Full browser verification result."""
    executed: bool
    status: BrowserVerificationStatus
    passed: int = 0
    failed: int = 0
    scenarios_run: list[str] = field(default_factory=list)
    scenario_results: list[ScenarioResult] = field(default_factory=list)
    screenshots: list[str] = field(default_factory=list)
    console_errors: list[ConsoleError] = field(default_factory=list)
    accessibility_snapshot: str | None = None
    exception_reason: ExceptionReason | None = None
    exception_details: str | None = None
    duration_seconds: float = 0.0
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    finished_at: str | None = None


DEFAULT_SCENARIOS = [
    "page_render",
    "console_check",
    "accessibility_snapshot",
]


def check_playwright_available() -> bool:
    """Check if Playwright is available in the environment."""
    try:
        import playwright
        return True
    except ImportError:
        return False


def run_browser_verification(
    url: str,
    project_name: str | None = None,
    scenarios: list[str] | None = None,
    timeout: int = 60,
    screenshot_dir: Path | None = None,
) -> BrowserVerificationResult:
    """Run browser verification via Playwright.
    
    Args:
        url: URL to verify
        project_name: Project name for screenshot subdirectory
        scenarios: List of scenarios to run (default: page_render, console_check, accessibility_snapshot)
        timeout: Timeout in seconds
        screenshot_dir: Base directory for screenshots (defaults to screenshots/{project_name}/)
        
    Returns:
        BrowserVerificationResult with verification outcome
    """
    start_time = datetime.now()
    
    if not check_playwright_available():
        return BrowserVerificationResult(
            executed=False,
            status=BrowserVerificationStatus.EXCEPTION,
            exception_reason=ExceptionReason.PLAYWRIGHT_UNAVAILABLE,
            exception_details="Playwright is not installed in this environment",
            duration_seconds=0,
        )
    
    target_scenarios = scenarios or DEFAULT_SCENARIOS
    
    if screenshot_dir:
        screenshot_path = screenshot_dir
    elif project_name:
        screenshot_path = Path.cwd() / "screenshots" / project_name
    else:
        screenshot_path = Path.cwd() / "screenshots" / "default"
    
    screenshot_path.mkdir(parents=True, exist_ok=True)
    
    results: list[ScenarioResult] = []
    console_errors: list[ConsoleError] = []
    screenshots: list[str] = []
    accessibility_snapshot: str | None = None
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(timeout=timeout * 1000)
            page = browser.new_page()
            
            for scenario in target_scenarios:
                scenario_start = datetime.now()
                
                try:
                    if scenario == "page_render":
                        page.goto(url, timeout=timeout * 1000)
                        screenshot_file = screenshot_path / f"page-render-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
                        page.screenshot(path=str(screenshot_file))
                        screenshots.append(str(screenshot_file))
                        results.append(ScenarioResult(
                            name=scenario,
                            passed=True,
                            screenshot_path=str(screenshot_file),
                            duration_seconds=(datetime.now() - scenario_start).total_seconds(),
                        ))
                    
                    elif scenario == "console_check":
                        page.goto(url, timeout=timeout * 1000)
                        
                        def capture_console(msg):
                            if msg.type in ["error", "warning"]:
                                console_errors.append(ConsoleError(
                                    level=msg.type,
                                    message=msg.text,
                                    url=msg.location.get("url"),
                                    line=msg.location.get("lineNumber"),
                                ))
                        
                        page.on("console", capture_console)
                        page.wait_for_timeout(2000)
                        
                        passed = len([e for e in console_errors if e.level == "error"]) == 0
                        results.append(ScenarioResult(
                            name=scenario,
                            passed=passed,
                            error_message=f"{len(console_errors)} console messages captured" if not passed else None,
                            duration_seconds=(datetime.now() - scenario_start).total_seconds(),
                        ))
                    
                    elif scenario == "accessibility_snapshot":
                        page.goto(url, timeout=timeout * 1000)
                        snapshot = page.accessibility.snapshot()
                        accessibility_snapshot = str(snapshot)
                        results.append(ScenarioResult(
                            name=scenario,
                            passed=snapshot is not None,
                            duration_seconds=(datetime.now() - scenario_start).total_seconds(),
                        ))
                    
                    else:
                        results.append(ScenarioResult(
                            name=scenario,
                            passed=False,
                            error_message=f"Unknown scenario: {scenario}",
                            duration_seconds=(datetime.now() - scenario_start).total_seconds(),
                        ))
                
                except Exception as e:
                    results.append(ScenarioResult(
                        name=scenario,
                        passed=False,
                        error_message=str(e),
                        duration_seconds=(datetime.now() - scenario_start).total_seconds(),
                    ))
            
            browser.close()
    
    except Exception as e:
        return BrowserVerificationResult(
            executed=False,
            status=BrowserVerificationStatus.EXCEPTION,
            exception_reason=ExceptionReason.ENVIRONMENT_BLOCKED,
            exception_details=str(e),
            duration_seconds=(datetime.now() - start_time).total_seconds(),
        )
    
    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count
    
    final_status = BrowserVerificationStatus.SUCCESS if failed_count == 0 else BrowserVerificationStatus.FAILED
    
    return BrowserVerificationResult(
        executed=True,
        status=final_status,
        passed=passed_count,
        failed=failed_count,
        scenarios_run=target_scenarios,
        scenario_results=results,
        screenshots=screenshots,
        console_errors=console_errors,
        accessibility_snapshot=accessibility_snapshot,
        duration_seconds=(datetime.now() - start_time).total_seconds(),
        finished_at=datetime.now().isoformat(),
    )


def create_exception_result(
    reason: ExceptionReason,
    details: str,
) -> BrowserVerificationResult:
    """Create an exception result without running verification."""
    return BrowserVerificationResult(
        executed=False,
        status=BrowserVerificationStatus.EXCEPTION,
        exception_reason=reason,
        exception_details=details,
        duration_seconds=0,
    )


def to_execution_result_dict(result: BrowserVerificationResult) -> dict[str, Any]:
    """Convert BrowserVerificationResult to ExecutionResult dict format."""
    return {
        "browser_verification": {
            "executed": result.executed,
            "passed": result.passed,
            "failed": result.failed,
            "scenarios_run": result.scenarios_run,
            "screenshots": result.screenshots,
            "console_errors": [
                {
                    "level": e.level,
                    "message": e.message,
                    "url": e.url,
                    "line": e.line,
                }
                for e in result.console_errors
            ],
            "exception_reason": result.exception_reason.value if result.exception_reason else None,
            "exception_details": result.exception_details,
            "duration": f"{result.duration_seconds:.2f}s",
        },
    }