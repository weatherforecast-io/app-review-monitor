"""Fetch Google Play Store reviews using google-play-scraper."""

import logging
from datetime import datetime, timezone, timedelta

from google_play_scraper import Sort, reviews

logger = logging.getLogger(__name__)

# google-play-scraper language codes for major countries
COUNTRY_LANG_MAP = {
    "kr": "ko", "us": "en", "jp": "ja", "gb": "en", "de": "de",
    "fr": "fr", "au": "en", "ca": "en", "cn": "zh", "tw": "zh",
    "in": "en", "br": "pt", "mx": "es", "es": "es", "it": "it",
    "nl": "nl", "se": "sv", "no": "no", "dk": "da", "fi": "fi",
    "sg": "en", "hk": "zh", "th": "th", "id": "id", "my": "en",
    "ph": "en", "sa": "ar", "ae": "ar", "tr": "tr", "pl": "pl",
}


def fetch_reviews_google(package_name: str, country: str, max_count: int = 50) -> list[dict]:
    """Fetch recent reviews from Google Play Store."""
    lang = COUNTRY_LANG_MAP.get(country, "en")

    try:
        result, _ = reviews(
            package_name,
            lang=lang,
            country=country,
            sort=Sort.NEWEST,
            count=max_count,
        )
    except Exception as e:
        logger.warning("Failed to fetch Google Play reviews for %s/%s: %s", package_name, country, e)
        return []

    parsed = []
    for r in result:
        review_date = r.get("at")
        if isinstance(review_date, datetime):
            date_str = review_date.isoformat()
        else:
            date_str = str(review_date) if review_date else ""

        parsed.append({
            "id": r.get("reviewId", ""),
            "title": "",  # Google Play reviews don't have separate titles
            "content": r.get("content", ""),
            "rating": r.get("score", 0),
            "author": r.get("userName", ""),
            "version": r.get("reviewCreatedVersion") or "?",
            "date": date_str,
            "vote_count": r.get("thumbsUpCount", 0),
            "country": country,
            "store": "google",
        })

    return parsed


def filter_new_reviews_google(reviews_list: list[dict], last_seen_id: str | None) -> list[dict]:
    """Return only reviews newer than the last-seen ID."""
    if not reviews_list:
        return []

    if last_seen_id is None:
        # First run: return the most recent 10 reviews
        return reviews_list[:10]

    new = []
    for r in reviews_list:
        if r["id"] == last_seen_id:
            break
        new.append(r)

    return new
