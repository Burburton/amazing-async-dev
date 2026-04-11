"""API failure classification for Live API execution errors."""

from enum import Enum


class APIFailureClassification(str, Enum):
    """Classification of Live API execution failures.
    
    These classifications determine retry behavior and recovery actions.
    """
    
    AUTH_CONFIG_FAILURE = "auth_config_failure"
    """Authentication/configuration failure.
    
    Cause: Missing API key, invalid credentials, misconfigured endpoint
    Recovery: Fix configuration, retry not recommended until fixed
    """
    
    PROVIDER_NETWORK_FAILURE = "provider_network_failure"
    """Provider or network connectivity failure.
    
    Cause: API endpoint unreachable, network timeout, DNS failure
    Recovery: Retry after delay, check network connectivity
    """
    
    TIMEOUT_FAILURE = "timeout_failure"
    """Request timeout exceeded.
    
    Cause: Slow response, complex task, provider overload
    Recovery: Retry with simpler request or longer timeout
    """
    
    RATE_LIMIT_FAILURE = "rate_limit_failure"
    """Rate limit exceeded.
    
    Cause: Too many requests, quota exhausted
    Recovery: Wait for reset, retry later
    """
    
    MALFORMED_RESPONSE = "malformed_response"
    """Response could not be parsed.
    
    Cause: Invalid JSON, unexpected format, truncated output
    Recovery: Check prompt format, retry with clearer instructions
    """
    
    VALIDATION_FAILURE = "validation_failure"
    """Response failed ExecutionResult validation.
    
    Cause: Missing required fields, invalid status, inconsistent data
    Recovery: Retry with stricter prompt, manual inspection
    """
    
    PARTIAL_RESULT = "partial_result"
    """Execution produced incomplete result.
    
    Cause: Task interrupted, resource limits, early termination
    Recovery: May preserve partial result, retry for completion
    """
    
    UNSAFE_RESUME = "unsafe_resume"
    """Failure state cannot be safely recovered.
    
    Cause: State corruption, ambiguous outcome, missing context
    Recovery: Manual inspection required, do not auto-resume
    """
    
    CONTENT_FILTER_FAILURE = "content_filter_failure"
    """Content filter blocked request/response.
    
    Cause: Safety policy violation, sensitive content detected
    Recovery: Adjust task content, use different approach
    """
    
    MODEL_ERROR = "model_error"
    """Model-specific error.
    
    Cause: Model overload, internal error, capacity issue
    Recovery: Retry, switch model, wait for recovery
    """


RETRYABLE_FAILURES = {
    APIFailureClassification.PROVIDER_NETWORK_FAILURE,
    APIFailureClassification.TIMEOUT_FAILURE,
    APIFailureClassification.RATE_LIMIT_FAILURE,
    APIFailureClassification.MODEL_ERROR,
}

NO_RETRY_FAILURES = {
    APIFailureClassification.AUTH_CONFIG_FAILURE,
    APIFailureClassification.MALFORMED_RESPONSE,
    APIFailureClassification.VALIDATION_FAILURE,
    APIFailureClassification.UNSAFE_RESUME,
    APIFailureClassification.CONTENT_FILTER_FAILURE,
}


def is_retryable(failure: APIFailureClassification) -> bool:
    """Check if failure type is safe to retry."""
    return failure in RETRYABLE_FAILURES


def get_recovery_hint(failure: APIFailureClassification) -> str:
    """Get actionable recovery hint for failure type."""
    hints = {
        APIFailureClassification.AUTH_CONFIG_FAILURE: "Fix API key configuration, then retry",
        APIFailureClassification.PROVIDER_NETWORK_FAILURE: "Check network, retry after 30s delay",
        APIFailureClassification.TIMEOUT_FAILURE: "Simplify request or increase timeout",
        APIFailureClassification.RATE_LIMIT_FAILURE: "Wait for quota reset, retry later",
        APIFailureClassification.MALFORMED_RESPONSE: "Check prompt format, manual inspection",
        APIFailureClassification.VALIDATION_FAILURE: "Retry with stricter output requirements",
        APIFailureClassification.PARTIAL_RESULT: "Review partial result, retry for completion",
        APIFailureClassification.UNSAFE_RESUME: "Manual inspection required before retry",
        APIFailureClassification.CONTENT_FILTER_FAILURE: "Adjust task content, use alternative approach",
        APIFailureClassification.MODEL_ERROR: "Retry immediately, or switch model",
    }
    return hints.get(failure, "Check logs and retry manually")


def classify_api_error(error: Exception) -> APIFailureClassification:
    """Classify an API exception into failure type.
    
    Args:
        error: Exception from API call
        
    Returns:
        APIFailureClassification for the error
    """
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()
    
    # Authentication errors
    if "auth" in error_str or "key" in error_str or "credential" in error_str:
        return APIFailureClassification.AUTH_CONFIG_FAILURE
    if "401" in error_str or "403" in error_str:
        return APIFailureClassification.AUTH_CONFIG_FAILURE
    
    # Rate limit
    if "rate" in error_str or "limit" in error_str or "quota" in error_str:
        return APIFailureClassification.RATE_LIMIT_FAILURE
    if "429" in error_str:
        return APIFailureClassification.RATE_LIMIT_FAILURE
    
    # Timeout
    if "timeout" in error_str or "timed out" in error_str:
        return APIFailureClassification.TIMEOUT_FAILURE
    
    # Network/connectivity
    if "network" in error_str or "connect" in error_str or "unreachable" in error_str:
        return APIFailureClassification.PROVIDER_NETWORK_FAILURE
    if "connection" in error_type or "connectionerror" in error_type:
        return APIFailureClassification.PROVIDER_NETWORK_FAILURE
    
    # Content filter
    if "filter" in error_str or "safety" in error_str or "content" in error_str:
        return APIFailureClassification.CONTENT_FILTER_FAILURE
    
    # Model errors
    if "model" in error_str or "capacity" in error_str or "overload" in error_str:
        return APIFailureClassification.MODEL_ERROR
    if "500" in error_str or "503" in error_str:
        return APIFailureClassification.MODEL_ERROR
    
    # Default to unsafe resume for unknown errors
    return APIFailureClassification.UNSAFE_RESUME