"""Fetch App Store reviews via RSS feed and filter new ones."""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

RSS_URL = (
    "https://itunes.apple.com/{country}/rss/customerreviews"
    "/page={page}/id={app_id}/sortBy=mostRecent/json"
)

STATE_DIR = Path(".state")
STATE_FILE = STATE_DIR / "last_seen.json"


def _create_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def _parse_entry(entry: dict, country: str) -> dict:
    return {
        "id": entry["id"]["label"],
        "title": entry.get("title", {}).get("label", ""),
        "content": entry.get("content", {}).get("label", ""),
        "rating": int(entry.get("im:rating", {}).get("label", "0")),
        "author": entry.get("author", {}).get("name", {}).get("label", ""),
        "version": entry.get("im:version", {}).get("label", ""),
        "date": entry.get("updated", {}).get("label", ""),
        "vote_count": int(entry.get("im:voteCount", {}).get("label", "0")),
        "country": country,
    }


def fetch_reviews(app_id: str, country: str, max_pages: int = 3) -> list[dict]:
    """Fetch recent reviews from Apple RSS feed."""
    session = _create_session()
    all_reviews = []

    for page in range(1, max_pages + 1):
        url = RSS_URL.format(country=country, page=page, app_id=app_id)
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as e:
            logger.warning("Failed to fetch page %d for app %s/%s: %s", page, app_id, country, e)
            break

        feed = data.get("feed", {})
        entries = feed.get("entry", [])

        # Apple returns a single entry as dict instead of list
        if isinstance(entries, dict):
            entries = [entries]

        # First entry is often the app metadata, not a review
        reviews = [e for e in entries if "im:rating" in e]

        if not reviews:
            break

        for entry in reviews:
            all_reviews.append(_parse_entry(entry, country))

    return all_reviews


def load_state() -> dict:
    """Load last-seen review IDs from state file."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    """Save last-seen review IDs to state file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def filter_new_reviews(reviews: list[dict], last_seen_id: str | None) -> list[dict]:
    """Return only reviews newer than the last-seen ID."""
    if not reviews:
        return []

    if last_seen_id is None:
        # First run: return reviews from the last 6 hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=6)
        new = []
        for r in reviews:
            try:
                review_date = datetime.fromisoformat(r["date"].replace("Z", "+00:00"))
                if review_date >= cutoff:
                    new.append(r)
            except (ValueError, KeyError):
                continue
        return new

    # Collect reviews until we hit the last-seen ID
    new = []
    for r in reviews:
        if r["id"] == last_seen_id:
            break
        new.append(r)

    return new
