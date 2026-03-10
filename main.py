"""App Store Review Monitor - Orchestrator."""

import logging
import os
import sys

import yaml

from scripts.check_reviews import fetch_reviews, filter_new_reviews, load_state, save_state
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

    if app_ids_env and not config.get("apps"):
        ids = [x.strip() for x in app_ids_env.split(",")]
        names = [x.strip() for x in app_names_env.split(",")] if app_names_env else ids
        countries = [x.strip() for x in countries_env.split(",")]

        config["apps"] = [
            {"name": name, "app_id": app_id, "countries": countries}
            for app_id, name in zip(ids, names)
        ]

    return config


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
        countries = app.get("countries", ["us"])
        webhook_url = webhook_urls[i] if i < len(webhook_urls) else webhook_urls[-1]

        logger.info("Checking reviews for %s (ID: %s)...", app_name, app_id)
        app_reviews = []

        for country in countries:
            reviews = fetch_reviews(app_id, country)
            state_key = f"{app_id}_{country}"
            new_reviews = filter_new_reviews(reviews, state.get(state_key))

            if new_reviews:
                state[state_key] = new_reviews[0]["id"]
                app_reviews.extend(new_reviews)
                logger.info("  %s/%s: %d new reviews", country.upper(), app_name, len(new_reviews))
            else:
                logger.info("  %s/%s: no new reviews", country.upper(), app_name)

        if app_reviews:
            logger.info("Classifying and translating %d reviews with Claude...", len(app_reviews))
            classifications = classify_and_translate_reviews(app_reviews, anthropic_api_key)
            send_slack(webhook_url, app_name, app_reviews, classifications)
            total_new += len(app_reviews)
        else:
            logger.info("No new reviews for %s", app_name)

    save_state(state)
    logger.info("Done. Total new reviews processed: %d", total_new)


if __name__ == "__main__":
    main()
