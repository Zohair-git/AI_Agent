"""
Database Module
SQLite-backed persistence layer for leads, emails, and outreach logs.
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class Database:
    """Thread-safe SQLite wrapper for all lead-gen data."""

    def __init__(self, db_path: str = "leads.db"):
        self.db_path = db_path

    # ── Connection ─────────────────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row          # dict-like rows
        conn.execute("PRAGMA journal_mode=WAL")  # better concurrency
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    # ── Schema ─────────────────────────────────────────────────────────────────

    def initialize(self) -> None:
        """Create tables if they don't exist."""
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS leads (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    place_id        TEXT UNIQUE,          -- Google Maps place_id
                    name            TEXT NOT NULL,
                    address         TEXT,
                    phone           TEXT,
                    website         TEXT,
                    has_website     INTEGER DEFAULT 0,     -- 0=no, 1=yes
                    is_nopcommerce  INTEGER DEFAULT 0,     -- 0=no, 1=yes
                    analyzed        INTEGER DEFAULT 0,     -- 0=pending, 1=done
                    keyword         TEXT,
                    location        TEXT,
                    created_at      TEXT DEFAULT (datetime('now')),
                    updated_at      TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS emails (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id     INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
                    email       TEXT NOT NULL,
                    source_url  TEXT,
                    created_at  TEXT DEFAULT (datetime('now')),
                    UNIQUE(lead_id, email)
                );

                CREATE TABLE IF NOT EXISTS outreach_log (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id     INTEGER REFERENCES leads(id),
                    email       TEXT NOT NULL,
                    subject     TEXT,
                    status      TEXT NOT NULL,   -- sent | failed | simulated
                    error_msg   TEXT,
                    sent_at     TEXT DEFAULT (datetime('now'))
                );

                CREATE INDEX IF NOT EXISTS idx_leads_analyzed   ON leads(analyzed);
                CREATE INDEX IF NOT EXISTS idx_leads_website    ON leads(has_website);
                CREATE INDEX IF NOT EXISTS idx_leads_nop        ON leads(is_nopcommerce);
                CREATE INDEX IF NOT EXISTS idx_emails_lead_id   ON emails(lead_id);
                CREATE INDEX IF NOT EXISTS idx_outreach_email   ON outreach_log(email);
            """)
        logger.info(f"Database initialized at '{self.db_path}'")

    # ── Leads ──────────────────────────────────────────────────────────────────

    def upsert_lead(self, lead: Dict[str, Any]) -> Optional[int]:
        """Insert or update a lead; return its row id."""
        sql = """
            INSERT INTO leads (place_id, name, address, phone, website, has_website, keyword, location)
            VALUES (:place_id, :name, :address, :phone, :website, :has_website, :keyword, :location)
            ON CONFLICT(place_id) DO UPDATE SET
                name        = excluded.name,
                address     = excluded.address,
                phone       = excluded.phone,
                website     = excluded.website,
                has_website = excluded.has_website,
                updated_at  = datetime('now')
        """
        try:
            with self._connect() as conn:
                cur = conn.execute(sql, lead)
                # For upserts we need the id of either the new or existing row
                if cur.lastrowid:
                    return cur.lastrowid
                row = conn.execute("SELECT id FROM leads WHERE place_id=?", (lead["place_id"],)).fetchone()
                return row["id"] if row else None
        except sqlite3.Error as e:
            logger.error(f"upsert_lead error: {e}")
            return None

    def get_unanalyzed_leads(self, limit: int = 50) -> List[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM leads WHERE analyzed=0 LIMIT ?", (limit,)
            ).fetchall()

    def get_leads_with_websites_no_emails(self, limit: int = 50) -> List[sqlite3.Row]:
        """Leads that have a website but no emails extracted yet."""
        sql = """
            SELECT l.* FROM leads l
            WHERE l.has_website = 1
              AND NOT EXISTS (SELECT 1 FROM emails e WHERE e.lead_id = l.id)
            LIMIT ?
        """
        with self._connect() as conn:
            return conn.execute(sql, (limit,)).fetchall()

    def get_leads_for_outreach(self, limit: int = 10) -> List[sqlite3.Row]:
        """
        Returns leads that:
          - are targets (no website OR nopcommerce)
          - have at least one email
          - have NOT been contacted before
        """
        sql = """
            SELECT DISTINCT l.*, e.email
            FROM leads l
            JOIN emails e ON e.lead_id = l.id
            WHERE (l.has_website = 0 OR l.is_nopcommerce = 1)
              AND e.email NOT IN (SELECT email FROM outreach_log WHERE status IN ('sent','simulated'))
            LIMIT ?
        """
        with self._connect() as conn:
            return conn.execute(sql, (limit,)).fetchall()

    def mark_lead_analyzed(self, lead_id: int, has_website: bool, is_nopcommerce: bool) -> None:
        with self._connect() as conn:
            conn.execute(
                """UPDATE leads SET analyzed=1, has_website=?, is_nopcommerce=?, updated_at=datetime('now')
                   WHERE id=?""",
                (int(has_website), int(is_nopcommerce), lead_id)
            )

    # ── Emails ─────────────────────────────────────────────────────────────────

    def save_email(self, lead_id: int, email: str, source_url: str = "") -> None:
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO emails (lead_id, email, source_url) VALUES (?,?,?)",
                    (lead_id, email.lower().strip(), source_url)
                )
        except sqlite3.Error as e:
            logger.error(f"save_email error: {e}")

    # ── Outreach Log ───────────────────────────────────────────────────────────

    def log_outreach(self, lead_id: int, email: str, subject: str,
                     status: str, error_msg: str = "") -> None:
        try:
            with self._connect() as conn:
                conn.execute(
                    """INSERT INTO outreach_log (lead_id, email, subject, status, error_msg)
                       VALUES (?,?,?,?,?)""",
                    (lead_id, email, subject, status, error_msg)
                )
        except sqlite3.Error as e:
            logger.error(f"log_outreach error: {e}")

    def emails_sent_last_hour(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                """SELECT COUNT(*) AS cnt FROM outreach_log
                   WHERE status IN ('sent','simulated')
                     AND sent_at >= datetime('now', '-1 hour')"""
            ).fetchone()
            return row["cnt"] if row else 0

    # ── Stats ──────────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        with self._connect() as conn:
            def scalar(sql, *params):
                row = conn.execute(sql, params).fetchone()
                return row[0] if row else 0

            return {
                "Total leads":           scalar("SELECT COUNT(*) FROM leads"),
                "Leads analyzed":        scalar("SELECT COUNT(*) FROM leads WHERE analyzed=1"),
                "Leads with website":    scalar("SELECT COUNT(*) FROM leads WHERE has_website=1"),
                "Leads without website": scalar("SELECT COUNT(*) FROM leads WHERE has_website=0 AND analyzed=1"),
                "NopCommerce sites":     scalar("SELECT COUNT(*) FROM leads WHERE is_nopcommerce=1"),
                "Emails collected":      scalar("SELECT COUNT(*) FROM emails"),
                "Emails sent":           scalar("SELECT COUNT(*) FROM outreach_log WHERE status='sent'"),
                "Emails simulated":      scalar("SELECT COUNT(*) FROM outreach_log WHERE status='simulated'"),
                "Emails failed":         scalar("SELECT COUNT(*) FROM outreach_log WHERE status='failed'"),
            }
