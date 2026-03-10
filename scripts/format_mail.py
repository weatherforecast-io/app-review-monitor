"""Classify App Store reviews by importance and category."""

import logging

logger = logging.getLogger(__name__)

DEFAULT_IMPORTANCE_RULES = {
    "critical": ["crash", "not working", "broken", "data loss", "can't login", "security", "작동 안", "먹통", "삭제됨"],
    "high": ["bug", "error", "freeze", "slow", "battery", "버그", "오류", "느려", "멈춤"],
    "low": ["love", "great", "amazing", "best app", "좋아요", "최고", "감사"],
}

DEFAULT_CATEGORY_RULES = {
    "performance": ["slow", "lag", "freeze", "battery", "memory", "느려", "렉", "배터리"],
    "stability": ["crash", "force close", "not responding", "크래시", "멈춤", "강제종료"],
    "ux": ["confusing", "hard to find", "ui", "design", "불편", "디자인", "찾기 어"],
    "feature_request": ["wish", "please add", "would be nice", "should have", "추가해", "기능 요청"],
    "login_auth": ["login", "password", "sign in", "account", "로그인", "비밀번호", "계정"],
    "billing": ["subscription", "charge", "refund", "price", "payment", "구독", "결제", "환불"],
}


def classify_review(review: dict, importance_rules: dict = None, category_rules: dict = None) -> dict:
    """Classify a review by importance and category."""
    imp_rules = importance_rules or DEFAULT_IMPORTANCE_RULES
    cat_rules = category_rules or DEFAULT_CATEGORY_RULES

    text = f"{review.get('title', '')} {review.get('content', '')}".lower()
    rating = review.get("rating", 3)

    # Importance
    importance = None
    for level in ["critical", "high", "low"]:
        keywords = imp_rules.get(level, [])
        if any(kw.lower() in text for kw in keywords):
            importance = level
            break
    if importance is None:
        importance = "high" if rating <= 2 else ("medium" if rating == 3 else "low")

    # Category
    category = "general"
    for cat, keywords in cat_rules.items():
        if any(kw.lower() in text for kw in keywords):
            category = cat
            break

    return {"importance": importance, "category": category}
