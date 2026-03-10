"""Send review notifications to Slack via Incoming Webhook."""

import json
import logging

import requests

logger = logging.getLogger(__name__)


def send_slack(webhook_url: str, app_name: str, reviews: list[dict], classifications: list[dict]) -> None:
    """Send formatted review notification to Slack."""
    total = len(reviews)
    avg_rating = sum(r["rating"] for r in reviews) / total

    importance_counts = {}
    for c in classifications:
        imp = c["importance"]
        importance_counts[imp] = importance_counts.get(imp, 0) + 1

    # Header
    critical_count = importance_counts.get("critical", 0)
    header = f"📱 *{app_name}* - 새 리뷰 {total}개"
    if critical_count > 0:
        header += f" (🚨 critical {critical_count}개)"

    # Summary
    stars = "★" * round(avg_rating) + "☆" * (5 - round(avg_rating))
    summary = f"평균 별점: {stars} ({avg_rating:.1f})"

    importance_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    paired = sorted(
        zip(reviews, classifications),
        key=lambda x: (importance_order.get(x[1]["importance"], 4), -x[0]["rating"]),
    )

    # Review blocks
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": f"📱 {app_name} - 새 리뷰 알림"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"{summary}\n총 {total}개 리뷰"}},
        {"type": "divider"},
    ]

    importance_emoji = {
        "critical": "🚨",
        "high": "⚠️",
        "medium": "📌",
        "low": "✅",
    }

    for review, cls in paired:
        rating = review["rating"]
        stars_display = "★" * rating + "☆" * (5 - rating)
        emoji = importance_emoji.get(cls["importance"], "")
        country = review.get("country", "").upper()

        text = (
            f"{stars_display} {emoji} *{cls['importance'].upper()}* | `{cls['category']}`\n"
            f"*{review.get('title', '(제목 없음)')}*\n"
            f"{review.get('content', '')[:300]}\n"
            f"_{review.get('author', 'Anonymous')}_ · v{review.get('version', '?')} · {country} · {review.get('date', '')[:10]}"
        )

        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})
        blocks.append({"type": "divider"})

    # Slack block limit is 50
    if len(blocks) > 50:
        blocks = blocks[:49]
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"_...외 {total - 23}개 리뷰 생략_"}})

    payload = {"blocks": blocks}

    try:
        resp = requests.post(webhook_url, json=payload, timeout=30)
        resp.raise_for_status()
        logger.info("Slack notification sent for %s: %d reviews", app_name, total)
    except requests.RequestException:
        logger.exception("Failed to send Slack notification")
        raise
