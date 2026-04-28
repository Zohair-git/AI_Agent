"""
Configuration Module
Loads settings from .env file and environment variables
"""

import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """Central configuration class. All settings sourced from .env or env vars."""

    def __init__(self, env_file: str = ".env"):
        load_dotenv(env_file)

        # ── Database ──────────────────────────────────────────────────────────
        self.db_path: str = os.getenv("DB_PATH", "leads.db")

        # ── Google Maps / Places API ──────────────────────────────────────────
        self.google_maps_api_key: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
        if not self.google_maps_api_key:
            logger.warning("GOOGLE_MAPS_API_KEY not set – lead collection will fail.")

        # ── Email (SMTP) ──────────────────────────────────────────────────────
        self.smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user: str = os.getenv("SMTP_USER", "")
        self.smtp_password: str = os.getenv("SMTP_PASSWORD", "")
        self.sender_name: str = os.getenv("SENDER_NAME", "Your Name")
        self.sender_email: str = os.getenv("SENDER_EMAIL", self.smtp_user)

        # ── SendGrid (optional alternative) ───────────────────────────────────
        self.use_sendgrid: bool = os.getenv("USE_SENDGRID", "false").lower() == "true"
        self.sendgrid_api_key: str = os.getenv("SENDGRID_API_KEY", "")

        # ── Rate Limits ───────────────────────────────────────────────────────
        self.max_emails_per_hour: int = int(os.getenv("MAX_EMAILS_PER_HOUR", "10"))
        self.request_delay_seconds: float = float(os.getenv("REQUEST_DELAY_SECONDS", "2.0"))
        self.max_crawl_pages: int = int(os.getenv("MAX_CRAWL_PAGES", "3"))

        # ── Email Template ────────────────────────────────────────────────────
        self.email_subject: str = os.getenv(
            "EMAIL_SUBJECT",
            "Improve your business online presence"
        )
        self.email_body_template: str = os.getenv(
            "EMAIL_BODY_TEMPLATE",
            (
                "Hi {business_name},\n\n"
                "I came across your business and noticed it may not have a website, "
                "or could benefit from a more modern online store.\n\n"
                "I specialize in building fast, scalable eCommerce solutions. "
                "I'd love to help you establish or improve your online presence.\n\n"
                "Would you be open to a quick 15-minute chat?\n\n"
                "Best regards,\n{sender_name}"
            )
        )

        # ── Scheduler ─────────────────────────────────────────────────────────
        self.schedule_collect_interval_hours: int = int(
            os.getenv("SCHEDULE_COLLECT_INTERVAL_HOURS", "24")
        )
        self.schedule_send_interval_hours: int = int(
            os.getenv("SCHEDULE_SEND_INTERVAL_HOURS", "6")
        )

        # ── HTTP ──────────────────────────────────────────────────────────────
        self.request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "10"))
        self.user_agent: str = os.getenv(
            "USER_AGENT",
            "Mozilla/5.0 (compatible; LeadGenBot/1.0; +https://example.com/bot)"
        )

    def validate(self) -> bool:
        """Return True if the minimum required settings are present."""
        ok = True
        if not self.google_maps_api_key:
            logger.error("Missing GOOGLE_MAPS_API_KEY")
            ok = False
        if not self.smtp_user and not self.use_sendgrid:
            logger.warning("No SMTP_USER set – emails will fail unless USE_SENDGRID=true")
        return ok
