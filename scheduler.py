"""
Scheduler Module
Runs the collection → analysis → extraction → email pipeline on a timer.
Uses APScheduler for robust job management.
"""

import logging
from config import Config
from database import Database
from collector import LeadCollector
from analyzer import WebsiteAnalyzer
from email_extractor import EmailExtractor
from mailer import Mailer

logger = logging.getLogger(__name__)


class Scheduler:
    """Orchestrates periodic pipeline execution."""

    def __init__(self, config: Config, db: Database):
        self.config = config
        self.db = db

    def start(self) -> None:
        """Start the scheduler (blocking – runs until Ctrl+C)."""
        try:
            from apscheduler.schedulers.blocking import BlockingScheduler  # type: ignore
        except ImportError:
            logger.error("APScheduler not installed. Run: pip install apscheduler")
            return

        scheduler = BlockingScheduler(timezone="UTC")

        # Run analysis + email pipeline every N hours
        scheduler.add_job(
            self._run_pipeline,
            "interval",
            hours=self.config.schedule_send_interval_hours,
            id="pipeline",
            max_instances=1,
        )

        logger.info(
            f"Scheduler started – pipeline every {self.config.schedule_send_interval_hours}h"
        )

        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped.")

    # ── Jobs ───────────────────────────────────────────────────────────────────

    def _run_pipeline(self) -> None:
        """Single pipeline run: analyze → extract → send."""
        logger.info("═══ Scheduled pipeline starting ═══")

        try:
            analyzer  = WebsiteAnalyzer(self.config, self.db)
            extractor = EmailExtractor(self.config, self.db)
            mailer    = Mailer(self.config, self.db)

            result = analyzer.analyze_all(limit=20)
            logger.info(f"Analysis: {result}")

            email_count = extractor.extract_all(limit=20)
            logger.info(f"Emails extracted: {email_count}")

            sent = mailer.send_outreach(limit=self.config.max_emails_per_hour)
            logger.info(f"Emails sent: {sent}")

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)

        logger.info("═══ Scheduled pipeline complete ═══")
