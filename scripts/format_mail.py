"""Classify and translate App Store reviews using Claude API."""

import json
import logging
import time
from pathlib import Path

import anthropic

logger = logging.getLogger(__name__)

GUIDE_PATH = Path(__file__).parent.parent / "classification_guide.md"


def _load_guide() -> str:
    return GUIDE_PATH.read_text(encoding="utf-8")


def classify_and_translate_reviews(reviews: list[dict], api_key: str) -> list[dict]:
    """Classify importance/category and translate non-Korean reviews using Claude.

    Returns a list of dicts with keys: importance, category, title_ko, content_ko
    """
    if not reviews:
        return []

    guide = _load_guide()
    client = anthropic.Anthropic(api_key=api_key)

    # Build review list for the prompt
    review_items = []
    for i, r in enumerate(reviews):
        review_items.append(
            f"[{i}] rating={r['rating']} country={r.get('country', '')} "
            f"title=\"{r.get('title', '')}\" "
            f"content=\"{r.get('content', '')[:500]}\""
        )

    reviews_text = "\n".join(review_items)

    prompt = f"""아래 분류 가이드를 참고하여 앱스토어 리뷰들을 분류하고, 한국어가 아닌 리뷰는 한국어로 번역해주세요.

<classification_guide>
{guide}
</classification_guide>

<reviews>
{reviews_text}
</reviews>

각 리뷰에 대해 아래 JSON 배열을 반환해주세요. 다른 텍스트 없이 JSON만 반환하세요.

[
  {{
    "index": 0,
    "importance": "critical|high|medium|low",
    "category": "카테고리명",
    "title_ko": "한국어 제목 (원래 한국어면 그대로, 아니면 번역)",
    "content_ko": "한국어 내용 요약 (원래 한국어면 그대로, 아니면 번역. 최대 200자)"
  }},
  ...
]"""

    # Process in batches of 20 to stay within token limits
    batch_size = 20
    all_results = []

    for batch_idx, batch_start in enumerate(range(0, len(reviews), batch_size)):
        if batch_idx > 0:
            time.sleep(2.0)
        batch_reviews = reviews[batch_start:batch_start + batch_size]
        batch_items = []
        for i, r in enumerate(batch_reviews):
            batch_items.append(
                f"[{i}] rating={r['rating']} country={r.get('country', '')} "
                f"title=\"{r.get('title', '')}\" "
                f"content=\"{r.get('content', '')[:500]}\""
            )

        batch_text = "\n".join(batch_items)
        batch_prompt = f"""아래 분류 가이드를 참고하여 앱스토어 리뷰들을 분류하고, 한국어가 아닌 리뷰는 한국어로 번역해주세요.

<classification_guide>
{guide}
</classification_guide>

<reviews>
{batch_text}
</reviews>

각 리뷰에 대해 아래 JSON 배열을 반환해주세요. 다른 텍스트 없이 JSON만 반환하세요.

[
  {{
    "index": 0,
    "importance": "critical|high|medium|low",
    "category": "카테고리명",
    "title_ko": "한국어 제목 (원래 한국어면 그대로, 아니면 번역)",
    "content_ko": "한국어 내용 요약 (원래 한국어면 그대로, 아니면 번역. 최대 200자)"
  }},
  ...
]"""

        try:
            # Retry with exponential backoff on rate limit errors
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    message = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=4096,
                        messages=[{"role": "user", "content": batch_prompt}],
                    )
                    break
                except anthropic.RateLimitError:
                    if attempt < max_retries - 1:
                        wait = 2 ** (attempt + 1)
                        logger.info("Rate limited, retrying in %ds...", wait)
                        time.sleep(wait)
                    else:
                        raise

            response_text = message.content[0].text.strip()

            # Extract JSON from response (handle markdown code blocks)
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            batch_results = json.loads(response_text)
            all_results.extend(batch_results)

        except (json.JSONDecodeError, anthropic.APIError, IndexError, KeyError) as e:
            logger.warning("Claude API batch failed (start=%d): %s", batch_start, e)
            # Fallback: return basic classification for this batch
            for r in batch_reviews:
                rating = r.get("rating", 3)
                importance = "high" if rating <= 2 else ("medium" if rating == 3 else "low")
                all_results.append({
                    "importance": importance,
                    "category": "other",
                    "title_ko": r.get("title", ""),
                    "content_ko": r.get("content", "")[:200],
                })

    return all_results
