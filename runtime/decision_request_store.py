"""Decision request store for async human decision channel (Feature 021)."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
import json


class DecisionRequestStatus(str, Enum):
    """Status of decision request."""
    
    PENDING = "pending"
    SENT = "sent"
    REPLY_RECEIVED = "reply_received"
    REPLY_VALIDATING = "reply_validating"
    REPLY_INVALID = "reply_invalid"
    RESOLVED = "resolved"
    EXPIRED = "expired"


class DecisionType(str, Enum):
    """Type of decision needed."""
    
    TECHNICAL = "technical"
    SCOPE = "scope"
    PRIORITY = "priority"
    DESIGN = "design"
    RISKY_CONFIRMATION = "risky_confirmation"
    BLOCKER_RESOLUTION = "blocker_resolution"
    OTHER = "other"


class DeliveryChannel(str, Enum):
    """Channel for decision delivery."""
    
    EMAIL = "email"
    MOCK_FILE = "mock_file"
    CONSOLE = "console"
    RESEND = "resend"


class DecisionRequestStore:
    """Store for decision request lifecycle management."""
    
    DEFAULT_OUTBOX_PATH = ".runtime/email-outbox"
    DEFAULT_REQUESTS_PATH = ".runtime/decision-requests"
    
    def __init__(self, runtime_path: Path) -> None:
        self.runtime_path = runtime_path
        self.requests_path = runtime_path / self.DEFAULT_REQUESTS_PATH
        self.outbox_path = runtime_path / self.DEFAULT_OUTBOX_PATH
        self.requests_path.mkdir(parents=True, exist_ok=True)
        self.outbox_path.mkdir(parents=True, exist_ok=True)
    
    def generate_request_id(self) -> str:
        """Generate unique decision request ID."""
        today = datetime.now().strftime("%Y%m%d")
        existing = list(self.requests_path.glob(f"dr-{today}-*.json"))
        next_num = len(existing) + 1
        return f"dr-{today}-{next_num:03d}"
    
    def create_request(
        self,
        product_id: str,
        feature_id: str,
        pause_reason_category: str,
        decision_type: DecisionType,
        question: str,
        options: list[dict[str, str]],
        recommendation: str,
        defer_impact: str | None = None,
        recommended_next_action: str | None = None,
        expires_hours: int | None = None,
        delivery_channel: DeliveryChannel = DeliveryChannel.MOCK_FILE,
    ) -> dict[str, Any]:
        """Create a new decision request.
        
        Args:
            product_id: Product context
            feature_id: Feature context
            pause_reason_category: From Feature 020 pause reason
            decision_type: Type of decision
            question: The decision question
            options: Available options with id, label, description
            recommendation: AI recommendation
            defer_impact: What happens if deferred
            recommended_next_action: What happens after valid reply
            expires_hours: Hours until expiration
            delivery_channel: How to deliver
            
        Returns:
            Created decision request
        """
        request_id = self.generate_request_id()
        now = datetime.now().isoformat()
        
        expires_at = None
        if expires_hours:
            expires_dt = datetime.now() + timedelta(hours=expires_hours)
            expires_at = expires_dt.isoformat()
        
        request = {
            "decision_request_id": request_id,
            "product_id": product_id,
            "feature_id": feature_id,
            "pause_reason_category": pause_reason_category,
            "decision_type": decision_type.value,
            "question": question,
            "options": options,
            "recommendation": recommendation,
            "reply_format_hint": self._build_reply_hint(options),
            "defer_impact": defer_impact,
            "recommended_next_action_after_reply": recommended_next_action,
            "expires_at": expires_at,
            "delivery_channel": delivery_channel.value,
            "sent_at": now,
            "status": DecisionRequestStatus.PENDING.value,
        }
        
        self.save_request(request)
        return request
    
    def _build_reply_hint(self, options: list[dict[str, str]]) -> str:
        """Build reply format hint from options."""
        option_ids = [opt.get("id", "?") for opt in options]
        commands = [f"DECISION {id}" for id in option_ids]
        commands.extend(["DEFER", "RETRY"])
        return f"Reply with: {', '.join(commands)}"
    
    def save_request(self, request: dict[str, Any]) -> None:
        """Save decision request to file."""
        request_id = request.get("decision_request_id", "unknown")
        file_path = self.requests_path / f"{request_id}.json"
        with open(file_path, "w") as f:
            json.dump(request, f, indent=2)
    
    def load_request(self, request_id: str) -> dict[str, Any] | None:
        """Load decision request by ID."""
        file_path = self.requests_path / f"{request_id}.json"
        if not file_path.exists():
            return None
        with open(file_path) as f:
            return json.load(f)
    
    def list_requests(
        self,
        status: DecisionRequestStatus | None = None,
    ) -> list[dict[str, Any]]:
        """List decision requests, optionally filtered by status."""
        requests = []
        for file_path in self.requests_path.glob("dr-*.json"):
            with open(file_path) as f:
                request = json.load(f)
                if status is None or request.get("status") == status.value:
                    requests.append(request)
        return sorted(requests, key=lambda r: r.get("sent_at", ""))
    
    def update_request_status(
        self,
        request_id: str,
        status: DecisionRequestStatus,
        resolution: str | None = None,
        reply_raw_text: str | None = None,
    ) -> dict[str, Any] | None:
        """Update decision request status."""
        request = self.load_request(request_id)
        if not request:
            return None
        
        request["status"] = status.value
        now = datetime.now().isoformat()
        
        if status == DecisionRequestStatus.REPLY_RECEIVED:
            request["reply_received_at"] = now
            request["reply_raw_text"] = reply_raw_text
        
        if status == DecisionRequestStatus.RESOLVED:
            request["resolved_at"] = now
            request["resolution"] = resolution
        
        self.save_request(request)
        return request
    
    def mark_sent(
        self,
        request_id: str,
        email_to: str | None = None,
        email_subject: str | None = None,
        mock_path: str | None = None,
    ) -> dict[str, Any] | None:
        """Mark request as sent."""
        request = self.load_request(request_id)
        if not request:
            return None
        
        request["status"] = DecisionRequestStatus.SENT.value
        
        if email_to:
            request["email_to"] = email_to
        if email_subject:
            request["email_subject"] = email_subject
        if mock_path:
            request["email_sent_mock_path"] = mock_path
        
        self.save_request(request)
        return request
    
    def check_expired(self) -> list[dict[str, Any]]:
        """Check for expired requests and update their status."""
        now = datetime.now()
        expired = []
        
        for request in self.list_requests(status=DecisionRequestStatus.SENT):
            expires_at = request.get("expires_at")
            if expires_at:
                expires_dt = datetime.fromisoformat(expires_at)
                if now > expires_dt:
                    self.update_request_status(
                        request["decision_request_id"],
                        DecisionRequestStatus.EXPIRED,
                    )
                    expired.append(request)
        
        return expired
    
    def get_pending_for_product(
        self,
        product_id: str,
        feature_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get pending decision requests for a product."""
        requests = self.list_requests(status=DecisionRequestStatus.SENT)
        filtered = [r for r in requests if r.get("product_id") == product_id]
        if feature_id:
            filtered = [r for r in filtered if r.get("feature_id") == feature_id]
        return filtered
    
    def get_statistics(self) -> dict[str, int]:
        """Get statistics about decision requests."""
        stats = {}
        for status in DecisionRequestStatus:
            count = len(self.list_requests(status=status))
            stats[status.value] = count
        return stats


from datetime import timedelta  # Import at end to avoid circular reference