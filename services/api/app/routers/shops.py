from __future__ import annotations

from datetime import datetime, timezone, date
from typing import Any, Dict, Iterable, List, Set
from uuid import UUID
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..db import get_session
from ..meili import search as meili_search, build_filter
from ..schemas import (
    AvailabilityCalendar,
    AvailabilityDay,
    AvailabilitySlot,
    ContactInfo,
    FacetValue,
    GeoLocation,
    HighlightedReview,
    MediaImage,
    MenuItem,
    Promotion,
    ReviewSummary,
    ShopDetail,
    ShopSearchResponse,
    ShopSummary,
    SocialLink,
    StaffSummary,
)
from ..utils.profiles import build_profile_doc, infer_store_name


router = APIRouter(prefix="/api/v1/shops", tags=["shops"])


def _unix_to_dt(ts: int | None) -> datetime | None:
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    except Exception:
        return None


def _doc_to_shop_summary(doc: Dict[str, Any]) -> ShopSummary:
    first_photo = None
    photos = doc.get("photos") or []
    if isinstance(photos, list) and photos:
        first_photo = photos[0]
    promotions_raw = doc.get("promotions")
    promotions = _normalize_promotions(promotions_raw)
    review_score = doc.get("review_score")
    rating = review_score if review_score is not None else doc.get("rating")
    review_count = doc.get("review_count")
    return ShopSummary(
        id=UUID(doc["id"]),
        slug=doc.get("slug"),
        name=doc.get("name", ""),
        area=doc.get("area", ""),
        area_name=doc.get("area_name"),
        address=doc.get("address"),
        categories=list(doc.get("categories", []) or []),
        service_tags=list(doc.get("body_tags", []) or []),
        min_price=doc.get("price_min", 0) or 0,
        max_price=doc.get("price_max", 0) or 0,
        rating=rating,
        review_count=review_count,
        lead_image_url=first_photo,
        badges=list(doc.get("ranking_badges", []) or []),
        today_available=doc.get("today"),
        next_available_at=_unix_to_dt(doc.get("next_available_at")),
        distance_km=doc.get("distance_km"),
        online_reservation=doc.get("online_reservation"),
        updated_at=_unix_to_dt(doc.get("updated_at")),
        ranking_reason=doc.get("ranking_reason"),
        promotions=promotions,
    )


def _build_facets(facet_distribution: Dict[str, Dict[str, int]] | None) -> Dict[str, List[FacetValue]]:
    if not facet_distribution:
        return {}
    response: Dict[str, List[FacetValue]] = {}
    for facet_name, values in facet_distribution.items():
        if not isinstance(values, dict):
            continue
        response[facet_name] = [
            FacetValue(value=value_key, label=value_key, count=count)
            for value_key, count in values.items()
        ]
    return response


def _hydrate_contact(contact_json: Dict[str, Any] | None) -> ContactInfo | None:
    if not isinstance(contact_json, dict):
        return None
    sns_list = []
    raw_sns = contact_json.get("sns")
    if isinstance(raw_sns, list):
        for entry in raw_sns:
            if not isinstance(entry, dict):
                continue
            platform = entry.get("platform") or entry.get("name")
            url = entry.get("url")
            if not platform or not url:
                continue
            sns_list.append(SocialLink(platform=platform, url=url, label=entry.get("label")))
    return ContactInfo(
        phone=contact_json.get("phone"),
        line_id=contact_json.get("line_id") or contact_json.get("line"),
        website_url=contact_json.get("web") or contact_json.get("website_url"),
        reservation_form_url=contact_json.get("reservation_form_url"),
        sns=sns_list,
    )


def _hydrate_location(contact_json: Dict[str, Any] | None) -> GeoLocation | None:
    if not isinstance(contact_json, dict):
        return None
    lat = contact_json.get("latitude")
    lon = contact_json.get("longitude")
    nearest = contact_json.get("nearest_station") or contact_json.get("station")
    address = contact_json.get("address")
    if not any([lat, lon, nearest, address]):
        return None
    return GeoLocation(
        address=address,
        latitude=lat,
        longitude=lon,
        nearest_station=nearest,
    )


def _convert_slots(slots_json: Any) -> List[AvailabilitySlot]:
    slots: List[AvailabilitySlot] = []
    slot_items: Iterable[Any]
    if isinstance(slots_json, dict):
        slot_items = slots_json.get("slots") or slots_json.values()
    elif isinstance(slots_json, list):
        slot_items = slots_json
    else:
        slot_items = []
    for item in slot_items:
        if not isinstance(item, dict):
            continue
        start = item.get("start_at") or item.get("start")
        end = item.get("end_at") or item.get("end")
        status = item.get("status") or 'open'
        if not (start and end):
            continue
        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
        except Exception:
            continue
        slots.append(
            AvailabilitySlot(
                start_at=start_dt,
                end_at=end_dt,
                status=status if status in {'open', 'tentative', 'blocked'} else 'open',
                staff_id=item.get("staff_id"),
                menu_id=item.get("menu_id"),
            )
        )
    return slots


def _slots_have_open(slots_json: Any) -> bool:
    if not slots_json:
        return False
    for slot in _convert_slots(slots_json):
        if slot.status == 'open' or slot.status is None:
            return True
    return False


def _uuid_from_seed(seed: str, value: str | None = None) -> UUID:
    if value:
        try:
            return UUID(value)
        except Exception:
            pass
    return uuid.uuid5(uuid.NAMESPACE_URL, seed)


def _normalize_menus(raw: Any, shop_id: UUID) -> List[MenuItem]:
    if not isinstance(raw, list):
        return []
    items: List[MenuItem] = []
    for idx, entry in enumerate(raw):
        if not isinstance(entry, dict):
            continue
        price = entry.get('price', 0)
        try:
            price_int = int(price)
        except Exception:
            price_int = 0
        menu_id = _uuid_from_seed(f"{shop_id}:menu:{entry.get('id') or entry.get('name') or idx}", entry.get('id'))
        items.append(MenuItem(
            id=menu_id,
            name=str(entry.get('name') or f"メニュー{idx + 1}"),
            description=entry.get('description'),
            duration_minutes=entry.get('duration_minutes') or entry.get('duration'),
            price=price_int,
            currency=entry.get('currency') or 'JPY',
            is_reservable_online=entry.get('is_reservable_online', True),
            tags=[str(tag) for tag in (entry.get('tags') or [])],
        ))
    return items


def _normalize_staff(raw: Any, shop_id: UUID) -> List[StaffSummary]:
    if not isinstance(raw, list):
        return []
    members: List[StaffSummary] = []
    for idx, entry in enumerate(raw):
        if not isinstance(entry, dict):
            continue
        staff_id = _uuid_from_seed(f"{shop_id}:staff:{entry.get('id') or entry.get('name') or idx}", entry.get('id'))
        members.append(StaffSummary(
            id=staff_id,
            name=str(entry.get('name') or f"スタッフ{idx + 1}"),
            alias=entry.get('alias'),
            avatar_url=entry.get('avatar_url'),
            headline=entry.get('headline'),
            rating=entry.get('rating'),
            review_count=entry.get('review_count'),
            specialties=[str(tag) for tag in (entry.get('specialties') or [])],
        ))
    return members


def _safe_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _normalize_date_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return None


def _parse_review_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except Exception:
                continue
        try:
            return datetime.fromisoformat(value).date()
        except Exception:
            return None
    return None


def _normalize_promotions(*sources: Any) -> List[Promotion]:
    promotions: List[Promotion] = []
    seen: Set[tuple[str, str | None, str | None]] = set()
    for source in sources:
        if not isinstance(source, list):
            continue
        for entry in source:
            if not isinstance(entry, dict):
                continue
            label_raw = entry.get("label") or entry.get("title") or entry.get("name")
            if not label_raw:
                continue
            label = str(label_raw).strip()
            if not label:
                continue
            description = entry.get("description") or entry.get("detail")
            expires_at = _normalize_date_string(entry.get("expires_at") or entry.get("until"))
            key = (label, description, expires_at)
            if key in seen:
                continue
            seen.add(key)
            promotions.append(
                Promotion(
                    label=label,
                    description=str(description) if description else None,
                    expires_at=expires_at,
                    highlight=entry.get("highlight"),
                )
            )
    return promotions


def _normalize_reviews(raw: Any) -> ReviewSummary:
    if raw is None:
        return ReviewSummary()

    highlighted: List[HighlightedReview] = []
    average_score: float | None = None
    review_count: int | None = None
    items: List[dict[str, Any]] = []

    if isinstance(raw, dict):
        average_score = _safe_float(raw.get("average_score") or raw.get("score"))
        review_count = _safe_int(raw.get("review_count") or raw.get("count"))
        extra = raw.get("highlighted") or raw.get("reviews") or raw.get("items") or []
        if isinstance(extra, list):
            items = [x for x in extra if isinstance(x, dict)]
    elif isinstance(raw, list):
        items = [x for x in raw if isinstance(x, dict)]

    for entry in items:
        review_id_raw = entry.get("id") or entry.get("review_id")
        review_id: UUID | None = None
        if review_id_raw:
            try:
                review_id = UUID(str(review_id_raw))
            except Exception:
                review_id = None
        title = str(entry.get("title") or entry.get("headline") or entry.get("summary") or "口コミ")
        body = str(entry.get("body") or entry.get("text") or entry.get("comment") or "")
        score = _safe_int(entry.get("score") or entry.get("rating")) or 0
        visited_at = _parse_review_date(entry.get("visited_at") or entry.get("visited_on"))
        author_alias = entry.get("author_alias") or entry.get("author") or entry.get("user")
        highlighted.append(
            HighlightedReview(
                review_id=review_id,
                title=title,
                body=body,
                score=score,
                visited_at=visited_at,
                author_alias=str(author_alias) if author_alias else None,
            )
        )

    if average_score is None and highlighted:
        scores = [h.score for h in highlighted if isinstance(h.score, int)]
        if scores:
            average_score = round(sum(scores) / len(scores), 1)

    if review_count is None:
        review_count = len(highlighted) if highlighted else None

    return ReviewSummary(
        average_score=average_score,
        review_count=review_count,
        highlighted=highlighted,
    )

async def _fetch_availability(
    db: AsyncSession, shop_id: UUID, start_date: date | None = None, end_date: date | None = None
) -> AvailabilityCalendar | None:
    stmt = (
        select(models.Availability)
        .where(models.Availability.profile_id == shop_id)
        .order_by(models.Availability.date.asc())
    )
    if start_date:
        stmt = stmt.where(models.Availability.date >= start_date)
    if end_date:
        stmt = stmt.where(models.Availability.date <= end_date)

    result = await db.execute(stmt)
    records = list(result.scalars().all())
    if not records:
        return None

    days: List[AvailabilityDay] = []
    today = date.today()
    for record in records:
        slots = _convert_slots(record.slots_json)
        days.append(
            AvailabilityDay(
                date=record.date,
                is_today=record.date == today,
                slots=slots,
            )
        )
    return AvailabilityCalendar(
        shop_id=shop_id,
        generated_at=datetime.now(timezone.utc),
        days=days,
    )


async def _filter_results_by_availability(
    db: AsyncSession, shops: List[ShopSummary], target_date: date
) -> List[ShopSummary]:
    if not shops:
        return []
    shop_ids = [shop.id for shop in shops]
    stmt = (
        select(models.Availability.profile_id, models.Availability.slots_json)
        .where(models.Availability.profile_id.in_(shop_ids))
        .where(models.Availability.date == target_date)
    )
    res = await db.execute(stmt)
    rows = res.all()
    eligible: Set[UUID] = set()
    for profile_id, slots_json in rows:
        if _slots_have_open(slots_json):
            eligible.add(profile_id)
    return [shop for shop in shops if shop.id in eligible]


@router.get("")
async def search_shops(
    q: str | None = Query(default=None, description="Free text query"),
    area: str | None = Query(default=None, description="Area code filter"),
    category: str | None = Query(default=None, description="Service category"),
    service_tags: str | None = Query(default=None, description="Comma separated service tags"),
    price_min: int | None = Query(default=None, ge=0),
    price_max: int | None = Query(default=None, ge=0),
    available_date: date | None = Query(default=None, description="Required availability date"),
    open_now: bool | None = Query(default=None),
    sort: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    db: AsyncSession = Depends(get_session),
):
    # Map request filters to existing Meilisearch document structure
    body_tags = [tag.strip() for tag in (service_tags or "").split(",") if tag.strip()]
    filter_expr = build_filter(
        area,
        bust=None,
        service_type=category,
        body_tags=body_tags or None,
        today=open_now,
        price_min=price_min,
        price_max=price_max,
        status='published',
    )
    sort_expr = sort
    res = meili_search(
        q,
        filter_expr,
        sort_expr,
        page,
        page_size,
        facets=["area", "service_type", "body_tags", "today"],
    )
    hits = res.get("hits", [])
    results = [_doc_to_shop_summary(doc) for doc in hits]

    if available_date:
        results = await _filter_results_by_availability(db, results, available_date)

    response = ShopSearchResponse(
        page=page,
        page_size=page_size,
        total=len(results) if available_date else res.get("estimatedTotalHits", 0),
        results=results,
        facets=_build_facets(res.get("facetDistribution")),
    )
    return response.model_dump()


@router.get("/{shop_id}")
async def get_shop_detail(shop_id: UUID, db: AsyncSession = Depends(get_session)):
    profile = await db.get(models.Profile, shop_id)
    if not profile:
        raise HTTPException(status_code=404, detail="shop not found")

    contact_data = profile.contact_json if isinstance(profile.contact_json, dict) else {}
    contact = _hydrate_contact(contact_data)
    location = _hydrate_location(contact_data)

    lead_image = profile.photos[0] if profile.photos else None
    doc = build_profile_doc(profile)
    menus = _normalize_menus(contact_data.get("menus"), profile.id)
    staff_members = _normalize_staff(contact_data.get("staff"), profile.id)
    service_tags = contact_data.get("service_tags") if isinstance(contact_data.get("service_tags"), list) else profile.body_tags or []
    promotions = _normalize_promotions(profile.discounts or [], contact_data.get("promotions"))
    review_summary = _normalize_reviews(contact_data.get("reviews"))
    ranking_reason = contact_data.get("ranking_reason") or doc.get("ranking_reason")

    if review_summary.average_score is None:
        review_summary.average_score = _safe_float(doc.get("review_score"))
    if review_summary.review_count is None:
        review_summary.review_count = _safe_int(doc.get("review_count"))

    metadata = {"store_name": infer_store_name(profile)}
    if ranking_reason:
        metadata["ranking_reason"] = ranking_reason

    shop_summary = ShopDetail(
        id=profile.id,
        slug=None,
        name=profile.name,
        area=profile.area,
        area_name=profile.area,
        address=contact_data.get("address"),
        categories=[],
        service_tags=service_tags,
        min_price=profile.price_min,
        max_price=profile.price_max,
        rating=review_summary.average_score,
        review_count=review_summary.review_count,
        lead_image_url=lead_image,
        badges=profile.ranking_badges or [],
        today_available=doc.get("today", False),
        next_available_at=None,
        distance_km=None,
        online_reservation=True if contact and contact.reservation_form_url else None,
        updated_at=_unix_to_dt(doc.get("updated_at")),
        description=contact_data.get("description"),
        catch_copy=contact_data.get("catch_copy"),
        photos=[MediaImage(url=photo) for photo in (profile.photos or [])],
        contact=contact,
        location=location,
        menus=menus,
        staff=staff_members,
        availability_calendar=None,
        reviews=review_summary,
        promotions=promotions,
        ranking_reason=str(ranking_reason) if ranking_reason else None,
        metadata=metadata,
    )

    availability = await _fetch_availability(db, profile.id)
    if availability:
        shop_summary.availability_calendar = availability

    return shop_summary.model_dump()


@router.get("/{shop_id}/availability")
async def get_shop_availability(
    shop_id: UUID,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: AsyncSession = Depends(get_session),
):
    profile = await db.get(models.Profile, shop_id)
    if not profile:
        raise HTTPException(status_code=404, detail="shop not found")

    availability = await _fetch_availability(db, shop_id, start_date=date_from, end_date=date_to)
    if not availability:
        raise HTTPException(status_code=404, detail="availability not found")
    return availability.model_dump()
