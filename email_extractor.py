"""
Email Extractor Module
Crawls websites and extracts publicly visible email addresses.
Only collects email addresses that are plainly visible in the HTML source.
"""

import re
import time
import logging
from typing import Set, List
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from config import Config
from database import Database

logger = logging.getLogger(__name__)

# Regex for valid email addresses
EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

# Common disposable / system email patterns to filter out
IGNORED_EMAIL_PATTERNS = [
    "example.com", "test.com", "sentry", "noreply", "no-reply",
    "mailer-daemon", "postmaster", "webmaster@example", "user@example",
    ".png", ".jpg", ".gif", ".svg",   # image filenames mistaken for emails
]

# Page paths likely to contain contact info (checked in order)
CONTACT_PATHS = [
    "/contact", "/contact-us", "/contactus", "/about", "/about-us",
    "/reach-us", "/get-in-touch", "/support", "/help",
]


class EmailExtractor:
    """Crawls lead websites and stores any public email addresses found."""

    def __init__(self, config: Config, db: Database):
        self.config = config
        self.db = db
        self.session = self._build_session()

    # ── Public API ─────────────────────────────────────────────────────────────

    def extract_all(self, limit: int = 50) -> int:
        """
        Process leads that have a website but no email yet.
        Returns total number of new emails saved.
        """
        leads = self.db.get_leads_with_websites_no_emails(limit=limit)
        logger.info(f"Extracting emails from {len(leads)} leads…")

        total_emails = 0
        for lead in leads:
            lead_id = lead["id"]
            website = lead["website"]
            name    = lead["name"]

            emails = self._extract_from_site(website)
            for email in emails:
                self.db.save_email(lead_id, email, source_url=website)
                logger.info(f"  [{name}] found email: {email}")

            total_emails += len(emails)
            time.sleep(self.config.request_delay_seconds)

        logger.info(f"Email extraction complete – {total_emails} emails saved")
        return total_emails

    # ── Crawling Logic ─────────────────────────────────────────────────────────

    def _extract_from_site(self, base_url: str) -> Set[str]:
        """
        Crawl up to `max_crawl_pages` pages of `base_url` and collect emails.
        Starts on the homepage, then probes common contact-page paths.
        """
        found: Set[str] = set()
        pages_checked = 0
        max_pages = self.config.max_crawl_pages

        # 1. Homepage
        html = self._fetch(base_url)
        if html:
            found.update(self._extract_emails_from_html(html))
            pages_checked += 1

            # 2. Follow any contact/about links found in the nav
            if pages_checked < max_pages:
                contact_links = self._find_contact_links(html, base_url)
                for link in contact_links[:max_pages - pages_checked]:
                    sub_html = self._fetch(link)
                    if sub_html:
                        found.update(self._extract_emails_from_html(sub_html))
                    pages_checked += 1
                    time.sleep(0.5)

        # 3. Probe well-known contact paths (if still under budget)
        if pages_checked < max_pages:
            base = base_url.rstrip("/")
            for path in CONTACT_PATHS:
                if pages_checked >= max_pages:
                    break
                url = base + path
                html = self._fetch(url)
                if html:
                    found.update(self._extract_emails_from_html(html))
                    pages_checked += 1
                    time.sleep(0.5)

        return found

    def _find_contact_links(self, html: str, base_url: str) -> List[str]:
        """Return hrefs that look like contact/about pages."""
        links = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup.find_all("a", href=True):
                href = tag["href"].lower()
                text = tag.get_text(strip=True).lower()
                if any(kw in href or kw in text for kw in ("contact", "about", "reach", "support")):
                    full_url = urljoin(base_url, tag["href"])
                    # Keep same-domain links only
                    if urlparse(full_url).netloc == urlparse(base_url).netloc:
                        links.append(full_url)
        except Exception as e:
            logger.debug(f"Link parsing error: {e}")
        return list(dict.fromkeys(links))  # deduplicate preserving order

    # ── Email Extraction ───────────────────────────────────────────────────────

    def _extract_emails_from_html(self, html: str) -> Set[str]:
        """
        Extract email addresses using regex on the raw HTML.
        Also checks for mailto: links which are the most reliable source.
        """
        raw_matches: Set[str] = set()

        # 1. Regex over full HTML text (catches obfuscated text too)
        raw_matches.update(EMAIL_RE.findall(html))

        # 2. mailto: links via BeautifulSoup
        try:
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup.find_all("a", href=True):
                href = tag["href"]
                if href.lower().startswith("mailto:"):
                    addr = href[7:].split("?")[0].strip()
                    raw_matches.add(addr)
        except Exception:
            pass

        return {e for e in raw_matches if self._is_valid_email(e)}

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Filter out obviously invalid / system addresses."""
        email = email.lower().strip()
        if not email or len(email) > 254:
            return False
        for pattern in IGNORED_EMAIL_PATTERNS:
            if pattern in email:
                return False
        # Must have at least one dot in domain
        parts = email.split("@")
        if len(parts) != 2 or "." not in parts[1]:
            return False
        return True

    # ── HTTP ───────────────────────────────────────────────────────────────────

    def _fetch(self, url: str) -> str:
        """Fetch URL and return text, or empty string."""
        try:
            resp = self.session.get(url, timeout=self.config.request_timeout)
            if resp.status_code == 200:
                return resp.text
            return ""
        except requests.RequestException as e:
            logger.debug(f"Fetch failed {url}: {e}")
            return ""

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        })
        return session
