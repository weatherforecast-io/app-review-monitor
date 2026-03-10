"""Send review notifications to Slack via Incoming Webhook."""

import logging

import requests

logger = logging.getLogger(__name__)

IMPORTANCE_EMOJI = {
    "critical": "🚨",
    "high": "⚠️",
    "medium": "📌",
    "low": "✅",
}


def send_slack(webhook_url: str, app_name: str, reviews: list[dict], classifications: list[dict]) -> None:
    """Send formatted review notification to Slack.

    Reviews are sorted with most recent at the bottom.
    """
    total = len(reviews)
    avg_rating = sum(r["rating"] for r in reviews) / total

    importance_counts = {}
    for c in classifications:
        imp = c["importance"]
        importance_counts[imp] = importance_counts.get(imp, 0) + 1

    critical_count = importance_counts.get("critical", 0)

    # Summary
    stars = "★" * round(avg_rating) + "☆" * (5 - round(avg_rating))
    summary_parts = [f"평균 별점: {stars} ({avg_rating:.1f})", f"총 {total}개 리뷰"]
    for level in ["critical", "high", "medium", "low"]:
        count = importance_counts.get(level, 0)
        if count > 0:
            summary_parts.append(f"{IMPORTANCE_EMOJI[level]} {level}: {count}")

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": f"📱 {app_name} - 새 리뷰 알림"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": " | ".join(summary_parts)}},
        {"type": "divider"},
    ]

    # Sort: oldest first, most recent at bottom
    paired = list(zip(reviews, classifications))
    paired.sort(key=lambda x: x[0].get("date", ""))

    for review, cls in paired:
        rating = review["rating"]
        stars_display = "★" * rating + "☆" * (5 - rating)
        emoji = IMPORTANCE_EMOJI.get(cls["importance"], "")
        country = review.get("country", "").upper()

        title_ko = cls.get("title_ko", review.get("title", "(제목 없음)"))
        content_ko = cls.get("content_ko", review.get("content", "")[:300])
        original_title = review.get("title", "")
        original_content = review.get("content", "")[:300]

        # Build review text
        store_icon = "🍎" if review.get("store") == "apple" else "🟢"
        text = f"{store_icon} {stars_display} {emoji} *{cls['importance'].upper()}* | `{cls['category']}`\n"

        # Korean translation first, then original if different
        is_korean = _is_korean(original_title + original_content)
        if is_korean:
            text += f"*{title_ko}*\n{content_ko}\n"
        else:
            text += f"*{title_ko}*\n{content_ko}\n"
            text += f"_{original_title} | {original_content[:150]}_\n"

        text += f"_{review.get('author', 'Anonymous')}_ · v{review.get('version', '?')} · {country} · {review.get('date', '')[:10]}"

        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})
        blocks.append({"type": "divider"})

    # Slack block limit is 50, send multiple messages if needed
    _send_blocks(webhook_url, blocks, app_name, total)


def _is_korean(text: str) -> bool:
    """Check if text contains Korean characters."""
    korean_count = sum(1 for c in text if '\uac00' <= c <= '\ud7a3' or '\u3131' <= c <= '\u3163')
    return korean_count > len(text) * 0.1 if text else True


def _send_blocks(webhook_url: str, blocks: list, app_name: str, total: int) -> None:
    """Send blocks to Slack, splitting into multiple messages if over 50 blocks."""
    max_blocks = 50

    if len(blocks) <= max_blocks:
        _post_slack(webhook_url, blocks)
        logger.info("Slack notification sent for %s: %d reviews", app_name, total)
        return

    # Split into chunks, keeping header in first message only
    header_blocks = blocks[:3]  # header + summary + divider
    review_blocks = blocks[3:]

    # First message with header
    first_chunk = header_blocks + review_blocks[:max_blocks - 3]
    _post_slack(webhook_url, first_chunk)

    # Remaining messages
    remaining = review_blocks[max_blocks - 3:]
    while remaining:
        chunk = remaining[:max_blocks]
        remaining = remaining[max_blocks:]
        _post_slack(webhook_url, chunk)

    logger.info("Slack notification sent for %s: %d reviews (multiple messages)", app_name, total)


def _post_slack(webhook_url: str, blocks: list) -> None:
    """Post a single message to Slack."""
    try:
        resp = requests.post(webhook_url, json={"blocks": blocks}, timeout=30)
        resp.raise_for_status()
    except requests.RequestException:
        logger.exception("Failed to send Slack notification")
        raise
