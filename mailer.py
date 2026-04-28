"""
Mailer Module
Sends personalized outreach emails via SMTP (or optionally SendGrid).
Includes per-hour throttling and full logging of every attempt.
"""

import smtplib
import logging
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from config import Config
from database import Database

logger = logging.getLogger(__name__)


class Mailer:
    """Handles personalized outreach email sending with throttling."""

    def __init__(self, config: Config, db: Database):
        self.config = config
        self.db = db

    # ── Public API ─────────────────────────────────────────────────────────────

    def send_outreach(self, limit: int = 10, dry_run: bool = False) -> int:
        """
        Send (or simulate) outreach emails to qualifying leads.
        Returns the number of emails sent / simulated.
        """
        sent = 0
        leads = self.db.get_leads_for_outreach(limit=limit)

        if not leads:
            logger.info("No qualifying leads to email right now.")
            return 0

        logger.info(f"{'[DRY-RUN] ' if dry_run else ''}Preparing to send {len(leads)} emails…")

        for lead in leads:
            # ── Throttle check ────────────────────────────────────────────────
            emails_this_hour = self.db.emails_sent_last_hour()
            if emails_this_hour >= self.config.max_emails_per_hour:
                logger.warning(
                    f"Hourly cap reached ({emails_this_hour}/{self.config.max_emails_per_hour}). "
                    "Stopping for now."
                )
                break

            lead_id      = lead["id"]
            business_name = lead["name"]
            recipient     = lead["email"]
            subject       = self.config.email_subject
            body          = self._render_body(business_name)

            if dry_run:
                logger.info(f"  [SIMULATED] → {recipient} | {business_name}")
                self.db.log_outreach(lead_id, recipient, subject, status="simulated")
                sent += 1
            else:
                success, error = self._send_email(recipient, subject, body)
                status    = "sent" if success else "failed"
                error_msg = "" if success else error
                self.db.log_outreach(lead_id, recipient, subject, status, error_msg)

                if success:
                    logger.info(f"  ✉  Sent → {recipient} | {business_name}")
                    sent += 1
                else:
                    logger.error(f"  ✗  Failed → {recipient} | {error}")

            # Brief pause between sends (anti-spam courtesy)
            time.sleep(max(1.0, 3600 / max(self.config.max_emails_per_hour, 1)))

        return sent

    # ── Template Rendering ─────────────────────────────────────────────────────

    def _render_body(self, business_name: str) -> str:
        return self.config.email_body_template.format(
            business_name=business_name,
            sender_name=self.config.sender_name,
        )

    # ── SMTP Sending ───────────────────────────────────────────────────────────

    def _send_email(self, to: str, subject: str, body: str) -> tuple[bool, str]:
        """
        Send a single email via SMTP (TLS).
        Returns (success: bool, error_message: str).
        """
        if self.config.use_sendgrid:
            return self._send_via_sendgrid(to, subject, body)
        return self._send_via_smtp(to, subject, body)

    def _send_via_smtp(self, to: str, subject: str, body: str) -> tuple[bool, str]:
        """Send via Python smtplib with STARTTLS."""
        if not self.config.smtp_user or not self.config.smtp_password:
            return False, "SMTP credentials not configured"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{self.config.sender_name} <{self.config.sender_email}>"
        msg["To"]      = to
        msg.attach(MIMEText(body, "plain", "utf-8"))

        try:
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.config.smtp_user, self.config.smtp_password)
                server.sendmail(self.config.sender_email, to, msg.as_string())
            return True, ""
        except smtplib.SMTPException as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {e}"

    def _send_via_sendgrid(self, to: str, subject: str, body: str) -> tuple[bool, str]:
        """Send via SendGrid REST API (optional)."""
        try:
            import sendgrid  # type: ignore
            from sendgrid.helpers.mail import Mail  # type: ignore
        except ImportError:
            return False, "sendgrid package not installed"

        if not self.config.sendgrid_api_key:
            return False, "SENDGRID_API_KEY not configured"

        mail = Mail(
            from_email=self.config.sender_email,
            to_emails=to,
            subject=subject,
            plain_text_content=body,
        )
        try:
            sg = sendgrid.SendGridAPIClient(api_key=self.config.sendgrid_api_key)
            response = sg.send(mail)
            if response.status_code in (200, 202):
                return True, ""
            return False, f"SendGrid status {response.status_code}"
        except Exception as e:
            return False, str(e)
