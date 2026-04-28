"""
Website Analyzer Module
Detects NopCommerce installations and flags leads with no website.
"""

import time
import logging
from typing import Tuple
import requests
from bs4 import BeautifulSoup
from config import Config
from database import Database

logger = logging.getLogger(__name__)

# ── NopCommerce fingerprints ───────────────────────────────────────────────────
# These are reliable, publicly visible markers of a NopCommerce installation.

NOP_TEXT_MARKERS = [
    "nopcommerce",          # appears in HTML source, generator meta tag
    "nop-ajax-cart",        # CSS class used by nop theme
    "nopAjaxCartButton",    # JS variable / HTML attribute
    "/themes/default",      # default NopCommerce theme path
    "Powered by nopCommerce",
]

NOP_META_GENERATOR = "nopcommerce"  # <meta name="generator" content="nopCommerce ...">

# Paths that are unique to NopCommerce admin/backend
NOP_PROBE_PATHS = [
    "/Admin/Login",
    "/install",
]


class WebsiteAnalyzer:
    """Analyzes each lead's website (or lack thereof) and updates the database."""

    def __init__(self, config: Config, db: Database):
        self.config = config
        self.db = db
        self.session = self._build_session()

    # ── Public API ─────────────────────────────────────────────────────────────

    def analyze_all(self, limit: int = 50) -> dict:
        """
        Process all unanalyzed leads.
        Returns summary counts.
        """
        leads = self.db.get_unanalyzed_leads(limit=limit)
        logger.info(f"Analyzing {len(leads)} leads…")

        stats = {"analyzed": 0, "nopcommerce": 0, "no_website": 0}

        for lead in leads:
            lead_id  = lead["id"]
            name     = lead["name"]
            website  = lead["website"] or ""

            if not website:
                # No website at all – mark and move on
                logger.info(f"[NO WEBSITE] {name}")
                self.db.mark_lead_analyzed(lead_id, has_website=False, is_nopcommerce=False)
                stats["no_website"] += 1
            else:
                is_nop = self._check_nopcommerce(website, name)
                logger.info(f"[{'NOP' if is_nop else 'OTHER'}] {name} – {website}")
                self.db.mark_lead_analyzed(lead_id, has_website=True, is_nopcommerce=is_nop)
                if is_nop:
                    stats["nopcommerce"] += 1

            stats["analyzed"] += 1
            time.sleep(self.config.request_delay_seconds)

        return stats

    # ── NopCommerce Detection ──────────────────────────────────────────────────

    def _check_nopcommerce(self, url: str, name: str = "") -> bool:
        """
        Return True if the site at `url` appears to be running NopCommerce.
        Uses three complementary checks:
          1. HTML body / meta generator tag fingerprinting
          2. Known admin path probing
        """
        html = self._fetch_html(url)
        if html and self._fingerprint_html(html):
            logger.debug(f"NopCommerce confirmed via HTML fingerprint: {url}")
            return True

        if self._probe_admin_paths(url):
            logger.debug(f"NopCommerce confirmed via admin path probe: {url}")
            return True

        return False

    def _fingerprint_html(self, html: str) -> bool:
        """Check HTML source for NopCommerce markers."""
        lower_html = html.lower()

        # Fast text scan
        for marker in NOP_TEXT_MARKERS:
            if marker.lower() in lower_html:
                return True

        # Meta generator tag
        try:
            soup = BeautifulSoup(html, "html.parser")
            meta_gen = soup.find("meta", attrs={"name": "generator"})
            if meta_gen:
                content = meta_gen.get("content", "").lower()
                if NOP_META_GENERATOR in content:
                    return True
        except Exception as e:
            logger.debug(f"BeautifulSoup parse error: {e}")

        return False

    def _probe_admin_paths(self, base_url: str) -> bool:
        """
        Try known NopCommerce-specific paths.
        A 200 or redirect to /Admin/ strongly indicates NopCommerce.
        """
        base = base_url.rstrip("/")
        for path in NOP_PROBE_PATHS:
            probe_url = base + path
            try:
                resp = self.session.get(
                    probe_url,
                    timeout=self.config.request_timeout,
                    allow_redirects=True,
                )
                # NopCommerce /Admin redirects to /Admin/Login with 200
                if resp.status_code == 200 and "nopcommerce" in resp.text.lower():
                    return True
            except requests.RequestException:
                pass
            time.sleep(0.5)
        return False

    # ── HTTP helpers ───────────────────────────────────────────────────────────

    def _fetch_html(self, url: str) -> str:
        """Fetch and return raw HTML for a URL, or empty string on failure."""
        try:
            resp = self.session.get(url, timeout=self.config.request_timeout)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return ""

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "User-Agent": self.config.user_agent,
            "Accept-Language": "en-US,en;q=0.9",
        })
        return session
