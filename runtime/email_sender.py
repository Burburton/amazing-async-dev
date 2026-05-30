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


def render_html_email(template_name: str, context: dict[str, Any]) -> str:
    """Render HTML email template.

    Args:
        template_name: Name of template file (without path)
        context: Template context dict

    Returns:
        Rendered HTML string
    """
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        templates_path = Path(__file__).parent.parent / "templates" / "email"
        if not templates_path.exists():
            return ""

        env = Environment(
            loader=FileSystemLoader(str(templates_path)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        env.filters["default"] = lambda v, d="": v if v else d

        template = env.get_template(template_name)
        return template.render(**context)
    except ImportError:
        return ""
    except Exception:
        return ""


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

        self.config.mock_outbox_path.mkdir(parents=True, exist_ok=True)

        subject, plain_text, html_text = self._build_multipart_email(request)
        email_content = self._build_email_content(request)

        content_for_file = f"{email_content}\n\n--- HTML VERSION ---\n\n{html_text}"

        with open(mock_path, "w", encoding="utf-8") as f:
            f.write(content_for_file)

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

        subject, plain_text, html_text = self._build_multipart_email(request)

        msg = MIMEMultipart("alternative")
        msg["From"] = self.config.from_address
        msg["To"] = to_address
        msg["Subject"] = subject

        msg.attach(MIMEText(plain_text, "plain"))
        if html_text:
            msg.attach(MIMEText(html_text, "html"))

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

        subject, plain_text, html_text = self._build_multipart_email(request)

        msg = MIMEMultipart("alternative")
        msg["From"] = email
        msg["To"] = to_address
        msg["Subject"] = subject

        msg.attach(MIMEText(plain_text, "plain"))
        if html_text:
            msg.attach(MIMEText(html_text, "html"))

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

    def _build_multipart_email(self, request: dict[str, Any]) -> tuple[str, str, str]:
        """Build multipart email (subject, plain_text, html_text)."""
        subject = self._build_subject(request)
        plain_text = self._build_body(request)
        html_text = self._build_html_body(request)
        return subject, plain_text, html_text
    
    def _build_subject(self, request: dict[str, Any]) -> str:
        """Build email subject with urgency, project, and time estimate."""
        product_id = request.get("product_id", "unknown")
        feature_id = request.get("feature_id", "")
        request_id = request.get("decision_request_id", "")
        question = request.get("question", "")
        severity = request.get("severity", "medium")
        time_estimate = request.get("time_estimate", "~2min")

        severity_icons = {
            "critical": "CRITICAL",
            "high": "Decision",
            "medium": "Review",
            "low": "Update",
            "info": "Info",
        }

        severity_text = severity_icons.get(severity.lower(), "Decision")

        if question and len(question) > 40:
            question_short = question[:37] + "..."
        elif question:
            question_short = question
        else:
            question_short = "Decision needed"

        return f"{self.config.subject_prefix} {severity_text}: {question_short} | {product_id} | {time_estimate}"
    
    def _build_body(self, request: dict[str, Any]) -> str:
        """Build email body."""
        lines = []
        
        severity = request.get("severity", "medium").upper()
        product_id = request.get("product_id", "unknown")
        feature_id = request.get("feature_id", "")
        request_id = request.get("decision_request_id", "")
        question = request.get("question", "")
        options = request.get("options", [])
        recommendation = request.get("recommendation", "")
        defer_impact = request.get("defer_impact", "")
        reply_hint = request.get("reply_format_hint", "")
        next_action = request.get("recommended_next_action_after_reply", "")
        
        lines.append("=" * 60)
        lines.append(f"⚠️  DECISION REQUIRED  [{severity}]")
        lines.append("=" * 60)
        lines.append(f"Project: {product_id}")
        if feature_id:
            lines.append(f"Feature: {feature_id}")
        lines.append(f"Time estimate: {request.get('time_estimate', '~2min')}")
        lines.append("-" * 60)
        
        lines.append(f"\n📋 {question}\n")
        
        if recommendation:
            lines.append(f"💡 AI Recommendation: {recommendation}\n")
        
        lines.append("Options:")
        for i, opt in enumerate(options, 1):
            opt_id = opt.get("id", "?")
            label = opt.get("label", "")
            desc = opt.get("description", "")
            marker = "→" if recommendation and label in recommendation else " "
            lines.append(f"  {marker} [{opt_id}] {label}")
            if desc:
                lines.append(f"      {desc}")
        
        if defer_impact:
            lines.append(f"\n⚠️  If Deferred: {defer_impact}")
        
        if next_action:
            lines.append(f"\n📅 After Reply: {next_action}")
        
        lines.append(f"\nReply: {reply_hint}")
        
        exec_context = request.get("execution_context", {})
        if exec_context:
            lines.append("\n" + "=" * 60)
            lines.append("📋 TODAY'S PROGRESS")
            lines.append("=" * 60)
            
            completed = exec_context.get("completed_items", [])
            if completed:
                lines.append(f"\n✅ Completed ({len(completed)}):")
                for item in completed[:5]:
                    lines.append(f"   • {item}")
                if len(completed) > 5:
                    lines.append(f"   • ... and {len(completed) - 5} more")
            
            artifacts = exec_context.get("artifacts_created", [])
            if artifacts:
                lines.append(f"\n📄 Artifacts ({len(artifacts)}):")
                for art in artifacts[:5]:
                    if isinstance(art, dict):
                        lines.append(f"   • {art.get('name', 'unknown')} ({art.get('type', 'file')})")
                    else:
                        lines.append(f"   • {art}")
                if len(artifacts) > 5:
                    lines.append(f"   • ... and {len(artifacts) - 5} more")
            
            issues = exec_context.get("issues_found", [])
            if issues:
                lines.append(f"\n⚠️  Issues ({len(issues)}):")
                for issue in issues[:3]:
                    lines.append(f"   • {issue}")
                if len(issues) > 3:
                    lines.append(f"   • ... and {len(issues) - 3} more")
            
            status = exec_context.get("status", "")
            duration = exec_context.get("duration", "")
            if status:
                lines.append(f"\n🔧 Execution: {status}" + (f" | {duration}" if duration else ""))
        
        project_progress = request.get("project_progress", {})
        if project_progress:
            lines.append("\n" + "=" * 60)
            lines.append("📊 PROJECT PROGRESS")
            lines.append("=" * 60)
            lines.append(f"Status: {project_progress.get('project_status', 'N/A')}")
            lines.append(f"Progress: {project_progress.get('progress_percent', 'N/A')}")
            lines.append(f"Phases: {project_progress.get('phases_complete_count', 0)} complete")
            if project_progress.get('current_feature'):
                lines.append(f"Feature: {project_progress.get('current_feature')}")
            if project_progress.get('health_status'):
                lines.append(f"Health: {project_progress.get('health_status')}")
        
        lines.append("\n" + "=" * 60)
        lines.append(f"Request ID: {request_id}")
        lines.append(f"Sent: {request.get('sent_at', datetime.now().isoformat())}")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _build_html_body(self, request: dict[str, Any]) -> str:
        """Build HTML email body using template."""
        template_context = {
            "subject": self._build_subject(request),
            "product_id": request.get("product_id", "unknown"),
            "feature_id": request.get("feature_id", ""),
            "request_id": request.get("decision_request_id", ""),
            "question": request.get("question", ""),
            "options": request.get("options", []),
            "recommendation": request.get("recommendation", ""),
            "defer_impact": request.get("defer_impact", ""),
            "reply_hint": request.get("reply_format_hint", ""),
            "next_action": request.get("recommended_next_action_after_reply", ""),
            "sent_at": request.get("sent_at", datetime.now().isoformat()),
            "reply_base_url": request.get("reply_base_url", "https://async-dev.example.com/reply"),
            "severity": request.get("severity", "medium"),
            "time_estimate": request.get("time_estimate", "~2min"),
            "execution_context": request.get("execution_context", {}),
            "project_progress": request.get("project_progress", {}),
        }

        html = render_html_email("decision-request.html", template_context)
        if not html:
            html = self._build_body_as_html_fallback(request)

        return html

    def _build_body_as_html_fallback(self, request: dict[str, Any]) -> str:
        """Fallback HTML if template rendering fails."""
        options_html = ""
        for opt in request.get("options", []):
            opt_id = opt.get("id", "?")
            label = opt.get("label", "")
            desc = opt.get("description", "")
            options_html += f'<li>[{opt_id}] <strong>{label}</strong> - {desc}</li>'

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h1>⚠️ Decision Required</h1>
            <p><strong>Project:</strong> {request.get('product_id', 'unknown')}</p>
            <p><strong>Feature:</strong> {request.get('feature_id', '')}</p>
            <h2>{request.get('question', '')}</h2>
            <ul>{options_html}</ul>
            <p><em>Recommendation: {request.get('recommendation', '')}</em></p>
        </body>
        </html>
        """
    
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

    def send_day_end_summary(
        self,
        review_pack: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Send day-end summary email.
        
        Args:
            review_pack: DailyReviewPack dict
            
        Returns:
            (success, mock_path_if_mock_mode)
        """
        if self.config.delivery_mode == "mock_file":
            return self._send_day_end_mock(review_pack)
        elif self.config.delivery_mode == "console":
            return self._send_day_end_console(review_pack)
        elif self.config.delivery_mode == "resend":
            return self._send_day_end_resend(review_pack)
        else:
            return self._send_day_end_smtp(review_pack)

    def _send_day_end_resend(self, review_pack: dict[str, Any]) -> tuple[bool, str | None]:
        from runtime.resend_provider import ResendProvider, ResendConfig
        
        resend_config = ResendConfig()
        if not resend_config.is_configured():
            return False, None
        
        provider = ResendProvider(resend_config)
        success, message_id, response = provider.send_day_end_summary(review_pack)
        
        return success, message_id

    def _send_day_end_mock(self, review_pack: dict[str, Any]) -> tuple[bool, str]:
        summary_id = review_pack.get("date", datetime.now().strftime("%Y%m%d"))
        mock_path = self.config.mock_outbox_path / f"day-end-{summary_id}.md"
        
        self.config.mock_outbox_path.mkdir(parents=True, exist_ok=True)
        
        subject = self._build_day_end_subject(review_pack)
        plain_text = self._build_day_end_body(review_pack)
        html_text = self._build_day_end_html_body(review_pack)
        
        content_for_file = f"Subject: {subject}\n\n{plain_text}\n\n--- HTML VERSION ---\n\n{html_text}"
        
        with open(mock_path, "w", encoding="utf-8") as f:
            f.write(content_for_file)
        
        return True, str(mock_path)

    def _send_day_end_console(self, review_pack: dict[str, Any]) -> tuple[bool, None]:
        subject = self._build_day_end_subject(review_pack)
        plain_text = self._build_day_end_body(review_pack)
        print("\n" + "="*60)
        print("DAY-END SUMMARY EMAIL (console mode)")
        print("="*60)
        print(f"Subject: {subject}")
        print("-"*60)
        print(plain_text)
        print("="*60 + "\n")
        return True, None

    def _send_day_end_smtp(self, review_pack: dict[str, Any]) -> tuple[bool, None]:
        if not self.config.is_smtp_configured():
            return False, None
        
        to_address = self.config.to_address
        
        subject = self._build_day_end_subject(review_pack)
        body = self._build_day_end_body(review_pack)
        
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

    def _build_day_end_subject(self, review_pack: dict[str, Any]) -> str:
        project_id = review_pack.get("project_id", "unknown")
        date = review_pack.get("date", "")
        decisions_count = len(review_pack.get("decisions_needed", []))
        blocked_count = len(review_pack.get("blocked_items", []))
        
        status_suffix = ""
        if decisions_count > 0:
            status_suffix = f" [{decisions_count} decisions needed]"
        elif blocked_count > 0:
            status_suffix = f" [{blocked_count} blocked]"
        
        return f"{self.config.subject_prefix} Daily Summary: {project_id} - {date}{status_suffix}"

    def _build_day_end_body(self, review_pack: dict[str, Any]) -> str:
        lines = []
        
        date = review_pack.get("date", "")
        project_id = review_pack.get("project_id", "")
        feature_id = review_pack.get("feature_id", "")
        today_goal = review_pack.get("today_goal", "")
        
        lines.append("=" * 60)
        lines.append("📋  DAILY REVIEW SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Date: {date}")
        lines.append(f"Project: {project_id}")
        if feature_id:
            lines.append(f"Feature: {feature_id}")
        
        completed = review_pack.get("what_was_completed", [])
        blocked = review_pack.get("blocked_items", [])
        decisions = review_pack.get("decisions_needed", [])
        
        summary_parts = []
        if completed:
            summary_parts.append(f"✅ {len(completed)} completed")
        if blocked:
            summary_parts.append(f"🚫 {len(blocked)} blocked")
        if decisions:
            summary_parts.append(f"⚠️ {len(decisions)} decisions")
        if summary_parts:
            lines.append(" | ".join(summary_parts))
        
        lines.append("-" * 60)
        
        if today_goal:
            lines.append(f"\n🎯 Today's Goal: {today_goal}\n")
        
        if completed:
            lines.append("✅ COMPLETED")
            lines.append("-" * 40)
            for item in completed:
                if isinstance(item, dict):
                    lines.append(f"  ✓ {item.get('item', '')}")
                else:
                    lines.append(f"  ✓ {item}")
            lines.append("")
        
        evidence = review_pack.get("evidence", [])
        if evidence:
            lines.append("📄 EVIDENCE CREATED")
            lines.append("-" * 40)
            for e in evidence:
                if isinstance(e, dict):
                    lines.append(f"  • {e.get('name', 'unknown')} ({e.get('type', 'file')})")
                else:
                    lines.append(f"  • {e}")
            lines.append("")
        
        if blocked:
            lines.append("🚫 BLOCKED ITEMS")
            lines.append("-" * 40)
            for block in blocked:
                reason = block.get("reason", block.get("item", "Unknown blocker"))
                lines.append(f"  ⚠ {reason}")
                if block.get("resolution"):
                    lines.append(f"    → Resolution: {block['resolution']}")
            lines.append("")
        
        if decisions:
            lines.append("⚠️ DECISIONS REQUIRED")
            lines.append("-" * 40)
            for i, decision in enumerate(decisions, 1):
                question = decision.get("decision", decision.get("question", "Decision needed"))
                lines.append(f"  {i}. {question}")
                
                options = decision.get("options", [])
                if options:
                    for opt in options:
                        if isinstance(opt, str):
                            lines.append(f"     • {opt}")
                        elif isinstance(opt, dict):
                            opt_id = opt.get("id", "?")
                            label = opt.get("label", "")
                            lines.append(f"     [{opt_id}] {label}")
                
                recommendation = decision.get("recommendation", "")
                if recommendation:
                    lines.append(f"     💡 Recommended: {recommendation}")
            lines.append("")
        
        tomorrow_plan = review_pack.get("tomorrow_plan", "")
        if tomorrow_plan:
            lines.append("📅 TOMORROW'S PLAN")
            lines.append("-" * 40)
            lines.append(f"  {tomorrow_plan}")
            lines.append("")
        
        doctor_assessment = review_pack.get("doctor_assessment", {})
        if doctor_assessment:
            status = doctor_assessment.get("doctor_status", "")
            if status:
                lines.append("🏥 WORKSPACE STATUS")
                lines.append("-" * 40)
                lines.append(f"  {status}")
            recommended = doctor_assessment.get("recommended_action", "")
            if recommended:
                lines.append(f"  → {recommended}")
            lines.append("")
        
        issues_summary = review_pack.get("issues_summary", {})
        metrics = review_pack.get("metrics_summary", {})
        project_progress = review_pack.get("project_progress", {})
        
        if metrics or project_progress or (issues_summary and issues_summary.get("total_issues", 0) > 0):
            lines.append("📊 METRICS & PROGRESS")
            lines.append("-" * 40)
            
            if metrics:
                duration = metrics.get("execution_time", "")
                files_read = metrics.get("files_read", "")
                files_written = metrics.get("files_written", "")
                if duration:
                    lines.append(f"  ⏱️  Duration: {duration}")
                if files_read or files_written:
                    lines.append(f"  📁 Files: {files_read} read, {files_written} written")
            
            if issues_summary:
                total_issues = issues_summary.get("total_issues", 0)
                if total_issues > 0:
                    lines.append(f"  ⚠️  Issues: {total_issues}")
            
            if project_progress:
                lines.append(f"  📈 Status: {project_progress.get('project_status', 'N/A')}")
                lines.append(f"  📊 Progress: {project_progress.get('progress_percent', 'N/A')}")
                lines.append(f"  � phase: {project_progress.get('phases_complete_count', 0)} phases complete")
            
            lines.append("")
        
        lines.append("=" * 60)
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append("=" * 60)
        
        return "\n".join(lines)

    def _build_day_end_html_body(self, review_pack: dict[str, Any]) -> str:
        template_context = {
            "date": review_pack.get("date", ""),
            "project_id": review_pack.get("project_id", "unknown"),
            "feature_id": review_pack.get("feature_id", ""),
            "completed": review_pack.get("what_was_completed", []),
            "evidence": review_pack.get("evidence", []),
            "blocked": review_pack.get("blocked_items", []),
            "decisions": review_pack.get("decisions_needed", []),
            "tomorrow_plan": review_pack.get("tomorrow_plan", ""),
            "doctor_status": review_pack.get("doctor_assessment", {}).get("doctor_status", ""),
            "recommended_action": review_pack.get("doctor_assessment", {}).get("recommended_action", ""),
            "issues_summary": review_pack.get("issues_summary", {}),
            "metrics_summary": review_pack.get("metrics_summary", {}),
            "reply_base_url": review_pack.get("reply_base_url", "https://async-dev.example.com/reply"),
            "project_progress": review_pack.get("project_progress", {}),
        }
        
        html = render_html_email("day-end-summary.html", template_context)
        if not html:
            return self._build_day_end_html_fallback(review_pack)
        
        return html

    def _build_day_end_html_fallback(self, review_pack: dict[str, Any]) -> str:
        completed = review_pack.get("what_was_completed", [])
        decisions = review_pack.get("decisions_needed", [])
        blocked = review_pack.get("blocked_items", [])
        
        completed_html = ""
        for item in completed:
            if isinstance(item, dict):
                completed_html += f"<li>{item.get('item', '')}</li>"
            else:
                completed_html += f"<li>{item}</li>"
        
        decisions_html = ""
        for i, decision in enumerate(decisions, 1):
            decisions_html += f"<h3>{i}. {decision.get('decision', 'Decision needed')}</h3>"
            for opt in decision.get("options", []):
                if isinstance(opt, dict):
                    decisions_html += f"<p>[{opt.get('id', '?')}] {opt.get('label', '')}</p>"
        
        blocked_html = ""
        for block in blocked:
            blocked_html += f"<p>⚠ {block.get('reason', block.get('item', 'Unknown'))}</p>"
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h1>📋 Daily Review Summary</h1>
            <p><strong>Project:</strong> {review_pack.get('project_id', 'unknown')}</p>
            <p><strong>Date:</strong> {review_pack.get('date', '')}</p>
            <h2>Completed</h2>
            <ul>{completed_html}</ul>
            <h2>Blocked</h2>
            {blocked_html or '<p>None</p>'}
            <h2>Decisions</h2>
            {decisions_html or '<p>None required</p>'}
        </body>
        </html>
        """


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


def send_day_end_summary_email(
    review_pack: dict[str, Any],
    runtime_path: Path,
) -> tuple[bool, str | None]:
    """Send day-end summary email using configured mode.
    
    Args:
        review_pack: DailyReviewPack dict
        runtime_path: Runtime path for config
        
    Returns:
        (success, mock_path_if_mock)
    """
    config = create_email_config(runtime_path)
    sender = EmailSender(config)
    return sender.send_day_end_summary(review_pack)