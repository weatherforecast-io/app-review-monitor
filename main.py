"""App Store Review Monitor - Orchestrator."""

import logging
import os
import sys

import yaml

from scripts.check_reviews import fetch_reviews, filter_new_reviews, load_state, save_state
from scripts.format_mail import classify_review
from scripts.send_mail import send_slack

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "apps": [],
    "classification": {
        "importance_rules": None,
        "category_rules": None,
    },
}


def load_config() -> dict:
    """Load config from config.yml or environment variables."""
    config = DEFAULT_CONFIG.copy()

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

    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        logger.error("Missing SLACK_WEBHOOK_URL env var.")
        sys.exit(1)

    classification = config.get("classification", {})
    state = load_state()
    total_new = 0

    for app in config["apps"]:
        app_name = app["name"]
        app_id = app["app_id"]
        countries = app.get("countries", ["us"])

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
            classifications = [
                classify_review(
                    r,
                    importance_rules=classification.get("importance_rules"),
                    category_rules=classification.get("category_rules"),
                )
                for r in app_reviews
            ]

            send_slack(webhook_url, app_name, app_reviews, classifications)
            total_new += len(app_reviews)
        else:
            logger.info("No new reviews for %s", app_name)

    save_state(state)
    logger.info("Done. Total new reviews processed: %d", total_new)


if __name__ == "__main__":
    main()
