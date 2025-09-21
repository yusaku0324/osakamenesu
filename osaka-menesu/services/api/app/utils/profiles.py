from __future__ import annotations

from typing import Optional, Iterable, Tuple, Any

from .. import models


def _safe_int(v: object) -> Optional[int]:
    try:
        if v is None:
            return None
        return int(v)  # type: ignore[arg-type]
    except Exception:
        return None


def _safe_float(v: object) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)  # type: ignore[arg-type]
    except Exception:
        return None


def _extract_review_stats(reviews: Any) -> tuple[Optional[float], Optional[int]]:
    average: Optional[float] = None
    count: Optional[int] = None
    items: list[dict[str, Any]] = []

    if isinstance(reviews, dict):
        average = _safe_float(reviews.get("average_score") or reviews.get("score"))
        count = _safe_int(reviews.get("review_count") or reviews.get("count"))
        raw_items = reviews.get("highlighted") or reviews.get("reviews") or reviews.get("items")
        if isinstance(raw_items, list):
            items = [x for x in raw_items if isinstance(x, dict)]
    elif isinstance(reviews, list):
        items = [x for x in reviews if isinstance(x, dict)]

    if average is None and items:
        scores = [_safe_float(item.get("score") or item.get("rating")) for item in items]
        scores = [s for s in scores if s is not None]
        if scores:
            average = round(sum(scores) / len(scores), 1)

    if count is None and items:
        count = len(items)

    return average, count


def infer_height_age(profile: models.Profile) -> Tuple[Optional[int], Optional[int]]:
    """Prefer DB columns; fall back to contact_json integers.

    Returns (height_cm, age).
    """
    height_cm = getattr(profile, "height_cm", None)
    age = getattr(profile, "age", None)
    if height_cm is None or age is None:
        try:
            cj = profile.contact_json or {}
        except Exception:
            cj = {}
        if height_cm is None:
            height_cm = _safe_int(cj.get("height_cm"))
        if age is None:
            age = _safe_int(cj.get("age"))
    return height_cm, age


def infer_store_name(
    profile: models.Profile,
    outlinks: Optional[Iterable[models.Outlink]] = None,
) -> Optional[str]:
    """Determine store name.

    Priority:
    1) profile.contact_json.store_name
    2) domain from a 'web' outlink in provided outlinks
    3) domain from profile.contact_json.web
    """
    store_name: Optional[str] = None
    try:
        cj = profile.contact_json or {}
        store_name = cj.get("store_name")
    except Exception:
        store_name = None

    if store_name:
        return store_name

    # Try provided outlinks
    if outlinks:
        try:
            web = next((o for o in outlinks if getattr(o, "kind", None) == "web"), None)
        except Exception:
            web = None
        if web and getattr(web, "target_url", None):
            try:
                from urllib.parse import urlparse

                host = urlparse(web.target_url).hostname
                if host:
                    return host
            except Exception:
                pass

    # Fallback to contact_json.web
    try:
        from urllib.parse import urlparse

        cj = profile.contact_json or {}
        if isinstance(cj.get("web"), str):
            host = urlparse(cj["web"]).hostname
            if host:
                return host
    except Exception:
        pass

    return None


def build_profile_doc(
    profile: models.Profile,
    *,
    today: bool = False,
    tag_score: float = 0.0,
    ctr7d: float = 0.0,
    outlinks: Optional[Iterable[models.Outlink]] = None,
) -> dict:
    """Build a search document for Meilisearch based on a Profile model.

    Centralizes field normalization and derived attributes.
    """
    height_cm, age = infer_height_age(profile)
    store_name = infer_store_name(profile, outlinks)
    try:
        contact_json = profile.contact_json or {}
    except Exception:
        contact_json = {}

    promotions: list[dict[str, Any]] = []
    for source in (profile.discounts or [], contact_json.get("promotions")):
        if not isinstance(source, list):
            continue
        for entry in source:
            if not isinstance(entry, dict):
                continue
            label = entry.get("label") or entry.get("title")
            if not label:
                continue
            promotions.append(
                {
                    "label": label,
                    "description": entry.get("description") or entry.get("detail"),
                    "expires_at": entry.get("expires_at") or entry.get("until"),
                    "highlight": entry.get("highlight"),
                }
            )

    review_score, review_count = _extract_review_stats(contact_json.get("reviews"))
    ranking_reason = contact_json.get("ranking_reason") or contact_json.get("ranking_message")
    return {
        "id": str(profile.id),
        "name": profile.name,
        "area": profile.area,
        "price_min": profile.price_min,
        "price_max": profile.price_max,
        "bust_tag": profile.bust_tag,
        "service_type": profile.service_type,
        "store_name": store_name,
        "body_tags": profile.body_tags or [],
        "height_cm": height_cm,
        "age": age,
        "photos": profile.photos or [],
        "discounts": profile.discounts or [],
        "ranking_badges": profile.ranking_badges or [],
        "ranking_weight": profile.ranking_weight,
        "status": profile.status,
        "today": today,
        "tag_score": tag_score,
        "ctr7d": ctr7d,
        "updated_at": int((profile.updated_at or profile.created_at).timestamp()),
        "promotions": promotions,
        "review_score": review_score,
        "review_count": review_count,
        "ranking_reason": ranking_reason,
        "staff_preview": contact_json.get("staff"),
    }
