"""Email sender for async decision channel (Feature 021).

Supports SMTP, mock file, and Gmail OAuth2 delivery modes.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailConfig:
    """Email configuration loaded from env and config file."""
    
    def __init__(self, config_path: Path | None = None) -> None:
        self.smtp_host = os.getenv("ASYNCDEV_SMTP_HOST", "")
        self.smtp_port = int(os.getenv("ASYNCDEV_SMTP_PORT", "587"))
        self.smtp_username = os.getenv("ASYNCDEV_SMTP_USERNAME", "")
        self.smtp_password = os.getenv("ASYNCDEV_SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("ASYNCDEV_SMTP_USE_TLS", "true").lower() == "true"
        
        self.from_address = os.getenv("ASYNCDEV_FROM_ADDRESS", "asyncdev@localhost")
        self.to_address = os.getenv("ASYNCDEV_TO_ADDRESS", "")
        
        self.delivery_mode = os.getenv("ASYNCDEV_DELIVERY_MODE", "mock_file")
        self.mock_outbox_path = Path(os.getenv("ASYNCDEV_MOCK_OUTBOX", ".runtime/email-outbox"))
        self.subject_prefix = os.getenv("ASYNCDEV_SUBJECT_PREFIX", "[async-dev]")
        
        self.use_oauth2 = os.getenv("ASYNCDEV_USE_OAUTH2", "false").lower() == "true"
        self.oauth2_token_path = Path(os.getenv("ASYNCDEV_OAUTH2_TOKEN_PATH", ".runtime/gmail-oauth2-token.json"))
        
        self.use_resend = os.getenv("RESEND_API_KEY", "") != ""
        
        if config_path and config_path.exists():
            self._load_config_file(config_path)
    
    def _load_config_file(self, config_path: Path) -> None:
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
        
        if not self.smtp_host:
            self.smtp_host = config.get("smtp_host", "")
        if not self.to_address:
            self.to_address = config.get("to_address", "")
        
        self.delivery_mode = config.get("delivery_mode", self.delivery_mode)
        self.mock_outbox_path = Path(config.get("mock_outbox_path", str(self.mock_outbox_path)))
        self.subject_prefix = config.get("email_subject_prefix", self.subject_prefix)
        
        if config.get("use_oauth2"):
            self.use_oauth2 = True
        if config.get("oauth2_token_path"):
            self.oauth2_token_path = Path(config.get("oauth2_token_path"))
    
    def is_smtp_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_username and self.smtp_password)
    
    def is_oauth2_configured(self) -> bool:
        if self.use_oauth2:
            from runtime.gmail_oauth2 import is_gmail_oauth2_configured
            return is_gmail_oauth2_configured(self.oauth2_token_path)
        return False
    
    def is_resend_configured(self) -> bool:
        from runtime.resend_provider import is_resend_configured
        return is_resend_configured()
    
    def can_send_email(self) -> bool:
        return self.is_smtp_configured() or self.is_oauth2_configured() or self.is_resend_configured()


class EmailSender:
    """Email sender with SMTP and mock support."""
    
    def __init__(self, config: EmailConfig) -> None:
        self.config = config
        if config.delivery_mode == "mock_file":
            config.mock_outbox_path.mkdir(parents=True, exist_ok=True)
    
    def send_decision_request(
        self,
        request: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Send decision request email.
        
        Args:
            request: Decision request dict
            
        Returns:
            (success, mock_path_if_mock_mode)
        """
        if self.config.delivery_mode == "mock_file":
            return self._send_mock(request)
        elif self.config.delivery_mode == "console":
            return self._send_console(request)
        elif self.config.delivery_mode == "resend":
            return self._send_resend(request)
        else:
            return self._send_smtp(request)
    
    def _send_resend(self, request: dict[str, Any]) -> tuple[bool, str | None]:
        """Send via Resend API."""
        from runtime.resend_provider import ResendProvider, ResendConfig
        
        resend_config = ResendConfig()
        if not resend_config.is_configured():
            return False, None
        
        provider = ResendProvider(resend_config)
        success, message_id, response = provider.send_decision_request(request)
        
        return success, message_id
    
    def _send_mock(self, request: dict[str, Any]) -> tuple[bool, str]:
        """Mock send - write to file."""
        request_id = request.get("decision_request_id", "unknown")
        mock_path = self.config.mock_outbox_path / f"{request_id}.md"
        
        email_content = self._build_email_content(request)
        
        with open(mock_path, "w") as f:
            f.write(email_content)
        
        return True, str(mock_path)
    
    def _send_console(self, request: dict[str, Any]) -> tuple[bool, None]:
        """Console send - output to stdout."""
        email_content = self._build_email_content(request)
        print("\n" + "="*60)
        print("DECISION EMAIL (console mode)")
        print("="*60)
        print(email_content)
        print("="*60 + "\n")
        return True, None
    
    def _send_smtp(self, request: dict[str, Any]) -> tuple[bool, None]:
        """Real SMTP send with OAuth2 or password auth."""
        if self.config.use_oauth2:
            return self._send_smtp_oauth2(request)
        else:
            return self._send_smtp_password(request)
    
    def _send_smtp_password(self, request: dict[str, Any]) -> tuple[bool, None]:
        """SMTP send with username/password auth."""
        if not self.config.is_smtp_configured():
            return False, None
        
        to_address = self.config.to_address
        if not to_address:
            to_address = request.get("email_to", "")
        
        subject = self._build_subject(request)
        body = self._build_body(request)
        
        msg = MIMEMultipart()
        msg["From"] = self.config.from_address
        msg["To"] = to_address
        msg["Subject"] = subject
        
        msg.attach(MIMEText(body, "plain"))
        
        try:
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=30) as server:
                if self.config.smtp_use_tls:
                    server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.sendmail(self.config.from_address, [to_address], msg.as_string())
            return True, None
        except Exception:
            return False, None
    
    def _send_smtp_oauth2(self, request: dict[str, Any]) -> tuple[bool, None]:
        """SMTP send with Gmail XOAUTH2."""
        from runtime.gmail_oauth2 import GmailOAuth2Config
        
        oauth2_config = GmailOAuth2Config(self.config.oauth2_token_path)
        
        if not oauth2_config.is_configured():
            return False, None
        
        auth_string = oauth2_config.get_auth_string()
        email = oauth2_config.get_email()
        
        if not auth_string or not email:
            return False, None
        
        to_address = self.config.to_address
        if not to_address:
            to_address = email
        
        subject = self._build_subject(request)
        body = self._build_body(request)
        
        msg = MIMEMultipart()
        msg["From"] = email
        msg["To"] = to_address
        msg["Subject"] = subject
        
        msg.attach(MIMEText(body, "plain"))
        
        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                server.starttls()
                server.docmd("AUTH XOAUTH2 " + auth_string)
                server.sendmail(email, [to_address], msg.as_string())
            return True, None
        except Exception:
            return False, None
    
    def _build_email_content(self, request: dict[str, Any]) -> str:
        """Build full email content."""
        subject = self._build_subject(request)
        body = self._build_body(request)
        
        return f"Subject: {subject}\n\n{body}"
    
    def _build_subject(self, request: dict[str, Any]) -> str:
        """Build email subject."""
        product_id = request.get("product_id", "unknown")
        feature_id = request.get("feature_id", "")
        request_id = request.get("decision_request_id", "")
        
        return f"{self.config.subject_prefix} Decision needed: {product_id} / {feature_id} [{request_id}]"
    
    def _build_body(self, request: dict[str, Any]) -> str:
        """Build email body."""
        request_id = request.get("decision_request_id", "")
        question = request.get("question", "")
        options = request.get("options", [])
        recommendation = request.get("recommendation", "")
        defer_impact = request.get("defer_impact", "")
        reply_hint = request.get("reply_format_hint", "")
        next_action = request.get("recommended_next_action_after_reply", "")
        
        lines = [
            f"Decision Request: {request_id}",
            "",
            f"Question: {question}",
            "",
            "Options:",
        ]
        
        for opt in options:
            opt_id = opt.get("id", "?")
            label = opt.get("label", "")
            desc = opt.get("description", "")
            lines.append(f"  [{opt_id}] {label} - {desc}")
        
        lines.extend([
            "",
            f"Recommendation: {recommendation}",
            "",
        ])
        
        if defer_impact:
            lines.extend([
                f"If deferred: {defer_impact}",
                "",
            ])
        
        lines.extend([
            f"Reply format: {reply_hint}",
            "",
        ])
        
        if next_action:
            lines.extend([
                f"After reply: {next_action}",
                "",
            ])
        
        lines.extend([
            "---",
            f"Request ID: {request_id}",
            f"Sent at: {request.get('sent_at', datetime.now().isoformat())}",
        ])
        
        return "\n".join(lines)
    
    def send_status_report(
        self,
        report: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Send status report email.
        
        Args:
            report: Status report dict
            
        Returns:
            (success, mock_path_if_mock_mode)
        """
        if self.config.delivery_mode == "mock_file":
            return self._send_status_mock(report)
        elif self.config.delivery_mode == "console":
            return self._send_status_console(report)
        elif self.config.delivery_mode == "resend":
            return self._send_status_resend(report)
        else:
            return self._send_status_smtp(report)
    
    def _send_status_resend(self, report: dict[str, Any]) -> tuple[bool, str | None]:
        from runtime.resend_provider import ResendProvider, ResendConfig
        
        resend_config = ResendConfig()
        if not resend_config.is_configured():
            return False, None
        
        provider = ResendProvider(resend_config)
        success, message_id, response = provider.send_status_report(report)
        
        return success, message_id
    
    def _send_status_mock(self, report: dict[str, Any]) -> tuple[bool, str]:
        report_id = report.get("report_id", "unknown")
        mock_path = self.config.mock_outbox_path / f"{report_id}.md"
        
        email_content = self._build_status_email_content(report)
        
        with open(mock_path, "w") as f:
            f.write(email_content)
        
        return True, str(mock_path)
    
    def _send_status_console(self, report: dict[str, Any]) -> tuple[bool, None]:
        email_content = self._build_status_email_content(report)
        print("\n" + "="*60)
        print("STATUS REPORT EMAIL (console mode)")
        print("="*60)
        print(email_content)
        print("="*60 + "\n")
        return True, None
    
    def _send_status_smtp(self, report: dict[str, Any]) -> tuple[bool, None]:
        if self.config.use_oauth2:
            return self._send_status_smtp_oauth2(report)
        else:
            return self._send_status_smtp_password(report)
    
    def _send_status_smtp_password(self, report: dict[str, Any]) -> tuple[bool, None]:
        if not self.config.is_smtp_configured():
            return False, None
        
        to_address = self.config.to_address
        
        subject = self._build_status_subject(report)
        body = self._build_status_body(report)
        
        msg = MIMEMultipart()
        msg["From"] = self.config.from_address
        msg["To"] = to_address
        msg["Subject"] = subject
        
        msg.attach(MIMEText(body, "plain"))
        
        try:
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=30) as server:
                if self.config.smtp_use_tls:
                    server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.sendmail(self.config.from_address, [to_address], msg.as_string())
            return True, None
        except Exception:
            return False, None
    
    def _send_status_smtp_oauth2(self, report: dict[str, Any]) -> tuple[bool, None]:
        from runtime.gmail_oauth2 import GmailOAuth2Config
        
        oauth2_config = GmailOAuth2Config(self.config.oauth2_token_path)
        
        if not oauth2_config.is_configured():
            return False, None
        
        auth_string = oauth2_config.get_auth_string()
        email = oauth2_config.get_email()
        
        if not auth_string or not email:
            return False, None
        
        to_address = self.config.to_address
        if not to_address:
            to_address = email
        
        subject = self._build_status_subject(report)
        body = self._build_status_body(report)
        
        msg = MIMEMultipart()
        msg["From"] = email
        msg["To"] = to_address
        msg["Subject"] = subject
        
        msg.attach(MIMEText(body, "plain"))
        
        try:
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                server.starttls()
                server.docmd("AUTH XOAUTH2 " + auth_string)
                server.sendmail(email, [to_address], msg.as_string())
            return True, None
        except Exception:
            return False, None
    
    def _build_status_email_content(self, report: dict[str, Any]) -> str:
        subject = self._build_status_subject(report)
        body = self._build_status_body(report)
        return f"Subject: {subject}\n\n{body}"
    
    def _build_status_subject(self, report: dict[str, Any]) -> str:
        report_type = report.get("report_type", "progress")
        project_id = report.get("project_id", "")
        report_id = report.get("report_id", "")
        
        type_labels = {
            "progress": "Progress",
            "milestone": "Milestone",
            "blocker": "BLOCKER",
            "dogfood": "Dogfood",
        }
        
        type_label = type_labels.get(report_type, "Status")
        
        return f"{self.config.subject_prefix} {type_label}: {project_id} [{report_id}]"
    
    def _build_status_body(self, report: dict[str, Any]) -> str:
        from runtime.status_report_builder import format_report_for_email
        return format_report_for_email(report)


def create_email_config(runtime_path: Path) -> EmailConfig:
    """Create email config from runtime path."""
    config_path = runtime_path / ".runtime" / "email-config.yaml"
    return EmailConfig(config_path)


def send_decision_email(
    request: dict[str, Any],
    runtime_path: Path,
) -> tuple[bool, str | None]:
    """Send decision email using configured mode.
    
    Args:
        request: Decision request
        runtime_path: Runtime path for config
        
    Returns:
        (success, mock_path_if_mock)
    """
    config = create_email_config(runtime_path)
    sender = EmailSender(config)
    return sender.send_decision_request(request)


def send_status_report_email(
    report: dict[str, Any],
    runtime_path: Path,
) -> tuple[bool, str | None]:
    """Send status report email using configured mode (Feature 044).
    
    Args:
        report: Status report dict
        runtime_path: Runtime path for config
        
    Returns:
        (success, mock_path_if_mock)
    """
    config = create_email_config(runtime_path)
    sender = EmailSender(config)
    return sender.send_status_report(report)