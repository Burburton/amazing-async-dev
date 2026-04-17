"""Resend email provider integration (Feature 053).

Provides outbound email sending via Resend API and inbound webhook handling.
"""

import json
import os
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any


RESEND_API_URL = "https://api.resend.com"
RESEND_SEND_ENDPOINT = "/emails"
RESEND_RATE_LIMIT_PER_SECOND = 5


RESEND_TEST_ADDRESS = "delivered@resend.dev"
RESEND_TEST_ADDRESSES = {
    "delivered": "delivered@resend.dev",
    "bounced": "bounced@resend.dev",
    "complained": "complained@resend.dev",
    "suppressed": "suppressed@resend.dev",
}


class ResendConfig:
    """Resend API configuration."""
    
    def __init__(self) -> None:
        self.api_key = os.getenv("RESEND_API_KEY", "")
        self.from_email = os.getenv("RESEND_FROM_EMAIL", "")
        self.webhook_secret = os.getenv("RESEND_WEBHOOK_SECRET", "")
        self.sandbox_mode = os.getenv("RESEND_SANDBOX_MODE", "false").lower() == "true"
    
    def is_configured(self) -> bool:
        """Check if Resend is properly configured."""
        return bool(self.api_key and self.from_email)
    
    def get_test_address(self) -> str:
        """Get test email address for sandbox mode."""
        return RESEND_TEST_ADDRESS


class ResendProvider:
    """Resend email provider for sending emails via API."""
    
    def __init__(self, config: ResendConfig | None = None) -> None:
        self.config = config or ResendConfig()
    
    def send_email(
        self,
        to: str | list[str],
        subject: str,
        html: str | None = None,
        text: str | None = None,
        reply_to: str | None = None,
        headers: dict[str, str] | None = None,
        request_id: str | None = None,
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Send email via Resend API.
        
        Args:
            to: Recipient email address(es)
            subject: Email subject
            html: HTML body (optional)
            text: Plain text body (optional)
            reply_to: Reply-to address (optional)
            headers: Custom headers (optional)
            request_id: Decision request ID for correlation (optional)
            
        Returns:
            (success, message_id, response_data)
        """
        if not self.config.is_configured():
            return False, None, {"error": "Resend not configured"}
        
        if isinstance(to, str):
            to = [to]
        
        payload = {
            "from": self.config.from_email,
            "to": to,
            "subject": subject,
        }
        
        if html:
            payload["html"] = html
        if text:
            payload["text"] = text
        if reply_to:
            payload["reply_to"] = reply_to
        if headers:
            payload["headers"] = headers
        
        if self.config.sandbox_mode:
            payload["to"] = [self.config.get_test_address()]
        
        return self._call_api(payload)
    
    def send_decision_request(
        self,
        request: dict[str, Any],
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Send decision request email.
        
        Args:
            request: Decision request dict
            
        Returns:
            (success, message_id, response_data)
        """
        from runtime.email_sender import EmailSender, EmailConfig
        
        config = EmailConfig()
        sender = EmailSender(config)
        
        subject = sender._build_subject(request)
        body = sender._build_body(request)
        
        request_id = request.get("decision_request_id")
        
        return self.send_email(
            to=self.config.from_email if self.config.sandbox_mode else (config.to_address or self.config.from_email),
            subject=subject,
            text=body,
            headers={"X-Decision-Request-Id": request_id} if request_id else None,
            request_id=request_id,
        )
    
    def send_status_report(
        self,
        report: dict[str, Any],
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Send status report email.
        
        Args:
            report: Status report dict
            
        Returns:
            (success, message_id, response_data)
        """
        from runtime.email_sender import EmailSender, EmailConfig
        from runtime.status_report_builder import format_report_for_email
        
        config = EmailConfig()
        sender = EmailSender(config)
        
        subject = sender._build_status_subject(report)
        body = format_report_for_email(report)
        
        report_id = report.get("report_id")
        
        return self.send_email(
            to=self.config.from_email if self.config.sandbox_mode else (config.to_address or self.config.from_email),
            subject=subject,
            text=body,
            headers={"X-Report-Id": report_id} if report_id else None,
        )
    
    def _call_api(
        self,
        payload: dict[str, Any],
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Call Resend API.
        
        Args:
            payload: JSON payload
            
        Returns:
            (success, message_id, response_data)
        """
        url = RESEND_API_URL + RESEND_SEND_ENDPOINT
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "amazing-async-dev/1.0",
        }
        
        data = json.dumps(payload).encode("utf-8")
        
        try:
            req = urllib.request.Request(
                url,
                data=data,
                headers=headers,
                method="POST",
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                
                message_id = result.get("id")
                
                return True, message_id, {
                    "id": message_id,
                    "sent_at": datetime.now().isoformat(),
                    "to": payload.get("to"),
                    "subject": payload.get("subject"),
                }
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            return False, None, {
                "error": f"HTTP {e.code}: {error_body}",
                "status_code": e.code,
            }
        except Exception as e:
            return False, None, {"error": str(e)}
    
    def test_connection(self) -> tuple[bool, str]:
        """Test Resend API connection.
        
        Returns:
            (success, explanation)
        """
        if not self.config.api_key:
            return False, "No API key configured"
        
        if not self.config.from_email:
            return False, "No from_email configured"
        
        success, message_id, response = self.send_email(
            to=RESEND_TEST_ADDRESS,
            subject="Test connection from async-dev",
            text="This is a test email to verify Resend integration.",
        )
        
        if success:
            return True, f"Test email sent successfully. Message ID: {message_id}"
        else:
            return False, f"Failed: {response.get('error', 'Unknown error')}"


class ResendWebhookHandler:
    """Handler for Resend webhook events."""
    
    def __init__(self, config: ResendConfig | None = None) -> None:
        self.config = config or ResendConfig()
    
    def handle_event(
        self,
        payload: dict[str, Any],
        signature: str | None = None,
    ) -> dict[str, Any]:
        """Handle webhook event from Resend.
        
        Args:
            payload: Webhook payload
            signature: Webhook signature for verification (optional)
            
        Returns:
            Processing result
        """
        event_type = payload.get("type", "")
        
        if event_type == "email.received":
            return self._handle_email_received(payload)
        elif event_type == "email.sent":
            return self._handle_email_sent(payload)
        elif event_type == "email.delivered":
            return self._handle_email_delivered(payload)
        elif event_type == "email.bounced":
            return self._handle_email_bounced(payload)
        else:
            return {"status": "ignored", "event_type": event_type}
    
    def _handle_email_received(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle inbound email received event.
        
        Args:
            payload: Webhook payload
            
        Returns:
            Processing result
        """
        data = payload.get("data", {})
        
        email_id = data.get("email_id")
        from_address = data.get("from", {}).get("address")
        to_address = data.get("to", [{}])[0].get("address") if data.get("to") else None
        subject = data.get("subject")
        
        result = {
            "status": "processed",
            "event_type": "email.received",
            "email_id": email_id,
            "from": from_address,
            "to": to_address,
            "subject": subject,
        }
        
        headers = data.get("headers", [])
        decision_request_id = None
        
        for header in headers:
            if header.get("name") == "X-Decision-Request-Id":
                decision_request_id = header.get("value")
                break
        
        if decision_request_id:
            result["decision_request_id"] = decision_request_id
            result["linked"] = True
        
        return result
    
    def _handle_email_sent(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle email sent event.
        
        Args:
            payload: Webhook payload
            
        Returns:
            Processing result
        """
        data = payload.get("data", {})
        
        return {
            "status": "recorded",
            "event_type": "email.sent",
            "email_id": data.get("email_id"),
            "from": data.get("from"),
            "to": data.get("to"),
            "created_at": data.get("created_at"),
        }
    
    def _handle_email_delivered(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle email delivered event.
        
        Args:
            payload: Webhook payload
            
        Returns:
            Processing result
        """
        data = payload.get("data", {})
        
        return {
            "status": "recorded",
            "event_type": "email.delivered",
            "email_id": data.get("email_id"),
            "delivered_at": data.get("created_at"),
        }
    
    def _handle_email_bounced(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle email bounced event.
        
        Args:
            payload: Webhook payload
            
        Returns:
            Processing result
        """
        data = payload.get("data", {})
        
        from runtime.email_failure_handler import FailureRecordStore, FailureType
        
        email_id = data.get("email_id")
        
        result = {
            "status": "recorded",
            "event_type": "email.bounced",
            "email_id": email_id,
            "bounced_at": data.get("created_at"),
        }
        
        return result
    
    def parse_reply_from_payload(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Parse reply content from webhook payload.
        
        Args:
            payload: Webhook payload
            
        Returns:
            Reply dict or None
        """
        if payload.get("type") != "email.received":
            return None
        
        data = payload.get("data", {})
        
        reply_text = data.get("text") or data.get("html")
        
        if not reply_text:
            return None
        
        headers = data.get("headers", [])
        decision_request_id = None
        
        for header in headers:
            if header.get("name") == "X-Decision-Request-Id":
                decision_request_id = header.get("value")
                break
        
        if not decision_request_id:
            subject = data.get("subject", "")
            import re
            match = re.search(r"\[dr-[0-9]{8}-[0-9]{3}\]", subject)
            if match:
                decision_request_id = match.group(0).strip("[]")
        
        return {
            "decision_request_id": decision_request_id,
            "reply_text": reply_text,
            "from": data.get("from", {}).get("address"),
            "email_id": data.get("email_id"),
            "received_at": payload.get("created_at"),
        }


def create_resend_config() -> ResendConfig:
    """Create Resend config from environment."""
    return ResendConfig()


def is_resend_configured() -> bool:
    """Check if Resend is configured."""
    return ResendConfig().is_configured()


def format_resend_setup_instructions() -> str:
    """Format setup instructions for Resend."""
    return """
## Resend Setup Instructions

### Step 1: Create Resend Account

1. Go to https://resend.com/
2. Sign up for an account
3. Verify your email

### Step 2: Get API Key

1. Go to https://resend.com/api-keys
2. Create a new API key
3. Copy the key (starts with `re_`)

### Step 3: Verify Sender Email

1. Go to https://resend.com/domains
2. Add your domain
3. Verify ownership (DNS records)
4. Use verified email as sender

### Step 4: Configure Environment Variables

```bash
export RESEND_API_KEY=re_xxxxxxxxxxxxx
export RESEND_FROM_EMAIL=noreply@yourdomain.com
export ASYNCDEV_DELIVERY_MODE=resend
```

### Step 5: Test Connection

```bash
asyncdev resend-auth test
```

### Webhook Setup (for inbound replies)

1. Go to https://resend.com/webhooks
2. Create webhook endpoint
3. Subscribe to events: email.received, email.sent
4. Copy webhook secret

```bash
export RESEND_WEBHOOK_SECRET=whsec_xxxxx
```

### Test Addresses (for safe testing)

Use these addresses to test without real delivery:
- delivered@resend.dev (simulates successful delivery)
- bounced@resend.dev (simulates bounce)
- complained@resend.dev (simulates spam complaint)
- suppressed@resend.dev (simulates suppression)

### Sandbox Mode

```bash
export RESEND_SANDBOX_MODE=true
```

All emails will go to delivered@resend.dev
"""