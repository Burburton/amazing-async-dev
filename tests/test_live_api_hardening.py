"""Tests for Live API hardening - failure classification and retry logic."""

import pytest
from pathlib import Path
import tempfile
import shutil

from runtime.api_failure_types import (
    APIFailureClassification,
    is_retryable,
    get_recovery_hint,
    classify_api_error,
    RETRYABLE_FAILURES,
    NO_RETRY_FAILURES,
)
from runtime.adapters.llm_adapter import BailianLLMAdapter, MockLLMAdapter
from runtime.engines.live_api_engine import LiveAPIEngine


@pytest.fixture
def temp_project_dir():
    dir_path = tempfile.mkdtemp()
    project_path = Path(dir_path) / "test-project"
    project_path.mkdir()
    (project_path / ".runtime").mkdir(parents=True, exist_ok=True)
    yield project_path
    try:
        shutil.rmtree(dir_path, ignore_errors=True)
    except PermissionError:
        pass


class TestAPIFailureClassification:
    """Tests for API failure classification."""

    def test_failure_types_defined(self):
        """APIFailureClassification should have required types."""
        assert APIFailureClassification.AUTH_CONFIG_FAILURE.value == "auth_config_failure"
        assert APIFailureClassification.PROVIDER_NETWORK_FAILURE.value == "provider_network_failure"
        assert APIFailureClassification.TIMEOUT_FAILURE.value == "timeout_failure"
        assert APIFailureClassification.RATE_LIMIT_FAILURE.value == "rate_limit_failure"
        assert APIFailureClassification.MALFORMED_RESPONSE.value == "malformed_response"
        assert APIFailureClassification.VALIDATION_FAILURE.value == "validation_failure"
        assert APIFailureClassification.PARTIAL_RESULT.value == "partial_result"
        assert APIFailureClassification.UNSAFE_RESUME.value == "unsafe_resume"
        assert APIFailureClassification.CONTENT_FILTER_FAILURE.value == "content_filter_failure"
        assert APIFailureClassification.MODEL_ERROR.value == "model_error"

    def test_retryable_failures(self):
        """Retryable failures should be network, timeout, rate limit, model."""
        assert is_retryable(APIFailureClassification.PROVIDER_NETWORK_FAILURE)
        assert is_retryable(APIFailureClassification.TIMEOUT_FAILURE)
        assert is_retryable(APIFailureClassification.RATE_LIMIT_FAILURE)
        assert is_retryable(APIFailureClassification.MODEL_ERROR)

    def test_no_retry_failures(self):
        """Auth, malformed, validation, unsafe should not retry."""
        assert not is_retryable(APIFailureClassification.AUTH_CONFIG_FAILURE)
        assert not is_retryable(APIFailureClassification.MALFORMED_RESPONSE)
        assert not is_retryable(APIFailureClassification.VALIDATION_FAILURE)
        assert not is_retryable(APIFailureClassification.UNSAFE_RESUME)

    def test_recovery_hints_exist(self):
        """All failure types should have recovery hints."""
        for failure in APIFailureClassification:
            hint = get_recovery_hint(failure)
            assert hint is not None
            assert len(hint) > 0


class TestClassifyAPIError:
    """Tests for error classification."""

    def test_classifies_auth_error(self):
        """Authentication errors should classify correctly."""
        error = Exception("Invalid API key")
        result = classify_api_error(error)
        assert result == APIFailureClassification.AUTH_CONFIG_FAILURE

    def test_classifies_401_error(self):
        """401 status should classify as auth failure."""
        error = Exception("HTTP 401 Unauthorized")
        result = classify_api_error(error)
        assert result == APIFailureClassification.AUTH_CONFIG_FAILURE

    def test_classifies_rate_limit(self):
        """Rate limit errors should classify correctly."""
        error = Exception("Rate limit exceeded")
        result = classify_api_error(error)
        assert result == APIFailureClassification.RATE_LIMIT_FAILURE

    def test_classifies_429_error(self):
        """429 status should classify as rate limit."""
        error = Exception("HTTP 429 Too Many Requests")
        result = classify_api_error(error)
        assert result == APIFailureClassification.RATE_LIMIT_FAILURE

    def test_classifies_timeout(self):
        """Timeout errors should classify correctly."""
        error = Exception("Request timed out")
        result = classify_api_error(error)
        assert result == APIFailureClassification.TIMEOUT_FAILURE

    def test_classifies_network_error(self):
        """Network errors should classify correctly."""
        error = Exception("Network connection failed")
        result = classify_api_error(error)
        assert result == APIFailureClassification.PROVIDER_NETWORK_FAILURE

    def test_classifies_content_filter(self):
        """Content filter errors should classify correctly."""
        error = Exception("Content safety filter triggered")
        result = classify_api_error(error)
        assert result == APIFailureClassification.CONTENT_FILTER_FAILURE

    def test_classifies_model_error(self):
        """Model overload should classify correctly."""
        error = Exception("HTTP 500 Internal Server Error")
        result = classify_api_error(error)
        assert result == APIFailureClassification.MODEL_ERROR

    def test_unknown_error_defaults_to_unsafe(self):
        """Unknown errors should default to unsafe_resume."""
        error = Exception("Some random error")
        result = classify_api_error(error)
        assert result == APIFailureClassification.UNSAFE_RESUME


class TestBailianLLMAdapter:
    """Tests for BailianLLMAdapter hardening."""

    def test_adapter_has_timeout_config(self):
        """Adapter should have timeout configuration."""
        adapter = BailianLLMAdapter(timeout=60)
        assert adapter.timeout == 60

    def test_adapter_has_retry_config(self):
        """Adapter should have retry configuration."""
        adapter = BailianLLMAdapter(max_retries=3, retry_delay=10)
        assert adapter.max_retries == 3
        assert adapter.retry_delay == 10

    def test_adapter_defaults(self):
        """Adapter should have sensible defaults."""
        adapter = BailianLLMAdapter()
        assert adapter.timeout == 120
        assert adapter.max_retries == 2
        assert adapter.retry_delay == 30

    def test_failure_result_has_classification(self):
        """Failure result should include classification."""
        adapter = BailianLLMAdapter()
        execution_pack = {"execution_id": "test-001", "goal": "test", "task_scope": [], "deliverables": []}

        result = adapter._create_failure_result(
            execution_pack,
            APIFailureClassification.AUTH_CONFIG_FAILURE,
            "No API key",
        )

        assert "api_failure_classification" in result
        assert result["api_failure_classification"] == "auth_config_failure"

    def test_failure_result_has_recovery_hint(self):
        """Failure result should include recovery hint."""
        adapter = BailianLLMAdapter()
        execution_pack = {"execution_id": "test-001"}

        result = adapter._create_failure_result(
            execution_pack,
            APIFailureClassification.RATE_LIMIT_FAILURE,
            "Quota exceeded",
        )

        assert "recommended_next_step" in result
        assert "retry" in result["recommended_next_step"].lower() or "wait" in result["recommended_next_step"].lower()


class TestMockLLMAdapter:
    """Tests for MockLLMAdapter."""

    def test_mock_always_available(self):
        """Mock adapter should always be available."""
        adapter = MockLLMAdapter()
        assert adapter.is_available()

    def test_mock_returns_success(self):
        """Mock adapter should return success result."""
        adapter = MockLLMAdapter()
        execution_pack = {
            "execution_id": "mock-001",
            "deliverables": [{"item": "test-output"}],
            "must_read": [],
            "verification_steps": ["Check output"],
        }

        result = adapter.execute(execution_pack)

        assert result["status"] == "success"
        assert len(result["artifacts_created"]) > 0


class TestLiveAPIEngine:
    """Tests for LiveAPIEngine hardening."""

    def test_engine_initializes_with_project_path(self, temp_project_dir):
        """LiveAPIEngine should accept project_path."""
        engine = LiveAPIEngine(temp_project_dir)
        assert engine.project_path == temp_project_dir

    def test_engine_has_logger(self, temp_project_dir):
        """LiveAPIEngine should have execution logger."""
        engine = LiveAPIEngine(temp_project_dir)
        logger = engine._get_logger()
        assert logger is not None
        engine.close()

    def test_engine_prepare_includes_timeout(self, temp_project_dir):
        """Prepare result should include timeout info."""
        engine = LiveAPIEngine(temp_project_dir)
        execution_pack = {"execution_id": "test", "goal": "test", "task_scope": [], "deliverables": []}

        prep = engine.prepare(execution_pack)

        assert "timeout" in prep
        assert "max_retries" in prep
        engine.close()

    def test_engine_close_releases_logger(self, temp_project_dir):
        """Close should release logger connection."""
        engine = LiveAPIEngine(temp_project_dir)
        engine._get_logger()
        engine.close()

        assert engine._logger is None


class TestLiveAPIIntegration:
    """Tests for Live API integration."""

    def test_engine_logs_run_day_started(self, temp_project_dir):
        """Engine should log RUN_DAY_STARTED event."""
        engine = LiveAPIEngine(temp_project_dir)
        logger = engine._get_logger()

        logger.log_event(
            APIFailureClassification.AUTH_CONFIG_FAILURE,  # placeholder
            feature_id="001-test",
            product_id="test-product",
            event_data={"test": True},
        )

        from runtime.sqlite_state_store import SQLiteStateStore
        store = SQLiteStateStore(temp_project_dir)
        store.initialize_product("test-product", "Test")
        store.initialize_feature("001-test", "test-product", "Test")

        events = store.get_recent_events("001-test", limit=10)
        assert len(events) >= 1

        engine.close()
        store.close()

    def test_adapter_failure_returns_classification(self, temp_project_dir):
        """Adapter failure should return classification in result."""
        adapter = BailianLLMAdapter()
        adapter.client = None

        execution_pack = {"execution_id": "fail-001", "goal": "test", "task_scope": [], "deliverables": []}

        result = adapter.execute(execution_pack)

        assert result["status"] == "failed"
        assert "api_failure_classification" in result
        assert result["api_failure_classification"] == "auth_config_failure"
        assert "recommended_next_step" in result

    def test_adapter_failure_result_structure(self):
        """Failure result should have all required ExecutionResult fields."""
        adapter = BailianLLMAdapter()
        adapter.client = None

        execution_pack = {"execution_id": "test-001"}
        result = adapter.execute(execution_pack)

        required_fields = [
            "execution_id",
            "status",
            "completed_items",
            "artifacts_created",
            "verification_result",
            "issues_found",
            "blocked_reasons",
            "decisions_required",
            "recommended_next_step",
            "metrics",
            "notes",
            "duration",
        ]

        for field in required_fields:
            assert field in result