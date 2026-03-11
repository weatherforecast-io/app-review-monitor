"""App Store Review Monitor - Orchestrator."""

import logging
import os
import sys

import yaml

from scripts.check_reviews import fetch_reviews, filter_new_reviews, load_state, save_state
from scripts.check_reviews_google import fetch_reviews_google, filter_new_reviews_google
from scripts.countries import resolve_countries
from scripts.format_mail import classify_and_translate_reviews
from scripts.send_mail import send_slack

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Load config from config.yml or environment variables."""
    config = {"apps": []}

    if os.path.exists("config.yml"):
        with open("config.yml", encoding="utf-8") as f:
            config.update(yaml.safe_load(f) or {})

    app_ids_env = os.environ.get("APP_IDS", "")
    app_names_env = os.environ.get("APP_NAMES", "")
    countries_env = os.environ.get("APP_COUNTRIES", "us")
    google_app_ids_env = os.environ.get("GOOGLE_APP_IDS", "")

    if app_ids_env and not config.get("apps"):
        ids = [x.strip() for x in app_ids_env.split(",")]
        names = [x.strip() for x in app_names_env.split(",")] if app_names_env else ids
        countries = resolve_countries(countries_env)
        google_ids = [x.strip() for x in google_app_ids_env.split(",")] if google_app_ids_env else [""] * len(ids)

        config["apps"] = [
            {
                "name": name,
                "app_id": app_id,
                "google_app_id": google_id if google_id else None,
                "countries": countries,
            }
            for app_id, name, google_id in zip(ids, names, google_ids)
        ]

    return config


def _collect_apple_reviews(app_id: str, countries: list[str], state: dict, app_name: str) -> list[dict]:
    """Collect new Apple App Store reviews."""
    app_reviews = []
    for country in countries:
        reviews = fetch_reviews(app_id, country)
        state_key = f"apple_{app_id}_{country}"
        new_reviews = filter_new_reviews(reviews, state.get(state_key))

        if new_reviews:
            state[state_key] = new_reviews[0]["id"]
            app_reviews.extend(new_reviews)
            logger.info("  🍎 %s/%s: %d new reviews", country.upper(), app_name, len(new_reviews))
        else:
            logger.info("  🍎 %s/%s: no new reviews", country.upper(), app_name)

    return app_reviews


def _collect_google_reviews(google_app_id: str, countries: list[str], state: dict, app_name: str) -> list[dict]:
    """Collect new Google Play Store reviews."""
    app_reviews = []
    for country in countries:
        reviews = fetch_reviews_google(google_app_id, country)
        state_key = f"google_{google_app_id}_{country}"
        new_reviews = filter_new_reviews_google(reviews, state.get(state_key))

        if new_reviews:
            state[state_key] = new_reviews[0]["id"]
            app_reviews.extend(new_reviews)
            logger.info("  🤖 %s/%s: %d new reviews", country.upper(), app_name, len(new_reviews))
        else:
            logger.info("  🤖 %s/%s: no new reviews", country.upper(), app_name)

    return app_reviews


def main() -> None:
    config = load_config()

    if not config.get("apps"):
        logger.error("No apps configured. Set APP_IDS env var or create config.yml.")
        sys.exit(1)

    webhook_urls_raw = os.environ.get("SLACK_WEBHOOK_URLS", os.environ.get("SLACK_WEBHOOK_URL", ""))
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not webhook_urls_raw:
        logger.error("Missing SLACK_WEBHOOK_URLS env var.")
        sys.exit(1)
    if not anthropic_api_key:
        logger.error("Missing ANTHROPIC_API_KEY env var.")
        sys.exit(1)

    webhook_urls = [u.strip() for u in webhook_urls_raw.split(",") if u.strip()]

    state = load_state()
    total_new = 0

    for i, app in enumerate(config["apps"]):
        app_name = app["name"]
        app_id = app["app_id"]
        google_app_id = app.get("google_app_id")
        countries_raw = app.get("countries", ["us"])
        countries = resolve_countries(countries_raw) if isinstance(countries_raw, str) else countries_raw
        webhook_url = webhook_urls[i] if i < len(webhook_urls) else webhook_urls[-1]

        logger.info("Checking reviews for %s...", app_name)

        # Collect from both stores
        all_reviews = []
        all_reviews.extend(_collect_apple_reviews(app_id, countries, state, app_name))
        if google_app_id:
            all_reviews.extend(_collect_google_reviews(google_app_id, countries, state, app_name))

        if all_reviews:
            max_reviews = int(os.environ.get("MAX_REVIEWS_PER_APP", "0"))
            if max_reviews > 0 and len(all_reviews) > max_reviews:
                # Split evenly between Apple and Google
                apple = [r for r in all_reviews if r.get("store") == "apple"]
                google = [r for r in all_reviews if r.get("store") == "google"]
                half = max_reviews // 2
                if not google:
                    apple = apple[:max_reviews]
                elif not apple:
                    google = google[:max_reviews]
                else:
                    apple = apple[:half]
                    google = google[:max_reviews - len(apple)]
                all_reviews = apple + google
                logger.info("Limiting to %d reviews (iOS %d + Android %d)", len(all_reviews), len(apple), len(google))

            logger.info("Classifying and translating %d reviews with Claude...", len(all_reviews))
            classifications = classify_and_translate_reviews(all_reviews, anthropic_api_key)
            send_slack(webhook_url, app_name, all_reviews, classifications)
            total_new += len(all_reviews)
        else:
            logger.info("No new reviews for %s", app_name)

    save_state(state)
    logger.info("Done. Total new reviews processed: %d", total_new)


if __name__ == "__main__":
    main()
