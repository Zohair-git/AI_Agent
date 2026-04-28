"""
Lead Collector Module
Fetches business leads from the Google Maps Places API.

Uses the Places Text Search endpoint which is officially allowed for
programmatic use with a valid API key.
"""

import time
import logging
from typing import Optional
import requests
from config import Config
from database import Database

logger = logging.getLogger(__name__)

PLACES_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


class LeadCollector:
    """Collects business leads using the Google Maps Places API."""

    def __init__(self, config: Config, db: Database):
        self.config = config
        self.db = db
        self.api_key = config.google_maps_api_key

    # ── Public API ─────────────────────────────────────────────────────────────

    def collect(self, keyword: str, location: str, max_results: int = 20) -> int:
        """
        Search for businesses matching `keyword` in `location`.
        Returns the number of new/updated leads saved.
        """
        if not self.api_key:
            logger.error("GOOGLE_MAPS_API_KEY is not set. Aborting collection.")
            return 0

        query = f"{keyword} in {location}"
        logger.info(f"Searching Places API for: '{query}' (max {max_results})")

        count = 0
        page_token: Optional[str] = None

        while count < max_results:
            batch = min(20, max_results - count)   # Places API max per page = 20
            results, next_token = self._fetch_page(query, page_token)
            if not results:
                break

            for place in results[:batch]:
                lead_id = self._process_place(place, keyword, location)
                if lead_id:
                    count += 1

            page_token = next_token
            if not page_token:
                break

            # Google requires a short delay before using next_page_token
            logger.debug("Waiting before fetching next page…")
            time.sleep(2)

        logger.info(f"Collection complete – {count} leads saved")
        return count

    # ── Internal Helpers ───────────────────────────────────────────────────────

    def _fetch_page(self, query: str, page_token: Optional[str]):
        """Fetch one page of Places Text Search results."""
        params = {
            "query": query,
            "key": self.api_key,
            "fields": "place_id,name,formatted_address,formatted_phone_number,website",
        }
        if page_token:
            params["pagetoken"] = page_token

        try:
            resp = requests.get(
                PLACES_TEXT_SEARCH_URL,
                params=params,
                timeout=self.config.request_timeout,
            )
            resp.raise_for_status()
            data = resp.json()

            status = data.get("status")
            if status not in ("OK", "ZERO_RESULTS"):
                logger.warning(f"Places API status: {status} – {data.get('error_message','')}")
                return [], None

            return data.get("results", []), data.get("next_page_token")

        except requests.RequestException as e:
            logger.error(f"Places API request failed: {e}")
            return [], None

    def _fetch_place_details(self, place_id: str) -> dict:
        """
        Fetch additional details (phone, website) for a single place.
        Text Search sometimes omits these; Details fills the gap.
        """
        params = {
            "place_id": place_id,
            "fields": "name,formatted_address,formatted_phone_number,website",
            "key": self.api_key,
        }
        try:
            resp = requests.get(
                PLACES_DETAILS_URL,
                params=params,
                timeout=self.config.request_timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("result", {})
        except requests.RequestException as e:
            logger.warning(f"Place details request failed for {place_id}: {e}")
            return {}

    def _process_place(self, place: dict, keyword: str, location: str) -> Optional[int]:
        """Parse a Places result, enrich with details if needed, then upsert."""
        place_id = place.get("place_id")
        if not place_id:
            return None

        name    = place.get("name", "Unknown")
        address = place.get("formatted_address", "")
        phone   = place.get("formatted_phone_number", "")
        website = place.get("website", "")

        # If the text-search result lacks phone/website, hit the Details endpoint
        if not website or not phone:
            logger.debug(f"Fetching details for '{name}' ({place_id})")
            details = self._fetch_place_details(place_id)
            phone   = phone   or details.get("formatted_phone_number", "")
            website = website or details.get("website", "")
            time.sleep(self.config.request_delay_seconds)  # respect rate limits

        # Normalise website URL
        website = self._normalise_url(website)

        lead = {
            "place_id":    place_id,
            "name":        name,
            "address":     address,
            "phone":       phone,
            "website":     website,
            "has_website": 1 if website else 0,
            "keyword":     keyword,
            "location":    location,
        }

        lead_id = self.db.upsert_lead(lead)
        logger.info(f"  Saved lead: {name} | website: {website or 'NONE'}")
        return lead_id

    @staticmethod
    def _normalise_url(url: str) -> str:
        """Add https:// scheme if missing."""
        if not url:
            return ""
        url = url.strip()
        if url and not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url
